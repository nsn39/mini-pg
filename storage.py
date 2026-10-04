# minipg/storage.py

import json
from pathlib import Path
from typing import Any, Dict, List

from catalog import Catalog
from index import BTreeIndex


Row = Dict[str, Any]


class Storage:
    """
    Storage engine for MiniPG.

    Each table is stored in its own file:

        data/
        ├── users
        ├── products
        └── orders

    Each line in a table file represents one JSON-encoded row.

    Indexes are currently kept in memory and are maintained
    automatically when rows are inserted or deleted.
    """

    def __init__(
        self,
        catalog: Catalog,
        data_dir: str = "data",
    ):
        self.catalog = catalog
        self.data_dir = Path(data_dir)

        # Create the data directory if it doesn't exist.
        self.data_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Actual index structures currently loaded in memory.
        #
        # Key:
        #     index name
        #
        # Value:
        #     BTreeIndex object
        self.indexes: Dict[str, BTreeIndex] = {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _table_path(
        self,
        table_name: str,
    ) -> Path:
        """Return the filesystem path for a table."""

        return self.data_dir / table_name

    def _ensure_table_exists(
        self,
        table_name: str,
    ) -> None:
        """Make sure the table exists in the catalog."""

        self.catalog.get_table(table_name)

    def _ensure_storage_exists(
        self,
        table_name: str,
    ) -> None:
        """Make sure the table's storage file exists."""

        path = self._table_path(table_name)

        if not path.exists():
            raise ValueError(
                f"storage for table '{table_name}' does not exist"
            )

    # ------------------------------------------------------------------
    # Table management
    # ------------------------------------------------------------------

    def create_table(
        self,
        table_name: str,
    ) -> None:
        """
        Create an empty storage file for a table.

        The catalog must already contain the table.
        """

        self._ensure_table_exists(table_name)

        path = self._table_path(table_name)

        if path.exists():
            raise ValueError(
                f"storage for table '{table_name}' already exists"
            )

        # Create an empty file.
        path.touch()

    def drop_table(
        self,
        table_name: str,
    ) -> None:
        """Delete the storage file for a table."""

        path = self._table_path(table_name)

        if not path.exists():
            raise ValueError(
                f"storage for table '{table_name}' does not exist"
            )

        # Remove indexes belonging to this table.
        indexes_to_remove = [
            index_name
            for index_name, index in self.indexes.items()
            if index.table_name == table_name
        ]

        for index_name in indexes_to_remove:
            del self.indexes[index_name]

        path.unlink()

    # ------------------------------------------------------------------
    # Index management
    # ------------------------------------------------------------------

    def create_index(
        self,
        index_name: str,
        table_name: str,
        column_name: str,
    ) -> None:
        """
        Create an in-memory index for an existing table column.

        The catalog stores the index metadata.
        Storage creates and builds the actual BTreeIndex.
        """

        table = self.catalog.get_table(table_name)

        valid_columns = {
            column.name
            for column in table.columns
        }

        if column_name not in valid_columns:
            raise ValueError(
                f"column '{column_name}' does not exist "
                f"in table '{table_name}'"
            )

        if index_name in self.indexes:
            raise ValueError(
                f"index '{index_name}' already exists"
            )

        index = BTreeIndex(
            table_name=table_name,
            column_name=column_name,
        )

        # Build the index using all existing rows.
        rows = self.select_all(table_name)

        index.build(rows)

        # Store the actual index in memory.
        self.indexes[index_name] = index

    def get_index(
        self,
        index_name: str,
    ) -> BTreeIndex:
        """Return an in-memory index."""

        try:
            return self.indexes[index_name]
        except KeyError:
            raise ValueError(
                f"index '{index_name}' does not exist"
            )

    # ------------------------------------------------------------------
    # Insert
    # ------------------------------------------------------------------

    def insert(
        self,
        table_name: str,
        row: Row,
    ) -> None:
        """Insert a single row into a table."""

        table = self.catalog.get_table(table_name)

        self._ensure_storage_exists(table_name)

        # Make a copy so that we don't modify the caller's dictionary.
        row = row.copy()

        # --------------------------------------------------------------
        # Validate columns
        # --------------------------------------------------------------

        valid_columns = {
            column.name
            for column in table.columns
        }

        unknown_columns = set(row) - valid_columns

        if unknown_columns:
            raise ValueError(
                f"unknown column(s): "
                f"{', '.join(sorted(unknown_columns))}"
            )

        # --------------------------------------------------------------
        # Fill missing nullable columns
        # --------------------------------------------------------------

        for column in table.columns:
            if column.name not in row:

                if not column.nullable:
                    raise ValueError(
                        f"column '{column.name}' cannot be NULL"
                    )

                row[column.name] = None

        # --------------------------------------------------------------
        # Write row to disk
        # --------------------------------------------------------------

        path = self._table_path(table_name)

        with path.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                json.dumps(row)
                + "\n"
            )

        # --------------------------------------------------------------
        # Update indexes
        # --------------------------------------------------------------

        for index in self.indexes.values():
            if index.table_name == table_name:
                index.insert(row)

    # ------------------------------------------------------------------
    # Select
    # ------------------------------------------------------------------

    def select_all(
        self,
        table_name: str,
    ) -> List[Row]:
        """Return all rows from a table."""

        self.catalog.get_table(table_name)

        self._ensure_storage_exists(table_name)

        path = self._table_path(table_name)

        rows: List[Row] = []

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:

            for line in file:
                line = line.strip()

                if not line:
                    continue

                rows.append(
                    json.loads(line)
                )

        return rows

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_all(
        self,
        table_name: str,
    ) -> int:
        """
        Delete all rows from a table.

        The table itself remains.
        Only its contents are removed.

        Returns the number of deleted rows.
        """

        self.catalog.get_table(table_name)

        self._ensure_storage_exists(table_name)

        path = self._table_path(table_name)

        rows = self.select_all(table_name)

        count = len(rows)

        # Truncate the file.
        path.write_text(
            "",
            encoding="utf-8",
        )

        # --------------------------------------------------------------
        # Update indexes
        # --------------------------------------------------------------

        for index in self.indexes.values():
            if index.table_name == table_name:
                for row in rows:
                    index.delete(row)

        return count

    def delete_rows(
        self,
        table_name: str,
        rows_to_delete: List[Row],
    ) -> int:
        """
        Delete specific rows from a table.

        The matching rows are removed and the remaining rows
        are written back to the table file.

        Returns the number of deleted rows.
        """

        self.catalog.get_table(table_name)

        self._ensure_storage_exists(table_name)

        path = self._table_path(table_name)

        rows = self.select_all(table_name)

        # Remove rows that match the rows_to_delete list.
        remaining_rows = [
            row
            for row in rows
            if row not in rows_to_delete
        ]

        count = len(rows) - len(remaining_rows)

        # Rewrite the table file with only the remaining rows.
        with path.open(
            "w",
            encoding="utf-8",
        ) as file:

            for row in remaining_rows:
                file.write(
                    json.dumps(row)
                    + "\n"
                )

        # --------------------------------------------------------------
        # Update indexes
        # --------------------------------------------------------------

        for index in self.indexes.values():
            if index.table_name == table_name:
                for row in rows_to_delete:
                    index.delete(row)

        return count

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def row_count(
        self,
        table_name: str,
    ) -> int:
        """Return the number of rows in a table."""

        self.catalog.get_table(table_name)

        self._ensure_storage_exists(table_name)

        count = 0

        path = self._table_path(table_name)

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:

            for line in file:
                if line.strip():
                    count += 1

        return count