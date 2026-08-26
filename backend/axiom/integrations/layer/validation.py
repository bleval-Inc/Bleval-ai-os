"""Data Validation — Validates incoming data against schemas and business rules."""

import json
from typing import Any, Callable, Dict, List, Optional, Tuple

from jsonschema import Draft7Validator, validate, ValidationError as JsonSchemaValidationError

from axiom.runtime.logging import RuntimeLogger

from .models import ValidationConfig, ValidationMode


class DataValidator:
    """Validates data against JSON Schema and business rules."""

    def __init__(
        self,
        config: ValidationConfig,
        logger: Optional[RuntimeLogger] = None,
    ) -> None:
        self.config = config
        self.logger = logger or RuntimeLogger()
        self._schema_validator: Optional[Draft7Validator] = None

        if config.schema:
            self._schema_validator = Draft7Validator(config.schema)

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate a single data item.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # 1. Check required fields
        for field in self.config.required_fields:
            if field not in data or data[field] is None:
                if not self.config.allow_null_required:
                    return False, f"Required field '{field}' is missing or null"

        # 2. Validate against JSON Schema
        if self._schema_validator:
            try:
                self._schema_validator.validate(data)
            except JsonSchemaValidationError as e:
                return False, f"Schema validation failed: {e.message}"

        # 3. Run business rules
        for i, rule in enumerate(self.config.business_rules):
            try:
                if not rule(data):
                    rule_name = (
                        self.config.business_rule_names[i]
                        if i < len(self.config.business_rule_names)
                        else f"rule_{i}"
                    )
                    return False, f"Business rule '{rule_name}' failed"
            except Exception as e:
                return False, f"Business rule error: {e}"

        # 4. Run custom validators
        for validator in self.config.custom_validators:
            try:
                is_valid, error = validator(data)
                if not is_valid:
                    return False, error
            except Exception as e:
                return False, f"Custom validator error: {e}"

        # 5. Type coercion (if enabled)
        if self.config.coerce_types and self._schema_validator:
            data = self._coerce_types(data)

        return True, ""

    def _coerce_types(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Coerce types based on schema."""
        if not self._schema_validator or not self._schema_validator.schema.get("properties"):
            return data

        coerced = data.copy()
        properties = self._schema_validator.schema["properties"]

        for field, schema in properties.items():
            if field not in coerced:
                continue

            field_type = schema.get("type")
            value = coerced[field]

            if value is None:
                continue

            try:
                if field_type == "string" and not isinstance(value, str):
                    coerced[field] = str(value)
                elif field_type == "integer" and not isinstance(value, int):
                    coerced[field] = int(float(value))
                elif field_type == "number" and not isinstance(value, (int, float)):
                    coerced[field] = float(value)
                elif field_type == "boolean" and not isinstance(value, bool):
                    if isinstance(value, str):
                        coerced[field] = value.lower() in ("true", "1", "yes", "on")
                    else:
                        coerced[field] = bool(value)
                elif field_type == "array" and not isinstance(value, list):
                    coerced[field] = [value]
                elif field_type == "object" and not isinstance(value, dict):
                    if isinstance(value, str):
                        coerced[field] = json.loads(value)
            except (ValueError, TypeError, json.JSONDecodeError):
                pass  # Keep original if coercion fails

        return coerced

    def validate_batch(self, data: List[Dict[str, Any]]) -> List[Tuple[bool, str]]:
        """Validate a batch of data items."""
        return [self.validate(item) for item in data]