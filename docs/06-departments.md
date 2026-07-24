# Axiom OS — Departments

## Overview

Departments group agents and workflows by function. Each department belongs to an organization and has a manager executive.

## Bleval Departments

| Department | Manager | Agents |
|-----------|---------|--------|
| sales | jenson | atlas, apollo, closer |
| marketing | jenson | nova, creator |
| development | jenson | forge, tester |
| operations | jenson | ledger, pulse |
| finance | jenson | treasury, auditor |

## HOV Departments

| Department | Manager | Agents |
|-----------|---------|--------|
| brand | valta_prime | — |
| creative | valta_prime | — |
| research | valta_prime | — |
| content | valta_prime | — |
| growth | valta_prime | — |
| operations | valta_prime | — |

## Personal Departments

| Department | Manager | Agents |
|-----------|---------|--------|
| productivity | yamako | — |
| knowledge | yamako | — |

## Department Configuration

Each department is defined in `departments/{org_id}/{dept}/` with:
- `department.yaml` — Definition, manager, agents, workflows
- `mission.md` — Department mission statement
- `metrics.md` — KPI definitions
- `playbook.md` — Operational playbook
- `processes.md` — Process documentation

## API Endpoints
- `GET /api/v1/organisations/{org_id}/departments` — List departments for org