# minipg/main.py

from .executor import Executor
from .parser import parse
from .planner import Planner


def print_rows(rows: list[dict]) -> None:
    """Print query results in a simple table format."""

    if not rows:
        print("(0 rows)")
        return

    columns = list(rows[0].keys())

    # Calculate column widths.
    widths = {}

    for column in columns:
        widths[column] = max(
            len(column),
            max(len(str(row.get(column, ""))) for row in rows),
        )

    # Header
    header = " | ".join(
        column.ljust(widths[column])
        for column in columns
    )

    separator = "-+-".join(
        "-" * widths[column]
        for column in columns
    )

    print(header)
    print(separator)

    # Rows
    for row in rows:
        print(
            " | ".join(
                str(row.get(column, "")).ljust(widths[column])
                for column in columns
            )
        )

    print(f"({len(rows)} row{'s' if len(rows) != 1 else ''})")


def run_shell() -> None:
    """Start the MiniPG interactive SQL shell."""

    executor = Executor()
    planner = Planner()

    print("MiniPG")
    print("Toy PostgreSQL-like database")
    print("Type SQL statements or \\q to quit.")
    print()

    while True:
        try:
            sql = input("minipg=# ")

        except (EOFError, KeyboardInterrupt):
            print()
            print("Bye!")
            break

        sql = sql.strip()

        if not sql:
            continue

        # --------------------------------------------------------------
        # Shell commands
        # --------------------------------------------------------------

        if sql.lower() in ("\\q", "quit", "exit"):
            print("Bye!")
            break

        if sql.lower() in ("\\dt",):
            tables = executor.list_tables()

            if not tables:
                print("No tables.")
            else:
                for table in tables:
                    print(table)

            continue

        # --------------------------------------------------------------
        # SQL
        # --------------------------------------------------------------

        try:
            statement = parse(sql)

            plan = planner.plan(statement)

            result = executor.execute(plan)

            # SELECT returns a list of rows.
            if isinstance(result, list):
                print_rows(result)

            else:
                print(result)

        except Exception as exc:
            print(f"ERROR: {exc}")


def main() -> None:
    run_shell()


if __name__ == "__main__":
    main()