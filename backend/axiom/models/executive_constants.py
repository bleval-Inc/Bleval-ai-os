"""Executive organization and department mappings.

Shared constants to avoid circular imports between executive_loop and executive_intelligence.
"""

from __future__ import annotations

from typing import Dict, List

# Executive → Organization mapping
EXECUTIVE_ORGS: Dict[str, str] = {
    "jenson": "bleval_inc",
    "valta_prime": "house_of_valta",
    "yamako": "personal",
}

# Executive → Department mapping
EXECUTIVE_DEPTS: Dict[str, List[str]] = {
    "jenson": ["sales", "marketing", "development", "operations", "finance"],
    "valta_prime": ["trading", "risk", "brand", "creative", "research", "content", "growth", "operations"],
    "yamako": ["operations", "productivity", "knowledge"],
}