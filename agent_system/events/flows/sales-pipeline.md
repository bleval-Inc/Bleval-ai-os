# Sales Pipeline Event Flow

```
Atlas discovers lead
    │
    ▼
lead-discovered event ──────────→ Jenson (review)
    │                              │
    │                              ▼
    │                         lead-qualified event ──────────→ Apollo (outreach)
    │                                                              │
    │                                                              ▼
    │                                                         outreach-sent event ──→ Jenson (tracking)
    │                                                              │
    │                                                              ▼
    │                                                         response-received event ──→ Closer (handle)
    │                                                              │
    │                                                              ▼
    │                                                         opportunity-created event ──→ Jenson, Ledger
    │                                                              │
    │                                                              ▼
    │                                                         deal-closed-won/lost event ──→ Jenson, Ledger, Pulse
    │
    └── learnings stored in department memory
```