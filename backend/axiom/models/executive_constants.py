"""Executive organization and department mappings.

Shared constants to avoid circular imports between executive_loop and executive_intelligence.
"""

from typing import Dict, List

# Executive → Organization mapping
EXECUTIVE_ORGS: Dict[str, str] = {
    "jenson": "bleval",
    "valta_prime": "hov",
    "yamako": "personal",
}

# Executive → Department mapping
EXECUTIVE_DEPTS: Dict[str, List[str]] = {
    "jenson": ["sales", "marketing", "development", "operations", "finance"],
    "valta_prime": ["brand", "creative", "research", "content", "growth", "operations"],
    "yamako": ["productivity", "knowledge"],
}