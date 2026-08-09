import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { HubConfig, Message } from "./types";
import { Sidebar } from "./components/Sidebar";
import { MessagePanel } from "./components/MessagePanel";
import { ChatInput } from "./components/ChatInput";
import "./App.css";

function App() {
  const [config, setConfig] = useState<HubConfig | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [activeUserId, setActiveUserId] = useState<string>("arijd");
  const [hubPath, setHubPath] = useState<string>("C:\\Users\\arijd\\Documents\\Atlas\\10-Projects\\hub-atlas");
  const [replyToMessageId, setReplyToMessageId] = useState<string | null>(null);
  
  // Real-time hub state
  const [isPanic, setIsPanic] = useState<boolean>(false);
  const [activeLocks, setActiveLocks] = useState<string[]>([]);
  const [dispatchLogs, setDispatchLogs] = useState<string>("");
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);
  const [isRunningDispatcher, setIsRunningDispatcher] = useState<boolean>(false);

  const loadAllData = async () => {
    try {
      // 1. Read config
      const loadedConfig = await invoke<HubConfig>("read_config");
      setConfig(loadedConfig);
      setHubPath(loadedConfig.hub_path);

      // 2. Load messages
      const loadedMessages = await invoke<Message[]>("load_messages");
      setMessages(loadedMessages);
    } catch (error) {
      console.error("Error loading data from HUB:", error);
    }
  };

  const fetchStatus = async () => {
    try {
      const active = await invoke<boolean>("is_panic_active");
      setIsPanic(active);

      const locks = await invoke<string[]>("get_active_locks");
      setActiveLocks(locks);

      const logs = await invoke<string>("read_dispatch_log");
      setDispatchLogs(logs);
    } catch (err) {
      console.error("Error fetching hub status:", err);
    }
  };

  useEffect(() => {
    // Initial load
    loadAllData();
    fetchStatus();

    // Polling for logs and locks status (every 2.5s)
    const interval = setInterval(() => {
      fetchStatus();
    }, 2500);

    // Setup listener for file changes from Tauri backend
    let unlisten: (() => void) | undefined;
    
    const setupListener = async () => {
      try {
        unlisten = await listen("hub-update", () => {
          loadAllData();
          fetchStatus();
        });
      } catch (err) {
        console.error("Failed to setup Tauri event listener:", err);
      }
    };

    setupListener();

    return () => {
      clearInterval(interval);
      if (unlisten) {
        unlisten();
      }
    };
  }, []);

  const handleSendMessage = async (content: string, parent?: string, project?: string) => {
    const activeParticipant = config?.participants.find((p) => p.id === activeUserId);
    if (!activeParticipant) return;

    try {
      await invoke("send_message", {
        sender: activeParticipant.name,
        content: content,
        parent: parent || null,
        project: project || null,
      });
      
      // Reload messages immediately
      const loadedMessages = await invoke<Message[]>("load_messages");
      setMessages(loadedMessages);
      setReplyToMessageId(null);
    } catch (error) {
      console.error("Error sending message:", error);
    }
  };

  const handleReceiveMessage = async (agentName: string, content: string, parent?: string, project?: string) => {
    try {
      await invoke("receive_message", {
        receiver: agentName,
        content: content,
        parent: parent || null,
        project: project || null,
      });
      
      // Reload messages
      const loadedMessages = await invoke<Message[]>("load_messages");
      setMessages(loadedMessages);
      setReplyToMessageId(null);
    } catch (error) {
      console.error("Error simulating agent response:", error);
    }
  };

  const handleInvokeEngine = async (content: string, parent?: string, project?: string) => {
    try {
      await invoke("invoke_engine", {
        prompt: content,
        parent: parent || null,
        project: project || null,
      });
      
      // Reload messages
      const loadedMessages = await invoke<Message[]>("load_messages");
      setMessages(loadedMessages);
      setReplyToMessageId(null);
    } catch (error) {
      console.error("Error invoking engine:", error);
    }
  };

  const handleToggleStatus = async (userId: string, currentOnline: boolean) => {
    try {
      await invoke("set_status", {
        agentId: userId,
        online: !currentOnline,
      });
      
      // Reload data
      loadAllData();
    } catch (error) {
      console.error("Error setting status:", error);
    }
  };

  const handleTogglePanic = async () => {
    try {
      const nextPanic = !isPanic;
      await invoke("toggle_panic", { panic: nextPanic });
      setIsPanic(nextPanic);
      fetchStatus();
    } catch (error) {
      console.error("Error toggling panic protocol:", error);
    }
  };

  const handleRunDispatcher = async (agent: string) => {
    setIsRunningDispatcher(true);
    setIsDrawerOpen(true); // Open console view to see execution logs
    try {
      const result = await invoke<string>("run_dispatcher", { agent });
      console.log("Dispatcher execution success:", result);
      await loadAllData();
      await fetchStatus();
    } catch (error) {
      console.error("Dispatcher execution failed:", error);
    } finally {
      setIsRunningDispatcher(false);
    }
  };

  const activeParticipant = config?.participants.find((p) => p.id === activeUserId) || null;

  const renderLogLines = () => {
    if (!dispatchLogs) return <div className="console-log-line">No hay logs registrados en el HUB.</div>;
    
    return dispatchLogs.split("\n").map((line, idx) => {
      let lineClass = "";
      if (line.includes("[OK]")) lineClass = "log-ok";
      else if (line.includes("[WARN]")) lineClass = "log-warn";
      else if (line.includes("[ERROR]")) lineClass = "log-error";
      else if (line.includes("[INFO]")) lineClass = "log-info";

      // Try matching standard timestamps like [2026-08-08 21:28:22]
      const timeMatch = line.match(/^\[(.*?)\]/);
      if (timeMatch) {
        const timePart = timeMatch[0];
        const restPart = line.substring(timePart.length);
        return (
          <div key={idx} className="console-log-line">
            <span className="log-time">{timePart}</span>
            <span className={lineClass}>{restPart}</span>
          </div>
        );
      }

      return (
        <div key={idx} className={`console-log-line ${lineClass}`}>
          {line}
        </div>
      );
    });
  };

  return (
    <div className="app-container" style={{ flexDirection: "column" }}>
      {isPanic && (
        <div className="panic-banner">
          <span>⚠️ PROTOCOLO DE PÁNICO ACTIVADO — EJECUCIONES DEL DISPATCHER Y AGENTES DETENIDAS ⚠️</span>
          <button className="panic-banner-btn" onClick={handleTogglePanic}>
            DESACTIVAR PÁNICO
          </button>
        </div>
      )}
      
      <div style={{ display: "flex", flex: 1, width: "100%", overflow: "hidden" }}>
        <Sidebar
          participants={config?.participants || []}
          currentUser={activeUserId}
          onSelectUser={setActiveUserId}
          onToggleStatus={handleToggleStatus}
          hubPath={hubPath}
          isPanic={isPanic}
          onTogglePanic={handleTogglePanic}
          activeLocks={activeLocks}
        />
        <main className="main-area">
          <MessagePanel
            messages={messages}
            participants={config?.participants || []}
            onSelectReply={setReplyToMessageId}
            replyToMessageId={replyToMessageId}
          />
          <ChatInput
            onSendMessage={handleSendMessage}
            onReceiveMessage={handleReceiveMessage}
            onInvokeEngine={handleInvokeEngine}
            activeParticipant={activeParticipant}
            participants={config?.participants || []}
            replyToMessageId={replyToMessageId}
            onClearReply={() => setReplyToMessageId(null)}
            isPanic={isPanic}
            isRunningDispatcher={isRunningDispatcher}
            onRunDispatcher={handleRunDispatcher}
          />
        </main>
      </div>

      {/* Toggle log drawer */}
      <button 
        className="console-drawer-toggle"
        onClick={() => setIsDrawerOpen(!isDrawerOpen)}
      >
        <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
          <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm-1 14H5c-.55 0-1-.45-1-1v-5h16v5c0 .55-.45 1-1 1zm1-6H4V8c0-.55.45-1 1-1h14c.55 0 1 .45 1 1v4z"/>
        </svg>
        {isDrawerOpen ? "Ocultar Consola" : "Ver Consola de Logs"}
      </button>

      {/* Logs console drawer */}
      <div className={`console-drawer ${isDrawerOpen ? "open" : ""}`}>
        <div className="console-header">
          <div className="console-title">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H7c0-2.76 2.24-5 5-5s5 2.24 5 5c0 1.04-.42 1.99-1.07 2.25z"/>
            </svg>
            Consola del Dispatcher (Logs en tiempo real)
          </div>
          <div className="console-actions">
            <button className="console-btn" onClick={fetchStatus}>Recargar</button>
            <button className="console-btn" onClick={() => setIsDrawerOpen(false)}>Cerrar</button>
          </div>
        </div>
        <div className="console-body">
          {renderLogLines()}
        </div>
      </div>
    </div>
  );
}

export default App;
