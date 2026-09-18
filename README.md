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

```
main.py
   ↓
SQL input
   ↓
parser.py
   ↓
planner.py
   ↓
executor.py
   ↓
storage.py / catalog.py

```