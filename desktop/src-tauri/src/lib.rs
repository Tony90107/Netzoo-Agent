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
            stop_daemon
        ])
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
