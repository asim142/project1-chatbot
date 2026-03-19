import { useRef, useState } from 'react'
import { uploadFile } from '../api'

export default function UploadButton() {
  const inputRef = useRef()
  const [status, setStatus] = useState('')
  const [isError, setIsError] = useState(false)

  async function handleFile(e) {
    const file = e.target.files[0]
    if (!file) return

    setStatus('Uploading...')
    setIsError(false)

    try {
      const data = await uploadFile(file)
      setStatus(`${file.name} — ${data.chunks_stored} chunks indexed`)
      setIsError(false)
    } catch {
      setStatus('Upload failed')
      setIsError(true)
    }

    e.target.value = ''
  }

  return (
    <div className="upload-area">
      <button className="upload-btn" onClick={() => inputRef.current.click()}>
        <span>+</span> Upload PDF
      </button>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.txt"
        style={{ display: 'none' }}
        onChange={handleFile}
      />
      {status && (
        <div className={`upload-status ${isError ? 'error' : ''}`}>
          {status}
        </div>
      )}
    </div>
  )
}