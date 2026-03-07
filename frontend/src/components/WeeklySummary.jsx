import React from 'react'

function ProgressRing({ percent }) {
  const r = 30
  const c = 2 * Math.PI * r
  const offset = c - (percent / 100) * c

  return (
    <svg className="progress-ring" width="72" height="72" viewBox="0 0 72 72">
      <circle cx="36" cy="36" r={r} fill="none" stroke="var(--line)" strokeWidth="5" />
      <circle
        cx="36" cy="36" r={r} fill="none"
        stroke="var(--accent)" strokeWidth="5"
        strokeDasharray={c} strokeDashoffset={offset}
        strokeLinecap="round"
        transform="rotate(-90 36 36)"
      />
      <text x="36" y="40" textAnchor="middle" fontSize="14" fontWeight="700" fill="var(--ink)">
        {percent}%
      </text>
    </svg>
  )
}

export default function WeeklySummary({ data }) {
  if (!data) return null

  return (
    <div className="weekly-summary-card">
      <h3 className="weekly-title">This Week</h3>
      <div className="weekly-body">
        <ProgressRing percent={data.consistency_pct} />
        <div className="weekly-stats">
          <div className="weekly-stat">
            <span className="stat-value">{data.total_meals}</span>
            <span className="stat-label">meals</span>
          </div>
          <div className="weekly-stat">
            <span className="stat-value">{data.active_days}/7</span>
            <span className="stat-label">active days</span>
          </div>
        </div>
      </div>
      {data.recurring_themes?.length > 0 && (
        <div className="weekly-themes">
          <span className="themes-label">Recurring:</span>
          {data.recurring_themes.map((t) => (
            <span key={t} className="theme-pill">{t}</span>
          ))}
        </div>
      )}
    </div>
  )
}
