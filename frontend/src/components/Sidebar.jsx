import UploadButton from './UploadButton'

export default function Sidebar({ sessions, activeId, onSelect, onNew, onDelete }) {
  return (
    <div className="sidebar">
      <div className="sidebar-logo">RAG Chatbot</div>

      <button className="new-chat-btn" onClick={onNew}>
        <span>+</span> New chat
      </button>

      <div className="sessions-list">
        {sessions.length > 0 && (
          <div className="sessions-label">Recent</div>
        )}
        {sessions.map(session => (
          <div
            key={session.id}
            className={`session-item ${session.id === activeId ? 'active' : ''}`}
            onClick={() => onSelect(session.id)}
          >
            <span className="session-name">{session.name}</span>
            <button
              className="session-delete"
              onClick={e => {
                e.stopPropagation()
                onDelete(session.id)
              }}
            >
              ×
            </button>
          </div>
        ))}
      </div>

      <div className="sidebar-bottom">
        <UploadButton />
      </div>
    </div>
  )
}