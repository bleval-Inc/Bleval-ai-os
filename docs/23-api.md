# Axiom OS — API Reference

## Base URL

All endpoints are at `/api/v1/`. Server runs on port 8000 by default.

## Interactive Docs

OpenAPI documentation available at `/docs` (Swagger UI).

## Endpoint Groups

### System
| Method | Path | Description |
|--------|------|-------------|
| GET | / | Root info |
| GET | /api/v1/status | Runtime status with all components |
| GET | /api/v1/health | Component health summary |

### Organizations
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/organisations | List organizations |
| GET | /api/v1/organisations/{id} | Organization detail |
| GET | /api/v1/organisations/{id}/departments | List departments |

### Executives
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/executives | List executives |
| GET | /api/v1/executives/{id} | Executive detail |
| GET | /api/v1/executives/board/status | Board status |
| POST | /api/v1/executives/board/trigger | Trigger all cycles |
| GET | /api/v1/executives/{id}/loop/status | Loop status |
| POST | /api/v1/executives/{id}/loop/trigger | Trigger cycle |
| GET | /api/v1/executives/{id}/loop/schedules | List schedules |

### Agents
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/agents | List all agents |
| GET | /api/v1/agents/{id} | Agent detail |

### Capabilities
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/capabilities | List/search capabilities |
| GET | /api/v1/capabilities/{id} | Capability detail |

### Workflows
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/workflows | List workflows |
| GET | /api/v1/workflows/{id} | Workflow definition |
| POST | /api/v1/workflows/launch | Launch workflow |

### Instances
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/instances | List instances |
| GET | /api/v1/instances/{id} | Instance detail |
| POST | /api/v1/instances/{id}/advance | Advance step |
| POST | /api/v1/instances/{id}/cancel | Cancel instance |

### Events
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/events/types | List event types |
| POST | /api/v1/events/publish | Publish event |

### Memory
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/memory/{agent_id} | Resolved memory context |

### Approvals
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/approvals | List approvals |
| POST | /api/v1/approvals/{id}/respond | Respond to approval |

### Learning
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/learning/status | Learning engine status |
| GET | /api/v1/learning/scores | All scores |
| GET | /api/v1/learning/scores/{type}/{id} | Entity score history |
| GET | /api/v1/learning/analytics/workflows | Workflow analytics |
| GET | /api/v1/learning/analytics/executives | Executive analytics |
| GET | /api/v1/learning/analytics/agents | Agent analytics |
| GET | /api/v1/learning/patterns | Detected patterns |
| GET | /api/v1/learning/recommendations | Recommendations |
| GET | /api/v1/learning/knowledge | Knowledge entries |
| GET | /api/v1/learning/cycles | Learning cycles |
| POST | /api/v1/learning/cycle/run | Run learning cycle |
| GET | /api/v1/learning/playbook-evolutions | Playbook changes |