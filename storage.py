# minipg/storage.py

from typing import Any, Dict, List

from .catalog import Catalog


Row = Dict[str, Any]


class Storage:
    """
    Storage engine for MiniPG.

    Responsible for storing and retrieving table rows.

    For now, rows are stored in memory. Later, this can be replaced
    with a disk-backed page storage system without changing the
    catalog or SQL execution layers.
    """

    def __init__(self, catalog: Catalog):
        self.catalog = catalog

        # table_name -> list of rows
        self._tables: Dict[str, List[Row]] = {}

    def create_table(self, table_name: str) -> None:
        """Create an empty storage area for a table."""

        if not self.catalog.table_exists(table_name):
            raise ValueError(
                f"table '{table_name}' does not exist in catalog"
            )

        if table_name in self._tables:
            raise ValueError(
                f"storage for table '{table_name}' already exists"
            )

        self._tables[table_name] = []

    def drop_table(self, table_name: str) -> None:
        """Delete all stored rows for a table."""

        if table_name not in self._tables:
            raise ValueError(
                f"table '{table_name}' does not exist in storage"
            )

        del self._tables[table_name]

    def insert(self, table_name: str, row: Row) -> None:
        """Insert a single row into a table."""

        table = self.catalog.get_table(table_name)

        if table_name not in self._tables:
            raise ValueError(
                f"table '{table_name}' has no storage"
            )

        # Make sure the row doesn't contain unknown columns.
        valid_columns = {column.name for column in table.columns}

        unknown_columns = set(row) - valid_columns

        if unknown_columns:
            raise ValueError(
                f"unknown column(s): {', '.join(sorted(unknown_columns))}"
            )

        # Add missing nullable columns as None.
        for column in table.columns:
            if column.name not in row:
                if not column.nullable:
                    raise ValueError(
                        f"column '{column.name}' cannot be NULL"
                    )

                row[column.name] = None

        self._tables[table_name].append(row)

    def select_all(self, table_name: str) -> List[Row]:
        """Return all rows from a table."""

        self.catalog.get_table(table_name)

        if table_name not in self._tables:
            raise ValueError(
                f"table '{table_name}' has no storage"
            )

        # Return copies so callers cannot accidentally modify
        # the stored rows directly.
        return [row.copy() for row in self._tables[table_name]]

    def delete_all(self, table_name: str) -> int:
        """Delete all rows from a table.

        Returns the number of deleted rows.
        """

        self.catalog.get_table(table_name)

        if table_name not in self._tables:
            raise ValueError(
                f"table '{table_name}' has no storage"
            )

        count = len(self._tables[table_name])
        self._tables[table_name].clear()

        return count

    def row_count(self, table_name: str) -> int:
        """Return the number of rows in a table."""

        self.catalog.get_table(table_name)

        if table_name not in self._tables:
            raise ValueError(
                f"table '{table_name}' has no storage"
            )

        return len(self._tables[table_name])