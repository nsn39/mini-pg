```
                    MiniPG
                       │
        ┌──────────────┴──────────────┐
        │                             │
     SQL CLI                    Persistent Storage
        │                             │
        ▼                             ▼
     Parser                       Data Files
        │
        ▼
  Query Representation
        │
        ▼
     Planner
      /    \
     /      \
Index Scan   Sequential Scan
     \      /
      \    /
       ▼  ▼
     Executor
        │
        ▼
      Results
```