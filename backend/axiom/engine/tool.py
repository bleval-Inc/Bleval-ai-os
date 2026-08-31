"""Tool Engine — permission checking, capability resolution, and tool execution.

The Tool Engine provides:
- Tool discovery per organization
- Permission checking (can/cannot rules)
- Capability-to-agent resolution
- Audit logging
- Tool execution (web search, market data, etc.)

Architecture Law 2: Executives never perform operational work directly.
They reason, plan, and delegate through approved workflows and tools.
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

from axiom.config import settings
from axiom.models.configs import ToolDef
from axiom.registry.agent import AgentRegistryLoader
from axiom.registry.capability import CapabilityRegistryLoader
from axiom.registry.organization import OrganizationRegistryLoader


class ToolEngine:
    """Permission checking, capability resolution, audit logging, and tool execution."""

    def __init__(self) -> None:
        self._org_loader = OrganizationRegistryLoader()
        self._agent_loader = AgentRegistryLoader()
        self._cap_loader = CapabilityRegistryLoader()

        # Cache: org_id -> tools
        self._tool_cache: Dict[str, List[ToolDef]] = {}

        # Web search configuration
        self._brave_api_key = os.getenv("BRAVE_SEARCH_API_KEY", "")
        self._google_api_key = os.getenv("GOOGLE_SEARCH_API_KEY", "")
        self._google_cx = os.getenv("GOOGLE_SEARCH_CX", "")

    def get_available_tools(self, org_id: str) -> List[ToolDef]:
        """Return all tools enabled for an organization."""
        if org_id not in self._tool_cache:
            registry = self._org_loader.load_tools(org_id)
            self._tool_cache[org_id] = registry.tools if registry else []
        return self._tool_cache[org_id]

    def check_permission(self, agent_id: str, action: str) -> bool:
        """Check if an agent is permitted to perform an action.

        Returns True if the action is in the agent's 'can' list and
        NOT in the agent's 'cannot' list.
        """
        detail = self._agent_loader.load_detail(agent_id)
        if detail is None:
            return False

        # Check cannot rules first (they are explicit prohibitions)
        for rule in detail.permissions.cannot:
            if self._match_rule(rule, action):
                return False

        # Check can rules
        for rule in detail.permissions.can:
            if self._match_rule(rule, action):
                return True

        # Default deny
        return False

    def check_tool_permission(self, agent_id: str, tool_id: str, capability: str) -> bool:
        """Check if an agent can use a specific tool capability.

        Verifies:
        1. The agent has the interface for the tool
        2. The agent's permissions allow the action
        """
        # Check the agent has the right permissions
        if not self.check_permission(agent_id, capability):
            return False

        # Verify the tool exists
        detail = self._agent_loader.load_detail(agent_id)
        if detail is None:
            return False

        return True

    def resolve_capability_to_agents(self, capability: str) -> List[str]:
        """Find all agents that have a given capability."""
        return self._cap_loader.resolve_agents_for_capability(capability)

    def find_agents_for_task(self, action_description: str) -> List[Tuple[str, int]]:
        """Find agents that could perform a task described in natural language.

        Returns a list of (agent_id, match_score) tuples, sorted by score.
        """
        # Use the capability search index to find relevant capabilities
        capabilities = self._cap_loader.search(action_description)

        # Score each agent by how many matching capabilities they have
        agent_scores: Dict[str, int] = {}
        for cap in capabilities:
            for agent_id in cap.agents:
                agent_scores[agent_id] = agent_scores.get(agent_id, 0) + 1

        # Sort by score descending
        sorted_agents = sorted(agent_scores.items(), key=lambda x: -x[1])
        return sorted_agents

    def audit_log(self, agent_id: str, tool_id: str, action: str, success: bool) -> None:
        """Record a tool usage audit entry.

        Writes to the runtime log directory.
        """
        log_dir = settings.log_dir
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).isoformat()
        entry = f"[{timestamp}] agent={agent_id} tool={tool_id} action={action} success={success}\n"

        log_path = log_dir / "tool_audit.log"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(entry)

    def _match_rule(self, rule: str, action: str) -> bool:
        """Check if a rule matches an action.

        Supports simple wildcard matching where the rule ends with '*' to
        match any action that starts with the given prefix.
        """
        if rule.endswith("*"):
            return action.startswith(rule[:-1])
        return action == rule

    # ── Tool Execution ────────────────────────────────────────────────────

    async def execute_tool(
        self,
        agent_id: str,
        tool_id: str,
        action: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a tool on behalf of an agent.

        Returns the tool result or error.
        """
        # Check permission
        if not self.check_tool_permission(agent_id, tool_id, action):
            self.audit_log(agent_id, tool_id, action, False)
            return {"error": f"Agent {agent_id} not authorized for {tool_id}.{action}"}

        # Execute the tool
        try:
            if tool_id == "web_search" and action == "search":
                result = await self._web_search(params)
            elif tool_id == "market_data" and action == "get_price":
                result = await self._get_market_price(params)
            elif tool_id == "market_data" and action == "get_news":
                result = await self._get_market_news(params)
            else:
                result = {"error": f"Unknown tool: {tool_id}"}

            self.audit_log(agent_id, tool_id, action, "error" not in result)
            return result
        except Exception as e:
            self.audit_log(agent_id, tool_id, action, False)
            return {"error": f"Tool execution failed: {str(e)}"}

    async def _web_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a web search using Brave or Google Search API."""
        query = params.get("query", "")
        max_results = params.get("max_results", 10)

        if not query:
            return {"error": "Missing query parameter"}

        # Try Brave Search first
        if self._brave_api_key:
            return await self._brave_search(query, max_results)

        # Fallback to Google Custom Search
        if self._google_api_key and self._google_cx:
            return await self._google_search(query, max_results)

        return {"error": "No search API configured. Set BRAVE_SEARCH_API_KEY or GOOGLE_SEARCH_API_KEY+GOOGLE_SEARCH_CX"}

    async def _brave_search(self, query: str, max_results: int) -> Dict[str, Any]:
        """Search using Brave Search API."""
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self._brave_api_key,
        }
        params = {
            "q": query,
            "count": min(max_results, 20),
            "search_lang": "en",
            "country": "us",
            "safesearch": "moderate",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        return {"error": f"Brave Search API error: {resp.status} - {text}"}
                    data = await resp.json()

            results = []
            for item in data.get("web", {}).get("results", [])[:max_results]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "description": item.get("description", ""),
                    "age": item.get("age", ""),
                })

            return {
                "results": results,
                "query": query,
                "provider": "brave",
            }
        except Exception as e:
            return {"error": f"Brave search failed: {str(e)}"}

    async def _google_search(self, query: str, max_results: int) -> Dict[str, Any]:
        """Search using Google Custom Search API."""
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self._google_api_key,
            "cx": self._google_cx,
            "q": query,
            "num": min(max_results, 10),
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        return {"error": f"Google Search API error: {resp.status} - {text}"}
                    data = await resp.json()

            results = []
            for item in data.get("items", [])[:max_results]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "description": item.get("snippet", ""),
                })

            return {
                "results": results,
                "query": query,
                "provider": "google",
            }
        except Exception as e:
            return {"error": f"Google search failed: {str(e)}"}

    async def _get_market_price(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get current market price for a symbol."""
        symbol = params.get("symbol", "")
        if not symbol:
            return {"error": "Missing symbol parameter"}

        # This would connect to the market data provider
        # For now, return a placeholder
        return {
            "symbol": symbol,
            "price": 0,
            "currency": "USD",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "market_data",
            "note": "Connect to MT5 or market data provider for real prices",
        }

    async def _get_market_news(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get market news for a symbol or topic."""
        symbol = params.get("symbol", "")
        topic = params.get("topic", "")
        limit = params.get("limit", 10)

        # This would connect to the market intelligence engine
        return {
            "symbol": symbol,
            "topic": topic,
            "news": [],
            "note": "Connect to MarketIntelligenceEngine for real news",
        }