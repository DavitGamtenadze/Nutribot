import React, { useState, useRef } from 'react'

export default function TagInput({ label, values, onChange, placeholder }) {
  const [inputVal, setInputVal] = useState('')
  const inputRef = useRef(null)

  const addTag = (raw) => {
    const trimmed = raw.trim().replace(/,+$/, '')
    if (!trimmed) return
    const next = [...values.filter((v) => v !== trimmed), trimmed]
    onChange(next)
    setInputVal('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      addTag(inputVal)
    } else if (e.key === 'Backspace' && inputVal === '' && values.length) {
      onChange(values.slice(0, -1))
    }
  }

  const handleBlur = () => {
    if (inputVal.trim()) addTag(inputVal)
  }

  const removeTag = (tag) => onChange(values.filter((v) => v !== tag))

  return (
    <label className="tag-input-label">
      {label}
      <div className="tag-input-box" onClick={() => inputRef.current?.focus()}>
        {values.map((tag) => (
          <span key={tag} className="tag-chip">
            {tag}
            <button
              type="button"
              className="tag-remove"
              onClick={(e) => { e.stopPropagation(); removeTag(tag) }}
              aria-label={`Remove ${tag}`}
            >
              ×
            </button>
          </span>
        ))}
        <input
          ref={inputRef}
          className="tag-input-inner"
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={handleBlur}
          placeholder={values.length === 0 ? placeholder : ''}
        />
      </div>
    </label>
  )
}
