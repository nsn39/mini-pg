# minipg/parser.py

from dataclasses import dataclass
import re
from typing import Any, List, Optional


# ----------------------------------------------------------------------
# AST nodes
# ----------------------------------------------------------------------

@dataclass
class ColumnDef:
    name: str
    data_type: str
    nullable: bool = True


@dataclass
class CreateTable:
    table_name: str
    columns: List[ColumnDef]


@dataclass
class DropTable:
    table_name: str


@dataclass
class Insert:
    table_name: str
    columns: List[str]
    values: List[Any]


@dataclass
class Select:
    columns: List[str]
    table_name: str


@dataclass
class Delete:
    table_name: str


Statement = CreateTable | DropTable | Insert | Select | Delete


# ----------------------------------------------------------------------
# Tokenization helpers
# ----------------------------------------------------------------------

def _split_csv(value: str) -> List[str]:
    """
    Split comma-separated values while ignoring commas inside strings.

    Example:
        "1, 'Alice', 'New York'"
        ->
        ["1", "'Alice'", "'New York'"]
    """

    parts = []
    current = []
    in_string = False
    quote = None

    for char in value:
        if char in ("'", '"'):
            if in_string and char == quote:
                in_string = False
            elif not in_string:
                in_string = True
                quote = char

        if char == "," and not in_string:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)

    if current:
        parts.append("".join(current).strip())

    return parts


def _parse_value(value: str) -> Any:
    """Convert a SQL literal into a Python value."""

    value = value.strip()

    # Strings
    if (
        len(value) >= 2
        and value[0] == "'"
        and value[-1] == "'"
    ):
        return value[1:-1]

    # NULL
    if value.upper() == "NULL":
        return None

    # Integer
    if re.fullmatch(r"-?\d+", value):
        return int(value)

    # Floating-point number
    if re.fullmatch(r"-?\d+\.\d+", value):
        return float(value)

    # Boolean
    if value.upper() == "TRUE":
        return True

    if value.upper() == "FALSE":
        return False

    raise ValueError(f"unsupported value: {value}")


# ----------------------------------------------------------------------
# Statement parsers
# ----------------------------------------------------------------------

def _parse_create_table(sql: str) -> CreateTable:
    pattern = re.compile(
        r"""
        ^CREATE\s+TABLE\s+
        ([a-zA-Z_][a-zA-Z0-9_]*)
        \s*\(
        (.*)
        \)
        $
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    match = pattern.match(sql)

    if not match:
        raise ValueError("invalid CREATE TABLE statement")

    table_name = match.group(1)
    column_text = match.group(2)

    columns = []

    for definition in _split_csv(column_text):
        parts = definition.split()

        if len(parts) < 2:
            raise ValueError(
                f"invalid column definition: {definition}"
            )

        column_name = parts[0]
        data_type = parts[1].upper()

        nullable = True

        if len(parts) > 2:
            constraints = [part.upper() for part in parts[2:]]

            if "NOT" in constraints and "NULL" in constraints:
                nullable = False

        columns.append(
            ColumnDef(
                name=column_name,
                data_type=data_type,
                nullable=nullable,
            )
        )

    return CreateTable(
        table_name=table_name,
        columns=columns,
    )


def _parse_drop_table(sql: str) -> DropTable:
    pattern = re.compile(
        r"^DROP\s+TABLE\s+([a-zA-Z_][a-zA-Z0-9_]*)$",
        re.IGNORECASE,
    )

    match = pattern.match(sql)

    if not match:
        raise ValueError("invalid DROP TABLE statement")

    return DropTable(
        table_name=match.group(1),
    )


def _parse_insert(sql: str) -> Insert:
    pattern = re.compile(
        r"""
        ^INSERT\s+INTO\s+
        ([a-zA-Z_][a-zA-Z0-9_]*)
        \s*
        \(
            (.*?)
        \)
        \s*
        VALUES
        \s*
        \(
            (.*?)
        \)
        $
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    match = pattern.match(sql)

    if not match:
        raise ValueError("invalid INSERT statement")

    table_name = match.group(1)

    columns = [
        column.strip()
        for column in _split_csv(match.group(2))
    ]

    values = [
        _parse_value(value)
        for value in _split_csv(match.group(3))
    ]

    if len(columns) != len(values):
        raise ValueError(
            "number of columns does not match number of values"
        )

    return Insert(
        table_name=table_name,
        columns=columns,
        values=values,
    )


def _parse_select(sql: str) -> Select:
    pattern = re.compile(
        r"""
        ^SELECT\s+
        (.+?)
        \s+FROM\s+
        ([a-zA-Z_][a-zA-Z0-9_]*)
        $
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    match = pattern.match(sql)

    if not match:
        raise ValueError("invalid SELECT statement")

    column_text = match.group(1).strip()
    table_name = match.group(2)

    if column_text == "*":
        columns = ["*"]
    else:
        columns = [
            column.strip()
            for column in _split_csv(column_text)
        ]

    return Select(
        columns=columns,
        table_name=table_name,
    )


def _parse_delete(sql: str) -> Delete:
    pattern = re.compile(
        r"""
        ^DELETE\s+FROM\s+
        ([a-zA-Z_][a-zA-Z0-9_]*)
        $
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    match = pattern.match(sql)

    if not match:
        raise ValueError("invalid DELETE statement")

    return Delete(
        table_name=match.group(1),
    )


# ----------------------------------------------------------------------
# Public parser
# ----------------------------------------------------------------------

def parse(sql: str) -> Statement:
    """
    Parse a SQL statement and return an AST node.

    Supported statements:

        CREATE TABLE
        DROP TABLE
        INSERT INTO ... VALUES
        SELECT ... FROM
        DELETE FROM
    """

    sql = sql.strip()

    # Remove optional semicolon.
    if sql.endswith(";"):
        sql = sql[:-1].strip()

    if not sql:
        raise ValueError("empty SQL statement")

    keyword = sql.split(None, 1)[0].upper()

    if keyword == "CREATE":
        return _parse_create_table(sql)

    if keyword == "DROP":
        return _parse_drop_table(sql)

    if keyword == "INSERT":
        return _parse_insert(sql)

    if keyword == "SELECT":
        return _parse_select(sql)

    if keyword == "DELETE":
        return _parse_delete(sql)

    raise ValueError(
        f"unsupported SQL statement: {keyword}"
    )