# Auditor — Outputs

## Monthly Outputs

- Monthly audit memo
- Transaction sample review findings
- Budget variance verification
- Monthly risk register update

## Quarterly Outputs

- Full compliance review report
- Internal controls assessment
- Risk register refresh
- Quarterly audit report to Jenson

## Event-Triggered Outputs

| Event | Trigger | Deliverable |
|-------|---------|-------------|
| `audit-completed` | Audit cycle finishes | Audit report path, key findings, recommendations |
| `compliance-issue-detected` | Issue identified | Issue details, severity, recommended action |

## Periodic Schedule

| Cadence | Activity | Audience |
|---------|----------|----------|
| Daily | No routine output (event-driven) | — |
| Weekly | Risk register health check (if triggered) | Department memory |
| Monthly | Audit memo | Jenson, department memory |
| Quarterly | Full audit report | Jenson |

## Templates

### Monthly Audit Memo
```
# Monthly Audit Memo — {Month} {Year}

## Scope
## Methodology
## Findings
### Positive
### Concerns
## Recommendations
## Follow-up Items
```

### Compliance Issue Report
```
# Compliance Issue Report
**Severity:** {critical/high/medium/low}
**Detected:** {date}
**Department:** {department}
**Description:**
**Evidence:**
**Risk:**
**Recommended Action:**
**Escalated To:** Jenson
```