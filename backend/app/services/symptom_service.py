SYMPTOM_MAP = {
    "tooth": "Dental",
    "gum": "Dental",
    "bone": "Orthopedic",
    "knee": "Orthopedic",
    "fever": "General Medicine",
    "cough": "General Medicine",
    "skin": "Dermatology",
    "rash": "Dermatology",
    "eyes": "Ophthalmology",
}


def suggest_specialization(symptoms: list[str]) -> tuple[str, str]:
    normalized = " ".join(symptoms).lower()
    for key, specialization in SYMPTOM_MAP.items():
        if key in normalized:
            return (
                f"Based on symptoms, consider booking a {specialization} specialist.",
                specialization,
            )
    return (
        "Symptoms are broad. Start with General Medicine for initial evaluation.",
        "General Medicine",
    )
