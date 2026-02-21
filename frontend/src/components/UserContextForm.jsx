import React, { useState } from 'react'
import TagInput from './TagInput'

export default function UserContextForm({
  userName,
  setUserName,
  profileForm,
  setProfileForm,
  onSaveProfile,
  loadingProfile,
}) {
  const [saveToast, setSaveToast] = useState(false)

  const updateField = (key, value) => setProfileForm((prev) => ({ ...prev, [key]: value }))


  const handleSave = async () => {
    try {
      await onSaveProfile()
      setSaveToast(true)
      setTimeout(() => setSaveToast(false), 2200)
    } catch {
      // error is shown via App.jsx error state
    }
  }


  return (
    <div className="profile-section">
      <div className="section-header">
        <h2>Profile</h2>
      </div>

      <label className="plain-label">
        Display Name
        <input
          className="plain-input"
          value={userName}
          onChange={(e) => setUserName(e.target.value)}
          placeholder="Your name"
        />
      </label>

      <TagInput
        label="Goals"
        values={profileForm.goals}
        onChange={(v) => updateField('goals', v)}
        placeholder="fat loss, energy…"
      />

      <TagInput
        label="Dietary Preferences"
        values={profileForm.dietary_preferences}
        onChange={(v) => updateField('dietary_preferences', v)}
        placeholder="vegetarian…"
      />

      <TagInput
        label="Allergies"
        values={profileForm.allergies}
        onChange={(v) => updateField('allergies', v)}
        placeholder="peanuts…"
      />

      <TagInput
        label="Medications"
        values={profileForm.medications}
        onChange={(v) => updateField('medications', v)}
        placeholder="metformin…"
      />

      <label className="plain-label">
        Extra Notes
        <textarea
          className="plain-textarea"
          rows={3}
          value={profileForm.notes}
          onChange={(e) => updateField('notes', e.target.value)}
          placeholder="Night shifts, budget limits…"
        />
      </label>

      <div className="save-row">
        <button className="save-btn" type="button" onClick={handleSave} disabled={loadingProfile}>
          {loadingProfile ? 'Saving…' : 'Save Profile'}
        </button>
        {saveToast && <span className="save-toast">✓ Saved</span>}
      </div>
    </div>
  )
}
