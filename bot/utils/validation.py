import re
from bot.config import MIN_INTRO_LENGTH

# Keywords that suggest each section of the intro format
LOCATION_KEYWORDS = [
    "based in", "from", "located", "living in", "stay in",
    "kuala lumpur", "kl", "penang", "johor", "malaysia",
    "singapore", "remote", "📍",
]

CONTRIBUTION_KEYWORDS = [
    "contribute", "looking to", "want to", "help with",
    "building", "working on", "interested in", "passionate about",
    "🤝", "looking forward",
]

FUN_FACT_KEYWORDS = [
    "fun fact", "interesting", "hobby", "love", "enjoy",
    "first", "fun thing", "🧑‍🎓", "😄", "😊",
]

IDENTITY_KEYWORDS = [
    "i'm", "i am", "my name", "i do", "i work",
    "developer", "designer", "builder", "founder", "student",
    "engineer", "marketer", "community", "👋",
]


def _has_keywords(text: str, keywords: list[str]) -> bool:
    return any(kw in text for kw in keywords)


def validate_intro(text: str) -> tuple[bool, list[str]]:
    """Validate an intro message against heuristic rules.

    Returns (is_acceptable, missing_hints) where:
        - is_acceptable: True if the intro is good enough
        - missing_hints: list of suggestions for improvement
    """
    if not text:
        return False, ["Your message appears to be empty."]

    lower = re.sub(r"\s+", " ", text.lower().strip())
    missing: list[str] = []
    score = 0

    if len(text.strip()) >= MIN_INTRO_LENGTH:
        score += 1
    else:
        missing.append("Add a bit more detail (at least a few sentences).")

    if _has_keywords(lower, IDENTITY_KEYWORDS):
        score += 1
    else:
        missing.append("Tell us who you are and what you do.")

    if _has_keywords(lower, LOCATION_KEYWORDS):
        score += 1
    else:
        missing.append("Mention where you're based.")

    if _has_keywords(lower, FUN_FACT_KEYWORDS):
        score += 1
    else:
        missing.append("Share a fun fact about yourself.")

    if _has_keywords(lower, CONTRIBUTION_KEYWORDS):
        score += 1
    else:
        missing.append("Tell us how you'd like to contribute.")

    # Accept if at least 3 out of 5 criteria met
    is_acceptable = score >= 3
    return is_acceptable, missing
