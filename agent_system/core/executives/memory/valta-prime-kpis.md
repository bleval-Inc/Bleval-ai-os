---
title: Valta Prime KPI Definitions
executive: Valta Prime
type: kpi-definitions
version: 1.0
created: 2026-08-02
updated: 2026-08-02
description: Key Performance Indicators for Valta Prime's analysis, reporting, and decision-support functions. Tracks timeliness, accuracy, and effectiveness of market intelligence.
review_frequency: weekly
report_to: Founder
---

# Valta Prime — KPI Definitions & Tracking

---

## 1. Reports Delivered On Time

Valta Prime is responsible for five non-negotiable reports each week. Timeliness is a binary metric — on time or not.

### Report Schedule

| Report           | Day       | Time       | Content |
|------------------|-----------|------------|---------|
| Morning Report   | Monday-Friday | 07:30 | Overnight action, Asia open, key levels, economic calendar |
| Evening Report   | Monday-Friday | 18:00 | Daily recap, P&L, trade journal, tomorrow's outlook |
| Weekly Review    | Friday        | 17:00 | Week in review, performance stats, lessons learned |
| Sunday Prep      | Sunday        | 18:00 | Week ahead, macro calendar, key levels, positioning plan |
| Monthly Deep-Dive | Last day of month | 17:00 | Monthly performance, strategy review, adjustments |

### KPI Definition

| Field | Value |
|-------|-------|
| **Metric** | Percentage of reports delivered within 15 minutes of scheduled time |
| **Current Target** | 100% |
| **Minimum Acceptable** | 95% |
| **Tracking Method** | Report delivery log with timestamp |
| **Notes** | A late report is a missed commitment. Volume is not a substitute for timeliness. If running late, send a brief holding message with estimated delay. |

---

## 2. POI Detection Accuracy

POI (Point of Interest) detection is Valta Prime's highest-value function. Accuracy measures how often price action respects the identified level.

### KPI Definition

| Field | Value |
|-------|-------|
| **Metric** | Percentage of POI alerts where price reaches within 0.1% of the identified level within 48 hours |
| **Current Target** | 80% |
| **Minimum Acceptable** | 65% |
| **Stretch Goal** | 90% |
| **Tracking Method** | POI alert log cross-referenced with market data after 48 hours |
| **Calculation** | `(POIs where price touched level) / (Total POIs alerted) x 100` |
| **Notes** | A "touch" includes wicks. If price reverses 5+ points from POI without touching, that's a near-miss — flag for review but does not count as hit. |

### POI Detection Tier System

| Tier | Precision Window | Target Accuracy | Action |
|------|------------------|-----------------|--------|
| A    | Within 5 pips / 10 points | 90% | Alert immediately |
| B    | Within 10 pips / 20 points | 75% | Alert with caveat |
| C    | Within 20 pips / 40 points | 60% | Note in report, no alert |

---

## 3. Alert Response Time

Time from Valta Prime identifying a critical condition (POI reached, news event, technical break) to delivering the alert to the Founder.

### KPI Definition

| Field | Value |
|-------|-------|
| **Metric** | Time between detection and alert delivery |
| **Current Target** | 5 minutes |
| **Maximum Acceptable** | 15 minutes |
| **Stretch Goal** | 2 minutes |
| **Tracking Method** | Alert log with detection timestamp and delivery timestamp |
| **Notes** | Speed matters most during active market hours. Outside market hours, 30-minute response is acceptable for non-critical alerts. |

### Escalation Tiers

| Tier | Condition | Target Response | Alert Method |
|------|-----------|-----------------|--------------|
| 1    | GOLD at POI | < 5 min | Direct message |
| 2    | US30 at POI | < 5 min | Direct message |
| 3    | Major news event | < 10 min | Structured alert |
| 4    | Technical break | < 15 min | Report update |
| 5    | General market observation | Next report | Include in next scheduled report |

---

## 4. Bias Challenge Effectiveness

Measures how often Valta Prime's challenges to Founder bias result in improved decision-making.

### KPI Definition

| Field | Value |
|-------|-------|
| **Metric** | Percentage of bias challenges where Founder either changed position or acknowledged the bias |
| **Current Target** | 50% |
| **Minimum Acceptable** | 30% |
| **Stretch Goal** | 75% |
| **Tracking Method** | Bias challenge log cross-referenced with decision history |
| **Calculation** | `(Challenges where Founder adjusted behavior) / (Total challenges issued) x 100` |
| **Notes** | A bias challenge is only counted if the bias was clearly articulated. Founder acknowledging the bias counts even if they don't change position — awareness is the first step. |

### Challenge Types

| Type | Description | Typical Context |
|------|-------------|-----------------|
| **Overconfidence** | Founder is too sure of a direction | After 3+ winning trades |
| **Revenge Trading** | Founder wants to recover a loss | After a losing trade |
| **Confirmation Bias** | Founder only sees data supporting position | During an existing trade |
| **Holding Bias** | Founder won't close a losing position | Trade in drawdown |
| **FOMO** | Founder wants to chase a move | After missing an entry |

---

## 5. Analysis Quality Score

A composite assessment of the thoroughness, objectivity, and usefulness of each analysis delivered.

### Scoring Rubric

| Criterion | Weight | Score 0 | Score 1 | Score 2 |
|-----------|--------|---------|---------|---------|
| Data completeness | 25% | Missing key data | Partial data | Full data with sources |
| Objectivity | 25% | One-sided | Mentions other view | Equal weight to both sides |
| Actionable recommendation | 25% | No recommendation | Vague recommendation | Clear entry/exit/stay |
| Supporting evidence | 25% | No evidence | Some evidence | Multiple timeframe/data confirmation |

### KPI Definition

| Field | Value |
|-------|-------|
| **Metric** | Average quality score across all analyses delivered in a week |
| **Current Target** | 7.0 / 8.0 |
| **Minimum Acceptable** | 5.5 / 8.0 |
| **Stretch Goal** | 7.5 / 8.0 |
| **Tracking Method** | Self-scored after each analysis. Reviewed weekly. |
| **Notes** | Score is recorded in the analysis log alongside the analysis itself. Used for continuous improvement, not performance pressure. |

---

## Summary Dashboard

| KPI                     | Target    | Frequency   | Alert Trigger          |
|-------------------------|-----------|-------------|------------------------|
| Reports On Time         | 100%      | Weekly      | Any late report        |
| POI Detection Accuracy  | 80%       | Weekly      | < 65% in a week        |
| Alert Response Time     | < 5 min   | Per alert   | > 15 min               |
| Bias Challenge Success  | 50%       | Weekly      | 0 successes in a week  |
| Analysis Quality Score  | 7.0/8.0   | Weekly      | < 5.5/8.0              |

---

## Weekly Performance Review

Each Friday, Valta Prime produces a self-assessment covering:

1. **Report timeliness**: All reports delivered on time? Any delays with root cause.
2. **POI accuracy**: Hit rate for the week. Patterns in misses.
3. **Alert speed**: Average response time. Any slow alerts and why.
4. **Bias challenges**: How many issued, how many effective. Founder bias patterns.
5. **Quality score**: Average score. Areas for improvement.

> *"Accuracy is the only metric that compounds. Every analysis, every POI, every challenge — each one sharpens the blade."*
> — Valta Prime — House of Valta