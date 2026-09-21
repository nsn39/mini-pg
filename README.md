# MiniPG

A toy implementation of a PostgreSQL-like database built using AI coding tools as an assignment for the **Software Development Principles** course at **North Dakota State University (NDSU)**.

**By:** Nishan Poudel

**Original Reference URL:** https://github.com/postgres/postgres

**AI Tools Used:**

* ChatGPT GPT-5
* Claude Sonnet (June 30 version)

## Overview

MiniPG is a small educational database system inspired by the architecture and functionality of PostgreSQL. It is not intended to be a replacement for PostgreSQL. Instead, it implements a small subset of database functionality to demonstrate how the major components of a database system work together.

The project was developed incrementally using AI coding tools, with functionality added step by step.

## Architecture

```text
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

The current implementation is organized into the following flow:

```text
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

## Project Structure

```text
mini-postgres/
│
├── main.py
├── parser.py
├── planner.py
├── executor.py
├── storage.py
├── catalog.py
└── README.md
```

### Components

* **main.py** — Provides the interactive SQL command-line interface.
* **parser.py** — Parses SQL commands into a query representation.
* **planner.py** — Determines how a query should be executed.
* **executor.py** — Executes the planned operations.
* **storage.py** — Handles table data storage.
* **catalog.py** — Maintains information about tables and their columns.

## Supported Functionality

The current version supports basic database operations including:

* `CREATE TABLE`
* `INSERT`
* `SELECT`
* `WHERE`
* `UPDATE`
* `DELETE`
* `DROP TABLE`

The project is intentionally kept small and focuses on demonstrating the basic components of a database system rather than implementing the full PostgreSQL feature set.

## Running MiniPG

Make sure Python 3 is installed, then run:

```bash
python main.py
```

This starts the MiniPG interactive SQL shell.

### Example Demo

Create a table:

```sql
CREATE TABLE users (
    id INT,
    name TEXT,
    age INT
);
```

Insert some records:

```sql
INSERT INTO users VALUES (1, 'Nishan', 25);
```

```sql
INSERT INTO users VALUES (2, 'Alice', 24);
```

```sql
INSERT INTO users VALUES (3, 'Bob', 30);
```

Select all records:

```sql
SELECT * FROM users;
```

Select records using a condition:

```sql
SELECT * FROM users WHERE age > 25;
```

Update a record:

```sql
UPDATE users SET age = 26 WHERE id = 1;
```

Delete a record:

```sql
DELETE FROM users WHERE id = 2;
```

Finally, the table can be removed with:

```sql
DROP TABLE users;
```

The shell can be exited using:

```text
.exit
```

## Purpose

MiniPG demonstrates the basic flow of a database system:

**SQL input → Parsing → Planning → Execution → Storage**

The project was developed as a small-scale implementation to explore database architecture and software development principles while using AI coding assistants as development tools.
