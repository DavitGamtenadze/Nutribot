import React, { useEffect, useRef } from 'react'

const MAX_MESSAGE_LENGTH = 4000

const CameraIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
    <circle cx="12" cy="13" r="4" />
  </svg>
)

const SendIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <line x1="22" y1="2" x2="11" y2="13" />
    <polygon points="22 2 15 22 11 13 2 9 22 2" />
  </svg>
)

const SpinnerIcon = () => (
  <span className="send-spinner" aria-hidden="true">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" aria-hidden="true">
      <circle cx="12" cy="12" r="10" strokeOpacity="0.25" />
      <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" />
    </svg>
  </span>
)

export default function ConversationPanel({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  messages,
  message,
  setMessage,
  imagePreview,
  onImageSelected,
  onImageClear,
  onSubmit,
  loading,
  nightMode,
  setNightMode,
}) {
  const fileInputRef = useRef(null)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (!loading) onSubmit()
    }
  }

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (file) onImageSelected(file)
  }

  return (
    <>
      <div className="chat-header">
        <h2>Coach Chat</h2>
        <div className="chat-header-actions">
          <button type="button" className="ghost-btn" onClick={onNewConversation}>
            + New thread
          </button>
          <button
            type="button"
            className="theme-toggle"
            onClick={() => setNightMode((v) => !v)}
            title={nightMode ? 'Switch to light mode' : 'Switch to night mode'}
            aria-label={nightMode ? 'Switch to light mode' : 'Switch to night mode'}
          >
            <span className="theme-toggle-icon sun" aria-hidden="true">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
            </span>
            <span className="theme-toggle-icon moon" aria-hidden="true">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
            </span>
          </button>
        </div>
      </div>

      <ul className="message-list">
        {messages.map((entry) => (
          <li
            key={entry.message_id}
            className={entry.role === 'assistant' ? 'assistant-bubble' : 'user-bubble'}
          >
            <div className="bubble-role">{entry.role === 'assistant' ? 'Coach' : 'You'}</div>
            <div className="bubble-text">{entry.content}</div>
            {entry.image_url && (
              <img
                src={
                  entry.image_url.startsWith('/')
                    ? `${window.__API_BASE || ''}${entry.image_url}`
                    : entry.image_url
                }
                alt="Meal"
                className="message-image"
              />
            )}
          </li>
        ))}
        {!messages.length && (
          <li className="empty-note">
            Tell the coach what you ate and your current goal.
          </li>
        )}
        <div ref={messagesEndRef} />
      </ul>

      <div className="compose-bar">
        {imagePreview && (
          <div className="image-preview-row">
            <img src={imagePreview} alt="Preview" />
            <button
              type="button"
              className="remove-preview-btn"
              onClick={() => {
                onImageClear()
                if (fileInputRef.current) fileInputRef.current.value = ''
              }}
            >
              Remove
            </button>
          </div>
        )}

        <div className="compose-row">
          <div className="compose-input-wrap">
            <textarea
              className="compose-textarea"
              rows={2}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="I ate eggs and toast… (Enter to send, Shift+Enter for newline)"
              disabled={loading}
              maxLength={MAX_MESSAGE_LENGTH}
              title={`Message (max ${MAX_MESSAGE_LENGTH} characters)`}
            />
            {message.length > 3000 && (
              <span className="compose-char-count" aria-live="polite">
                {message.length} / {MAX_MESSAGE_LENGTH}
              </span>
            )}
          </div>

          <button
            type="button"
            className="icon-btn"
            title="Attach meal photo"
            disabled={loading}
            onClick={() => fileInputRef.current?.click()}
          >
            <CameraIcon />
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            style={{ display: 'none' }}
            onChange={handleFileChange}
          />

          <button
            type="button"
            className="send-btn"
            onClick={onSubmit}
            disabled={loading}
            title={loading ? 'Waiting for response…' : 'Send (Enter)'}
          >
            {loading ? <SpinnerIcon /> : <SendIcon />}
          </button>
        </div>
      </div>
    </>
  )
}
