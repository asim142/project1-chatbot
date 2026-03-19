import { useState, useRef, useEffect } from 'react'
import MessageBubble from './MessageBubble'
import { sendMessageStream, getSession } from '../api'

export default function ChatWindow({ sessionId, sessionName }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef()

  useEffect(() => {
    let cancelled = false
    async function loadHistory() {
      try {
        const data = await getSession(sessionId)
        if (cancelled) return
        if (data.history && data.history.length > 0) {
          const mapped = data.history.map(m => ({
            role: m.role === 'human' ? 'user' : 'assistant',
            content: m.content,
          }))
          setMessages(mapped)
        } else {
          setMessages([])
        }
      } catch {
        if (!cancelled) setMessages([])
      }
    }
    loadHistory()
    return () => { cancelled = true }
  }, [sessionId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function handleSend() {
    const text = input.trim()
    if (!text || loading) return

    setMessages(prev => [...prev, { role: 'user', content: text }])
    setInput('')
    setLoading(true)

    // Add an empty assistant message that we'll stream tokens into
    setMessages(prev => [...prev, { role: 'assistant', content: '', sources: [] }])

    try {
      await sendMessageStream(
        sessionId,
        text,
        (token) => {
          setMessages(prev => {
            const updated = [...prev]
            const last = updated[updated.length - 1]
            updated[updated.length - 1] = { ...last, content: last.content + token }
            return updated
          })
        },
        (sources) => {
          setMessages(prev => {
            const updated = [...prev]
            updated[updated.length - 1] = { ...updated[updated.length - 1], sources }
            return updated
          })
          setLoading(false)
        }
      )
    } catch {
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = { role: 'assistant', content: 'Something went wrong. Is the backend running?', sources: [] }
        return updated
      })
      setLoading(false)
    }
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="chat-area">
      <div className="chat-header">
        <span>{sessionName}</span>
        <span className="chat-header-sub">RAG · Ollama · pgvector</span>
      </div>

      <div className="messages">
        {messages.length === 0 && !loading && (
          <div className="empty-state">
            <div className="empty-state-icon">◎</div>
            <h2>How can I help?</h2>
            <p>Upload a PDF from the sidebar, then ask anything about it.</p>
          </div>
        )}

        {messages.map((msg, i) => {
          const isLast = i === messages.length - 1
          const isStreamingThis = loading && isLast && msg.role === 'assistant'
          if (isStreamingThis && msg.content === '') {
            return (
              <div key={i} className="message-row assistant">
                <div className="message-label">Assistant</div>
                <div className="typing"><span /><span /><span /></div>
              </div>
            )
          }
          return <MessageBubble key={i} message={msg} isStreaming={isStreamingThis && msg.content !== ''} />
        })}


        <div ref={bottomRef} />
      </div>

      <div className="input-area">
        <div className="input-box">
          <textarea
            rows={1}
            placeholder="Message RAG Chatbot..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            onInput={e => {
              e.target.style.height = 'auto'
              e.target.style.height = e.target.scrollHeight + 'px'
            }}
          />
          <button
            className="send-btn"
            onClick={handleSend}
            disabled={!input.trim() || loading}
          >
            ↑
          </button>
        </div>
        <div className="input-hint">Enter to send · Shift+Enter for new line</div>
      </div>
    </div>
  )
}