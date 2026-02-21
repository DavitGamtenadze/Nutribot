import React from 'react'

function PlanEmptyIcon() {
  return (
    <svg
      className="plan-empty-icon-svg"
      width="48"
      height="48"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <path d="M14 2v6h6M9 13h6M9 17h6" />
    </svg>
  )
}

function SkeletonPlan() {
  return (
    <>
      <div className="skeleton skeleton-line" style={{ width: '90%' }} />
      <div className="skeleton skeleton-line" style={{ width: '70%' }} />
      <div className="skeleton skeleton-card" />
      <div className="skeleton skeleton-card" />
      <div className="skeleton skeleton-card" />
    </>
  )
}

function PriorityCard({ item }) {
  return (
    <div className="priority-card">
      <h4>{item.title}</h4>
      <p><strong>Action:</strong> {item.action}</p>
      <p><strong>Why:</strong> {item.why_it_matters}</p>
      <p><strong>When:</strong> {item.timeframe}</p>
    </div>
  )
}

export default function ResponseCard({ response, conversationId, error, loading }) {
  return (
    <div className="plan-column">
      <div className="plan-header">
        <h2>Plan Board</h2>
        {conversationId && <span className="chip">#{conversationId}</span>}
      </div>

      <div className="plan-scroll">
        {error && (
          <div className="plan-alert">
            <h3>Couldn't build the plan</h3>
            <p>{error}</p>
          </div>
        )}

        {loading && !error && <SkeletonPlan />}

        {!loading && !error && !response && (
          <div className="plan-empty">
            <div className="plan-empty-icon">
              <PlanEmptyIcon />
            </div>
            <p>Send a check-in to get your prioritised action plan.</p>
          </div>
        )}

        {!loading && !error && response && (
          <>
            <p className="plan-summary">{response.summary}</p>

            <div className="plan-section-title">Top Priorities</div>
            {response.priorities.map((item, i) => (
              <PriorityCard key={`${item.title}-${i}`} item={item} />
            ))}
            {!response.priorities.length && (
              <p className="empty-note">No priorities yet.</p>
            )}

            <div className="plan-section-title">Meal Focus</div>
            <div className="plan-list-section">
              <ul>
                {response.meal_focus.map((item, i) => <li key={i}>{item}</li>)}
                {!response.meal_focus.length && <li>No meal guidance yet.</li>}
              </ul>
            </div>

            <div className="plan-section-title">Supplement Options</div>
            <div className="plan-list-section">
              <ul>
                {response.supplement_options.map((item, i) => <li key={i}>{item}</li>)}
                {!response.supplement_options.length && <li>No supplement notes.</li>}
              </ul>
            </div>

            <div className="plan-section-title">Safety Watchouts</div>
            <div className="plan-list-section">
              <ul>
                {response.safety_watchouts.map((item, i) => <li key={i}>{item}</li>)}
                {!response.safety_watchouts.length && <li>No safety watchouts.</li>}
              </ul>
            </div>

            <div className="plan-section-title">Follow-up Questions</div>
            <div className="plan-list-section">
              <ul>
                {response.follow_up_questions.map((item, i) => <li key={i}>{item}</li>)}
                {!response.follow_up_questions.length && <li>No follow-up questions.</li>}
              </ul>
            </div>

            <p className="plan-disclaimer">{response.disclaimer}</p>
          </>
        )}
      </div>
    </div>
  )
}
