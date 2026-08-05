"""GitHub Provider — Repository, PR, Issue, Actions, and Deployment management."""

import asyncio
import base64
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from axiom.engine.provider import ExternalAPIProvider, ProviderAPIError
from axiom.models.providers import (
    ProviderModel,
    ProviderToolDefinition,
    ProviderHealth,
    ProviderStatus,
    ToolInvocationResult,
    RateLimitConfig,
)
from axiom.runtime.logging import RuntimeLogger


class GitHubProvider(ExternalAPIProvider):
    """GitHub API integration for development workflows.

    Capabilities:
    - Repository management (create, read, update, delete)
    - Pull Request operations (create, review, merge, comments)
    - Issue management (create, update, label, assign, close)
    - GitHub Actions (workflow runs, logs, artifacts)
    - Deployments (create, status, environments)
    - Branch protection and rules
    - Webhooks and events
    """

    def __init__(
        self,
        config: ProviderModel,
        logger: Optional[RuntimeLogger] = None,
    ) -> None:
        super().__init__(config, logger)
        self._user_cache: Dict[str, Any] = {}

    def get_tool_definitions(self) -> List[ProviderToolDefinition]:
        return [
            # Repository Tools
            ProviderToolDefinition(
                tool_id="github_create_repo",
                name="Create Repository",
                description="Create a new GitHub repository",
                capability="repository_create",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Repository name"},
                        "description": {"type": "string", "description": "Repository description"},
                        "private": {"type": "boolean", "default": True},
                        "auto_init": {"type": "boolean", "default": True},
                        "gitignore_template": {"type": "string"},
                        "license_template": {"type": "string"},
                    },
                    "required": ["name"],
                },
                risk_level="medium",
                requires_approval=False,
            ),
            ProviderToolDefinition(
                tool_id="github_get_repo",
                name="Get Repository",
                description="Get repository details",
                capability="repository_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                    },
                    "required": ["owner", "repo"],
                },
            ),
            ProviderToolDefinition(
                tool_id="github_list_repos",
                name="List Repositories",
                description="List repositories for user/org",
                capability="repository_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "type": {"type": "string", "enum": ["all", "public", "private", "member"]},
                        "sort": {"type": "string", "enum": ["created", "updated", "pushed", "full_name"]},
                        "per_page": {"type": "integer", "default": 30},
                    },
                    "required": ["owner"],
                },
            ),
            # Pull Request Tools
            ProviderToolDefinition(
                tool_id="github_create_pr",
                name="Create Pull Request",
                description="Create a new pull request",
                capability="pr_create",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "title": {"type": "string"},
                        "head": {"type": "string", "description": "Branch name or SHA"},
                        "base": {"type": "string", "description": "Base branch"},
                        "body": {"type": "string"},
                        "draft": {"type": "boolean", "default": False},
                    },
                    "required": ["owner", "repo", "title", "head", "base"],
                },
                risk_level="medium",
            ),
            ProviderToolDefinition(
                tool_id="github_get_pr",
                name="Get Pull Request",
                description="Get PR details including reviews, checks, files",
                capability="pr_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "pr_number": {"type": "integer"},
                    },
                    "required": ["owner", "repo", "pr_number"],
                },
            ),
            ProviderToolDefinition(
                tool_id="github_list_prs",
                name="List Pull Requests",
                description="List PRs with filters",
                capability="pr_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "state": {"type": "string", "enum": ["open", "closed", "all"]},
                        "head": {"type": "string"},
                        "base": {"type": "string"},
                        "per_page": {"type": "integer", "default": 30},
                    },
                    "required": ["owner", "repo"],
                },
            ),
            ProviderToolDefinition(
                tool_id="github_merge_pr",
                name="Merge Pull Request",
                description="Merge a pull request",
                capability="pr_merge",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "pr_number": {"type": "integer"},
                        "commit_title": {"type": "string"},
                        "commit_message": {"type": "string"},
                        "merge_method": {"type": "string", "enum": ["merge", "squash", "rebase"]},
                    },
                    "required": ["owner", "repo", "pr_number"],
                },
                risk_level="high",
                requires_approval=True,
            ),
            ProviderToolDefinition(
                tool_id="github_pr_review",
                name="Review Pull Request",
                description="Submit a PR review (approve, request changes, comment)",
                capability="pr_review",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "pr_number": {"type": "integer"},
                        "event": {"type": "string", "enum": ["APPROVE", "REQUEST_CHANGES", "COMMENT"]},
                        "body": {"type": "string"},
                        "comments": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "path": {"type": "string"},
                                    "line": {"type": "integer"},
                                    "body": {"type": "string"},
                                },
                                "required": ["path", "line", "body"],
                            },
                        },
                    },
                    "required": ["owner", "repo", "pr_number", "event"],
                },
                risk_level="medium",
            ),
            # Issue Tools
            ProviderToolDefinition(
                tool_id="github_create_issue",
                name="Create Issue",
                description="Create a new issue",
                capability="issue_create",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "title": {"type": "string"},
                        "body": {"type": "string"},
                        "labels": {"type": "array", "items": {"type": "string"}},
                        "assignees": {"type": "array", "items": {"type": "string"}},
                        "milestone": {"type": "integer"},
                    },
                    "required": ["owner", "repo", "title"],
                },
            ),
            ProviderToolDefinition(
                tool_id="github_get_issue",
                name="Get Issue",
                description="Get issue details",
                capability="issue_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "issue_number": {"type": "integer"},
                    },
                    "required": ["owner", "repo", "issue_number"],
                },
            ),
            ProviderToolDefinition(
                tool_id="github_update_issue",
                name="Update Issue",
                description="Update issue (labels, assignees, state, milestone)",
                capability="issue_update",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "issue_number": {"type": "integer"},
                        "title": {"type": "string"},
                        "body": {"type": "string"},
                        "state": {"type": "string", "enum": ["open", "closed"]},
                        "labels": {"type": "array", "items": {"type": "string"}},
                        "assignees": {"type": "array", "items": {"type": "string"}},
                        "milestone": {"type": "integer"},
                    },
                    "required": ["owner", "repo", "issue_number"],
                },
            ),
            ProviderToolDefinition(
                tool_id="github_list_issues",
                name="List Issues",
                description="List issues with filters",
                capability="issue_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "state": {"type": "string", "enum": ["open", "closed", "all"]},
                        "labels": {"type": "string"},
                        "assignee": {"type": "string"},
                        "milestone": {"type": "string"},
                        "per_page": {"type": "integer", "default": 30},
                    },
                    "required": ["owner", "repo"],
                },
            ),
            # GitHub Actions
            ProviderToolDefinition(
                tool_id="github_list_workflows",
                name="List Workflows",
                description="List repository workflows",
                capability="actions_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                    },
                    "required": ["owner", "repo"],
                },
            ),
            ProviderToolDefinition(
                tool_id="github_trigger_workflow",
                name="Trigger Workflow",
                description="Trigger a workflow dispatch",
                capability="actions_trigger",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "workflow_id": {"type": "string"},
                        "ref": {"type": "string", "description": "Branch/tag/SHA"},
                        "inputs": {"type": "object"},
                    },
                    "required": ["owner", "repo", "workflow_id", "ref"],
                },
                risk_level="medium",
                requires_approval=True,
            ),
            ProviderToolDefinition(
                tool_id="github_get_workflow_run",
                name="Get Workflow Run",
                description="Get workflow run details and status",
                capability="actions_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "run_id": {"type": "integer"},
                    },
                    "required": ["owner", "repo", "run_id"],
                },
            ),
            ProviderToolDefinition(
                tool_id="github_get_workflow_logs",
                name="Get Workflow Logs",
                description="Get workflow run logs",
                capability="actions_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "run_id": {"type": "integer"},
                    },
                    "required": ["owner", "repo", "run_id"],
                },
            ),
            ProviderToolDefinition(
                tool_id="github_list_workflow_runs",
                name="List Workflow Runs",
                description="List recent workflow runs",
                capability="actions_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "workflow_id": {"type": "string"},
                        "status": {"type": "string"},
                        "branch": {"type": "string"},
                        "per_page": {"type": "integer", "default": 30},
                    },
                    "required": ["owner", "repo"],
                },
            ),
            # Deployments
            ProviderToolDefinition(
                tool_id="github_create_deployment",
                name="Create Deployment",
                description="Create a deployment",
                capability="deployment_create",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "ref": {"type": "string"},
                        "environment": {"type": "string"},
                        "description": {"type": "string"},
                        "payload": {"type": "object"},
                        "auto_merge": {"type": "boolean", "default": True},
                        "required_contexts": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["owner", "repo", "ref", "environment"],
                },
                risk_level="high",
                requires_approval=True,
            ),
            ProviderToolDefinition(
                tool_id="github_create_deployment_status",
                name="Create Deployment Status",
                description="Update deployment status",
                capability="deployment_update",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "deployment_id": {"type": "integer"},
                        "state": {"type": "string", "enum": ["pending", "success", "error", "failure", "inactive", "in_progress", "queued"]},
                        "environment": {"type": "string"},
                        "description": {"type": "string"},
                        "environment_url": {"type": "string"},
                        "log_url": {"type": "string"},
                    },
                    "required": ["owner", "repo", "deployment_id", "state"],
                },
            ),
            ProviderToolDefinition(
                tool_id="github_list_deployments",
                name="List Deployments",
                description="List deployments for an environment",
                capability="deployment_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "environment": {"type": "string"},
                        "per_page": {"type": "integer", "default": 30},
                    },
                    "required": ["owner", "repo"],
                },
            ),
            # Branch Protection
            ProviderToolDefinition(
                tool_id="github_get_branch_protection",
                name="Get Branch Protection",
                description="Get branch protection rules",
                capability="branch_protection_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "branch": {"type": "string"},
                    },
                    "required": ["owner", "repo", "branch"],
                },
            ),
            # Webhooks
            ProviderToolDefinition(
                tool_id="github_create_webhook",
                name="Create Webhook",
                description="Create a repository webhook",
                capability="webhook_create",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "url": {"type": "string"},
                        "events": {"type": "array", "items": {"type": "string"}},
                        "secret": {"type": "string"},
                        "active": {"type": "boolean", "default": True},
                    },
                    "required": ["owner", "repo", "url"],
                },
                risk_level="medium",
            ),
            # Search
            ProviderToolDefinition(
                tool_id="github_search_code",
                name="Search Code",
                description="Search code across repositories",
                capability="search_code",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "per_page": {"type": "integer", "default": 30},
                    },
                    "required": ["query"],
                },
            ),
            ProviderToolDefinition(
                tool_id="github_search_repos",
                name="Search Repositories",
                description="Search repositories",
                capability="search_repos",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "per_page": {"type": "integer", "default": 30},
                    },
                    "required": ["query"],
                },
            ),
        ]

    async def initialize(self) -> None:
        """Initialize and validate GitHub token."""
        await super().initialize()

        # Validate auth by getting authenticated user
        try:
            user = await self._request("GET", "/user")
            self._user_cache = user
            self.logger.info(f"GitHub authenticated as: {user.get('login')}")
        except ProviderAPIError as e:
            if e.status_code == 401:
                raise RuntimeError("GitHub authentication failed: Invalid token")
            raise

    # ── Tool Implementations ──────────────────────────────────────────────

    async def _execute_tool_impl(
        self, tool_id: str, parameters: Dict[str, Any]
    ) -> ToolInvocationResult:
        """Route to appropriate tool implementation."""
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

    # Repository Tools
    async def _execute_github_create_repo(self, params: Dict[str, Any]) -> ToolInvocationResult:
        data = {
            "name": params["name"],
            "description": params.get("description", ""),
            "private": params.get("private", True),
            "auto_init": params.get("auto_init", True),
        }
        if params.get("gitignore_template"):
            data["gitignore_template"] = params["gitignore_template"]
        if params.get("license_template"):
            data["license_template"] = params["license_template"]

        result = await self._request("POST", "/user/repos", json=data)
        return ToolInvocationResult(
            success=True,
            output=result,
            provider_id=self.provider_id,
            tool_id="github_create_repo",
        )

    async def _execute_github_get_repo(self, params: Dict[str, Any]) -> ToolInvocationResult:
        result = await self._request("GET", f"/repos/{params['owner']}/{params['repo']}")
        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="github_get_repo")

    async def _execute_github_list_repos(self, params: Dict[str, Any]) -> ToolInvocationResult:
        query_params = {
            "type": params.get("type", "all"),
            "sort": params.get("sort", "updated"),
            "per_page": params.get("per_page", 30),
        }
        result = await self._request("GET", f"/users/{params['owner']}/repos", params=query_params)
        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="github_list_repos")

    # Pull Request Tools
    async def _execute_github_create_pr(self, params: Dict[str, Any]) -> ToolInvocationResult:
        data = {
            "title": params["title"],
            "head": params["head"],
            "base": params["base"],
            "body": params.get("body", ""),
            "draft": params.get("draft", False),
        }
        result = await self._request("POST", f"/repos/{params['owner']}/{params['repo']}/pulls", json=data)
        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="github_create_pr")

    async def _execute_github_get_pr(self, params: Dict[str, Any]) -> ToolInvocationResult:
        result = await self._request("GET", f"/repos/{params['owner']}/{params['repo']}/pulls/{params['pr_number']}")
        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="github_get_pr")

    async def _execute_github_list_prs(self, params: Dict[str, Any]) -> ToolInvocationResult:
        query_params = {
            "state": params.get("state", "open"),
            "per_page": params.get("per_page", 30),
        }
        if params.get("head"):
            query_params["head"] = params["head"]
        if params.get("base"):
            query_params["base"] = params["base"]
        result = await self._request("GET", f"/repos/{params['owner']}/{params['repo']}/pulls", params=query_params)
        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="github_list_prs")

    async def _execute_github_merge_pr(self, params: Dict[str, Any]) -> ToolInvocationResult:
        data = {
            "commit_title": params.get("commit_title"),
            "commit_message": params.get("commit_message"),
            "merge_method": params.get("merge_method", "merge"),
        }
        result = await self._request(
            "PUT", f"/repos/{params['owner']}/{params['repo']}/pulls/{params['pr_number']}/merge", json=data
        )
        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="github_merge_pr")

    async def _execute_github_pr_review(self, params: Dict[str, Any]) -> ToolInvocationResult:
        data = {
            "event": params["event"],
            "body": params.get("body", ""),
        }
        if params.get("comments"):
            data["comments"] = params["comments"]
        result = await self._request(
            "POST", f"/repos/{params['owner']}/{params['repo']}/pulls/{params['pr_number']}/reviews", json=data
        )
        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="github_pr_review")

    # Issue Tools
    async def _execute_github_create_issue(self, params: Dict[str, Any]) -> ToolInvocationResult:
        data = {
            "title": params["title"],
            "body": params.get("body", ""),
        }
        if params.get("labels"):
            data["labels"] = params["labels"]
        if params.get("assignees"):
            data["assignees"] = params["assignees"]
        if params.get("milestone"):
            data["milestone"] = params["milestone"]

        result = await self._request("POST", f"/repos/{params['owner']}/{params['repo']}/issues", json=data)
        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="github_create_issue")

    async def _execute_github_get_issue(self, params: Dict[str, Any]) -> ToolInvocationResult:
        result = await self._request("GET", f"/repos/{params['owner']}/{params['repo']}/issues/{params['issue_number']}")
        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="github_get_issue")

    async def _execute_github_update_issue(self, params: Dict[str, Any]) -> ToolInvocationResult:
        data = {}
        for key in ["title", "body", "state", "labels", "assignees", "milestone"]:
            if params.get(key) is not None:
                data[key] = params[key]
        result = await self._request(
            "PATCH", f"/repos/{params['owner']}/{params['repo']}/issues/{params['issue_number']}", json=data
        )
        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="github_update_issue")

    async def _execute_github_list_issues(self, params: Dict[str, Any]) -> ToolInvocationResult:
        query_params = {
            "state": params.get("state", "open"),
            "per_page": params.get("per_page", 30),
        }
        for key in ["labels", "assignee", "milestone"]:
            if params.get(key):
                query_params[key] = params[key]
        result = await self._request("GET", f"/repos/{params['owner']}/{params['repo']}/issues", params=query_params)
        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="github_list_issues")

    # GitHub Actions
    async def _execute_github_list_workflows(self, params: Dict[str, Any]) -> ToolInvocationResult:
        result = await self._request("GET", f"/repos/{params['owner']}/{params['repo']}/actions/workflows")
        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="github_list_workflows")

    async def _execute_github_trigger_workflow(self, params: Dict[str, Any]) -> ToolInvocationResult:
        data = {
            "ref": params["ref"],
        }
        if params.get("inputs"):
            data["inputs"] = params["inputs"]
        result = await self._request(
            "POST", f"/repos/{params['owner']}/{params['repo']}/actions/workflows/{params['workflow_id']}/dispatches", json=data
        )
        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="github_trigger_workflow")

    async def _execute_github_get_workflow_run(self, params: Dict[str, Any]) -> ToolInvocationResult:
        result = await self._request("GET", f"/repos/{params['owner']}/{params['repo']}/actions/runs/{params['run_id']}")
        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="github_get_workflow_run")

    async def _execute_github_get_workflow_logs(self, params: Dict[str, Any]) -> ToolInvocationResult:
        result = await self._request("GET", f"/repos/{params['owner']}/{params['repo']}/actions/runs/{params['run_id']}/logs")
        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="github_get_workflow_logs")

    async def _execute_github_list_workflow_runs(self, params: Dict[str, Any]) -> ToolInvocationResult:
        query_params = {"per_page": params.get("per_page", 30)}
        for key in ["workflow_id", "status", "branch"]:
            if params.get(key):
                query_params[key] = params[key]
        result = await self._request("GET", f"/repos/{params['owner']}/{params['repo']}/actions/runs", params=query_params)
        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="github_list_workflow_runs")

    # Deployments
    async def _execute_github_create_deployment(self, params: Dict[str, Any]) -> ToolInvocationResult:
        data = {
            "ref": params["ref"],
            "environment": params["environment"],
            "description": params.get("description", ""),
            "auto_merge": params.get("auto_merge", True),
        }
        if params.get("payload"):
            data["payload"] = params["payload"]
        if params.get("required_contexts"):
            data["required_contexts"] = params["required_contexts"]

        result = await self._request("POST", f"/repos/{params['owner']}/{params['repo']}/deployments", json=data)
        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="github_create_deployment")

    async def _execute_github_create_deployment_status(self, params: Dict[str, Any]) -> ToolInvocationResult:
        data = {
            "state": params["state"],
            "environment": params.get("environment", ""),
        }
        for key in ["description", "environment_url", "log_url"]:
            if params.get(key) is not None:
                data[key] = params[key]

        result = await self._request(
            "POST",
            f"/repos/{params['owner']}/{params['repo']}/deployments/{params['deployment_id']}/statuses",
            json=data,
        )
        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="github_create_deployment_status")

    async def _execute_github_list_deployments(self, params: Dict[str, Any]) -> ToolInvocationResult:
        query_params = {"per_page": params.get("per_page", 30)}
        if params.get("environment"):
            query_params["environment"] = params["environment"]
        result = await self._request(
            "GET", f"/repos/{params['owner']}/{params['repo']}/deployments", params=query_params
        )
        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="github_list_deployments")

    # Branch Protection
    async def _execute_github_get_branch_protection(self, params: Dict[str, Any]) -> ToolInvocationResult:
        result = await self._request(
            "GET", f"/repos/{params['owner']}/{params['repo']}/branches/{params['branch']}/protection"
        )
        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="github_get_branch_protection")

    # Webhooks
    async def _execute_github_create_webhook(self, params: Dict[str, Any]) -> ToolInvocationResult:
        data = {
            "name": "web",
            "config": {
                "url": params["url"],
                "content_type": "json",
            },
            "events": params.get("events", ["push", "pull_request"]),
            "active": params.get("active", True),
        }
        if params.get("secret"):
            data["config"]["secret"] = params["secret"]

        result = await self._request("POST", f"/repos/{params['owner']}/{params['repo']}/hooks", json=data)
        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="github_create_webhook")

    # Search
    async def _execute_github_search_code(self, params: Dict[str, Any]) -> ToolInvocationResult:
        query_params = {"q": params["query"], "per_page": params.get("per_page", 30)}
        result = await self._request("GET", "/search/code", params=query_params)
        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="github_search_code")

    async def _execute_github_search_repos(self, params: Dict[str, Any]) -> ToolInvocationResult:
        query_params = {"q": params["query"], "per_page": params.get("per_page", 30)}
        result = await self._request("GET", "/search/repositories", params=query_params)
        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="github_search_repos")

    # Health Check
    async def _health_check_impl(self) -> ProviderHealth:
        """Check GitHub API health and rate limit."""
        try:
            # Use rate limit endpoint for health check
            result = await self._request("GET", "/rate_limit")
            remaining = result.get("resources", {}).get("core", {}).get("remaining", 0)

            status = ProviderStatus.HEALTHY
            if remaining < 100:
                status = ProviderStatus.DEGRADED

            return ProviderHealth(
                provider_id=self.provider_id,
                status=status,
                latency_ms=0,  # Measured in base class
                details={"rate_limit_remaining": remaining},
            )
        except ProviderAPIError as e:
            if e.status_code == 401:
                return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.NO_AUTH)
            return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.UNHEALTHY, error_message=str(e))
        except Exception as e:
            return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.UNHEALTHY, error_message=str(e))