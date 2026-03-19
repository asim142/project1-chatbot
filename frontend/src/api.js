const BASE_URL = 'http://localhost:8000'

export async function sendMessageStream(sessionId, message, onToken, onDone) {
  const res = await fetch(`${BASE_URL}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message })
  })
  if (!res.ok) throw new Error('Chat failed')

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let doneCalled = false

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() // keep last incomplete line in buffer
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      try {
        const data = JSON.parse(line.slice(6))
        if (data.done) {
          doneCalled = true
          onDone(data.sources)
        } else if (data.token) {
          onToken(data.token)
        }
      } catch {}
    }
  }

  // Fallback: if stream ended without a done event
  if (!doneCalled) onDone([])
}

export async function sendMessage(sessionId, message) {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message })
  })
  if (!res.ok) throw new Error('Chat failed')
  return res.json()
}

export async function uploadFile(file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE_URL}/upload`, {
    method: 'POST',
    body: form
  })
  if (!res.ok) throw new Error('Upload failed')
  return res.json()
}

export async function getSession(sessionId) {
  const res = await fetch(`${BASE_URL}/session/${sessionId}`)
  if (!res.ok) throw new Error('Session fetch failed')
  return res.json()
}

export async function clearSession(sessionId) {
  const res = await fetch(`${BASE_URL}/session/${sessionId}`, {
    method: 'DELETE'
  })
  if (!res.ok) throw new Error('Clear failed')
  return res.json()
}