---
title: Yamako KPI Definitions
executive: Yamako
type: kpi-definitions
version: 1.0
created: 2026-08-02
updated: 2026-08-02
description: Key Performance Indicators for Yamako's personal operations management. Tracks schedule adherence, routine compliance, and Founder productivity enablement.
review_frequency: weekly
report_to: Founder
---

# Yamako — KPI Definitions & Tracking

---

## 1. Wake-Up Adherence Rate

Measures how consistently the Founder wakes up at the 05:00 target time, with tolerance for the escalation protocol.

### KPI Definition

| Field | Value |
|-------|-------|
| **Metric** | Percentage of days Founder is awake within 15 minutes of 05:00 target |
| **Current Target** | 85% |
| **Minimum Acceptable** | 70% |
| **Stretch Goal** | 95% |
| **Tracking Method** | Wake-up log: target time, actual wake time, escalation level reached |
| **Calculation** | `(Days wake-up within 05:15) / (Total days) x 100` |
| **Exclusions** | Weekends, holidays, illness. Max 2 excused days/week. |
| **Notes** | Wake-up is the foundation of the entire day. A missed wake-up cascades into every other metric. Track sniffs separately — 1 snooze is within tolerance, 2+ in a row is a trend. |

### Escalation Level Tracking

| Level | Target Frequency | Concern Threshold |
|-------|----------------|-------------------|
| None (on time) | 60%+ | < 40% |
| Gentle (05:00-05:10) | 25% | > 40% |
| Firm (05:10-05:20) | 10% | > 20% |
| Urgent (05:20-05:30) | 5% | > 10% |
| Emergency (05:30+) | 0% | Any occurrence triggers review |

---

## 2. Schedule Compliance %

Measures how faithfully the daily schedule is executed against the planned blocks.

### KPI Definition

| Field | Value |
|-------|-------|
| **Metric** | Percentage of scheduled time blocks that start within 5 minutes of planned time and achieve their intended output |
| **Current Target** | 90% |
| **Minimum Acceptable** | 80% |
| **Stretch Goal** | 95% |
| **Tracking Method** | Schedule log: each block recorded with start time, duration, completion status, and output achieved |
| **Calculation** | `(Blocks completed as scheduled) / (Total scheduled blocks) x 100` |
| **Notes** | A block is "completed as scheduled" if: (a) started within 5 min of plan, (b) ran full duration, (c) primary output was achieved. Partial compliance (2 of 3 criteria) counts half. |

### Block Categories Tracked

| Category | Typical Blocks/Day | Weight |
|----------|--------------------|--------|
| Trading/Market | 2 (prep + review) | High |
| Learning | 1 | High |
| Client Work | 3-4 | Medium |
| Project Work | 1-2 | Medium |
| Meals/Breaks | 3 | Low |
| Exercise/Training | 1 | High |
| Wind-Down/Sleep | 2 | High |

---

## 3. Meeting Punctuality

Measures whether the Founder arrives on time for all scheduled meetings and calls.

### KPI Definition

| Field | Value |
|-------|-------|
| **Metric** | Percentage of meetings where Founder is ready and connected at scheduled start time |
| **Current Target** | 95% |
| **Minimum Acceptable** | 85% |
| **Stretch Goal** | 100% |
| **Tracking Method** | Calendar event log + Yamako confirmation at meeting start |
| **Calculation** | `(Meetings started on time) / (Total meetings) x 100` |
| **Notes** | "On time" means the Founder is at the meeting location (or on the call) and ready to engage. If Yamako had to send a reminder and the Founder was late, that counts as missed. |

### Reminder Protocol

| Timing | Method | Note |
|--------|--------|------|
| 15 min before | Message | Standard reminder with prep context |
| 5 min before | Message | "Meeting in 5 minutes at {location/link}" |
| At start | Confirmation | "Meeting started. Founder connected." Logged. |
| 5 min late | Escalation | If Founder not present, trigger escalation to Jenson |

---

## 4. Learning Completion Rate

Measures how well the Founder maintains the daily learning routine.

### KPI Definition

| Field | Value |
|-------|-------|
| **Metric** | Percentage of scheduled learning blocks completed with material reviewed and key concepts retained |
| **Current Target** | 90% |
| **Minimum Acceptable** | 75% |
| **Stretch Goal** | 100% |
| **Tracking Method** | Learning log: session date, material covered, pages/lessons completed, quiz score |
| **Calculation** | `(Learning blocks completed with >70% retention quiz score) / (Total scheduled learning blocks) x 100` |
| **Notes** | A learning block is only counted as completed if the Founder achieves a 7/10 or higher on the retention quiz. Completing the time without comprehension does not count. |

### Learning Progress Tracking

| Week | Hours Completed | Pages/Lessons | Quiz Avg | Topics Covered |
|------|-----------------|---------------|----------|----------------|
| 1    | 5.5             | 18 pages      | 7.8/10   | Macroeconomics |
| 2    | —               | —             | —        | —              |
| 3    | —               | —             | —        | —              |
| 4    | —               | —             | —        | —              |

*Table updated weekly in Friday summary.*

---

## 5. Training Adherence

Measures compliance with physical training and exercise routines.

### KPI Definition

| Field | Value |
|-------|-------|
| **Metric** | Percentage of scheduled training sessions completed per week |
| **Current Target** | 4 sessions / week (minimum) |
| **Minimum Acceptable** | 3 sessions / week |
| **Stretch Goal** | 6 sessions / week |
| **Tracking Method** | Training log: date, type, duration, intensity, notes |
| **Calculation** | `(Sessions completed) / (Sessions scheduled) x 100` |
| **Notes** | Training supports mental performance as much as physical. A missed session is flagged if not rescheduled within 24 hours. |

---

## 6. Sleep Schedule Compliance

Measures how consistently the Founder follows the sleep schedule (wind-down at 20:00, lights-out at 21:00).

### KPI Definition

| Field | Value |
|-------|-------|
| **Metric** | Percentage of nights where wind-down starts by 20:00 and lights-out by 21:00 |
| **Current Target** | 85% |
| **Minimum Acceptable** | 70% |
| **Stretch Goal** | 95% |
| **Tracking Method** | Sleep log: wind-down start, lights-out time, estimated sleep duration |
| **Calculation** | `(Nights meeting both wind-down and lights-out targets) / (Total nights) x 100` |
| **Notes** | 7+ hours of sleep per night is non-negotiable for cognitive performance. A late night must be balanced with an earlier night within 48 hours. |

### Sleep Compliance Tracker

| Day      | Wind-Down | Lights-Out | Hours Sleep | Compliance |
|----------|-----------|------------|-------------|------------|
| Mon      | —         | —          | —           | —          |
| Tue      | —         | —          | —           | —          |
| Wed      | —         | —          | —           | —          |
| Thu      | —         | —          | —           | —          |
| Fri      | —         | —          | —           | —          |
| Sat      | —         | —          | —           | —          |
| Sun      | —         | —          | —           | —          |

*Table updated nightly and reviewed each Friday.*

---

## 7. Quote Quality Score

Measures the quality and appropriateness of the daily grounding quote delivered each morning.

### KPI Definition

| Field | Value |
|-------|-------|
| **Metric** | Average quality score (1-10) based on relevance to current context, authenticity of source, and impact on Founder's mindset |
| **Current Target** | 8.0 / 10 |
| **Minimum Acceptable** | 6.5 / 10 |
| **Stretch Goal** | 9.5 / 10 |
| **Tracking Method** | Quote log with Founder feedback rating (optional weekly self-report) |
| **Notes** | Quotes must be from real historical figures only. No fabricated or misattributed quotes. Score is based on Yamako's self-assessment unless Founder provides feedback. |

### Quote Selection Criteria

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Authenticity | 30% | Source must be verifiably real historical figure. Citation included. |
| Relevance | 30% | Quote should connect to Founder's current challenges, goals, or mindset. |
| Originality | 20% | Avoid overused quotes. Seek lesser-known but powerful lines. |
| Emotional Impact | 20% | Does the quote land? Does it ground the Founder for the day? |

---

## Summary Dashboard

| KPI                        | Target    | Frequency   | Alert Trigger                  |
|----------------------------|-----------|-------------|--------------------------------|
| Wake-Up Adherence          | 85%       | Weekly      | < 70% in a week                |
| Schedule Compliance        | 90%       | Weekly      | < 80% in a week                |
| Meeting Punctuality        | 95%       | Weekly      | < 85% in a week                |
| Learning Completion Rate   | 90%       | Weekly      | < 75% in a week                |
| Training Adherence         | 4/wk      | Weekly      | < 3 sessions in a week         |
| Sleep Schedule Compliance  | 85%       | Weekly      | < 70% in a week                |
| Quote Quality Score        | 8.0/10    | Weekly      | < 6.5/10                       |

---

## Weekly Report Template (Friday 17:00)

```
# Yamako — Weekly Performance Report
## Week of {date}

### Summary
| Metric               | This Week | Target   | Status |
|----------------------|-----------|----------|--------|
| Wake-Up Adherence    | {x}%      | 85%      | {ok/warn/critical} |
| Schedule Compliance  | {x}%      | 90%      | {ok/warn/critical} |
| Meeting Punctuality  | {x}%      | 95%      | {ok/warn/critical} |
| Learning Completion  | {x}%      | 90%      | {ok/warn/critical} |
| Training Adherence   | {x}/wk    | 4/wk     | {ok/warn/critical} |
| Sleep Compliance     | {x}%      | 85%      | {ok/warn/critical} |
| Quote Quality        | {x}/10    | 8.0/10   | {ok/warn/critical} |

### Observations
- Key patterns: {notable trends or deviations}
- Escalations used: {count and context}
- Adjustments made: {schedule or protocol changes}

### Next Week Focus
{1-3 priorities for the coming week}
```

> *"The structure you keep is the freedom you earn. Every on-time wake-up, every completed block, every restful night — these are the bricks of a life well-built."*
> — Yamako — Personal Operations