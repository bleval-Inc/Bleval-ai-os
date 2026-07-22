# Content Creation Event Flow

```
Nova researches market
    │
    ▼
content-researched event ──────→ Jenson (review), Creator (produce)
    │                              │
    │                              ▼
    │                         Creator produces content
    │                              │
    │                              ▼
    │                         content-created event ───→ Jenson (review), Analyst (track)
    │                              │
    │                              ▼
    │                         content-published event ──→ Jenson, Analyst
    │                              │
    │                              ▼
    │                         Analyst measures performance
    │                              │
    │                              ▼
    │                         metric-updated event ────→ Jenson
    │
    └── learnings stored in department memory
```