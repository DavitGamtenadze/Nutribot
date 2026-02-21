from app.models.schemas import CoachResponse


def test_coach_response_schema_parses() -> None:
    payload = {
        "summary": "You are close to your goal but consistency needs work.",
        "priorities": [
            {
                "title": "Protein anchor",
                "action": "Add protein with breakfast.",
                "why_it_matters": "Improves satiety and recovery.",
                "timeframe": "today",
            }
        ],
        "meal_focus": ["Add one serving of vegetables at dinner."],
        "supplement_options": ["Creatine monohydrate can be considered."],
        "safety_watchouts": ["This is not medical advice."],
        "follow_up_questions": ["How many meals do you eat each day?"],
        "disclaimer": "General education only.",
    }

    parsed = CoachResponse.model_validate(payload)
    assert parsed.priorities[0].title == "Protein anchor"
    assert parsed.supplement_options[0] == "Creatine monohydrate can be considered."
