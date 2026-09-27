//! The shell: one window, one daemon container, one secret.
//!
//! The token is generated here and never written to disk or to `.env`. The
//! renderer receives it over IPC because it needs it for the WebSocket, but
//! nothing outside this process ever sees it, and a new one is minted every
//! launch.

mod docker;

use std::sync::Mutex;

use serde::Serialize;
use tauri::{Manager, State};

const DEFAULT_PORT: u16 = 8765;

struct Daemon {
    token: String,
    port: u16,
    root: Mutex<Option<std::path::PathBuf>>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct DaemonConfig {
    token: String,
    port: u16,
    base_url: String,
    socket_url: String,
}

#[tauri::command]
fn daemon_config(daemon: State<'_, Daemon>) -> DaemonConfig {
    DaemonConfig {
        token: daemon.token.clone(),
        port: daemon.port,
        base_url: format!("http://127.0.0.1:{}", daemon.port),
        socket_url: format!("ws://127.0.0.1:{}", daemon.port),
    }
}

#[tauri::command]
fn start_daemon(daemon: State<'_, Daemon>) -> Result<(), docker::DaemonFault> {
    let root = docker::project_root()?;
    docker::start(&root, &daemon.token, daemon.port)?;
    *daemon.root.lock().expect("daemon root lock") = Some(root);
    Ok(())
}

#[tauri::command]
fn stop_daemon(daemon: State<'_, Daemon>) {
    let root = daemon.root.lock().expect("daemon root lock").clone();
    if let Some(root) = root {
        docker::stop(&root);
    }
}

#[tauri::command]
async fn check_environment() -> Result<Vec<docker::EnvironmentCheck>, String> {
    tauri::async_runtime::spawn_blocking(docker::environment_checks)
        .await
        .map_err(|error| error.to_string())
}

/// Open a web destination in the system browser, never in the privileged webview.
#[tauri::command]
fn open_external_url(url: String) -> Result<(), String> {
    if !(url.starts_with("https://") || url.starts_with("http://"))
        || url.chars().any(char::is_control)
    {
        return Err("Only HTTP and HTTPS links can be opened.".into());
    }
    #[cfg(target_os = "macos")]
    let result = std::process::Command::new("/usr/bin/open")
        .arg(&url)
        .status();
    #[cfg(target_os = "linux")]
    let result = std::process::Command::new("xdg-open").arg(&url).status();
    #[cfg(target_os = "windows")]
    let result = std::process::Command::new("rundll32.exe")
        .args(["url.dll,FileProtocolHandler", &url])
        .status();
    result
        .map_err(|error| error.to_string())
        .and_then(|status| {
            if status.success() {
                Ok(())
            } else {
                Err("The system browser could not open this link.".into())
            }
        })
}

#[tauri::command]
fn export_run_log(contents: String, format: String) -> Result<String, String> {
    use std::io::Write;
    if !matches!(format.as_str(), "txt" | "json") || contents.len() > 20_000_000 {
        return Err(
            "Logs must be text or JSON and smaller than 20 MB. Filter the log before exporting."
                .into(),
        );
    }
    let home = std::env::var_os("HOME")
        .or_else(|| std::env::var_os("USERPROFILE"))
        .ok_or("Could not find your Downloads directory.")?;
    let directory = std::path::PathBuf::from(home).join("Downloads");
    if !directory.is_dir() {
        return Err("Your Downloads directory is unavailable. Use Copy matches instead.".into());
    }
    let path = directory.join(format!(
        "netzoo-run-{}.{}",
        uuid::Uuid::new_v4().simple(),
        format
    ));
    let mut file = std::fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&path)
        .map_err(|error| error.to_string())?;
    file.write_all(contents.as_bytes())
        .map_err(|error| error.to_string())?;
    Ok(format!("Saved to {}", path.display()))
}

fn mint_token() -> String {
    format!(
        "{}{}",
        uuid::Uuid::new_v4().simple(),
        uuid::Uuid::new_v4().simple()
    )
}

fn configured_port() -> u16 {
    std::env::var("NETZOO_DAEMON_PORT")
        .ok()
        .and_then(|value| value.parse().ok())
        .unwrap_or(DEFAULT_PORT)
}

fn shutdown_daemon(handle: &tauri::AppHandle) {
    let daemon = handle.state::<Daemon>();
    let root = daemon.root.lock().expect("daemon root lock").clone();
    if let Some(root) = root {
        docker::stop(&root);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn external_links_reject_local_files_and_control_characters() {
        for url in [
            "file:///etc/passwd",
            "javascript:alert(1)",
            "https://example.com\n--arg",
        ] {
            assert!(open_external_url(url.into()).is_err());
        }
    }

    #[test]
    fn log_exports_reject_other_formats_and_oversized_content() {
        assert!(export_run_log("test".into(), "sh".into()).is_err());
        assert!(export_run_log("x".repeat(20_000_001), "txt".into()).is_err());
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(Daemon {
            token: mint_token(),
            port: configured_port(),
            root: Mutex::new(None),
        })
        .invoke_handler(tauri::generate_handler![
            daemon_config,
            start_daemon,
            stop_daemon,
            check_environment,
            open_external_url,
            export_run_log
        ])
        .setup(|app| {
            // Without an application menu, macOS never delivers Cmd-C/V/X or
            // Cmd-A to the webview, so the task box cannot be pasted into.
            // Pasting a file path is the ordinary way to answer this agent.
            app.set_menu(tauri::menu::Menu::default(app.handle())?)?;
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("failed to start the NetZoo Agent window")
        .run(|handle, event| {
            // The container has to be stopped from the event loop, not from a
            // window event: quitting the app on macOS (Cmd-Q, the Dock, an
            // Apple Event) tears the process down without ever emitting
            // WindowEvent::Destroyed, which left the daemon running.
            if matches!(event, tauri::RunEvent::Exit) {
                shutdown_daemon(handle);
            }
        });
}
