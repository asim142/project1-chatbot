export default function MessageBubble({ message, isStreaming }) {
  const isUser = message.role === 'user'

  return (
    <div className={`message-row ${isUser ? 'user' : 'assistant'}`}>
      <div className="message-label">
        {isUser ? 'You' : 'Assistant'}
      </div>
      <div className={`bubble ${isUser ? 'user' : 'assistant'}`}>
        {message.content}
        {isStreaming && <span className="streaming-cursor" />}
      </div>
      {!isUser && message.sources && message.sources.length > 0 && (
        <div className="sources">
          {message.sources.map((src, i) => (
            <span key={i} className="source-tag">
              {src}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}