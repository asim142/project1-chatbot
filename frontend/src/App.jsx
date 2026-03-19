import { useState } from 'react'
import { v4 as uuidv4 } from 'uuid'
import Sidebar from './components/Sidebar'
import ChatWindow from './components/ChatWindow'
import { clearSession } from './api'

function loadSessions() {
  try {
    const saved = localStorage.getItem('chat_sessions')
    if (saved) return JSON.parse(saved)
  } catch {}
  return null
}

function saveSessions(sessions, activeId) {
  try {
    localStorage.setItem('chat_sessions', JSON.stringify(sessions))
    localStorage.setItem('chat_active_id', activeId)
  } catch {}
}

export default function App() {
  const savedSessions = loadSessions()
  const defaultSession = { id: uuidv4(), name: 'Chat 1' }

  const [sessions, setSessions] = useState(savedSessions || [defaultSession])
  const [activeId, setActiveId] = useState(
    () => localStorage.getItem('chat_active_id') || (savedSessions?.[0]?.id ?? defaultSession.id)
  )

  function handleNew() {
    const id = uuidv4()
    const name = `Chat ${sessions.length + 1}`
    const updated = [...sessions, { id, name }]
    setSessions(updated)
    setActiveId(id)
    saveSessions(updated, id)
  }

  async function handleDelete(id) {
    try { await clearSession(id) } catch {}
    const updated = sessions.filter(s => s.id !== id)
    let nextId = activeId
    if (activeId === id) {
      if (updated.length > 0) {
        nextId = updated[updated.length - 1].id
      } else {
        const newId = uuidv4()
        const fresh = [{ id: newId, name: 'Chat 1' }]
        setSessions(fresh)
        setActiveId(newId)
        saveSessions(fresh, newId)
        return
      }
    }
    setSessions(updated)
    setActiveId(nextId)
    saveSessions(updated, nextId)
  }

  function handleSelect(id) {
    setActiveId(id)
    saveSessions(sessions, id)
  }

  const activeSession = sessions.find(s => s.id === activeId)

  return (
    <div className="app">
      <Sidebar
        sessions={sessions}
        activeId={activeId}
        onSelect={handleSelect}
        onNew={handleNew}
        onDelete={handleDelete}
      />
      <ChatWindow
        key={activeId}
        sessionId={activeId}
        sessionName={activeSession?.name || 'Chat'}
      />
    </div>
  )
}