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

/// Where Docker actually lives, for an app that has no useful PATH.
///
/// A window launched from Finder inherits launchd's environment, which on a
/// stock macOS is `/usr/bin:/bin:/usr/sbin:/sbin` — and Docker Desktop
/// installs its CLI at `/usr/local/bin/docker`. Relying on PATH meant that
/// double-clicking the app told someone who had Docker installed and running
/// to go and install Docker.
const DOCKER_CANDIDATES: &[&str] = &[
    "/usr/local/bin/docker",
    "/opt/homebrew/bin/docker",
    "/Applications/Docker.app/Contents/Resources/bin/docker",
    "/usr/bin/docker",
];

fn docker_program() -> PathBuf {
    if let Ok(configured) = std::env::var("NETZOO_DOCKER") {
        let path = PathBuf::from(configured);
        if path.is_file() {
            return path;
        }
    }
    // Docker Desktop 4.18+ also installs into the user's home.
    if let Some(home) = std::env::var_os("HOME") {
        let in_home = PathBuf::from(home).join(".docker/bin/docker");
        if in_home.is_file() {
            return in_home;
        }
    }
    for candidate in DOCKER_CANDIDATES {
        let path = PathBuf::from(candidate);
        if path.is_file() {
            return path;
        }
    }
    // Launched from a shell, PATH is usually enough.
    PathBuf::from("docker")
}

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
    let mut command = Command::new(docker_program());
    command.current_dir(root).args(args);
    if let Some(token) = token {
        command.env("NETZOO_DESKTOP_TOKEN", token);
    }
    command.output().map_err(|error| {
        if error.kind() == std::io::ErrorKind::NotFound {
            DaemonFault::new(
                "docker_missing",
                "Could not find the docker command.",
                "If Docker Desktop is installed, set NETZOO_DOCKER to the full path \
of its `docker` binary. Otherwise install Docker Desktop and reopen NetZoo Agent.",
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

#[derive(Debug, Serialize)]
pub struct EnvironmentCheck {
    pub key: String,
    pub label: String,
    pub status: String,
    pub detail: String,
    pub remedy: String,
}

fn check(key: &str, label: &str, status: &str, detail: &str, remedy: &str) -> EnvironmentCheck {
    EnvironmentCheck {
        key: key.into(),
        label: label.into(),
        status: status.into(),
        detail: detail.into(),
        remedy: remedy.into(),
    }
}

/// Fixed, read-only Docker queries. No token, shell, build, pull, or container mutation.
fn diagnostic_query(root: &Path, args: &[&str]) -> Result<String, String> {
    let mut child = Command::new(docker_program())
        .current_dir(root)
        .args(args)
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::null())
        .spawn()
        .map_err(|error| error.to_string())?;
    let deadline = std::time::Instant::now() + Duration::from_secs(8);
    loop {
        if let Some(status) = child.try_wait().map_err(|error| error.to_string())? {
            let output = child
                .wait_with_output()
                .map_err(|error| error.to_string())?;
            return if status.success() {
                Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
            } else {
                Err("Docker did not complete this check successfully.".into())
            };
        }
        if std::time::Instant::now() >= deadline {
            let _ = child.kill();
            let _ = child.wait();
            return Err("Docker check timed out after 8 seconds.".into());
        }
        std::thread::sleep(Duration::from_millis(50));
    }
}

pub fn environment_checks() -> Vec<EnvironmentCheck> {
    let root = match project_root() {
        Ok(root) => root,
        Err(error) => {
            return vec![check(
                "project",
                "Project configuration",
                "failed",
                &error.message,
                &error.remedy,
            )]
        }
    };
    let mut checks = vec![check(
        "project",
        "Project configuration",
        "passed",
        &root.display().to_string(),
        "",
    )];
    match diagnostic_query(&root, &["--version"]) {
        Ok(version) => checks.push(check(
            "docker_cli",
            "Docker command",
            "passed",
            &version,
            "",
        )),
        Err(error) => {
            checks.push(check("docker_cli", "Docker command", "failed", &error,
                "Install Docker Desktop, or set NETZOO_DOCKER to the full path of its docker binary."));
            return checks;
        }
    }
    match diagnostic_query(&root, &["info", "--format", "{{.ServerVersion}}"]) {
        Ok(version) => checks.push(check(
            "docker_engine",
            "Docker engine",
            "passed",
            &version,
            "",
        )),
        Err(error) => {
            checks.push(check(
                "docker_engine",
                "Docker engine",
                "failed",
                &error,
                "Start Docker Desktop and wait until the engine is ready, then check again.",
            ));
            checks.push(check(
                "image",
                "NetZoo image",
                "unknown",
                "Image cache cannot be checked while the engine is unavailable.",
                "",
            ));
            return checks;
        }
    }
    match diagnostic_query(&root, &["compose", "version", "--short"]) {
        Ok(version) => checks.push(check("compose", "Docker Compose", "passed", &version, "")),
        Err(error) => checks.push(check(
            "compose",
            "Docker Compose",
            "failed",
            &error,
            "Update Docker Desktop to include Docker Compose v2.",
        )),
    }
    // Resolve the image from the project's compose file, including local overrides.
    match diagnostic_query(&root, &["compose", "config", "--images", "netzoo-daemon"]) {
        Ok(images) if !images.is_empty() => {
            for image in images.lines().collect::<std::collections::BTreeSet<_>>() {
                match diagnostic_query(&root, &["image", "inspect", image, "--format", "{{.Id}}"] ) {
                    Ok(id) => checks.push(check("image", "NetZoo image", "passed", &format!("{image} · {id}"), "")),
                    Err(error) => checks.push(check("image", "NetZoo image", "failed", &format!("{image}: {error}"),
                        "Check the image with docker image inspect, then build it with docker compose build netzoo and restart the desktop app.")),
                }
            }
        }
        _ => checks.push(check("image", "NetZoo image", "unknown", "Could not resolve the daemon image from Docker Compose.",
            "Run docker compose config --images netzoo-daemon in the project directory to check the configuration.")),
    }
    checks
}

pub fn start(root: &Path, token: &str, port: u16) -> Result<(), DaemonFault> {
    engine_ready(root)?;
    let port_flag = port.to_string();
    let output = run_with_timeout(root, token, &port_flag)?;
    if output.status.success() {
        return Ok(());
    }
    let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
    let kind = if stderr.contains("address already in use")
        || stderr.contains("port is already allocated")
    {
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
    let mut command = Command::new(docker_program());
    command
        .current_dir(root)
        .args(["compose", "up", "-d", "netzoo-daemon"])
        .env("NETZOO_DESKTOP_TOKEN", token)
        .env("NETZOO_DAEMON_PORT", port)
        // The container sees the project as /work and cannot know what it is
        // called out here; a path shown to the user has to be findable.
        .env("NETZOO_HOST_PROJECT_ROOT", root);
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
    let _ = Command::new(docker_program())
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
        assert!(
            compose.contains("netzoo-daemon:"),
            "compose file has no daemon service"
        );
    }
}

#[cfg(test)]
mod path_tests {
    use super::*;

    #[test]
    fn docker_is_found_without_a_useful_path() {
        // A Finder-launched app has launchd's PATH, which does not include
        // /usr/local/bin, so resolution must not depend on PATH at all.
        let program = docker_program();
        assert!(
            program.is_absolute() || program == PathBuf::from("docker"),
            "unexpected docker program: {program:?}"
        );
        if DOCKER_CANDIDATES.iter().any(|c| PathBuf::from(c).is_file()) {
            assert!(
                program.is_file(),
                "an installed docker must resolve to a file"
            );
        }
    }

    #[test]
    fn an_explicit_override_wins_when_it_exists() {
        let previous = std::env::var("NETZOO_DOCKER").ok();
        std::env::set_var("NETZOO_DOCKER", "/definitely/not/here/docker");
        let ignored = docker_program();
        std::env::set_var("NETZOO_DOCKER", "/bin/sh");
        let honoured = docker_program();
        match previous {
            Some(value) => std::env::set_var("NETZOO_DOCKER", value),
            None => std::env::remove_var("NETZOO_DOCKER"),
        }

        assert_ne!(ignored, PathBuf::from("/definitely/not/here/docker"));
        assert_eq!(honoured, PathBuf::from("/bin/sh"));
    }
}

#[cfg(all(test, unix))]
mod diagnostic_tests {
    use super::*;
    use std::os::unix::fs::PermissionsExt;

    #[test]
    fn diagnostics_only_inspect_and_resolve_the_compose_image() {
        let directory =
            std::env::temp_dir().join(format!("netzoo-diagnostics-{}", uuid::Uuid::new_v4()));
        std::fs::create_dir(&directory).unwrap();
        let binary = directory.join("docker");
        let log = directory.join("commands.log");
        std::fs::write(&binary, format!(
            "#!/bin/sh\nprintf '%s\\n' \"$*\" >> '{}'\ncase \"$1 $2\" in\n  'compose config') printf 'custom-netzoo:science\\n' ;;\n  'image inspect') printf 'sha256:test\\n' ;;\n  *) printf 'test-version\\n' ;;\nesac\n", log.display()
        )).unwrap();
        std::fs::set_permissions(&binary, std::fs::Permissions::from_mode(0o755)).unwrap();
        let previous = std::env::var_os("NETZOO_DOCKER");
        std::env::set_var("NETZOO_DOCKER", &binary);
        let checks = environment_checks();
        match previous {
            Some(value) => std::env::set_var("NETZOO_DOCKER", value),
            None => std::env::remove_var("NETZOO_DOCKER"),
        }
        let commands = std::fs::read_to_string(&log).unwrap();
        assert!(checks.iter().all(|check| check.status == "passed"));
        assert!(commands.contains("image inspect custom-netzoo:science --format {{.Id}}"));
        assert!(
            !commands.contains(" up ") && !commands.contains("build") && !commands.contains("pull")
        );
        std::fs::remove_dir_all(directory).unwrap();
    }
}
