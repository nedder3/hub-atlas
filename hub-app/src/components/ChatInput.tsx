import React, { useState, useRef, useEffect } from "react";
import { Participant } from "../types";

interface ChatInputProps {
  onSendMessage: (content: string, parent?: string, project?: string) => void;
  onReceiveMessage: (agentName: string, content: string, parent?: string, project?: string) => void;
  onInvokeEngine: (content: string, parent?: string, project?: string) => void;
  activeParticipant: Participant | null;
  participants: Participant[];
  replyToMessageId: string | null;
  onClearReply: () => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  onReceiveMessage,
  onInvokeEngine,
  activeParticipant,
  participants,
  replyToMessageId,
  onClearReply,
}) => {
  const [content, setContent] = useState("");
  const [projectName, setProjectName] = useState("");
  const [selectedAgentId, setSelectedAgentId] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Filter agents for simulation (role === "agente" or "sistema")
  const agents = participants.filter((p) => p.role !== "humano");

  useEffect(() => {
    if (agents.length > 0 && !selectedAgentId) {
      setSelectedAgentId(agents[0].id);
    }
  }, [agents, selectedAgentId]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.ctrlKey && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    const trimmed = content.trim();
    if (!trimmed || !activeParticipant) return;

    onSendMessage(trimmed, replyToMessageId || undefined, projectName || undefined);
    clearInput();
  };

  const handleInvokeEngine = () => {
    const trimmed = content.trim();
    if (!trimmed) return;

    onInvokeEngine(trimmed, replyToMessageId || undefined, projectName || undefined);
    clearInput();
  };

  const handleSimulateAgent = () => {
    const trimmed = content.trim();
    if (!trimmed || !selectedAgentId) return;

    const agent = participants.find((p) => p.id === selectedAgentId);
    if (!agent) return;

    onReceiveMessage(agent.name, trimmed, replyToMessageId || undefined, projectName || undefined);
    clearInput();
  };

  const clearInput = () => {
    setContent("");
    onClearReply();
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  // Auto-resize textarea as user types
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  }, [content]);

  return (
    <div className="chat-input-container">
      {/* Context Bar: Reply & Project details */}
      {(replyToMessageId || projectName || true) && (
        <div className="input-context-bar">
          {replyToMessageId && (
            <div className="context-item reply-badge animate-fade">
              <svg className="context-icon" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M7.707 3.293a1 1 0 010 1.414L5.414 7H11a7 7 0 017 7v2a1 1 0 11-2 0v-2a5 5 0 00-5-5H5.414l2.293 2.293a1 1 0 11-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              <span>Respondiendo a: <span className="mono">{replyToMessageId.split('_').slice(0, 3).join('_')}</span></span>
              <button className="context-clear-btn" onClick={onClearReply} title="Limpiar respuesta">
                &times;
              </button>
            </div>
          )}
          
          <div className="context-item project-input-badge">
            <span className="proj-emoji">📁</span>
            <input
              type="text"
              className="project-name-input"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="Proyecto (opcional)..."
            />
            {projectName && (
              <button className="context-clear-btn" onClick={() => setProjectName("")}>
                &times;
              </button>
            )}
          </div>
        </div>
      )}

      <div className="input-glow" style={{ borderColor: activeParticipant?.color || "#845ec2" }}></div>
      <div className="input-inner">
        <textarea
          ref={textareaRef}
          className="chat-textarea"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            activeParticipant
              ? `Escribir mensaje como ${activeParticipant.name}...`
              : "Selecciona un participante..."
          }
          disabled={!activeParticipant}
          rows={1}
        />
        <div className="input-actions-group">
          {/* Main Send Button */}
          <button
            className="send-button"
            onClick={handleSend}
            disabled={!content.trim() || !activeParticipant}
            title={`Enviar como ${activeParticipant?.name}`}
            style={{
              backgroundColor: activeParticipant?.color || "#845ec2",
              boxShadow: content.trim() && activeParticipant
                ? `0 0 16px ${activeParticipant.color}a0`
                : "none",
            }}
          >
            <svg className="send-icon" viewBox="0 0 20 20" fill="currentColor">
              <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
            </svg>
          </button>
        </div>
      </div>

      {/* Advanced Orchestration Panel */}
      <div className="orchestration-panel">
        <div className="engine-section">
          <button
            className="engine-invoke-btn"
            onClick={handleInvokeEngine}
            disabled={!content.trim()}
            title="Invocar motor de inteligencia Antigravity"
          >
            <svg className="pulse-icon" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
            </svg>
            Invocar Motor
          </button>
        </div>

        <div className="agent-simulator-section">
          <span className="orchest-label">Simular Agente:</span>
          <select
            className="agent-select"
            value={selectedAgentId}
            onChange={(e) => setSelectedAgentId(e.target.value)}
          >
            {agents.map((agent) => (
              <option key={agent.id} value={agent.id}>
                {agent.name} ({agent.role})
              </option>
            ))}
          </select>
          <button
            className="agent-simulate-btn"
            onClick={handleSimulateAgent}
            disabled={!content.trim() || !selectedAgentId}
            title="Simula la respuesta del agente seleccionado escribiendo en consensos/"
          >
            Simular Agente
          </button>
        </div>
      </div>
    </div>
  );
};
