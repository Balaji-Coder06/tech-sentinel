import re
from typing import Optional

TEMPLATE_EXPRESSION_PATTERNS = [
    re.compile(r"\{\{.*?\}\}", re.DOTALL),
    re.compile(r"\$\{.*?\}", re.DOTALL),
    re.compile(r"\$\([\'\"].*?[\'\"]\)", re.DOTALL),
    re.compile(r"<\%.*?\%>", re.DOTALL),
    re.compile(r"\[%.*?%\]", re.DOTALL),
]

INVALID_TITLE_EXACT = {
    "undefined", "null", "none", "nan", "n/a", "[object object]", "untitled", ""
}

def is_valid_title(title: Optional[str]) -> bool:
    """Checks if a title is clean and free of unrendered template expressions or invalid placeholders."""
    if not title or not isinstance(title, str):
        return False
    
    cleaned = title.strip()
    if len(cleaned) < 3:
        return False
        
    if cleaned.lower() in INVALID_TITLE_EXACT:
        return False
        
    for pat in TEMPLATE_EXPRESSION_PATTERNS:
        if pat.search(cleaned):
            return False
            
    return True
