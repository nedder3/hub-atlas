import React from "react";
import { Participant } from "../types";

interface SidebarProps {
  participants: Participant[];
  currentUser: string;
  onSelectUser: (userId: string) => void;
  onToggleStatus: (userId: string, currentStatus: boolean) => void;
  hubPath: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  participants,
  currentUser,
  onSelectUser,
  onToggleStatus,
  hubPath,
}) => {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-logo">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-.778.099-1.533.284-2.253" />
          </svg>
        </div>
        <div className="brand-info">
          <h1 className="brand-title">Sala de Mando</h1>
          <span className="brand-subtitle">ATLAS HUB</span>
        </div>
      </div>

      <div className="sidebar-section">
        <h2 className="section-title">Participantes</h2>
        <div className="participants-list">
          {participants.map((p) => {
            const isActive = p.id === currentUser;
            return (
              <div
                key={p.id}
                className={`participant-item ${isActive ? "active" : ""}`}
                onClick={() => onSelectUser(p.id)}
              >
                <div
                  className="p-avatar"
                  style={{
                    backgroundColor: p.color,
                    boxShadow: isActive ? `0 0 16px ${p.color}80` : `0 0 8px ${p.color}20`,
                  }}
                >
                  {p.avatar}
                  <span className={`status-indicator ${p.online ? "online" : "offline"}`} />
                </div>
                <div className="p-details">
                  <div className="p-name">{p.name}</div>
                  <div className="p-role">{p.role}</div>
                </div>

                <div className="p-actions">
                  <button
                    className={`status-toggle-btn ${p.online ? "online" : "offline"}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      onToggleStatus(p.id, p.online);
                    }}
                    title={p.online ? "Poner Offline" : "Poner Online"}
                  >
                    <svg className="toggle-power-icon" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 2a1 1 0 011 1v7a1 1 0 11-2 0V3a1 1 0 011-1zm-4.95 3.05a1 1 0 010 1.414 7 7 0 009.9 0 1 1 0 011.414-1.414 9 9 0 01-12.728 0 1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </button>
                </div>

                {isActive && (
                  <div className="active-badge">
                    <span>Activo</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div className="sidebar-footer">
        <div className="footer-title">Ruta del HUB</div>
        <div className="footer-path" title={hubPath}>
          <svg className="path-icon" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M2 6a2 2 0 012-2h4l2 2h4a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" clipRule="evenodd" />
          </svg>
          <span className="path-text">{hubPath}</span>
        </div>
        <div className="footer-status">
          <div className="status-dot"></div>
          <span>Monitoreo Activo</span>
        </div>
      </div>
    </aside>
  );
};
