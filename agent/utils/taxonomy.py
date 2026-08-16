import re
from typing import Optional

CANONICAL_SYNONYMS = {
    # AI & ML
    "ai": "ai",
    "artificial intelligence": "ai",
    "artificial-intelligence": "ai",
    "artificial_intelligence": "ai",
    "machine learning": "ai",
    "machine-learning": "ai",
    "machine_learning": "ai",
    "ml": "ai",
    "genai": "ai",
    "generative ai": "ai",
    "deep learning": "ai",
    "deep-learning": "ai",
    "deep_learning": "ai",
    "llm": "ai",
    "llms": "ai",
    
    # Cloud & DevOps
    "cloud": "cloud",
    "cloud computing": "cloud",
    "cloud-computing": "cloud",
    "cloud_computing": "cloud",
    "cloud infrastructure": "cloud",
    "cloud-infrastructure": "cloud",
    "cloud_infrastructure": "cloud",
    "devops": "cloud",
    "serverless": "cloud",
    "infrastructure": "cloud",
    "cloud & infrastructure": "cloud",
    "cloud-native": "cloud",
    
    # Development & Programming
    "development": "development",
    "software development": "development",
    "software-development": "development",
    "software_development": "development",
    "software dev": "development",
    "software-dev": "development",
    "software_dev": "development",
    "programming": "development",
    "software engineering": "development",
    "coding": "development",
    "web development": "development",
    "webdev": "development",
    "frontend": "development",
    "backend": "development",
    "fullstack": "development",
    "developer tools": "development",
    "devtools": "development",
    
    # Open Source
    "open_source": "open_source",
    "open source": "open_source",
    "open-source": "open_source",
    "opensource": "open_source",
    "oss": "open_source",
    "foss": "open_source",
    "free and open source": "open_source",
    
    # Cybersecurity
    "cybersecurity": "cybersecurity",
    "cyber security": "cybersecurity",
    "cyber-security": "cybersecurity",
    "cyber_security": "cybersecurity",
    "security": "cybersecurity",
    "infosec": "cybersecurity",
    "appsec": "cybersecurity",
    
    # Startups & Business
    "startups": "startups",
    "startup": "startups",
    "start-ups": "startups",
    "start_ups": "startups",
    "start-up": "startups",
    "start_up": "startups",
    "venture": "startups",
    "entrepreneurship": "startups",
    
    # Education & Learning
    "education": "education",
    "learning": "education",
    "student": "education",
    "students": "education",
    "training": "education",
    "tutorial": "education",
    "tutorials": "education",
}

def normalize_category(category: Optional[str]) -> str:
    """
    Normalizes raw category strings to canonical lowercase taxonomy slugs.
    Preserves new distinct domains cleanly (e.g. 'robotics' -> 'robotics').
    """
    if not category or not isinstance(category, str):
        return "development"

    cleaned = category.strip().lower()
    # Normalize punctuation and multiple spacing/underscores
    cleaned_spaces = re.sub(r"[\s_-]+", " ", cleaned).strip()
    cleaned_underscores = re.sub(r"[\s_-]+", "_", cleaned).strip()

    # Check direct dictionary matches
    if cleaned in CANONICAL_SYNONYMS:
        return CANONICAL_SYNONYMS[cleaned]
    if cleaned_spaces in CANONICAL_SYNONYMS:
        return CANONICAL_SYNONYMS[cleaned_spaces]
    if cleaned_underscores in CANONICAL_SYNONYMS:
        return CANONICAL_SYNONYMS[cleaned_underscores]

    # Clean fallback for new categories (e.g. 'Robotics & Automation' -> 'robotics_automation')
    slug = re.sub(r"[^\w\s-]", "", cleaned).strip()
    slug = re.sub(r"[\s-]+", "_", slug)
    return slug or "development"
