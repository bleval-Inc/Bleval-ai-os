# Axiom OS — Agents

## Overview

Agents are the executable entities that perform work. They are assigned to departments and have specific capabilities.

## Agent Registry

15 agents registered across all organizations:

### Sales (bleval)
| Agent | Capabilities |
|-------|-------------|
| atlas | lead-research, market-analysis, competitive-intelligence |
| apollo | email-campaigns, outreach-sequencing |
| closer | deal-structuring, negotiation, contract-generation |

### Marketing (bleval)
| Agent | Capabilities |
|-------|-------------|
| nova | trend-identification, seo-research, content-strategy |
| creator | content-creation, copywriting, brand-voice |

### Development (bleval)
| Agent | Capabilities |
|-------|-------------|
| forge | software-development, code-review, architecture-planning |
| tester | testing, qa-automation, bug-reporting |

### Operations (bleval)
| Agent | Capabilities |
|-------|-------------|
| ledger | process-optimization, workflow-automation |
| pulse | metric-tracking, reporting |

### Finance (bleval)
| Agent | Capabilities |
|-------|-------------|
| treasury | budget-planning, financial-forecasting |
| auditor | compliance-checking, risk-assessment |

### Executives (cross-org)
| Agent | Organization |
|-------|-------------|
| jenson | bleval |
| valta_prime | hov |
| yamako | personal |

## Agent Configuration

Each agent defined in `agents/{org}/{dept}/{role}/agent.yml` with:
- Identity file (`identity.md`)
- Instructions (`instructions.md`)
- Memory configuration (`memory.md`)
- Permissions (`permissions.md`)

## API Endpoints
- `GET /api/v1/agents` — List all agents
- `GET /api/v1/agents/{id}` — Get agent detail