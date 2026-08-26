"""Data Normalization — Transforms data to canonical formats."""

import re
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import phonenumbers
from email_normalize import normalize as normalize_email

from axiom.runtime.logging import RuntimeLogger

from .models import NormalizationConfig


class DataNormalizer:
    """Normalizes data to canonical formats."""

    def __init__(
        self,
        config: NormalizationConfig,
        logger: Optional[RuntimeLogger] = None,
    ) -> None:
        self.config = config
        self.logger = logger or RuntimeLogger()

    def normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a single data item."""
        result = data.copy()

        # 1. Field mapping (rename fields)
        result = self._apply_field_mapping(result)

        # 2. Type transformations
        result = self._apply_type_transformations(result)

        # 3. Value transformations
        result = self._apply_value_transformations(result)

        # 4. Standardize timestamps
        if self.config.standardize_timestamps:
            result = self._standardize_timestamps(result)

        # 5. Standardize currency
        if self.config.standardize_currency:
            result = self._standardize_currency(result)

        # 6. Standardize identifiers
        if self.config.standardize_identifiers:
            result = self._standardize_identifiers(result)

        # 7. Custom normalizers
        for normalizer in self.config.custom_normalizers:
            try:
                result = normalizer(result)
            except Exception as e:
                self.logger.warning(f"Custom normalizer failed: {e}")

        return result

    def _apply_field_mapping(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply field name mappings."""
        result = {}
        for key, value in data.items():
            new_key = self.config.field_mapping.get(key, key)
            result[new_key] = value
        return result

    def _apply_type_transformations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply type transformations."""
        result = data.copy()
        for field, target_type in self.config.type_transformations.items():
            if field in result:
                result[field] = self._coerce_value(result[field], target_type)
        return result

    def _coerce_value(self, value: Any, target_type: str) -> Any:
        """Coerce a value to target type."""
        if value is None:
            return None

        try:
            if target_type == "string":
                return str(value)
            elif target_type == "integer":
                return int(float(value))
            elif target_type == "float" or target_type == "number":
                return float(value)
            elif target_type == "boolean":
                if isinstance(value, str):
                    return value.lower() in ("true", "1", "yes", "on", "true")
                return bool(value)
            elif target_type == "datetime":
                if isinstance(value, str):
                    return self._parse_datetime(value)
                elif isinstance(value, (int, float)):
                    return datetime.fromtimestamp(value)
            elif target_type == "date":
                if isinstance(value, str):
                    return self._parse_datetime(value).date()
        except (ValueError, TypeError):
            pass
        return value

    def _parse_datetime(self, value: str) -> datetime:
        """Parse datetime from various formats."""
        formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue

        # Try ISO format
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass

        raise ValueError(f"Unable to parse datetime: {value}")

    def _apply_value_transformations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply custom value transformations."""
        result = data.copy()
        for field, transform_fn in self.config.value_transformations.items():
            if field in result:
                try:
                    result[field] = transform_fn(result[field])
                except Exception as e:
                    self.logger.warning(f"Value transformation failed for {field}: {e}")
        return result

    def _standardize_timestamps(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize timestamp fields to ISO 8601."""
        result = data.copy()
        timestamp_fields = [
            "timestamp", "created_at", "updated_at", "created", "modified",
            "date", "datetime", "time", "start_time", "end_time",
            "published_at", "fetched_at", "processed_at",
        ]

        for field in timestamp_fields:
            if field in result and result[field] is not None:
                try:
                    dt = self._coerce_value(result[field], "datetime")
                    if dt:
                        if self.config.timestamp_format == "iso8601":
                            result[field] = dt.isoformat() + "Z"
                        elif self.config.timestamp_format == "unix":
                            result[field] = int(dt.timestamp())
                        elif self.config.timestamp_format == "unix_ms":
                            result[field] = int(dt.timestamp() * 1000)
                        elif self.config.timestamp_format == "rfc3339":
                            result[field] = dt.isoformat()
                except (ValueError, TypeError):
                    pass  # Keep original if parsing fails

        return result

    def _standardize_currency(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize currency fields to base currency."""
        result = data.copy()
        currency_fields = [
            "amount", "price", "cost", "value", "total", "subtotal",
            "revenue", "profit", "margin", "budget", "spend",
        ]

        for field in currency_fields:
            if field in result and result[field] is not None:
                try:
                    # If it's a string with currency symbol, extract number
                    if isinstance(result[field], str):
                        # Remove currency symbols and commas
                        cleaned = re.sub(r"[^\d.-]", "", result[field])
                        result[field] = float(cleaned)
                    elif isinstance(result[field], (int, float)):
                        result[field] = float(result[field])
                except (ValueError, TypeError):
                    pass

        # Add currency metadata
        if any(f in result for f in currency_fields):
            result["_currency"] = self.config.base_currency

        return result

    def _standardize_identifiers(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize identifiers (emails, phones, UUIDs)."""
        result = data.copy()

        # Standardize emails
        email_fields = ["email", "email_address", "contact_email", "from_email", "to_email"]
        for field in email_fields:
            if field in result and result[field]:
                try:
                    result[field] = normalize_email(str(result[field]))
                except Exception:
                    pass

        # Standardize phone numbers
        phone_fields = ["phone", "phone_number", "mobile", "telephone", "contact_phone"]
        for field in phone_fields:
            if field in result and result[field]:
                try:
                    parsed = phonenumbers.parse(str(result[field]), None)
                    if phonenumbers.is_valid_number(parsed):
                        result[field] = phonenumbers.format_number(
                            parsed, phonenumbers.PhoneNumberFormat.E164
                        )
                except Exception:
                    pass

        # Standardize UUIDs (ensure lowercase)
        uuid_fields = ["id", "uuid", "guid", "identifier", "reference_id"]
        for field in uuid_fields:
            if field in result and result[field]:
                try:
                    # Just ensure it's a valid UUID format and lowercase
                    val = str(result[field]).lower().strip()
                    # Basic UUID validation
                    if re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", val):
                        result[field] = val
                except Exception:
                    pass

        return result

    def normalize_batch(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize a batch of data items."""
        return [self.normalize(item) for item in data]