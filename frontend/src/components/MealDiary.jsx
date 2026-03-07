import React from 'react'

function groupByDate(meals) {
  const groups = {}
  for (const meal of meals) {
    const date = new Date(meal.created_at).toLocaleDateString('en-US', {
      weekday: 'short', month: 'short', day: 'numeric',
    })
    if (!groups[date]) groups[date] = []
    groups[date].push(meal)
  }
  return groups
}

export default function MealDiary({ meals }) {
  if (!meals.length) {
    return (
      <div className="diary-empty">
        <p>No meals logged yet. Start chatting to build your food diary.</p>
      </div>
    )
  }

  const grouped = groupByDate(meals)

  return (
    <div className="diary-scroll">
      {Object.entries(grouped).map(([date, items]) => (
        <div key={date} className="diary-day">
          <h3 className="diary-date">{date}</h3>
          {items.map((meal) => (
            <div key={meal.id} className="diary-card">
              {meal.image_url && (
                <img
                  src={meal.image_url.startsWith('/') ? `${window.__API_BASE || ''}${meal.image_url}` : meal.image_url}
                  alt="Meal"
                  className="diary-img"
                />
              )}
              <div className="diary-card-body">
                {meal.meal_text && <p className="diary-text">{meal.meal_text}</p>}
                {meal.summary && <p className="diary-summary">{meal.summary}</p>}
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}
