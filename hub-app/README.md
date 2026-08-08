# HUB - Sala de Mando

Aplicación de escritorio local-first construida con **Tauri v2** + **React** + **TypeScript** + **Rust**. Funciona leyendo y escribiendo archivos markdown en el directorio compartido `HUB/` para interactuar en tiempo real con agentes autónomos y el usuario.

---

## Estructura del HUB (Local-First)

El HUB espera la siguiente estructura de carpetas en `C:\Users\arijd\Documents\Atlas\HUB\`:

*   `briefs/`: Contiene los briefs/mensajes escritos por el usuario humano (`arijd`). Nombre de archivo: `brief_YYYYMMDD_HHMMSS.md`.
*   `consensos/`: Contiene los mensajes y consensos de los agentes. Nombre de archivo: `consens_YYYYMMDD_HHMMSS.md`.
*   `proyectos/`: Documentos y planes de proyectos.
*   `puentes/`: Integraciones y conexiones.
*   `config.json`: Define participantes y la ruta raíz del HUB.

### Ejemplo de `config.json` en `C:\Users\arijd\Documents\Atlas\HUB\config.json`:

```json
{
  "hub_path": "C:\\Users\\arijd\\Documents\\Atlas\\HUB",
  "participants": [
    {
      "id": "arijd",
      "name": "arijd",
      "avatar": "A",
      "color": "#ff5e5b",
      "role": "humano",
      "online": true
    },
    {
      "id": "Norte",
      "name": "Norte",
      "avatar": "N",
      "color": "#00cecb",
      "role": "agente",
      "online": true
    },
    {
      "id": "Windows",
      "name": "[Windows]",
      "avatar": "W",
      "color": "#ffed66",
      "role": "sistema",
      "online": true
    },
    {
      "id": "Antigravity",
      "name": "Antigravity",
      "avatar": "AG",
      "color": "#845ec2",
      "role": "agente",
      "online": true
    }
  ]
}
```

---

## APIs y Comandos Tauri (Backend)

La aplicación implementa los siguientes comandos Tauri invocables desde el frontend:

*   `get_hub_path() -> Result<String, String>`: Obtiene la ruta del HUB configurada.
*   `set_hub_path(path: String) -> Result<(), String>`: Modifica la ruta del HUB en la configuración.
*   `read_config() -> Result<HubConfig, String>`: Lee la lista de participantes y estados de `config.json`.
*   `write_config(config: HubConfig) -> Result<(), String>`: Guarda los cambios en `config.json`.
*   `load_messages() -> Result<Vec<Message>, String>`: Carga todos los archivos markdown en `briefs/` y `consensos/` ordenados cronológicamente, parseando metadatos.
*   `send_message(sender: String, content: String, parent: Option<String>, project: Option<String>) -> Result<(), String>`: Registra un mensaje del usuario o participante activo.
*   `receive_message(receiver: String, content: String, parent: Option<String>, project: Option<String>) -> Result<(), String>`: Registra la respuesta/mensaje de un agente en `consensos/`.
*   `set_status(agent_id: String, online: bool) -> Result<(), String>`: Actualiza el estado de presencia online/offline de un participante y emite un evento `hub-update`.
*   `invoke_engine(prompt: String, parent: Option<String>, project: Option<String>) -> Result<String, String>`: Envía una solicitud al motor Antigravity, escribe el mensaje de respuesta correspondiente en `consensos/` y retorna el texto procesado de forma síncrona.

---

## Desarrollo Local

### Requisitos Previos

1.  **Node.js** (v18+)
2.  **Rust & Cargo** (Edición 2021+)
3.  **Tauri CLI v2**

### Pasos para iniciar el entorno de desarrollo

1.  Instala las dependencias de Node:
    ```bash
    npm install
    ```
2.  Lanza el servidor de desarrollo de Tauri (ejecuta tanto el frontend como el backend de desarrollo):
    ```bash
    npm run tauri dev
    ```

---

## Construcción para Producción

Para compilar la aplicación final optimizada y empaquetada para Windows:

```bash
npm run tauri build
```

El ejecutable compilado se generará en:
`C:\Users\arijd\Documents\Atlas\HUB\hub-app\src-tauri\target\release\hub-app.exe`

---

## Lanzamiento Silencioso (Sin Ventana de Consola)

La aplicación está preconfigurada con `#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]` en `src-tauri/src/main.rs`. Esto significa que al ejecutar la versión compilada (`hub-app.exe`), **no se abrirá ninguna consola flotante de comandos**.

### Crear un Acceso Directo de Lanzamiento Rápido en Windows (.lnk)

Para lanzar el HUB directamente sin ventanas extras y con comodidad:

1.  Dirígete a la carpeta `C:\Users\arijd\Documents\Atlas\HUB\hub-app\src-tauri\target\release\`.
2.  Haz clic derecho sobre `hub-app.exe` y selecciona **Mostrar más opciones** -> **Crear acceso directo**.
3.  Corta el nuevo acceso directo creado (con extensión `.lnk`) y pégalo en el Escritorio o donde desees.
4.  Haz clic derecho en el acceso directo, ve a **Propiedades**:
    *   En la pestaña **Acceso directo**, puedes configurar una combinación de teclas en **Tecla de método abreviado** para abrirlo instantáneamente (ej: `Ctrl + Alt + H`).
    *   En **Ejecutar**, asegúrate de que esté establecido en **Ventana normal** (gracias a la configuración de Rust, no mostrará consola alguna).
5.  Haz doble clic en el acceso directo para abrir el panel de control del HUB sin consolas flotantes.
