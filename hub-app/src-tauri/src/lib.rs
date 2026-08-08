use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use chrono::Local;
use serde::{Deserialize, Serialize};
use tauri::{AppHandle, Emitter};

const CONFIG_PATH: &str = "C:\\Users\\arijd\\Documents\\Atlas\\HUB\\config.json";

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Participant {
    pub id: String,
    pub name: String,
    pub avatar: String,
    pub color: String,
    pub role: String,
    pub online: bool,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct HubConfig {
    pub hub_path: String,
    pub participants: Vec<Participant>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Message {
    pub id: String,
    pub date: String,
    pub author: String,
    pub role: String,
    pub content: String,
    pub file_path: String,
    pub parent: Option<String>,
    pub project: Option<String>,
}

fn read_hub_path_from_config() -> Result<String, String> {
    if !Path::new(CONFIG_PATH).exists() {
        return Ok("C:\\Users\\arijd\\Documents\\Atlas\\HUB".to_string());
    }
    let content = fs::read_to_string(CONFIG_PATH).map_err(|e| e.to_string())?;
    let json: serde_json::Value = serde_json::from_str(&content).map_err(|e| e.to_string())?;
    if let Some(path) = json.get("hub_path").and_then(|v| v.as_str()) {
        Ok(path.to_string())
    } else {
        Ok("C:\\Users\\arijd\\Documents\\Atlas\\HUB".to_string())
    }
}

#[tauri::command]
fn get_hub_path() -> Result<String, String> {
    read_hub_path_from_config()
}

#[tauri::command]
fn set_hub_path(path: String) -> Result<(), String> {
    let mut config = if Path::new(CONFIG_PATH).exists() {
        let content = fs::read_to_string(CONFIG_PATH).map_err(|e| e.to_string())?;
        serde_json::from_str::<HubConfig>(&content).unwrap_or_else(|_| HubConfig {
            hub_path: "C:\\Users\\arijd\\Documents\\Atlas\\HUB".to_string(),
            participants: vec![],
        })
    } else {
        HubConfig {
            hub_path: "C:\\Users\\arijd\\Documents\\Atlas\\HUB".to_string(),
            participants: vec![],
        }
    };

    config.hub_path = path;
    
    // Ensure parent directories exist
    if let Some(parent) = Path::new(CONFIG_PATH).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let serialized = serde_json::to_string_pretty(&config).map_err(|e| e.to_string())?;
    fs::write(CONFIG_PATH, serialized).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn read_config() -> Result<HubConfig, String> {
    if !Path::new(CONFIG_PATH).exists() {
        // Return default configuration
        return Ok(HubConfig {
            hub_path: "C:\\Users\\arijd\\Documents\\Atlas\\HUB".to_string(),
            participants: vec![
                Participant {
                    id: "arijd".to_string(),
                    name: "arijd".to_string(),
                    avatar: "A".to_string(),
                    color: "#ff5e5b".to_string(),
                    role: "humano".to_string(),
                    online: true,
                },
                Participant {
                    id: "Norte".to_string(),
                    name: "Norte".to_string(),
                    avatar: "N".to_string(),
                    color: "#00cecb".to_string(),
                    role: "agente".to_string(),
                    online: true,
                },
                Participant {
                    id: "Windows".to_string(),
                    name: "[Windows]".to_string(),
                    avatar: "W".to_string(),
                    color: "#ffed66".to_string(),
                    role: "sistema".to_string(),
                    online: true,
                },
                Participant {
                    id: "Antigravity".to_string(),
                    name: "Antigravity".to_string(),
                    avatar: "AG".to_string(),
                    color: "#845ec2".to_string(),
                    role: "agente".to_string(),
                    online: true,
                },
            ],
        });
    }
    let content = fs::read_to_string(CONFIG_PATH).map_err(|e| e.to_string())?;
    let config: HubConfig = serde_json::from_str(&content).map_err(|e| e.to_string())?;
    Ok(config)
}

#[tauri::command]
fn write_config(config: HubConfig) -> Result<(), String> {
    if let Some(parent) = Path::new(CONFIG_PATH).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let serialized = serde_json::to_string_pretty(&config).map_err(|e| e.to_string())?;
    fs::write(CONFIG_PATH, serialized).map_err(|e| e.to_string())?;
    Ok(())
}

fn parse_markdown_with_frontmatter(content: &str) -> (HashMap<String, String>, String) {
    let mut frontmatter = HashMap::new();
    let body;

    if content.starts_with("---") {
        let parts: Vec<&str> = content.split("---").collect();
        if parts.len() >= 3 {
            let yaml_block = parts[1];
            body = parts[2..].join("---");

            for line in yaml_block.lines() {
                let line = line.trim();
                if line.is_empty() {
                    continue;
                }
                if let Some((key, val)) = line.split_once(':') {
                    frontmatter.insert(
                        key.trim().to_lowercase(),
                        val.trim().trim_matches('"').trim_matches('\'').to_string(),
                    );
                }
            }
        } else {
            body = content.to_string();
        }
    } else {
        body = content.to_string();
    }

    (frontmatter, body.trim().to_string())
}

#[tauri::command]
fn load_messages() -> Result<Vec<Message>, String> {
    let hub_path_str = read_hub_path_from_config()?;
    let hub_dir = PathBuf::from(hub_path_str);

    let mut messages = Vec::new();
    let folders = vec![("briefs", "humano"), ("consensos", "agente")];

    for (folder_name, default_role) in folders {
        let dir_path = hub_dir.join(folder_name);
        if !dir_path.exists() {
            continue;
        }

        let entries = fs::read_dir(dir_path).map_err(|e| e.to_string())?;
        for entry in entries.filter_map(Result::ok) {
            let path = entry.path();
            if path.is_file() && path.extension().map_or(false, |ext| ext == "md") {
                let content = fs::read_to_string(&path).unwrap_or_default();
                let file_name = path.file_name().unwrap_or_default().to_string_lossy().to_string();
                let (frontmatter, body) = parse_markdown_with_frontmatter(&content);

                let date = frontmatter.get("date").cloned().unwrap_or_else(|| {
                    if let Ok(metadata) = entry.metadata() {
                        if let Ok(modified) = metadata.modified() {
                            let datetime: chrono::DateTime<Local> = modified.into();
                            datetime.to_rfc3339()
                        } else {
                            Local::now().to_rfc3339()
                        }
                    } else {
                        Local::now().to_rfc3339()
                    }
                });

                let author = frontmatter.get("author").cloned().unwrap_or_else(|| {
                    file_name.split('_').nth(1).unwrap_or("Desconocido").to_string()
                });

                let role = frontmatter.get("role").cloned().unwrap_or_else(|| default_role.to_string());
                
                let parent = frontmatter.get("parent").cloned();
                let project = frontmatter.get("project").cloned();

                messages.push(Message {
                    id: file_name,
                    date,
                    author,
                    role,
                    content: body,
                    file_path: path.to_string_lossy().to_string(),
                    parent,
                    project,
                });
            }
        }
    }

    // Sort by date (RFC3339 strings can be sorted lexicographically)
    messages.sort_by(|a, b| a.date.cmp(&b.date));

    Ok(messages)
}

#[tauri::command]
fn send_message(
    sender: String,
    content: String,
    parent: Option<String>,
    project: Option<String>,
) -> Result<(), String> {
    let hub_path_str = read_hub_path_from_config()?;
    let hub_dir = PathBuf::from(hub_path_str);

    // Read config to find sender's role
    let config = read_config().unwrap_or_else(|_| HubConfig {
        hub_path: "C:\\Users\\arijd\\Documents\\Atlas\\HUB".to_string(),
        participants: vec![],
    });

    let participant = config.participants.iter().find(|p| p.name == sender || p.id == sender);
    let role = participant.map(|p| p.role.as_str()).unwrap_or("agente");

    let folder_name = if role == "humano" { "briefs" } else { "consensos" };
    let folder_dir = hub_dir.join(folder_name);
    fs::create_dir_all(&folder_dir).map_err(|e| e.to_string())?;

    let now = Local::now();
    let file_suffix = now.format("%Y%m%d_%H%M%S").to_string();
    let prefix = if role == "humano" { "brief" } else { "consens" };
    let file_name = format!("{}_{}.md", prefix, file_suffix);
    let file_path = folder_dir.join(file_name);

    let date_str = now.to_rfc3339();
    
    let mut frontmatter = format!(
        "---\ndate: {}\nauthor: {}\nrole: {}\n",
        date_str, sender, role
    );
    if let Some(ref p) = parent {
        frontmatter.push_str(&format!("parent: {}\n", p));
    }
    if let Some(ref prj) = project {
        frontmatter.push_str(&format!("project: {}\n", prj));
    }
    frontmatter.push_str("---\n");

    let markdown_content = format!("{}{}\n", frontmatter, content);

    fs::write(file_path, markdown_content).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn receive_message(
    app_handle: AppHandle,
    receiver: String,
    content: String,
    parent: Option<String>,
    project: Option<String>,
) -> Result<(), String> {
    let hub_path_str = read_hub_path_from_config()?;
    let hub_dir = PathBuf::from(hub_path_str);

    let folder_dir = hub_dir.join("consensos");
    fs::create_dir_all(&folder_dir).map_err(|e| e.to_string())?;

    let now = Local::now();
    let file_suffix = now.format("%Y%m%d_%H%M%S").to_string();
    let file_name = format!("consens_{}_{}.md", receiver, file_suffix);
    let file_path = folder_dir.join(file_name);

    let date_str = now.to_rfc3339();
    
    let mut frontmatter = format!(
        "---\ndate: {}\nauthor: {}\nrole: agente\n",
        date_str, receiver
    );
    if let Some(ref p) = parent {
        frontmatter.push_str(&format!("parent: {}\n", p));
    }
    if let Some(ref prj) = project {
        frontmatter.push_str(&format!("project: {}\n", prj));
    }
    frontmatter.push_str("---\n");

    let markdown_content = format!("{}{}\n", frontmatter, content);

    fs::write(file_path, markdown_content).map_err(|e| e.to_string())?;

    // Emit event to notify frontend
    let _ = app_handle.emit("hub-update", ());
    Ok(())
}

#[tauri::command]
fn set_status(app_handle: AppHandle, agent_id: String, online: bool) -> Result<(), String> {
    let mut config = read_config()?;
    if let Some(participant) = config.participants.iter_mut().find(|p| p.id == agent_id) {
        participant.online = online;
        write_config(config)?;
        let _ = app_handle.emit("hub-update", ());
        Ok(())
    } else {
        Err(format!("Participant with id '{}' not found", agent_id))
    }
}

#[tauri::command]
fn invoke_engine(
    app_handle: AppHandle,
    prompt: String,
    parent: Option<String>,
    project: Option<String>,
) -> Result<String, String> {
    // Stub implementation: returns processed prompt
    let response = format!(
        "Procesado por el motor Antigravity:\n\nRecibí tu prompt: \"{}\"\n\n*(Este es un stub de orquestación. Aquí se puede conectar la llamada a la API de Antigravity real)*",
        prompt
    );
    
    let hub_path_str = read_hub_path_from_config()?;
    let hub_dir = PathBuf::from(hub_path_str);
    let folder_dir = hub_dir.join("consensos");
    fs::create_dir_all(&folder_dir).map_err(|e| e.to_string())?;

    let now = Local::now();
    let file_suffix = now.format("%Y%m%d_%H%M%S").to_string();
    let file_name = format!("consens_Antigravity_{}.md", file_suffix);
    let file_path = folder_dir.join(file_name);

    let date_str = now.to_rfc3339();
    
    let mut frontmatter = format!(
        "---\ndate: {}\nauthor: Antigravity\nrole: agente\n",
        date_str
    );
    if let Some(ref p) = parent {
        frontmatter.push_str(&format!("parent: {}\n", p));
    }
    if let Some(ref prj) = project {
        frontmatter.push_str(&format!("project: {}\n", prj));
    }
    frontmatter.push_str("---\n");

    let markdown_content = format!("{}{}\n", frontmatter, response);

    fs::write(file_path, markdown_content).map_err(|e| e.to_string())?;

    // Emit event to notify frontend
    let _ = app_handle.emit("hub-update", ());
    Ok(response)
}

fn spawn_watcher(app_handle: AppHandle) {
    std::thread::spawn(move || {
        let mut last_state = HashMap::new();

        loop {
            std::thread::sleep(std::time::Duration::from_millis(1000));

            let hub_dir = match read_hub_path_from_config() {
                Ok(path) => PathBuf::from(path),
                Err(_) => PathBuf::from("C:\\Users\\arijd\\Documents\\Atlas\\HUB"),
            };

            let mut current_state = HashMap::new();

            // Scan briefs
            let briefs_dir = hub_dir.join("briefs");
            if let Ok(entries) = fs::read_dir(&briefs_dir) {
                for entry in entries.filter_map(Result::ok) {
                    let path = entry.path();
                    if path.is_file() && path.extension().map_or(false, |ext| ext == "md") {
                        if let Ok(metadata) = entry.metadata() {
                            if let Ok(modified) = metadata.modified() {
                                current_state.insert(path, modified);
                            }
                        }
                    }
                }
            }

            // Scan consensos
            let consensos_dir = hub_dir.join("consensos");
            if let Ok(entries) = fs::read_dir(&consensos_dir) {
                for entry in entries.filter_map(Result::ok) {
                    let path = entry.path();
                    if path.is_file() && path.extension().map_or(false, |ext| ext == "md") {
                        if let Ok(metadata) = entry.metadata() {
                            if let Ok(modified) = metadata.modified() {
                                current_state.insert(path, modified);
                            }
                        }
                    }
                }
            }

            // Scan config.json
            if let Ok(metadata) = fs::metadata(CONFIG_PATH) {
                if let Ok(modified) = metadata.modified() {
                    current_state.insert(PathBuf::from(CONFIG_PATH), modified);
                }
            }

            if !last_state.is_empty() && current_state != last_state {
                let _ = app_handle.emit("hub-update", ());
            }

            last_state = current_state;
        }
    });
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .setup(|app| {
            let app_handle = app.handle().clone();
            spawn_watcher(app_handle);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_hub_path,
            set_hub_path,
            read_config,
            write_config,
            load_messages,
            send_message,
            receive_message,
            set_status,
            invoke_engine
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
