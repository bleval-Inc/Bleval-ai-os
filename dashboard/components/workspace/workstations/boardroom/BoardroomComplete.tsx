"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { formatClock, formatDate, formatDuration, getExecutive, type BrMeeting } from "./boardroom-data";
import { BdButton, MonoLabel } from "./boardroom-ui";

// ── Meeting completion — structured summary ───────────────────────────
// Shown when the Founder ends a meeting. SAVE MEETING persists the record
// (boardroom-data → isolated backend integration point); RETURN TO
// BOARDROOM goes back to the landing view.

export default function BoardroomComplete({
  meeting,
  saved,
  onSave,
  onReturn,
}: {
  meeting: BrMeeting;
  saved: boolean;
  onSave: () => void;
  onReturn: () => void;
}) {
  const duration =
    meeting.completedAt != null ? formatDuration(meeting.startedAt, meeting.completedAt) : "—";

  return (
    <div className="flex-1 min-h-0 overflow-y-auto hide-scrollbar">
      <div className="max-w-3xl mx-auto px-5 md:px-8 py-10">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, ease: "easeOut" }}>
          <MonoLabel>AXIOM // SESSION COMPLETE</MonoLabel>
          <h1 className="mt-3 text-3xl md:text-4xl font-light tracking-tight text-[var(--axiom-text-primary)]">Meeting summary</h1>
          <p className="mt-2 text-[13px] text-[var(--axiom-text-tertiary)]">
            {meeting.title} · {formatDate(meeting.startedAt)} · began {formatClock(meeting.startedAt)} · {duration}
          </p>
        </motion.div>

        <div className="mt-8 space-y-5">
          <SummaryBlock title="Summary">{meeting.summary || "No summary captured for this session."}</SummaryBlock>

          <SummaryBlock title="Decisions">
            {meeting.decisions.length === 0 ? (
              <p className="text-[var(--axiom-text-tertiary)]">None recorded.</p>
            ) : (
              <ul className="space-y-1.5">
                {meeting.decisions.map((d) => (
                  <li key={d.id} className="flex items-start gap-2">
                    <span className={cn("mt-0.5 w-1.5 h-1.5 rounded-full flex-shrink-0", d.approved ? "bg-[var(--axiom-accent)]" : "bg-[var(--axiom-text-tertiary)]")} />
                    <span className="text-[12.5px] text-[var(--axiom-text-secondary)] leading-snug">{d.title}</span>
                  </li>
                ))}
              </ul>
            )}
          </SummaryBlock>

          <SummaryBlock title="Action items">
            {meeting.actionItems.length === 0 ? (
              <p className="text-[var(--axiom-text-tertiary)]">None created.</p>
            ) : (
              <ul className="space-y-1.5">
                {meeting.actionItems.map((a) => {
                  const e = getExecutive(a.owner);
                  return (
                    <li key={a.id} className="flex items-center gap-2.5 text-[12.5px] text-[var(--axiom-text-secondary)]">
                      <span className={cn("w-1.5 h-1.5 rounded-full flex-shrink-0", a.status === "COMPLETE" ? "bg-[var(--axiom-success)]" : "bg-[var(--axiom-accent)]")} />
                      <span className="min-w-0 flex-1 leading-snug">{a.title}</span>
                      <span className={cn("text-[10px]", e.text)}>@{e.name}</span>
                      {a.requiresApproval && (
                        <span className={cn("text-[8px] font-medium px-1.5 py-0.5 rounded-full border", a.approvalStatus === "approved" ? "text-[var(--axiom-success)] border-[var(--axiom-success)]/20 bg-[var(--axiom-success)]/10" : "text-[var(--axiom-warning)] border-[var(--axiom-warning)]/25 bg-[var(--axiom-warning)]/10")}>
                          {a.approvalStatus === "pending" ? "AWAITING APPROVAL" : a.approvalStatus === "approved" ? "APPROVED" : "LOCKED"}
                        </span>
                      )}
                    </li>
                  );
                })}
              </ul>
            )}
          </SummaryBlock>

          <SummaryBlock title="Recommendations">
            {meeting.recommendations.length === 0 ? <p className="text-[var(--axiom-text-tertiary)]">None.</p> : (
              <ul className="space-y-1.5">{meeting.recommendations.map((r, i) => <li key={i} className="text-[12.5px] text-[var(--axiom-text-secondary)] leading-snug">· {r}</li>)}</ul>
            )}
          </SummaryBlock>

          <SummaryBlock title="Follow-ups">
            {meeting.followUps.length === 0 ? <p className="text-[var(--axiom-text-tertiary)]">None.</p> : (
              <ul className="space-y-1.5">{meeting.followUps.map((f, i) => <li key={i} className="text-[12.5px] text-[var(--axiom-text-secondary)] leading-snug">· {f}</li>)}</ul>
            )}
          </SummaryBlock>

          <SummaryBlock title="Participants">
            <div className="flex flex-wrap gap-1.5">
              {meeting.participants.map((id) => {
                const e = getExecutive(id);
                return <span key={id} className="px-2 py-1 rounded-lg border border-[var(--axiom-border-hover)] bg-white/[0.02] text-[10px] text-[var(--axiom-text-secondary)]">{e.name} · {e.role}</span>;
              })}
            </div>
          </SummaryBlock>
        </div>

        {/* Actions */}
        <div className="mt-10 flex items-center justify-end gap-3">
          <BdButton variant="ghost" onClick={onReturn}>RETURN TO BOARDROOM</BdButton>
          <BdButton variant="primary" onClick={onSave} disabled={saved} className="px-5">
            {saved ? "MEETING SAVED ✓" : "SAVE MEETING"}
          </BdButton>
        </div>
      </div>
    </div>
  );
}

function SummaryBlock({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-[var(--axiom-border)] p-4" style={{ background: "rgba(13,16,20,0.4)" }}>
      <h3 className="text-[10px] font-semibold tracking-[0.14em] text-[var(--axiom-text-tertiary)] uppercase mb-2">{title}</h3>
      <div className="text-[13px] text-[var(--axiom-text-secondary)] leading-relaxed">{children}</div>
    </section>
  );
}