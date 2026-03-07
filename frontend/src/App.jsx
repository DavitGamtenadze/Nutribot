import React, { useEffect, useState, useMemo } from 'react'
import ConversationPanel from './components/ConversationPanel'
import ResponseCard from './components/ResponseCard'
import UserContextForm from './components/UserContextForm'
import OnboardingModal from './components/OnboardingModal'
import MealDiary from './components/MealDiary'
import WeeklySummary from './components/WeeklySummary'

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
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState(null)
  const [editingConvoId, setEditingConvoId] = useState(null)
  const [editingTitle, setEditingTitle] = useState('')
  const [activeTab, setActiveTab] = useState('chat') // 'chat' | 'diary'
  const [mealLogs, setMealLogs] = useState([])
  const [weeklySummary, setWeeklySummary] = useState(null)

  const [showOnboarding, setShowOnboarding] = useState(false)
  const [loadingProfile, setLoadingProfile] = useState(false)
  const [loadingResponse, setLoadingResponse] = useState(false)
  const [error, setError] = useState('')
  const [coachPlan, setCoachPlan] = useState(null)
  const [streak, setStreak] = useState(0)
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
    const init = async () => {
      await Promise.all([loadProfile(), loadConversations(), loadStreak()])
    }
    init().then(() => {
      // Check onboarding after data loads (uses state via closure won't work;
      // we check via a callback)
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Show onboarding when profile + conversations are loaded and both are empty
  const [initDone, setInitDone] = useState(false)
  useEffect(() => {
    if (!loadingProfile && conversations !== undefined) {
      setInitDone(true)
    }
  }, [loadingProfile, conversations])

  useEffect(() => {
    if (initDone && profileForm.goals.length === 0 && conversations.length === 0) {
      setShowOnboarding(true)
    }
  }, [initDone])

  const loadStreak = async () => {
    try {
      const res = await fetch(`${apiBase}/api/users/${encodeURIComponent(userId)}/streak`)
      if (res.ok) {
        const data = await res.json()
        setStreak(data.streak || 0)
      }
    } catch (_) {}
  }

  const handleOnboardingComplete = async ({ name, goals, dietary_preferences, starterPrompt }) => {
    setShowOnboarding(false)
    if (name) setUserName(name)
    const newProfile = { ...profileForm, goals, dietary_preferences }
    setProfileForm(newProfile)

    try {
      await fetch(`${apiBase}/api/users/${encodeURIComponent(userId)}/profile`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_name: name || null,
          goals,
          dietary_preferences,
        }),
      })
    } catch (_) {}

    if (starterPrompt) {
      setMessage(starterPrompt)
    }
  }

  const deleteConversation = async (conversationId) => {
    if (!window.confirm('Delete this conversation?')) return
    try {
      const res = await fetch(
        `${apiBase}/api/conversations/${encodeURIComponent(userId)}/${conversationId}`,
        { method: 'DELETE' },
      )
      if (!res.ok) throw new Error('Failed to delete')
      if (activeConversationId === conversationId) {
        setActiveConversationId(null)
        setMessages([])
        setCoachPlan(null)
      }
      await loadConversations()
    } catch (err) {
      setError(err.message)
    }
  }

  const searchConversations = async (query) => {
    setSearchQuery(query)
    if (!query.trim()) {
      setSearchResults(null)
      return
    }
    try {
      const res = await fetch(
        `${apiBase}/api/conversations/${encodeURIComponent(userId)}/search?q=${encodeURIComponent(query.trim())}`,
      )
      if (res.ok) {
        const data = await res.json()
        setSearchResults(data.conversations || [])
      }
    } catch (_) {}
  }

  // Debounced search
  const searchTimeoutRef = React.useRef(null)
  const handleSearchInput = (val) => {
    setSearchQuery(val)
    clearTimeout(searchTimeoutRef.current)
    searchTimeoutRef.current = setTimeout(() => searchConversations(val), 300)
  }

  const renameConversation = async (conversationId, newTitle) => {
    if (!newTitle.trim()) return
    try {
      await fetch(
        `${apiBase}/api/conversations/${encodeURIComponent(userId)}/${conversationId}`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: newTitle.trim() }),
        },
      )
      await loadConversations()
    } catch (_) {}
    setEditingConvoId(null)
    setEditingTitle('')
  }

  const loadMealLogs = async () => {
    try {
      const res = await fetch(`${apiBase}/api/users/${encodeURIComponent(userId)}/meals`)
      if (res.ok) {
        const data = await res.json()
        setMealLogs(data.meals || [])
      }
    } catch (_) {}
  }

  const loadWeeklySummary = async () => {
    try {
      const res = await fetch(`${apiBase}/api/users/${encodeURIComponent(userId)}/weekly-summary`)
      if (res.ok) {
        const data = await res.json()
        setWeeklySummary(data)
      }
    } catch (_) {}
  }

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

      await Promise.all([loadConversations(), loadMessages(data.conversation_id), loadStreak()])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoadingResponse(false)
    }
  }

  return (
    <div className="app-shell">
      {showOnboarding && (
        <OnboardingModal onComplete={handleOnboardingComplete} />
      )}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <p className="eyebrow">AI Coach</p>
          <h1>NutriBot</h1>
          {streak > 0 && (
            <div className="streak-badge" title={`${streak}-day streak`}>
              <span className="streak-fire">&#128293;</span>
              <span className="streak-count">{streak}d streak</span>
            </div>
          )}
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
          <input
            type="text"
            className="convo-search"
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => handleSearchInput(e.target.value)}
          />
          <ul className="conversation-list">
            {(searchResults || conversations).map((c) => (
              <li key={c.conversation_id} className="convo-item">
                {editingConvoId === c.conversation_id ? (
                  <input
                    type="text"
                    className="convo-rename-input"
                    value={editingTitle}
                    onChange={(e) => setEditingTitle(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') renameConversation(c.conversation_id, editingTitle)
                      if (e.key === 'Escape') { setEditingConvoId(null); setEditingTitle('') }
                    }}
                    onBlur={() => renameConversation(c.conversation_id, editingTitle)}
                    autoFocus
                  />
                ) : (
                  <button
                    type="button"
                    className={activeConversationId === c.conversation_id ? 'active-conversation' : ''}
                    onClick={() => loadMessages(c.conversation_id)}
                    onDoubleClick={() => {
                      setEditingConvoId(c.conversation_id)
                      setEditingTitle(c.title || '')
                    }}
                  >
                    <span className="convo-title">{c.title || `Chat ${c.conversation_id}`}</span>
                    <span className="convo-time">
                      {new Date(c.updated_at).toLocaleDateString()}
                    </span>
                  </button>
                )}
                <button
                  type="button"
                  className="convo-delete-btn"
                  title="Delete conversation"
                  onClick={(e) => { e.stopPropagation(); deleteConversation(c.conversation_id) }}
                >
                  &#128465;
                </button>
              </li>
            ))}
            {!(searchResults || conversations).length && (
              <li className="empty-note">
                {searchQuery ? 'No matching conversations.' : 'No saved conversations yet.'}
              </li>
            )}
          </ul>
        </div>
      </aside>

      <div className="chat-column">
        {activeTab === 'chat' ? (
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
            activeTab={activeTab}
            setActiveTab={(tab) => {
              setActiveTab(tab)
              if (tab === 'diary') { loadMealLogs(); loadWeeklySummary() }
            }}
          />
        ) : (
          <>
            <div className="chat-header">
              <h2>Food Diary</h2>
              <div className="chat-header-actions">
                <div className="tab-toggle">
                  <button type="button" className="tab-btn" onClick={() => setActiveTab('chat')}>Chat</button>
                  <button type="button" className="tab-btn active">Diary</button>
                </div>
              </div>
            </div>
            <WeeklySummary data={weeklySummary} />
            <MealDiary meals={mealLogs} />
          </>
        )}
      </div>

      <ResponseCard
        response={coachPlan}
        conversationId={activeConversationId}
        error={error}
        loading={loadingResponse}
        onFollowUpClick={(text) => setMessage(text)}
      />
    </div>
  )
}
