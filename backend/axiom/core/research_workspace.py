"""
Research Workspace — lifecycle manager for AXIOM research workspaces.

AXIOM creates a dedicated workspace for every substantial research request.
Each workspace tracks the full research lifecycle:

  - Conversation (queries + AXIOM responses)
  - Sources (documents, URLs, references)
  - Documents (uploaded or retrieved)
  - Images / Videos / Audio (multi-modal assets)
  - Findings (key insights extracted)
  - Notes (Founder annotations)
  - Conclusions (final synthesis)
  - References (citations, links)
  - Decisions (research-driven decisions)
  - Actions (follow-up tasks)
  - Generated assets (reports, summaries, presentations)

Design principle:
  The Founder inspects everything, but the default experience is concise.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class ResearchWorkspace:
    """A single research workspace with its full state."""

    id: str
    title: str
    query: str
    created_at: str
    status: str  # active | archived
    conversation: List[Dict[str, Any]] = field(default_factory=list)
    sources: List[Dict[str, Any]] = field(default_factory=list)
    documents: List[Dict[str, Any]] = field(default_factory=list)
    images: List[Dict[str, Any]] = field(default_factory=list)
    videos: List[Dict[str, Any]] = field(default_factory=list)
    audio: List[Dict[str, Any]] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    notes: List[Dict[str, Any]] = field(default_factory=list)
    conclusions: List[Dict[str, Any]] = field(default_factory=list)
    references: List[Dict[str, Any]] = field(default_factory=list)
    decisions: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    generated_assets: List[Dict[str, Any]] = field(default_factory=list)
    related_research: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for API responses."""
        return {
            "id": self.id,
            "title": self.title,
            "query": self.query,
            "created_at": self.created_at,
            "status": self.status,
            "sources_count": len(self.sources),
            "documents_count": len(self.documents),
            "images_count": len(self.images),
            "videos_count": len(self.videos),
            "audio_count": len(self.audio),
            "findings_count": len(self.findings),
            "notes_count": len(self.notes),
            "conclusions_count": len(self.conclusions),
            "references_count": len(self.references),
            "decisions_count": len(self.decisions),
            "actions_count": len(self.actions),
            "generated_assets_count": len(self.generated_assets),
            "conversation": self.conversation[-10:],
            "sources": self.sources,
            "findings": self.findings,
            "conclusions": self.conclusions,
        }

    def to_summary(self) -> Dict[str, Any]:
        """Compact summary for list views."""
        return {
            "id": self.id,
            "title": self.title,
            "query": self.query[:100],
            "created_at": self.created_at,
            "status": self.status,
            "sources_count": len(self.sources),
            "findings_count": len(self.findings),
            "conversation_length": len(self.conversation),
        }


class ResearchWorkspaceManager:
    """Manages the lifecycle of all research workspaces.

    Workspaces are held in memory by default. Persistence can be added
    by wiring a file-based or database-backed store.

    Each workspace tracks:
    - Conversation history
    - Multi-modal sources
    - Findings and conclusions
    - Decisions and actions
    - Generated assets
    """

    def __init__(self, logger: Any = None) -> None:
        self._workspaces: Dict[str, ResearchWorkspace] = {}
        self._logger = logger

    # ── CRUD ─────────────────────────────────────────────────────────────

    def create(
        self,
        title: str,
        query: str,
        source_material: Optional[Dict[str, Any]] = None,
    ) -> ResearchWorkspace:
        """Create a new research workspace with an initial query."""
        workspace_id = f"rws_{uuid.uuid4().hex[:12]}"

        workspace = ResearchWorkspace(
            id=workspace_id,
            title=title,
            query=query,
            created_at=datetime.now(timezone.utc).isoformat(),
            status="active",
            conversation=[
                {
                    "role": "founder",
                    "content": query,
                    "type": "query",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            ],
        )

        if source_material:
            workspace.sources.append(source_material)

        self._workspaces[workspace_id] = workspace

        if self._logger:
            self._logger.info(
                "research_workspace",
                f"Created: '{title}' ({workspace_id})",
            )

        return workspace

    def get(self, workspace_id: str) -> Optional[ResearchWorkspace]:
        """Get a workspace by ID."""
        return self._workspaces.get(workspace_id)

    def list_active(self) -> List[ResearchWorkspace]:
        """List all active workspaces."""
        return [w for w in self._workspaces.values() if w.status == "active"]

    def list_archived(self) -> List[ResearchWorkspace]:
        """List all archived workspaces."""
        return [w for w in self._workspaces.values() if w.status == "archived"]

    def list_all(self) -> List[ResearchWorkspace]:
        """List all workspaces regardless of status."""
        return list(self._workspaces.values())

    def archive(self, workspace_id: str) -> bool:
        """Archive a workspace (soft delete)."""
        workspace = self._workspaces.get(workspace_id)
        if workspace is None:
            return False
        workspace.status = "archived"
        return True

    def delete(self, workspace_id: str) -> bool:
        """Permanently delete a workspace."""
        if workspace_id in self._workspaces:
            del self._workspaces[workspace_id]
            return True
        return False

    # ── Conversation ─────────────────────────────────────────────────────

    def add_conversation_entry(
        self,
        workspace_id: str,
        role: str,
        content: str,
        entry_type: str = "message",
    ) -> Optional[ResearchWorkspace]:
        """Add a conversation entry to a workspace."""
        workspace = self._workspaces.get(workspace_id)
        if workspace is None:
            return None

        workspace.conversation.append({
            "role": role,
            "content": content,
            "type": entry_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return workspace

    # ── Sources ──────────────────────────────────────────────────────────

    def add_source(
        self,
        workspace_id: str,
        source_type: str,
        source: Dict[str, Any],
    ) -> Optional[ResearchWorkspace]:
        """Add a source reference to a workspace (URL, document, etc.)."""
        workspace = self._workspaces.get(workspace_id)
        if workspace is None:
            return None

        entry = {
            "type": source_type,
            **source,
            "added_at": datetime.now(timezone.utc).isoformat(),
        }
        workspace.sources.append(entry)
        return workspace

    # ── Multi-modal assets ───────────────────────────────────────────────

    def add_document(
        self,
        workspace_id: str,
        document: Dict[str, Any],
    ) -> Optional[ResearchWorkspace]:
        """Add a document reference to a workspace."""
        workspace = self._workspaces.get(workspace_id)
        if workspace is None:
            return None
        document["added_at"] = datetime.now(timezone.utc).isoformat()
        workspace.documents.append(document)
        return workspace

    def add_image(
        self,
        workspace_id: str,
        image: Dict[str, Any],
    ) -> Optional[ResearchWorkspace]:
        """Add an image reference to a workspace."""
        workspace = self._workspaces.get(workspace_id)
        if workspace is None:
            return None
        image["added_at"] = datetime.now(timezone.utc).isoformat()
        workspace.images.append(image)
        return workspace

    def add_video(
        self,
        workspace_id: str,
        video: Dict[str, Any],
    ) -> Optional[ResearchWorkspace]:
        """Add a video reference to a workspace."""
        workspace = self._workspaces.get(workspace_id)
        if workspace is None:
            return None
        video["added_at"] = datetime.now(timezone.utc).isoformat()
        workspace.videos.append(video)
        return workspace

    def add_audio(
        self,
        workspace_id: str,
        audio: Dict[str, Any],
    ) -> Optional[ResearchWorkspace]:
        """Add an audio reference to a workspace."""
        workspace = self._workspaces.get(workspace_id)
        if workspace is None:
            return None
        audio["added_at"] = datetime.now(timezone.utc).isoformat()
        workspace.audio.append(audio)
        return workspace

    # ── Findings & Notes ─────────────────────────────────────────────────

    def add_finding(
        self,
        workspace_id: str,
        finding: Dict[str, Any],
    ) -> Optional[ResearchWorkspace]:
        """Add a research finding to a workspace."""
        workspace = self._workspaces.get(workspace_id)
        if workspace is None:
            return None
        finding["added_at"] = datetime.now(timezone.utc).isoformat()
        workspace.findings.append(finding)
        return workspace

    def add_note(
        self,
        workspace_id: str,
        note: Dict[str, Any],
    ) -> Optional[ResearchWorkspace]:
        """Add a Founder note to a workspace."""
        workspace = self._workspaces.get(workspace_id)
        if workspace is None:
            return None
        note["added_at"] = datetime.now(timezone.utc).isoformat()
        workspace.notes.append(note)
        return workspace

    # ── Conclusions & References ─────────────────────────────────────────

    def set_conclusions(
        self,
        workspace_id: str,
        conclusions: List[Dict[str, Any]],
    ) -> Optional[ResearchWorkspace]:
        """Set the conclusions for a workspace (replaces existing)."""
        workspace = self._workspaces.get(workspace_id)
        if workspace is None:
            return None
        for c in conclusions:
            c["added_at"] = datetime.now(timezone.utc).isoformat()
        workspace.conclusions = conclusions
        return workspace

    def add_reference(
        self,
        workspace_id: str,
        reference: Dict[str, Any],
    ) -> Optional[ResearchWorkspace]:
        """Add a reference to a workspace."""
        workspace = self._workspaces.get(workspace_id)
        if workspace is None:
            return None
        reference["added_at"] = datetime.now(timezone.utc).isoformat()
        workspace.references.append(reference)
        return workspace

    # ── Decisions & Actions ──────────────────────────────────────────────

    def add_decision(
        self,
        workspace_id: str,
        decision: Dict[str, Any],
    ) -> Optional[ResearchWorkspace]:
        """Add a research-driven decision."""
        workspace = self._workspaces.get(workspace_id)
        if workspace is None:
            return None
        decision["added_at"] = datetime.now(timezone.utc).isoformat()
        workspace.decisions.append(decision)
        return workspace

    def add_action(
        self,
        workspace_id: str,
        action: Dict[str, Any],
    ) -> Optional[ResearchWorkspace]:
        """Add a follow-up action item."""
        workspace = self._workspaces.get(workspace_id)
        if workspace is None:
            return None
        action["added_at"] = datetime.now(timezone.utc).isoformat()
        workspace.actions.append(action)
        return workspace

    def add_generated_asset(
        self,
        workspace_id: str,
        asset: Dict[str, Any],
    ) -> Optional[ResearchWorkspace]:
        """Add a generated asset (report, summary, presentation)."""
        workspace = self._workspaces.get(workspace_id)
        if workspace is None:
            return None
        asset["added_at"] = datetime.now(timezone.utc).isoformat()
        workspace.generated_assets.append(asset)
        return workspace

    def add_related_research(
        self,
        workspace_id: str,
        related_id: str,
    ) -> Optional[ResearchWorkspace]:
        """Link another research workspace as related."""
        workspace = self._workspaces.get(workspace_id)
        if workspace is None:
            return None
        if related_id not in workspace.related_research:
            workspace.related_research.append(related_id)
        return workspace

    # ── Search ───────────────────────────────────────────────────────────

    def search(self, query: str) -> List[ResearchWorkspace]:
        """Search workspaces by title and query content."""
        query_lower = query.lower()
        results = []
        for workspace in self._workspaces.values():
            if (
                query_lower in workspace.title.lower()
                or query_lower in workspace.query.lower()
            ):
                results.append(workspace)
                continue
            # Check conversation content
            for entry in workspace.conversation:
                if query_lower in entry.get("content", "").lower():
                    results.append(workspace)
                    break
        return results

    # ── Stats ────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Return workspace usage statistics."""
        all_w = self.list_all()
        return {
            "total": len(all_w),
            "active": len(self.list_active()),
            "archived": len(self.list_archived()),
            "total_findings": sum(len(w.findings) for w in all_w),
            "total_sources": sum(len(w.sources) for w in all_w),
            "total_decisions": sum(len(w.decisions) for w in all_w),
            "total_actions": sum(len(w.actions) for w in all_w),
        }