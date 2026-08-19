"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import type { SpeakerId } from "@/lib/api-types";
import {
  DEADLINES,
  EXECUTIVES,
  formatClock,
  getExecutive,
  uid,
  type BrMeeting,
} from "./boardroom-data";
import { BdSection, MonoLabel } from "./boardroom-ui";

// ── Structured meeting notes + action items + Founder approvals ──────
// Notes are organized into the AXIOM Boardroom sections. Action items that
// require Founder approval start locked (status PENDING) until APPROVE /
// REJECT / SEND BACK — an executive cannot bypass approval.

interface NotesProps {
  meeting: BrMeeting;
  patch: (updater: (m: BrMeeting) => BrMeeting) => void;
}

export default function BoardroomNotes({ meeting, patch }: NotesProps) {
  return (
    <div className="flex-1 min-h-0 overflow-y-auto hide-scrollbar px-4 py-4 space-y-3">
      {/* Summary */}
      <BdSection title="Meeting summary">
        <textarea
          value={meeting.summary}
          onChange={(e) => patch((m) => ({ ...m, summary: e.target.value }))}
          placeholder="Summary of the session, captured live or written by the Founder…"
          className="w-full min-h-[72px] px-3 py-2.5 text-[12px] leading-relaxed text-[var(--axiom-text-secondary)] bg-transparent resize-none focus:outline-none"
        />
      </BdSection>

      <StringList
        title="Key discussion points"
        placeholder="Add a discussion point…"
        items={meeting.keyPoints}
        onAdd={(v) => patch((m) => ({ ...m, keyPoints: [...m.keyPoints, v] }))}
        onRemove={(i) => patch((m) => ({ ...m, keyPoints: m.keyPoints.filter((_, idx) => idx !== i) }))}
      />

      {/* Decisions */}
      <BdSection title="Decisions">
        {meeting.decisions.length === 0 && <EmptyNote>No decisions captured yet.</EmptyNote>}
        <div className="px-3 pb-2 space-y-1.5">
          {meeting.decisions.map((d) => (
            <div key={d.id} className="flex items-start gap-2 px-2.5 py-1.5 rounded-lg bg-white/[0.02] border border-[var(--axiom-border)]">
              <span className={cn("mt-0.5 w-1.5 h-1.5 rounded-full flex-shrink-0", d.approved ? "bg-[var(--axiom-accent)]" : "bg-[var(--axiom-text-tertiary)]")} />
              <div className="min-w-0 flex-1">
                <p className="text-[11px] text-[var(--axiom-text-primary)] leading-snug">{d.title}</p>
                <p className="text-[9px] text-[var(--axiom-text-tertiary)] mt-0.5">
                  Proposed by {getExecutive(d.proposedBy).name} · {d.approved ? "Approved" : "Carried forward"}
                </p>
              </div>
            </div>
          ))}
        </div>
      </BdSection>

      {/* Action items + approvals */}
      <ActionItems meeting={meeting} patch={patch} />

      <StringList
        title="Recommendations"
        placeholder="Add a recommendation…"
        items={meeting.recommendations}
        onAdd={(v) => patch((m) => ({ ...m, recommendations: [...m.recommendations, v] }))}
        onRemove={(i) => patch((m) => ({ ...m, recommendations: m.recommendations.filter((_, idx) => idx !== i) }))}
      />

      <StringList
        title="Questions"
        placeholder="Add a question raised…"
        items={meeting.questions}
        onAdd={(v) => patch((m) => ({ ...m, questions: [...m.questions, v] }))}
        onRemove={(i) => patch((m) => ({ ...m, questions: m.questions.filter((_, idx) => idx !== i) }))}
      />

      <StringList
        title="Follow-ups"
        placeholder="Add a follow-up…"
        items={meeting.followUps}
        onAdd={(v) => patch((m) => ({ ...m, followUps: [...m.followUps, v] }))}
        onRemove={(i) => patch((m) => ({ ...m, followUps: m.followUps.filter((_, idx) => idx !== i) }))}
      />

      {/* Participants + timestamp */}
      <BdSection title="Participants & session">
        <div className="px-3 py-2 flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            {meeting.participants.map((id) => {
              const e = getExecutive(id as SpeakerId);
              return (
                <span key={id} className="px-2 py-1 rounded-lg border border-[var(--axiom-border-hover)] bg-white/[0.02] text-[9px] text-[var(--axiom-text-secondary)]">
                  {e.name}
                </span>
              );
            })}
          </div>
          <MonoLabel>BEGAN {formatClock(meeting.startedAt)}</MonoLabel>
        </div>
      </BdSection>
    </div>
  );
}

// ── Generic editable list ─────────────────────────────────────────────
function StringList({
  title,
  placeholder,
  items,
  onAdd,
  onRemove,
}: {
  title: string;
  placeholder: string;
  items: string[];
  onAdd: (v: string) => void;
  onRemove: (i: number) => void;
}) {
  const [draft, setDraft] = useState("");
  const submit = () => {
    const v = draft.trim();
    if (!v) return;
    onAdd(v);
    setDraft("");
  };
  return (
    <BdSection title={title}>
      <div className="px-3 pb-2 space-y-1.5">
        {items.length === 0 && <EmptyNote>Nothing recorded.</EmptyNote>}
        {items.map((item, i) => (
          <div key={i} className="group flex items-start gap-2 px-2.5 py-1.5 rounded-lg bg-white/[0.02] border border-[var(--axiom-border)]">
            <span className="mt-1 w-1 h-1 rounded-full bg-[var(--axiom-text-tertiary)]/60 flex-shrink-0" />
            <p className="flex-1 min-w-0 text-[11px] text-[var(--axiom-text-secondary)] leading-snug">{item}</p>
            <button
              onClick={() => onRemove(i)}
              className="opacity-0 group-hover:opacity-60 hover:opacity-100 text-[var(--axiom-text-tertiary)] text-[13px] leading-none transition-all"
              aria-label="Remove"
            >
              ×
            </button>
          </div>
        ))}
        <div className="flex items-center gap-1.5">
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit()}
            placeholder={placeholder}
            className="flex-1 min-w-0 px-2.5 py-1.5 text-[11px] bg-transparent border border-[var(--axiom-border-hover)] rounded-lg text-[var(--axiom-text-secondary)] placeholder:text-[var(--axiom-text-tertiary)]/60 focus:outline-none"
          />
          <button onClick={submit} className="px-2.5 py-1.5 text-[10px] text-[var(--axiom-accent)] hover:text-[var(--axiom-accent-hover)]">
            Add
          </button>
        </div>
      </div>
    </BdSection>
  );
}

function EmptyNote({ children }: { children: React.ReactNode }) {
  return <p className="px-3 py-2 text-[10px] text-[var(--axiom-text-tertiary)]/70">{children}</p>;
}

// ── Action items + Founder approval ─────────────────────────────────
function ActionItems({ meeting, patch }: NotesProps) {
  const [composing, setComposing] = useState(false);
  const [title, setTitle] = useState("");
  const [owner, setOwner] = useState<SpeakerId>("jenson");
  const [deadline, setDeadline] = useState<(typeof DEADLINES)[number]>("Friday");
  const [requiresApproval, setRequiresApproval] = useState(true);

  const pending = meeting.actionItems.filter((a) => a.requiresApproval && a.approvalStatus === "pending");

  const submit = () => {
    const t = title.trim();
    if (!t) return;
    const item = {
      id: uid("ai"),
      title: t,
      owner: owner as SpeakerId,
      deadline: deadline as string,
      status: "PENDING" as const,
      requiresApproval,
      approvalStatus: requiresApproval ? ("pending" as const) : ("none" as const),
    };
    patch((m) => ({ ...m, actionItems: [...m.actionItems, item] }));
    setTitle("");
    setComposing(false);
  };

  const setApproval = (id: string, status: "approved" | "rejected" | "rework") =>
    patch((m) => ({
      ...m,
      actionItems: m.actionItems.map((a) => (a.id === id ? { ...a, approvalStatus: status } : a)),
    }));

  return (
    <BdSection
      title="Action items"
      right={
        <button onClick={() => setComposing((c) => !c)} className="text-[9px] font-medium text-[var(--axiom-accent)] hover:text-[var(--axiom-accent-hover)]">
          {composing ? "Cancel" : "+ Add"}
        </button>
      }
    >
      {/* Approval queue */}
      {pending.length > 0 && (
        <div className="px-3 pt-2">
          <p className="text-[9px] font-semibold tracking-wide text-[var(--axiom-warning)] uppercase flex items-center gap-1.5 mb-1.5">
            <span className="w-1 h-1 rounded-full bg-[var(--axiom-warning)] animate-pulse" />
            Founder approval required
          </p>
          <div className="space-y-2">
            {pending.map((a) => (
              <ApprovalCard key={a.id} title={a.title} owner={a.owner} onApprove={() => setApproval(a.id, "approved")} onReject={() => setApproval(a.id, "rejected")} onRework={() => setApproval(a.id, "rework")} />
            ))}
          </div>
        </div>
      )}

      {/* Composer */}
      {composing && (
        <div className="px-3 pt-2">
          <div className="space-y-2 rounded-xl border border-[var(--axiom-border-hover)] bg-white/[0.02] p-3">
            <input
              autoFocus
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submit()}
              placeholder="Action — e.g. Prepare acquisition campaign"
              className="w-full text-[12px] bg-transparent text-[var(--axiom-text-primary)] border-b border-[var(--axiom-border)] pb-1.5 focus:outline-none placeholder:text-[var(--axiom-text-tertiary)]/60"
            />
            <div className="flex items-center gap-2 text-[10px]">
              <span className="text-[var(--axiom-text-tertiary)]">Owner</span>
              <select value={owner} onChange={(e) => setOwner(e.target.value as SpeakerId)} className="bg-transparent text-[var(--axiom-text-secondary)] border border-[var(--axiom-border-hover)] rounded px-1.5 py-1 focus:outline-none">
                {EXECUTIVES.map((e) => (
                  <option key={e.id} value={e.id} className="bg-[var(--axiom-bg-surface)]">{e.name}</option>
                ))}
              </select>
              <span className="text-[var(--axiom-text-tertiary)]">Due</span>
              <select value={deadline} onChange={(e) => setDeadline(e.target.value as (typeof DEADLINES)[number])} className="bg-transparent text-[var(--axiom-text-secondary)] border border-[var(--axiom-border-hover)] rounded px-1.5 py-1 focus:outline-none">
                {DEADLINES.map((d) => (
                  <option key={d} value={d} className="bg-[var(--axiom-bg-surface)]">{d}</option>
                ))}
              </select>
            </div>
            <label className="flex items-center gap-2 text-[10px] text-[var(--axiom-text-tertiary)]">
              <input
                type="checkbox"
                checked={requiresApproval}
                onChange={(e) => setRequiresApproval(e.target.checked)}
                className="accent-[var(--axiom-accent)]"
              />
              Requires Founder approval
            </label>
            <button onClick={submit} className="w-full py-1.5 rounded-lg text-[10px] font-medium text-white" style={{ background: "linear-gradient(135deg, var(--axiom-accent), var(--axiom-violet))" }}>
              Create action item
            </button>
          </div>
        </div>
      )}

      {/* List */}
      {meeting.actionItems.length > 0 && (
        <div className="px-3 py-2 space-y-1.5">
          {meeting.actionItems.map((a) => {
            const e = getExecutive(a.owner);
            return (
              <div key={a.id} className="flex items-center gap-2.5 px-2.5 py-2 rounded-lg bg-white/[0.02] border border-[var(--axiom-border)]">
                <button onClick={() => patch((m) => ({ ...m, actionItems: m.actionItems.map((x) => (x.id === a.id ? { ...x, status: x.status === "COMPLETE" ? "PENDING" : "COMPLETE" } : x)) }))} className={cn("mt-0.5 w-3.5 h-3.5 rounded border flex-shrink-0 flex items-center justify-center transition-colors", a.status === "COMPLETE" ? "bg-[var(--axiom-accent)] border-[var(--axiom-accent)]" : "border-[var(--axiom-border-hover)]")}>
                  {a.status === "COMPLETE" && <span className="text-white">✓</span>}
                </button>
                <div className="flex-1 min-w-0">
                  <p className={cn("text-[11px] leading-snug", a.status === "COMPLETE" ? "text-[var(--axiom-text-tertiary)] line-through" : "text-[var(--axiom-text-primary)]")}>{a.title}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className={cn("text-[9px]", e.text)}>@{e.name}</span>
                    <span className="text-[9px] text-[var(--axiom-text-tertiary)]">due {a.deadline}</span>
                    {a.requiresApproval && <ApprovalBadge status={a.approvalStatus} />}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {!composing && meeting.actionItems.length === 0 && <EmptyNote>No action items yet. Decisions become action items.</EmptyNote>}
    </BdSection>
  );
}

function ApprovalCard({ title, owner, onApprove, onReject, onRework }: { title: string; owner: SpeakerId; onApprove: () => void; onReject: () => void; onRework: () => void }) {
  const e = getExecutive(owner);
  return (
    <div className="rounded-xl border border-[#ffb830]/25 bg-[#ffb830]/[0.05] p-3">
      <p className="text-[11px] text-[var(--axiom-text-primary)] leading-snug">{title}</p>
      <p className={cn("text-[9px] mt-1", e.text)}>Requested by {e.name}</p>
      <div className="flex items-center gap-1.5 mt-2.5 flex-wrap">
        <button onClick={onApprove} className="px-2.5 py-1 rounded-md text-[9px] font-medium text-white" style={{ background: "linear-gradient(135deg, var(--axiom-accent), var(--axiom-violet))" }}>
          Approve
        </button>
        <button onClick={onReject} className="px-2.5 py-1 rounded-md text-[9px] font-medium text-[var(--axiom-error)] border border-[var(--axiom-error)]/30 hover:bg-[var(--axiom-error)]/10">Reject</button>
        <button onClick={onRework} className="px-2.5 py-1 rounded-md text-[9px] font-medium text-[var(--axiom-warning)] border border-[var(--axiom-warning)]/30 hover:bg-[var(--axiom-warning)]/10">Send back</button>
      </div>
    </div>
  );
}

function ApprovalBadge({ status }: { status: BrMeeting["actionItems"][number]["approvalStatus"] }) {
  if (status === "approved") return <span className="text-[8px] font-medium text-[var(--axiom-success)] px-1.5 py-0.5 rounded-full bg-[var(--axiom-success)]/10 border border-[var(--axiom-success)]/20">APPROVED</span>;
  if (status === "rejected") return <span className="text-[8px] font-medium text-[var(--axiom-error)] px-1.5 py-0.5 rounded-full bg-[var(--axiom-error)]/10 border border-[var(--axiom-error)]/20">REJECTED</span>;
  if (status === "rework") return <span className="text-[8px] font-medium text-[var(--axiom-warning)] px-1.5 py-0.5 rounded-full bg-[var(--axiom-warning)]/10 border border-[var(--axiom-warning)]/20">SENT BACK</span>;
  if (status === "pending") return <span className="text-[8px] font-medium text-[var(--axiom-warning)] px-1.5 py-0.5 rounded-full bg-[var(--axiom-warning)]/10 border border-[var(--axiom-warning)]/20 animate-pulse">AWAITING APPROVAL</span>;
  return null;
}