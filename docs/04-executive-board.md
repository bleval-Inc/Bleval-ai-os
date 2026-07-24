# Axiom OS — Executive Board

## Overview

The ExecutiveBoard manages autonomous runtime loops for each executive agent. Each loop runs on its own schedule, independent of the others.

## Executives

| ID | Organization | Departments |
|----|-------------|-------------|
| jenson | bleval | sales, marketing, development, operations, finance |
| valta_prime | hov | brand, creative, research, content, growth, operations |
| yamako | personal | productivity, knowledge |

## Runtime Loop Cycle

Each executive loop follows this cycle:

```
Morning Review → Check KPIs → Review Memory → Identify Priorities
→ Launch Workflows → Review Results → Report
```

## Schedules

Each executive has 4 default schedules:
- `morning_review` — Daily review of priorities
- `midday_check` — Midday progress check
- `afternoon_review` — End-of-day review
- `daily_report` — Daily summary report

## API Endpoints

- `GET /api/v1/executives/board/status` — All loop statuses
- `POST /api/v1/executives/board/trigger` — Trigger all executives
- `GET /api/v1/executives/{id}/loop/status` — Single loop status
- `POST /api/v1/executives/{id}/loop/trigger` — Trigger single executive
- `GET /api/v1/executives/{id}/loop/schedules` — List schedules
- `POST /api/v1/executives/{id}/loop/schedules` — Set schedule