import React, { useState } from 'react'
import TagInput from './TagInput'

const STARTER_PROMPTS = [
  "I had eggs and toast for breakfast",
  "What should I eat for muscle gain?",
  "Help me plan healthy meals on a budget",
  "I want to lose weight without feeling hungry",
]

export default function OnboardingModal({ onComplete }) {
  const [step, setStep] = useState(0)
  const [name, setName] = useState('')
  const [goals, setGoals] = useState([])
  const [dietaryPreferences, setDietaryPreferences] = useState([])

  const handleFinish = (starterPrompt) => {
    onComplete({
      name: name.trim(),
      goals,
      dietary_preferences: dietaryPreferences,
      starterPrompt,
    })
  }

  return (
    <div className="onboarding-overlay">
      <div className="onboarding-card">
        <div className="onboarding-progress">
          {[0, 1, 2].map((i) => (
            <div key={i} className={`onboarding-dot ${i <= step ? 'active' : ''}`} />
          ))}
        </div>

        {step === 0 && (
          <div className="onboarding-step">
            <h2>Welcome to NutriBot</h2>
            <p>Your AI nutrition coach. Let's get to know you.</p>
            <label className="plain-label">
              What should I call you?
              <input
                className="plain-input"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Your name"
                autoFocus
              />
            </label>
            <button
              type="button"
              className="onboarding-next-btn"
              onClick={() => setStep(1)}
            >
              Next
            </button>
          </div>
        )}

        {step === 1 && (
          <div className="onboarding-step">
            <h2>Your goals & preferences</h2>
            <p>This helps NutriBot personalize advice for you.</p>
            <TagInput
              label="Goals"
              values={goals}
              onChange={setGoals}
              placeholder="e.g. lose weight, build muscle"
            />
            <TagInput
              label="Dietary preferences"
              values={dietaryPreferences}
              onChange={setDietaryPreferences}
              placeholder="e.g. vegetarian, keto"
            />
            <div className="onboarding-btn-row">
              <button type="button" className="ghost-btn" onClick={() => setStep(0)}>Back</button>
              <button
                type="button"
                className="onboarding-next-btn"
                onClick={() => setStep(2)}
              >
                Next
              </button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="onboarding-step">
            <h2>Let's get started!</h2>
            <p>Pick a prompt or type your own after setup.</p>
            <div className="onboarding-starter-grid">
              {STARTER_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  className="starter-chip"
                  onClick={() => handleFinish(prompt)}
                >
                  {prompt}
                </button>
              ))}
            </div>
            <div className="onboarding-btn-row">
              <button type="button" className="ghost-btn" onClick={() => setStep(1)}>Back</button>
              <button
                type="button"
                className="onboarding-next-btn"
                onClick={() => handleFinish(null)}
              >
                Skip — I'll type my own
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
