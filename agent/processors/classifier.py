import re
from typing import List, Tuple
from ..models import RawItem
from ..utils.taxonomy import normalize_category

class ContentClassifier:
    """Classifies articles into core categories and extracts relevant technology tags."""
    
    CATEGORY_KEYWORDS = {
        "ai": [
            "ai", "llm", "gpt", "claude", "gemini", "llama", "deepseek", "anthropic", "openai",
            "machine learning", "neural", "transformer", "diffusion", "vision model", "agent",
            "embedding", "rag", "fine-tuning", "hugging face", "groq", "mistral", "reasoning"
        ],
        "cloud": [
            "cloud", "aws", "azure", "gcp", "google cloud", "cloudflare", "serverless", "kubernetes",
            "docker", "d1", "lambda", "edge", "database", "postgres", "sqlite", "redis", "mongodb", "s3"
        ],
        "development": [
            "react", "next.js", "javascript", "typescript", "python", "rust", "golang", "webdev",
            "frontend", "backend", "api", "framework", "library", "css", "tailwind", "node.js",
            "vue", "svelte", "compiler", "debugging", "ide", "vscode", "copilot"
        ],
        "open_source": [
            "open source", "github", "gitlab", "oss", "repository", "mit license", "apache",
            "pull request", "contributor", "self-hosted", "weights", "fork"
        ],
        "cybersecurity": [
            "security", "vulnerability", "cve", "zero-day", "exploit", "hack", "breach",
            "malware", "auth", "encryption", "firewall", "cyber", "phishing", "cisa"
        ],
        "startups": [
            "startup", "funding", "seed round", "series a", "product hunt", "launch", "founder",
            "y combinator", "venture", "acquisition", "pricing", "saas", "market"
        ]
    }

    TAG_PATTERNS = [
        r"\b(AI|LLM|Claude|GPT-4o|Gemini|Llama|React|Next\.js|TypeScript|Python|Rust|Go|Cloudflare|AWS|Azure|GCP|Docker|Kubernetes|GitHub|Copilot|Tailwind|PostgreSQL|SQLite|Ollama)\b"
    ]

    def classify(self, item: RawItem) -> Tuple[str, List[str]]:
        """Determines best category and extracted tags."""
        text = f"{item.title} {item.description} {item.content}".lower()
        
        category_scores = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = 0
            for kw in keywords:
                # Give higher weight to matches in title
                if kw in item.title.lower():
                    score += 3
                elif kw in text:
                    score += 1
            category_scores[category] = score

        best_category = max(category_scores.items(), key=lambda x: x[1])
        raw_cat = best_category[0] if best_category[1] > 0 else (item.category or "development")
        assigned_category = normalize_category(raw_cat)

        # Extract tags
        found_tags = set()
        for pattern in self.TAG_PATTERNS:
            matches = re.findall(pattern, f"{item.title} {item.description}", re.IGNORECASE)
            for m in matches:
                found_tags.add(m.capitalize() if len(m) > 3 else m.upper())

        return assigned_category, list(found_tags)[:5]
