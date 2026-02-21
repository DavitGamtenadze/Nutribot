import React, { useEffect, useState, useMemo } from 'react'
import ConversationPanel from './components/ConversationPanel'
import ResponseCard from './components/ResponseCard'
import UserContextForm from './components/UserContextForm'

const THEME_KEY = 'nutribot-theme'

const EMPTY_PROFILE = {
  goals: [],
  dietary_preferences: [],
  allergies: [],
  medications: [],
  notes: '',
}

export default function App() {
  const apiBase = useMemo(
    () => import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
    [],
  )

  const userId = 'user-001'

  const [userName, setUserName] = useState('')
  const [profileForm, setProfileForm] = useState(EMPTY_PROFILE)

  const [conversations, setConversations] = useState([])
  const [activeConversationId, setActiveConversationId] = useState(null)
  const [messages, setMessages] = useState([])

  const [message, setMessage] = useState('')
  const [imageFile, setImageFile] = useState(null)
  const [imagePreview, setImagePreview] = useState('')

  const [loadingProfile, setLoadingProfile] = useState(false)
  const [loadingResponse, setLoadingResponse] = useState(false)
  const [error, setError] = useState('')
  const [coachPlan, setCoachPlan] = useState(null)
  const [nightMode, setNightMode] = useState(() => {
    try {
      return localStorage.getItem(THEME_KEY) === 'dark'
    } catch {
      return false
    }
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', nightMode ? 'dark' : 'light')
    try {
      localStorage.setItem(THEME_KEY, nightMode ? 'dark' : 'light')
    } catch (_) {}
  }, [nightMode])

  useEffect(() => {
    loadProfile()
    loadConversations()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const loadProfile = async () => {
    setLoadingProfile(true)
    setError('')
    try {
      const res = await fetch(`${apiBase}/api/users/${encodeURIComponent(userId)}/profile`)
      if (!res.ok) throw new Error(`Failed to load profile (${res.status})`)
      const data = await res.json()
      setUserName(data.user_name || '')
      setProfileForm({
        goals: data.goals || [],
        dietary_preferences: data.dietary_preferences || [],
        allergies: data.allergies || [],
        medications: data.medications || [],
        notes: data.notes || '',
      })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoadingProfile(false)
    }
  }

  const saveProfile = async () => {
    setLoadingProfile(true)
    setError('')
    try {
      const payload = {
        user_name: userName || null,
        goals: profileForm.goals,
        dietary_preferences: profileForm.dietary_preferences,
        allergies: profileForm.allergies,
        medications: profileForm.medications,
        notes: profileForm.notes || null,
      }
      const res = await fetch(`${apiBase}/api/users/${encodeURIComponent(userId)}/profile`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error(`Failed to save profile (${res.status})`)
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setLoadingProfile(false)
    }
  }

  const loadConversations = async () => {
    setError('')
    try {
      const res = await fetch(`${apiBase}/api/conversations/${encodeURIComponent(userId)}`)
      if (!res.ok) throw new Error(`Failed to load conversations (${res.status})`)
      const data = await res.json()
      setConversations(data.conversations || [])
    } catch (err) {
      setError(err.message)
    }
  }

  const loadMessages = async (conversationId) => {
    if (!conversationId) return
    setError('')
    try {
      const res = await fetch(
        `${apiBase}/api/conversations/${encodeURIComponent(userId)}/${conversationId}/messages`,
      )
      if (!res.ok) throw new Error(`Failed to load messages (${res.status})`)
      const data = await res.json()
      setMessages(data.messages || [])
      setActiveConversationId(conversationId)
    } catch (err) {
      setError(err.message)
    }
  }

  const onNewConversation = () => {
    setActiveConversationId(null)
    setMessages([])
    setCoachPlan(null)
    setError('')
  }

  const onImageSelected = (file) => {
    setImageFile(file)
    setImagePreview(URL.createObjectURL(file))
  }

  const onImageClear = () => {
    setImageFile(null)
    setImagePreview('')
  }

  const onSubmit = async () => {
    if (!message.trim() && !imageFile) {
      setError('Share a message or meal photo so NutriBot can build your plan.')
      return
    }

    setLoadingResponse(true)
    setError('')
    try {
      let uploadedImageUrl = null

      if (imageFile) {
        const formData = new FormData()
        formData.append('file', imageFile)
        const uploadRes = await fetch(`${apiBase}/api/upload-image`, {
          method: 'POST',
          body: formData,
        })
        if (uploadRes.ok) {
          const uploadData = await uploadRes.json()
          uploadedImageUrl = uploadData.image_url
        }
      }

      const trimmedMessage = (message && message.trim().slice(0, 4000)) || null;
      const payload = {
        user_id: userId,
        user_name: userName || null,
        conversation_id: activeConversationId,
        message: trimmedMessage,
        image_url: uploadedImageUrl,
        goals: profileForm.goals,
        dietary_preferences: profileForm.dietary_preferences,
        allergies: profileForm.allergies,
        medications: profileForm.medications,
        notes: profileForm.notes || null,
      }
      const res = await fetch(`${apiBase}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({ detail: 'Unknown API error' }))
        const detail = body.detail
        const message =
          typeof detail === 'string'
            ? detail
            : Array.isArray(detail)
              ? detail.map((e) => e.msg || e.message || JSON.stringify(e)).join('. ')
              : detail && typeof detail === 'object'
                ? detail.msg || detail.message || JSON.stringify(detail)
                : `Failed to generate plan (${res.status})`
        throw new Error(message || `Failed to generate plan (${res.status})`)
      }

      const data = await res.json()
      setActiveConversationId(data.conversation_id)
      setCoachPlan(data.response)
      setMessage('')
      onImageClear()

      await Promise.all([loadConversations(), loadMessages(data.conversation_id)])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoadingResponse(false)
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <p className="eyebrow">AI Coach</p>
          <h1>NutriBot</h1>
        </div>

        <UserContextForm
          userName={userName}
          setUserName={setUserName}
          profileForm={profileForm}
          setProfileForm={setProfileForm}
          onSaveProfile={saveProfile}
          loadingProfile={loadingProfile}
        />

        <div className="convo-section">
          <h2>Conversations</h2>
          <ul className="conversation-list">
            {conversations.map((c) => (
              <li key={c.conversation_id}>
                <button
                  type="button"
                  className={activeConversationId === c.conversation_id ? 'active-conversation' : ''}
                  onClick={() => loadMessages(c.conversation_id)}
                >
                  <span className="convo-title">{c.title || `Chat ${c.conversation_id}`}</span>
                  <span className="convo-time">
                    {new Date(c.updated_at).toLocaleDateString()}
                  </span>
                </button>
              </li>
            ))}
            {!conversations.length && (
              <li className="empty-note">No saved conversations yet.</li>
            )}
          </ul>
        </div>
      </aside>

      <div className="chat-column">
        <ConversationPanel
          conversations={conversations}
          activeConversationId={activeConversationId}
          onSelectConversation={loadMessages}
          onNewConversation={onNewConversation}
          messages={messages}
          message={message}
          setMessage={setMessage}
          imagePreview={imagePreview}
          onImageSelected={onImageSelected}
          onImageClear={onImageClear}
          onSubmit={onSubmit}
          loading={loadingResponse}
          nightMode={nightMode}
          setNightMode={setNightMode}
        />
      </div>

      <ResponseCard
        response={coachPlan}
        conversationId={activeConversationId}
        error={error}
        loading={loadingResponse}
      />
    </div>
  )
}
