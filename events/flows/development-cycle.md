# Development Cycle Event Flow

```
Jenson identifies need
    │
    ▼
feature-requested event ────────→ Forge (implement)
    │                              │
    │                              ▼
    │                         Forge builds feature
    │                              │
    │                              ▼
    │                         development-completed event ──→ Tester (QA), Jenson (review)
    │                              │
    │                              ▼
    │                         Tester validates
    │                              │
    │                              ▼
    │                         test-completed event ────→ Jenson, Forge
    │
    └── learnings stored in department memory
```