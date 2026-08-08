import React, { useEffect, useRef } from "react";
import { Message, Participant } from "../types";
import { openPath } from "@tauri-apps/plugin-opener";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github-dark.css";

interface MessagePanelProps {
  messages: Message[];
  participants: Participant[];
  onSelectReply: (messageId: string) => void;
  replyToMessageId: string | null;
}

export const MessagePanel: React.FC<MessagePanelProps> = ({
  messages,
  participants,
  onSelectReply,
  replyToMessageId,
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const getParticipantInfo = (authorName: string) => {
    const participant = participants.find(
      (p) => p.name.toLowerCase() === authorName.toLowerCase() || p.id.toLowerCase() === authorName.toLowerCase()
    );
    return (
      participant || {
        id: authorName,
        name: authorName,
        avatar: authorName.substring(0, 2).toUpperCase(),
        color: "#6b7280",
        role: "desconocido",
        online: false,
      }
    );
  };

  const formatMessageDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch {
      return dateString;
    }
  };

  const handleOpenFile = async (filePath: string) => {
    try {
      await openPath(filePath);
    } catch (error) {
      console.error("Failed to open file:", error);
    }
  };

  return (
    <div className="message-panel" ref={scrollRef}>
      {messages.length === 0 ? (
        <div className="empty-panel">
          <div className="empty-glow"></div>
          <svg className="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 18.09a2.605 2.605 0 01-1.19-.494 3.57 3.57 0 001.082-1.285 7.979 7.979 0 01-2.302-5.311C3 7.444 7.03 3.75 12 3.75s9 3.694 9 8.25z" />
          </svg>
          <p className="empty-text">No hay mensajes cargados en el HUB</p>
          <p className="empty-subtext">Envía un mensaje o añade archivos .md en `briefs/` o `consensos/` para comenzar.</p>
        </div>
      ) : (
        <div className="messages-list">
          {messages.map((message) => {
            const participant = getParticipantInfo(message.author);
            
            // Align: Humano to the left, Agents/others to the right
            const isHumano = participant.role === "humano";
            const alignLeft = isHumano;

            const isReplyingToThis = replyToMessageId === message.id;

            return (
              <div
                key={message.id}
                className={`message-wrapper ${alignLeft ? "left-aligned" : "me"} ${participant.role} ${message.parent ? "indented" : ""}`}
                style={{
                  marginLeft: message.parent && alignLeft ? "48px" : undefined,
                  marginRight: message.parent && !alignLeft ? "48px" : undefined,
                }}
              >
                <div
                  className="message-avatar"
                  style={{
                    backgroundColor: participant.color,
                    boxShadow: `0 0 12px ${participant.color}40`,
                  }}
                >
                  {participant.avatar}
                </div>
                <div className="message-content-wrapper">
                  <div className="message-header">
                    <span className="message-author">{participant.name}</span>
                    <span className="message-role-tag">{participant.role}</span>
                    <span className="message-time">{formatMessageDate(message.date)}</span>
                    {message.project && (
                      <span className="message-project-tag" title="Proyecto">
                        📁 {message.project}
                      </span>
                    )}
                  </div>
                  
                  {message.parent && (
                    <div className="message-parent-reference">
                      <svg className="reply-arrow-icon" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M7.707 3.293a1 1 0 010 1.414L5.414 7H11a7 7 0 017 7v2a1 1 0 11-2 0v-2a5 5 0 00-5-5H5.414l2.293 2.293a1 1 0 11-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                      <span>Responde a @{message.parent.split('_').slice(0, 3).join('_')}</span>
                    </div>
                  )}

                  <div className="message-bubble" style={{ borderColor: !alignLeft ? `${participant.color}40` : undefined }}>
                    <div className="markdown-body">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        rehypePlugins={[rehypeHighlight]}
                      >
                        {message.content}
                      </ReactMarkdown>
                    </div>
                  </div>
                  <div className="message-footer">
                    <button
                      className="file-link-btn"
                      onClick={() => handleOpenFile(message.file_path)}
                      title={`Abrir archivo: ${message.id}`}
                    >
                      <svg className="file-icon" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                      </svg>
                      {message.id}
                    </button>

                    <button
                      className={`reply-action-btn ${isReplyingToThis ? "active" : ""}`}
                      onClick={() => onSelectReply(isReplyingToThis ? "" : message.id)}
                      title="Responder a este mensaje"
                    >
                      <svg className="reply-icon" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M7.707 3.293a1 1 0 010 1.414L5.414 7H11a7 7 0 017 7v2a1 1 0 11-2 0v-2a5 5 0 00-5-5H5.414l2.293 2.293a1 1 0 11-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                      {isReplyingToThis ? "Cancelado" : "Responder"}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
