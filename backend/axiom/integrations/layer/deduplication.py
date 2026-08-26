"""Data Deduplication — Removes duplicate records using configurable strategies."""

import hashlib
import json
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

from difflib import SequenceMatcher

from axiom.runtime.logging import RuntimeLogger

from .models import DeduplicationConfig, DeduplicationStrategy


class Deduplicator:
    """Deduplicates data using configurable strategies."""

    def __init__(
        self,
        config: DeduplicationConfig,
        logger: Optional[RuntimeLogger] = None,
    ) -> None:
        self.config = config
        self.logger = logger or RuntimeLogger()
        self._seen_hashes: Set[str] = set()
        self._seen_keys: Dict[str, Dict[str, Any]] = {}

    def deduplicate(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate a list of records."""
        if not data:
            return []

        if self.config.strategy == DeduplicationStrategy.CUSTOM and self.config.custom_dedup_fn:
            return self.config.custom_dedup_fn(data)

        if self.config.strategy == DeduplicationStrategy.EXACT_MATCH:
            return self._deduplicate_exact(data)
        elif self.config.strategy == DeduplicationStrategy.FUZZY_MATCH:
            return self._deduplicate_fuzzy(data)
        elif self.config.strategy == DeduplicationStrategy.SEMANTIC_HASH:
            return self._deduplicate_semantic_hash(data)
        elif self.config.strategy == DeduplicationStrategy.COMPOSITE_KEY:
            return self._deduplicate_composite_key(data)
        elif self.config.strategy == DeduplicationStrategy.TIME_WINDOW:
            return self._deduplicate_time_window(data)
        else:
            # Default to exact match
            return self._deduplicate_exact(data)

    def _deduplicate_exact(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate by exact field match."""
        seen = set()
        result = []

        for item in data:
            # Build key from key_fields or all fields
            if self.config.key_fields:
                key_parts = [str(item.get(f, "")) for f in self.config.key_fields]
            else:
                # Use all fields, sorted for consistency
                key_parts = [f"{k}:{v}" for k, v in sorted(item.items())]

            key = "|".join(key_parts)

            if key not in seen:
                seen.add(key)
                result.append(item)

        return result

    def _deduplicate_fuzzy(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate using fuzzy matching on specified fields."""
        result = []

        for item in data:
            is_duplicate = False

            for existing in result:
                if self._fuzzy_match(item, existing):
                    is_duplicate = True
                    # Apply keep strategy
                    if self._should_replace(existing, item):
                        result.remove(existing)
                        result.append(item)
                    break

            if not is_duplicate:
                result.append(item)

        return result

    def _fuzzy_match(self, item1: Dict[str, Any], item2: Dict[str, Any]) -> bool:
        """Check if two items match fuzzily on configured fields."""
        if not self.config.fuzzy_fields:
            return False

        scores = []
        for field in self.config.fuzzy_fields:
            val1 = str(item1.get(field, ""))
            val2 = str(item2.get(field, ""))

            if not val1 or not val2:
                continue

            similarity = SequenceMatcher(None, val1.lower(), val2.lower()).ratio()
            scores.append(similarity)

        if not scores:
            return False

        avg_score = sum(scores) / len(scores)
        return avg_score >= self.config.fuzzy_threshold

    def _deduplicate_semantic_hash(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate using semantic hash of normalized content."""
        seen_hashes = set()
        result = []

        for item in data:
            # Create canonical representation for hashing
            canonical = self._canonicalize(item)
            item_hash = hashlib.sha256(canonical.encode()).hexdigest()[:32]

            if item_hash not in seen_hashes:
                seen_hashes.add(item_hash)
                result.append(item)

        return result

    def _canonicalize(self, item: Dict[str, Any]) -> str:
        """Create canonical string representation for hashing."""
        # Sort keys and serialize
        return json.dumps(item, sort_keys=True, default=str)

    def _deduplicate_composite_key(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate using composite key from multiple fields."""
        seen = set()
        result = []

        for item in data:
            if not self.config.composite_fields:
                # Fall back to exact match
                key_parts = [str(item.get(f, "")) for f in self.config.key_fields] if self.config.key_fields else [f"{k}:{v}" for k, v in sorted(item.items())]
            else:
                key_parts = [str(item.get(f, "")) for f in self.config.composite_fields]

            key = "|".join(key_parts)

            if key not in seen:
                seen.add(key)
                result.append(item)

        return result

    def _deduplicate_time_window(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate within a time window."""
        # Sort by time field
        time_field = self.config.time_field
        try:
            sorted_data = sorted(data, key=lambda x: self._parse_time(x.get(time_field)))
        except Exception:
            # If time parsing fails, fall back to exact match
            return self._deduplicate_exact(data)

        result = []
        window_start = None

        for item in sorted_data:
            item_time = self._parse_time(item.get(time_field))

            if window_start is None:
                window_start = item_time
                result.append(item)
                continue

            # Check if within time window
            if (item_time - window_start).total_seconds() <= self.config.time_window_seconds:
                # Within window - check for duplicate on key fields
                is_dup = False
                for existing in result:
                    if self._keys_match(item, existing):
                        is_dup = True
                        if self._should_replace(existing, item):
                            result.remove(existing)
                            result.append(item)
                        break

                if not is_dup:
                    result.append(item)
            else:
                # New window
                window_start = item_time
                result.append(item)

        return result

    def _parse_time(self, value: Any) -> datetime:
        """Parse time value to datetime."""
        if value is None:
            return datetime.utcnow()

        if isinstance(value, datetime):
            return value

        if isinstance(value, (int, float)):
            # Assume unix timestamp
            return datetime.fromtimestamp(value)

        if isinstance(value, str):
            # Try ISO format
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                pass

            # Try common formats
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y/%m/%d %H:%M:%S",
                "%d/%m/%Y %H:%M:%S",
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue

        return datetime.utcnow()

    def _keys_match(self, item1: Dict[str, Any], item2: Dict[str, Any]) -> bool:
        """Check if key fields match between two items."""
        if self.config.key_fields:
            for field in self.config.key_fields:
                if item1.get(field) != item2.get(field):
                    return False
            return True

        # If no key fields, compare all
        return item1 == item2

    def _should_replace(self, existing: Dict[str, Any], new_item: Dict[str, Any]) -> bool:
        """Determine if new item should replace existing based on keep strategy."""
        strategy = self.config.keep_strategy
        field = self.config.keep_field

        if strategy == "first":
            return False
        elif strategy == "last":
            return True
        elif strategy == "max_field" and field:
            return self._get_comparable(new_item.get(field)) > self._get_comparable(existing.get(field))
        elif strategy == "min_field" and field:
            return self._get_comparable(new_item.get(field)) < self._get_comparable(existing.get(field))

        return False

    def _get_comparable(self, value: Any) -> Any:
        """Get comparable value for max/min comparison."""
        if value is None:
            return float("-inf")
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return value
        if isinstance(value, datetime):
            return value.timestamp()
        return value

    def reset(self) -> None:
        """Reset deduplication state (for new batch)."""
        self._seen_hashes.clear()
        self._seen_keys.clear()