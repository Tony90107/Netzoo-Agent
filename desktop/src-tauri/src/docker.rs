//! Owning the daemon container's lifetime.
//!
//! The shell runs `docker compose` itself, through `std::process::Command`,
//! rather than exposing a shell plugin to the webview. The renderer can ask
//! for "start the daemon" and nothing else; it cannot name a command.
//!
//! Most of this file is about telling the three failure modes apart. "Cannot
//! connect" is useless to someone whose Docker Desktop simply is not running,
//! so each case carries the one action that fixes it.

use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::time::Duration;

use serde::Serialize;

/// How long a compose invocation may take before we stop waiting on it.
const COMPOSE_TIMEOUT: Duration = Duration::from_secs(120);

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct DaemonFault {
    /// Machine-readable so the UI can choose a retry affordance.
    pub kind: &'static str,
    pub message: String,
    pub remedy: String,
    pub detail: String,
}

impl DaemonFault {
    fn new(kind: &'static str, message: &str, remedy: &str, detail: String) -> Self {
        Self {
            kind,
            message: message.to_string(),
            remedy: remedy.to_string(),
            detail,
        }
    }
}

/// Where the compose file lives, relative to the running binary or the repo.
pub fn project_root() -> Result<PathBuf, DaemonFault> {
    if let Ok(configured) = std::env::var("NETZOO_PROJECT_ROOT") {
        let path = PathBuf::from(configured);
        if path.join("docker-compose.yml").is_file() {
            return Ok(path);
        }
    }
    // `cargo tauri dev` runs from src-tauri; a bundled app runs from anywhere,
    // so walk up looking for the compose file that defines the daemon.
    let mut candidates: Vec<PathBuf> = Vec::new();
    if let Ok(current) = std::env::current_dir() {
        candidates.push(current);
    }
    if let Ok(exe) = std::env::current_exe() {
        candidates.extend(exe.ancestors().map(Path::to_path_buf));
    }
    for candidate in candidates {
        for ancestor in candidate.ancestors() {
            if ancestor.join("docker-compose.yml").is_file() {
                return Ok(ancestor.to_path_buf());
            }
        }
    }
    Err(DaemonFault::new(
        "project_not_found",
        "Cannot find the NetZoo project.",
        "Set NETZOO_PROJECT_ROOT to the directory that holds docker-compose.yml.",
        String::new(),
    ))
}

fn run(root: &Path, args: &[&str], token: Option<&str>) -> Result<Output, DaemonFault> {
    let mut command = Command::new("docker");
    command.current_dir(root).args(args);
    if let Some(token) = token {
        command.env("NETZOO_DESKTOP_TOKEN", token);
    }
    command.output().map_err(|error| {
        if error.kind() == std::io::ErrorKind::NotFound {
            DaemonFault::new(
                "docker_missing",
                "Docker is not installed, or is not on this app's PATH.",
                "Install Docker Desktop, then reopen NetZoo Agent.",
                error.to_string(),
            )
        } else {
            DaemonFault::new(
                "docker_unavailable",
                "Could not run the docker command.",
                "Check that Docker Desktop is installed and you can run `docker ps` in a terminal.",
                error.to_string(),
            )
        }
    })
}

/// Is the Docker engine reachable at all?  Checked separately so that the most
/// common failure gets its own message instead of a compose stack trace.
pub fn engine_ready(root: &Path) -> Result<(), DaemonFault> {
    let output = run(root, &["info", "--format", "{{.ServerVersion}}"], None)?;
    if output.status.success() {
        return Ok(());
    }
    Err(DaemonFault::new(
        "docker_not_running",
        "Docker Desktop is not running.",
        "Start Docker Desktop, wait for the whale icon to stop animating, then press Retry.",
        String::from_utf8_lossy(&output.stderr).trim().to_string(),
    ))
}

pub fn start(root: &Path, token: &str, port: u16) -> Result<(), DaemonFault> {
    engine_ready(root)?;
    let port_flag = port.to_string();
    let output = run_with_timeout(root, token, &port_flag)?;
    if output.status.success() {
        return Ok(());
    }
    let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
    let kind = if stderr.contains("address already in use") || stderr.contains("port is already allocated") {
        "port_in_use"
    } else if stderr.contains("pull access denied") || stderr.contains("not found") {
        "image_missing"
    } else {
        "compose_failed"
    };
    let remedy = match kind {
        "port_in_use" => format!(
            "Something else is already listening on port {port}. Close it, or set NETZOO_DAEMON_PORT to a free port."
        ),
        "image_missing" => {
            "Build the image first: docker compose build netzoo".to_string()
        }
        _ => "Run `docker compose up netzoo-daemon` in a terminal to see the full output.".to_string(),
    };
    Err(DaemonFault::new(
        kind,
        "The NetZoo daemon container did not start.",
        &remedy,
        stderr,
    ))
}

fn run_with_timeout(root: &Path, token: &str, port: &str) -> Result<Output, DaemonFault> {
    // `docker compose up -d` returns once the container is created; the image
    // build it may trigger is what can take minutes, hence the generous cap.
    let mut command = Command::new("docker");
    command
        .current_dir(root)
        .args(["compose", "up", "-d", "netzoo-daemon"])
        .env("NETZOO_DESKTOP_TOKEN", token)
        .env("NETZOO_DAEMON_PORT", port);
    let mut child = command
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::piped())
        .spawn()
        .map_err(|error| {
            DaemonFault::new(
                "docker_unavailable",
                "Could not run docker compose.",
                "Check that Docker Desktop is installed and running.",
                error.to_string(),
            )
        })?;
    let deadline = std::time::Instant::now() + COMPOSE_TIMEOUT;
    loop {
        if child.try_wait().ok().flatten().is_some() {
            return child.wait_with_output().map_err(|error| {
                DaemonFault::new(
                    "compose_failed",
                    "Could not read the result of docker compose.",
                    "Run `docker compose up netzoo-daemon` in a terminal.",
                    error.to_string(),
                )
            });
        }
        if std::time::Instant::now() > deadline {
            let _ = child.kill();
            return Err(DaemonFault::new(
                "compose_timeout",
                "Starting the daemon container timed out.",
                "The first launch may need to build the image. Run `docker compose build netzoo` once, then reopen the app.",
                String::new(),
            ));
        }
        std::thread::sleep(Duration::from_millis(120));
    }
}

pub fn stop(root: &Path) {
    // Best effort: the app is closing either way, and leaving a stopped
    // container behind is better than blocking quit on Docker.
    let _ = Command::new("docker")
        .current_dir(root)
        .args(["compose", "stop", "netzoo-daemon"])
        .output();
}

#[cfg(test)]
mod tests {
    use super::*;

    /// These touch the real `docker` binary and the process environment, so
    /// they are written to run one at a time (`--test-threads=1`).
    #[test]
    fn an_unreachable_engine_is_reported_as_docker_not_running() {
        let root = project_root().expect("the repo must contain docker-compose.yml");
        let previous = std::env::var("DOCKER_HOST").ok();
        std::env::set_var("DOCKER_HOST", "unix:///tmp/netzoo-no-such-docker.sock");

        let fault = engine_ready(&root).expect_err("a dead socket must not look healthy");

        match previous {
            Some(value) => std::env::set_var("DOCKER_HOST", value),
            None => std::env::remove_var("DOCKER_HOST"),
        }

        assert_eq!(fault.kind, "docker_not_running");
        // The remedy is the point of the whole error type: it has to name the
        // one action that fixes it.
        assert!(fault.remedy.contains("Start Docker Desktop"), "{fault:?}");
    }

    #[test]
    fn the_project_root_is_the_directory_holding_the_compose_file() {
        let root = project_root().expect("the repo must contain docker-compose.yml");
        assert!(root.join("docker-compose.yml").is_file());
        // The daemon service must be the one the shell starts.
        let compose = std::fs::read_to_string(root.join("docker-compose.yml")).unwrap();
        assert!(compose.contains("netzoo-daemon:"), "compose file has no daemon service");
    }
}
