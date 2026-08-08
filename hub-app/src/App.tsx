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
  const [hubPath, setHubPath] = useState<string>("C:\\Users\\arijd\\Documents\\Atlas\\HUB");
  const [replyToMessageId, setReplyToMessageId] = useState<string | null>(null);

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

  useEffect(() => {
    // Initial load
    loadAllData();

    // Setup listener for file changes from Tauri backend
    let unlisten: (() => void) | undefined;
    
    const setupListener = async () => {
      try {
        unlisten = await listen("hub-update", () => {
          loadAllData();
        });
      } catch (err) {
        console.error("Failed to setup Tauri event listener:", err);
      }
    };

    setupListener();

    return () => {
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

  const activeParticipant = config?.participants.find((p) => p.id === activeUserId) || null;

  return (
    <div className="app-container">
      <Sidebar
        participants={config?.participants || []}
        currentUser={activeUserId}
        onSelectUser={setActiveUserId}
        onToggleStatus={handleToggleStatus}
        hubPath={hubPath}
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
        />
      </main>
    </div>
  );
}

export default App;
