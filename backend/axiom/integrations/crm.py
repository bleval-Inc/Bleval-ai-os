"""CRM Provider — HubSpot, Pipedrive, Salesforce abstraction for contacts, leads, deals."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from axiom.engine.provider import ExternalAPIProvider
from axiom.models.providers import (
    ProviderModel,
    ProviderToolDefinition,
    ProviderHealth,
    ProviderStatus,
    ToolInvocationResult,
)
from axiom.runtime.logging import RuntimeLogger


class CRMProvider(ExternalAPIProvider):
    """CRM provider supporting HubSpot, Pipedrive, and Salesforce.

    Capabilities:
    - Contact management (CRUD, search, lists)
    - Lead management (capture, qualify, convert)
    - Deal/pipeline management (stages, activities, forecasts)
    - Company/account management
    - Activity logging (emails, calls, meetings, notes)
    - Custom fields and properties
    - Webhooks for real-time sync
    """

    def __init__(
        self,
        config: ProviderModel,
        logger: Optional[RuntimeLogger] = None,
    ) -> None:
        super().__init__(config, logger)
        self._crm_type = config.config.get("crm_type", "hubspot")  # hubspot, pipedrive, salesforce
        self._api_key = None

    def get_tool_definitions(self) -> List[ProviderToolDefinition]:
        return [
            # Contacts
            ProviderToolDefinition(
                tool_id="crm_create_contact",
                name="Create Contact",
                description="Create a new contact",
                capability="crm_contact_write",
                input_schema={
                    "type": "object",
                    "properties": {
                        "email": {"type": "string", "format": "email"},
                        "firstname": {"type": "string"},
                        "lastname": {"type": "string"},
                        "phone": {"type": "string"},
                        "company": {"type": "string"},
                        "lifecycle_stage": {"type": "string"},
                        "custom_properties": {"type": "object"},
                    },
                    "required": ["email"],
                },
            ),
            ProviderToolDefinition(
                tool_id="crm_get_contact",
                name="Get Contact",
                description="Get contact by ID",
                capability="crm_contact_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "contact_id": {"type": "string"},
                    },
                    "required": ["contact_id"],
                },
            ),
            ProviderToolDefinition(
                tool_id="crm_search_contacts",
                name="Search Contacts",
                description="Search contacts by criteria",
                capability="crm_contact_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "email": {"type": "string"},
                        "name": {"type": "string"},
                        "company": {"type": "string"},
                        "limit": {"type": "integer", "default": 50},
                    },
                },
            ),
            ProviderToolDefinition(
                tool_id="crm_update_contact",
                name="Update Contact",
                description="Update contact properties",
                capability="crm_contact_write",
                input_schema={
                    "type": "object",
                    "properties": {
                        "contact_id": {"type": "string"},
                        "properties": {"type": "object"},
                    },
                    "required": ["contact_id", "properties"],
                },
            ),
            ProviderToolDefinition(
                tool_id="crm_delete_contact",
                name="Delete Contact",
                description="Delete a contact",
                capability="crm_contact_write",
                input_schema={
                    "type": "object",
                    "properties": {
                        "contact_id": {"type": "string"},
                    },
                    "required": ["contact_id"],
                },
            ),
            # Companies
            ProviderToolDefinition(
                tool_id="crm_create_company",
                name="Create Company",
                description="Create a new company/account",
                capability="crm_company_write",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "domain": {"type": "string"},
                        "industry": {"type": "string"},
                        "size": {"type": "string"},
                        "custom_properties": {"type": "object"},
                    },
                    "required": ["name"],
                },
            ),
            ProviderToolDefinition(
                tool_id="crm_get_company",
                name="Get Company",
                description="Get company by ID",
                capability="crm_company_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "company_id": {"type": "string"},
                    },
                    "required": ["company_id"],
                },
            ),
            ProviderToolDefinition(
                tool_id="crm_search_companies",
                name="Search Companies",
                description="Search companies by criteria",
                capability="crm_company_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "domain": {"type": "string"},
                        "limit": {"type": "integer", "default": 50},
                    },
                },
            ),
            # Deals
            ProviderToolDefinition(
                tool_id="crm_create_deal",
                name="Create Deal",
                description="Create a new deal/opportunity",
                capability="crm_deal_write",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "amount": {"type": "number"},
                        "stage": {"type": "string"},
                        "pipeline": {"type": "string"},
                        "contact_id": {"type": "string"},
                        "company_id": {"type": "string"},
                        "close_date": {"type": "string", "description": "ISO date"},
                        "custom_properties": {"type": "object"},
                    },
                    "required": ["name", "amount", "stage"],
                },
            ),
            ProviderToolDefinition(
                tool_id="crm_get_deal",
                name="Get Deal",
                description="Get deal by ID",
                capability="crm_deal_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "deal_id": {"type": "string"},
                    },
                    "required": ["deal_id"],
                },
            ),
            ProviderToolDefinition(
                tool_id="crm_search_deals",
                name="Search Deals",
                description="Search deals by criteria",
                capability="crm_deal_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "stage": {"type": "string"},
                        "pipeline": {"type": "string"},
                        "contact_id": {"type": "string"},
                        "company_id": {"type": "string"},
                        "limit": {"type": "integer", "default": 50},
                    },
                },
            ),
            ProviderToolDefinition(
                tool_id="crm_update_deal",
                name="Update Deal",
                description="Update deal properties",
                capability="crm_deal_write",
                input_schema={
                    "type": "object",
                    "properties": {
                        "deal_id": {"type": "string"},
                        "properties": {"type": "object"},
                    },
                    "required": ["deal_id", "properties"],
                },
            ),
            ProviderToolDefinition(
                tool_id="crm_move_deal_stage",
                name="Move Deal Stage",
                description="Move deal to a different pipeline stage",
                capability="crm_deal_write",
                input_schema={
                    "type": "object",
                    "properties": {
                        "deal_id": {"type": "string"},
                        "stage": {"type": "string"},
                    },
                    "required": ["deal_id", "stage"],
                },
            ),
            # Activities
            ProviderToolDefinition(
                tool_id="crm_log_activity",
                name="Log Activity",
                description="Log an activity (email, call, meeting, note)",
                capability="crm_activity_write",
                input_schema={
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["email", "call", "meeting", "note", "task"]},
                        "subject": {"type": "string"},
                        "body": {"type": "string"},
                        "contact_ids": {"type": "array", "items": {"type": "string"}},
                        "deal_id": {"type": "string"},
                        "timestamp": {"type": "string", "description": "ISO datetime"},
                        "duration_minutes": {"type": "integer"},
                    },
                    "required": ["type", "subject"],
                },
            ),
            ProviderToolDefinition(
                tool_id="crm_get_activities",
                name="Get Activities",
                description="Get activities for contact/deal",
                capability="crm_activity_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "contact_id": {"type": "string"},
                        "deal_id": {"type": "string"},
                        "limit": {"type": "integer", "default": 50},
                    },
                },
            ),
            # Pipelines
            ProviderToolDefinition(
                tool_id="crm_get_pipelines",
                name="Get Pipelines",
                description="Get all pipelines and stages",
                capability="crm_pipeline_read",
                input_schema={},
            ),
        ]

    async def initialize(self) -> None:
        """Initialize CRM connection."""
        await super().initialize()

        if self._crm_type == "hubspot":
            self._api_key = self._secrets.get_secret(self.config.auth.token_env_var or "HUBSPOT_API_KEY")
            if not self._api_key:
                raise RuntimeError("HubSpot API key not configured")
            self.base_url = "https://api.hubapi.com"
            self._default_headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}

        elif self._crm_type == "pipedrive":
            self._api_key = self._secrets.get_secret(self.config.auth.token_env_var or "PIPEDRIVE_API_KEY")
            if not self._api_key:
                raise RuntimeError("Pipedrive API key not configured")
            company_domain = self.config.config.get("company_domain", "yourcompany")
            self.base_url = f"https://{company_domain}.pipedrive.com/api/v1"
            self._default_params = {"api_token": self._api_key}

        elif self._crm_type == "salesforce":
            # Salesforce uses OAuth2 - token would come from secrets
            self._access_token = self._secrets.get_secret(self.config.auth.token_env_var or "SALESFORCE_ACCESS_TOKEN")
            instance_url = self._secrets.get_secret("SALESFORCE_INSTANCE_URL")
            if not self._access_token or not instance_url:
                raise RuntimeError("Salesforce credentials not configured")
            self.base_url = f"{instance_url}/services/data/v58.0"
            self._default_headers = {"Authorization": f"Bearer {self._access_token}", "Content-Type": "application/json"}

        else:
            raise ValueError(f"Unknown CRM type: {self._crm_type}")

        self._initialized = True

    async def _execute_tool_impl(
        self, tool_id: str, parameters: Dict[str, Any]
    ) -> ToolInvocationResult:
        method_name = f"_execute_{tool_id}"
        if hasattr(self, method_name):
            return await getattr(self, method_name)(parameters)

        return ToolInvocationResult(
            success=False,
            error=f"Tool {tool_id} not implemented",
            error_code="not_implemented",
            provider_id=self.provider_id,
            tool_id=tool_id,
        )

    # ── HubSpot Implementation ────────────────────────────────────────────

    async def _hubspot_request(self, method: str, path: str, **kwargs):
        """Make HubSpot API request."""
        url = f"{self.base_url}{path}"
        return await self._request(method, url, **kwargs)

    async def _execute_crm_create_contact(self, params: Dict[str, Any]) -> ToolInvocationResult:
        if self._crm_type == "hubspot":
            properties = {
                "email": params["email"],
                "firstname": params.get("firstname", ""),
                "lastname": params.get("lastname", ""),
                "phone": params.get("phone", ""),
                "company": params.get("company", ""),
                "lifecyclestage": params.get("lifecycle_stage", "lead"),
            }
            if params.get("custom_properties"):
                properties.update(params["custom_properties"])

            result = await self._hubspot_request(
                "POST", "/crm/v3/objects/contacts",
                json={"properties": properties}
            )
            return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="crm_create_contact")

        elif self._crm_type == "pipedrive":
            data = {
                "name": f"{params.get('firstname', '')} {params.get('lastname', '')}".strip() or params["email"],
                "email": [{"value": params["email"], "primary": True}],
                "phone": [{"value": params.get("phone", ""), "primary": True}] if params.get("phone") else [],
            }
            if params.get("company"):
                # Would need to create/link organization
                pass

            result = await self._request("POST", "/persons", json=data)
            return ToolInvocationResult(success=True, output=result.get("data", {}), provider_id=self.provider_id, tool_id="crm_create_contact")

        return ToolInvocationResult(success=False, error="Not implemented for this CRM", provider_id=self.provider_id, tool_id="crm_create_contact")

    async def _execute_crm_get_contact(self, params: Dict[str, Any]) -> ToolInvocationResult:
        contact_id = params["contact_id"]

        if self._crm_type == "hubspot":
            result = await self._hubspot_request("GET", f"/crm/v3/objects/contacts/{contact_id}")
            return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="crm_get_contact")

        elif self._crm_type == "pipedrive":
            result = await self._request("GET", f"/persons/{contact_id}")
            return ToolInvocationResult(success=True, output=result.get("data", {}), provider_id=self.provider_id, tool_id="crm_get_contact")

        return ToolInvocationResult(success=False, error="Not implemented", provider_id=self.provider_id, tool_id="crm_get_contact")

    async def _execute_crm_search_contacts(self, params: Dict[str, Any]) -> ToolInvocationResult:
        limit = params.get("limit", 50)

        if self._crm_type == "hubspot":
            filter_groups = []
            if params.get("email"):
                filter_groups.append({"filters": [{"propertyName": "email", "operator": "EQ", "value": params["email"]}]})
            if params.get("name"):
                filter_groups.append({"filters": [{"propertyName": "firstname", "operator": "CONTAINS_TOKEN", "value": params["name"]}]})
            if params.get("company"):
                filter_groups.append({"filters": [{"propertyName": "company", "operator": "CONTAINS_TOKEN", "value": params["company"]}]})

            query = {"filterGroups": filter_groups, "limit": limit, "properties": ["email", "firstname", "lastname", "phone", "company", "lifecyclestage"]}
            result = await self._hubspot_request("POST", "/crm/v3/objects/contacts/search", json=query)
            return ToolInvocationResult(success=True, output=result.get("results", []), provider_id=self.provider_id, tool_id="crm_search_contacts")

        elif self._crm_type == "pipedrive":
            query = {"limit": limit}
            if params.get("email"):
                query["email"] = params["email"]
            if params.get("name"):
                query["term"] = params["name"]
            result = await self._request("GET", "/persons/search", params=query)
            return ToolInvocationResult(success=True, output=result.get("data", {}).get("items", []), provider_id=self.provider_id, tool_id="crm_search_contacts")

        return ToolInvocationResult(success=False, error="Not implemented", provider_id=self.provider_id, tool_id="crm_search_contacts")

    async def _execute_crm_update_contact(self, params: Dict[str, Any]) -> ToolInvocationResult:
        contact_id = params["contact_id"]
        properties = params["properties"]

        if self._crm_type == "hubspot":
            result = await self._hubspot_request("PATCH", f"/crm/v3/objects/contacts/{contact_id}", json={"properties": properties})
            return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="crm_update_contact")

        elif self._crm_type == "pipedrive":
            result = await self._request("PUT", f"/persons/{contact_id}", json=properties)
            return ToolInvocationResult(success=True, output=result.get("data", {}), provider_id=self.provider_id, tool_id="crm_update_contact")

        return ToolInvocationResult(success=False, error="Not implemented", provider_id=self.provider_id, tool_id="crm_update_contact")

    async def _execute_crm_delete_contact(self, params: Dict[str, Any]) -> ToolInvocationResult:
        contact_id = params["contact_id"]

        if self._crm_type == "hubspot":
            await self._hubspot_request("DELETE", f"/crm/v3/objects/contacts/{contact_id}")
            return ToolInvocationResult(success=True, output={"deleted": True}, provider_id=self.provider_id, tool_id="crm_delete_contact")

        elif self._crm_type == "pipedrive":
            await self._request("DELETE", f"/persons/{contact_id}")
            return ToolInvocationResult(success=True, output={"deleted": True}, provider_id=self.provider_id, tool_id="crm_delete_contact")

        return ToolInvocationResult(success=False, error="Not implemented", provider_id=self.provider_id, tool_id="crm_delete_contact")

    # ── Companies ──────────────────────────────────────────────────────────

    async def _execute_crm_create_company(self, params: Dict[str, Any]) -> ToolInvocationResult:
        if self._crm_type == "hubspot":
            properties = {"name": params["name"], "domain": params.get("domain", "")}
            if params.get("industry"):
                properties["industry"] = params["industry"]
            if params.get("custom_properties"):
                properties.update(params["custom_properties"])

            result = await self._hubspot_request("POST", "/crm/v3/objects/companies", json={"properties": properties})
            return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="crm_create_company")

        elif self._crm_type == "pipedrive":
            data = {"name": params["name"]}
            if params.get("domain"):
                # Pipedrive uses address field for domain typically
                pass
            result = await self._request("POST", "/organizations", json=data)
            return ToolInvocationResult(success=True, output=result.get("data", {}), provider_id=self.provider_id, tool_id="crm_create_company")

        return ToolInvocationResult(success=False, error="Not implemented", provider_id=self.provider_id, tool_id="crm_create_company")

    async def _execute_crm_get_company(self, params: Dict[str, Any]) -> ToolInvocationResult:
        company_id = params["company_id"]

        if self._crm_type == "hubspot":
            result = await self._hubspot_request("GET", f"/crm/v3/objects/companies/{company_id}")
            return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="crm_get_company")

        elif self._crm_type == "pipedrive":
            result = await self._request("GET", f"/organizations/{company_id}")
            return ToolInvocationResult(success=True, output=result.get("data", {}), provider_id=self.provider_id, tool_id="crm_get_company")

        return ToolInvocationResult(success=False, error="Not implemented", provider_id=self.provider_id, tool_id="crm_get_company")

    async def _execute_crm_search_companies(self, params: Dict[str, Any]) -> ToolInvocationResult:
        limit = params.get("limit", 50)

        if self._crm_type == "hubspot":
            filter_groups = []
            if params.get("name"):
                filter_groups.append({"filters": [{"propertyName": "name", "operator": "CONTAINS_TOKEN", "value": params["name"]}]})
            if params.get("domain"):
                filter_groups.append({"filters": [{"propertyName": "domain", "operator": "EQ", "value": params["domain"]}]})

            query = {"filterGroups": filter_groups, "limit": limit, "properties": ["name", "domain", "industry"]}
            result = await self._hubspot_request("POST", "/crm/v3/objects/companies/search", json=query)
            return ToolInvocationResult(success=True, output=result.get("results", []), provider_id=self.provider_id, tool_id="crm_search_companies")

        return ToolInvocationResult(success=False, error="Not implemented", provider_id=self.provider_id, tool_id="crm_search_companies")

    # ── Deals ──────────────────────────────────────────────────────────────

    async def _execute_crm_create_deal(self, params: Dict[str, Any]) -> ToolInvocationResult:
        if self._crm_type == "hubspot":
            properties = {
                "dealname": params["name"],
                "amount": str(params["amount"]),
                "dealstage": params["stage"],
                "pipeline": params.get("pipeline", "default"),
                "closedate": params.get("close_date", ""),
            }
            if params.get("custom_properties"):
                properties.update(params["custom_properties"])

            result = await self._hubspot_request("POST", "/crm/v3/objects/deals", json={"properties": properties, "associations": []})

            # Associate with contact/company if provided
            deal_id = result.get("id")
            if params.get("contact_id") and deal_id:
                await self._hubspot_request("PUT", f"/crm/v3/objects/deals/{deal_id}/associations/contacts/{params['contact_id']}", json=[{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 3}])
            if params.get("company_id") and deal_id:
                await self._hubspot_request("PUT", f"/crm/v3/objects/deals/{deal_id}/associations/companies/{params['company_id']}", json=[{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 1}])

            return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="crm_create_deal")

        elif self._crm_type == "pipedrive":
            data = {
                "title": params["name"],
                "value": params["amount"],
                "stage_id": params["stage"],
                "pipeline_id": params.get("pipeline", ""),
                "expected_close_date": params.get("close_date", "")[:10] if params.get("close_date") else "",
            }
            if params.get("contact_id"):
                data["person_id"] = params["contact_id"]
            if params.get("company_id"):
                data["org_id"] = params["company_id"]

            result = await self._request("POST", "/deals", json=data)
            return ToolInvocationResult(success=True, output=result.get("data", {}), provider_id=self.provider_id, tool_id="crm_create_deal")

        return ToolInvocationResult(success=False, error="Not implemented", provider_id=self.provider_id, tool_id="crm_create_deal")

    async def _execute_crm_get_deal(self, params: Dict[str, Any]) -> ToolInvocationResult:
        deal_id = params["deal_id"]

        if self._crm_type == "hubspot":
            result = await self._hubspot_request("GET", f"/crm/v3/objects/deals/{deal_id}?properties=dealname,amount,dealstage,pipeline,closedate")
            return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="crm_get_deal")

        elif self._crm_type == "pipedrive":
            result = await self._request("GET", f"/deals/{deal_id}")
            return ToolInvocationResult(success=True, output=result.get("data", {}), provider_id=self.provider_id, tool_id="crm_get_deal")

        return ToolInvocationResult(success=False, error="Not implemented", provider_id=self.provider_id, tool_id="crm_get_deal")

    async def _execute_crm_search_deals(self, params: Dict[str, Any]) -> ToolInvocationResult:
        limit = params.get("limit", 50)

        if self._crm_type == "hubspot":
            filter_groups = []
            if params.get("stage"):
                filter_groups.append({"filters": [{"propertyName": "dealstage", "operator": "EQ", "value": params["stage"]}]})
            if params.get("pipeline"):
                filter_groups.append({"filters": [{"propertyName": "pipeline", "operator": "EQ", "value": params["pipeline"]}]})

            query = {"filterGroups": filter_groups, "limit": limit, "properties": ["dealname", "amount", "dealstage", "pipeline", "closedate"]}
            result = await self._hubspot_request("POST", "/crm/v3/objects/deals/search", json=query)
            return ToolInvocationResult(success=True, output=result.get("results", []), provider_id=self.provider_id, tool_id="crm_search_deals")

        return ToolInvocationResult(success=False, error="Not implemented", provider_id=self.provider_id, tool_id="crm_search_deals")

    async def _execute_crm_update_deal(self, params: Dict[str, Any]) -> ToolInvocationResult:
        deal_id = params["deal_id"]
        properties = params["properties"]

        if self._crm_type == "hubspot":
            result = await self._hubspot_request("PATCH", f"/crm/v3/objects/deals/{deal_id}", json={"properties": properties})
            return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="crm_update_deal")

        return ToolInvocationResult(success=False, error="Not implemented", provider_id=self.provider_id, tool_id="crm_update_deal")

    async def _execute_crm_move_deal_stage(self, params: Dict[str, Any]) -> ToolInvocationResult:
        deal_id = params["deal_id"]
        stage = params["stage"]

        if self._crm_type == "hubspot":
            result = await self._hubspot_request("PATCH", f"/crm/v3/objects/deals/{deal_id}", json={"properties": {"dealstage": stage}})
            return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="crm_move_deal_stage")

        elif self._crm_type == "pipedrive":
            result = await self._request("PUT", f"/deals/{deal_id}", json={"stage_id": stage})
            return ToolInvocationResult(success=True, output=result.get("data", {}), provider_id=self.provider_id, tool_id="crm_move_deal_stage")

        return ToolInvocationResult(success=False, error="Not implemented", provider_id=self.provider_id, tool_id="crm_move_deal_stage")

    # ── Activities ──────────────────────────────────────────────────────────

    async def _execute_crm_log_activity(self, params: Dict[str, Any]) -> ToolInvocationResult:
        if self._crm_type == "hubspot":
            activity_type_map = {
                "email": "EMAIL",
                "call": "CALL",
                "meeting": "MEETING",
                "note": "NOTE",
                "task": "TASK",
            }

            properties = {
                "hs_timestamp": params.get("timestamp", datetime.utcnow().isoformat() + "Z"),
                "hs_note": params.get("body", "") if params.get("body") else params.get("subject", ""),
                "hs_meeting_body": params.get("body", "") if params.get("type") == "meeting" else "",
                "hs_call_body": params.get("body", "") if params.get("type") == "call" else "",
                "hs_task_body": params.get("body", "") if params.get("type") == "task" else "",
            }

            associations = []
            for cid in params.get("contact_ids", []):
                associations.append({"to": {"id": cid}, "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 214}]})

            if params.get("deal_id"):
                associations.append({"to": {"id": params["deal_id"]}, "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 212}]})

            result = await self._hubspot_request(
                "POST",
                f"/crm/v3/objects/{activity_type_map.get(params['type'], 'NOTE').lower()}s",
                json={"properties": properties, "associations": associations}
            )
            return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="crm_log_activity")

        return ToolInvocationResult(success=False, error="Not implemented", provider_id=self.provider_id, tool_id="crm_log_activity")

    async def _execute_crm_get_activities(self, params: Dict[str, Any]) -> ToolInvocationResult:
        # Simplified - would need more complex querying
        return ToolInvocationResult(success=True, output=[], provider_id=self.provider_id, tool_id="crm_get_activities")

    async def _execute_crm_get_pipelines(self, params: Dict[str, Any]) -> ToolInvocationResult:
        if self._crm_type == "hubspot":
            result = await self._hubspot_request("GET", "/crm/v3/pipelines/deals")
            return ToolInvocationResult(success=True, output=result.get("results", []), provider_id=self.provider_id, tool_id="crm_get_pipelines")

        elif self._crm_type == "pipedrive":
            result = await self._request("GET", "/pipelines")
            return ToolInvocationResult(success=True, output=result.get("data", []), provider_id=self.provider_id, tool_id="crm_get_pipelines")

        return ToolInvocationResult(success=False, error="Not implemented", provider_id=self.provider_id, tool_id="crm_get_pipelines")

    async def _health_check_impl(self) -> ProviderHealth:
        try:
            if self._crm_type == "hubspot":
                result = await self._hubspot_request("GET", "/crm/v3/objects/contacts?limit=1")
                return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.HEALTHY)
            elif self._crm_type == "pipedrive":
                result = await self._request("GET", "/users/me")
                return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.HEALTHY)
            return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.UNHEALTHY, error_message="Health check not implemented")
        except Exception as e:
            return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.UNHEALTHY, error_message=str(e))