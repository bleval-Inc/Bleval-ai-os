# Treasury — Outputs

## Daily Outputs

- Cash position summary (written to department memory)
- Inflow/outflow tracking log
- Threshold alerts (if triggered)

## Weekly Outputs

- Rolling 13-week cash flow forecast
- Expense review report (top 10 expenses, anomalies flagged)
- Budget variance report by department

## Monthly Outputs

- Monthly financial summary (P&L, cash flow, balance sheet)
- 6-month rolling financial forecast
- Budget rebalancing recommendations
- Financial risk assessment and mitigation update

## Event Emissions

| Event | Trigger | Payload |
|-------|---------|---------|
| `financial-report-ready` | Monthly report complete | Report path, summary metrics, key findings |
| `metric-updated` | Any metric change | Metric name, old value, new value, trend |

## Templates

### Cash Flow Forecast
```
# 13-Week Cash Flow Forecast
**Generated:** {date}
**Confidence:** {high/medium/low}

| Week | Opening | Inflows | Outflows | Closing | Notes |
|------|---------|---------|----------|---------|-------|
```

### Monthly Summary
```
# Monthly Financial Summary — {Month} {Year}
## Revenue
## Expenses
## Cash Flow
## Budget Variance
## Key Metrics
## Forecast Update
## Recommendations
```