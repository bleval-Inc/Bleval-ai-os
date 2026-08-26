// ACQUISITION — placeholder prospect/acquisition data.
// Later supplied by the dedicated BLEVAL lead database / CRM.

import type { MetricKpi } from "./types";

export const acquisitionKpis: MetricKpi[] = [
  { key: "prospects", label: "Prospects", value: "248", delta: "+32 new", series: [132, 148, 166, 181, 199, 215, 232, 248] },
  { key: "qualified", label: "Qualified Leads", value: "41", delta: "+6", series: [16, 19, 22, 25, 29, 32, 37, 41] },
  { key: "conversations", label: "Active Conversations", value: "24", delta: "8 this week", series: [10, 12, 13, 15, 17, 19, 22, 24] },
  { key: "calls", label: "Sales Calls", value: "14", delta: "4 today", series: [5, 6, 7, 8, 9, 10, 12, 14] },
];

export const acquisitionFunnel: { id: string; label: string; value: number }[] = [
  { id: "prospects", label: "Prospects", value: 248 },
  { id: "contacted", label: "Contacted", value: 172 },
  { id: "engaged", label: "Engaged", value: 86 },
  { id: "qualified", label: "Qualified", value: 41 },
  { id: "warm", label: "Warm", value: 29 },
  { id: "callbooked", label: "Call Booked", value: 17 },
  { id: "closed", label: "Closed", value: 6 },
];

export interface Lead {
  id: string;
  company: string;
  contact: string;
  industry: string;
  value: string;
}

export const leadColumns: { id: string; label: string; leads: Lead[] }[] = [
  { id: "new", label: "New", leads: [
    { id: "l1", company: "Aster Group", contact: "M. Botha", industry: "Energy", value: "R18k" },
    { id: "l2", company: "Plume Studio", contact: "D. Nkosi", industry: "Creative", value: "R9k" },
  ] },
  { id: "contacted", label: "Contacted", leads: [
    { id: "l3", company: "Listenatix", contact: "R. Adams", industry: "SaaS", value: "R14k" },
    { id: "l4", company: "Havn Retail", contact: "S. Govender", industry: "Retail", value: "R11k" },
  ] },
  { id: "engaged", label: "Engaged", leads: [
    { id: "l5", company: "Fernwood", contact: "C. du Toit", industry: "Property", value: "R16k" },
  ] },
  { id: "qualified", label: "Qualified", leads: [
    { id: "l6", company: "Veld Growth", contact: "L. Meyer", industry: "Fintech", value: "R22k" },
    { id: "l7", company: "North End Co", contact: "T. Patel", industry: "Retail", value: "R12k" },
  ] },
  { id: "warm", label: "Warm", leads: [
    { id: "l8", company: "Silent Lake", contact: "K. James", industry: "Health", value: "R19k" },
  ] },
  { id: "callbooked", label: "Call Booked", leads: [
    { id: "l9", company: "Veridian", contact: "P. Mokoena", industry: "Health", value: "R21k" },
  ] },
  { id: "closed", label: "Closed", leads: [
    { id: "l10", company: "Helios Capital", contact: "B. Naidoo", industry: "Finance", value: "R24k" },
  ] },
];

export interface OutreachChannel {
  id: string;
  label: string;
  sent: number;
  responded: number;
  status: "active" | "paused";
}

export const outreachChannels: OutreachChannel[] = [
  { id: "email", label: "Email", sent: 132, responded: 42, status: "active" },
  { id: "sms", label: "SMS", sent: 76, responded: 19, status: "active" },
  { id: "social", label: "Social DM", sent: 54, responded: 12, status: "active" },
  { id: "phone", label: "Phone", sent: 18, responded: 6, status: "active" },
  { id: "followup", label: "Follow-up", sent: 9, responded: 4, status: "paused" },
];

export const jensonOversight = {
  campaign: "Solar Growth Blitz",
  workflow: "Acquisition-042",
  attentionLeads: 6,
  recommendations: [
    "Prioritise Veld Growth — highest qualified value left open (R22k).",
    "48h rule: 9 engaged leads have gone quiet; nudge today.",
    "Pause Follow-up cadence until email deliverability clears.",
  ],
};