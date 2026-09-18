# minipg/executor.py

from typing import Any, Dict, List

from .catalog import Catalog, Column, Table
from .storage import Row, Storage


class Executor:
    """
    Executes database operations against the catalog and storage engine.

    The executor does not parse SQL. It receives structured commands
    from the parser and performs the corresponding database operation.
    """

    def __init__(self):
        self.catalog = Catalog()
        self.storage = Storage(self.catalog)

    # ------------------------------------------------------------------
    # DDL
    # ------------------------------------------------------------------

    def create_table(
        self,
        table_name: str,
        columns: List[Column],
    ) -> str:
        """Create a new table."""

        table = Table(
            name=table_name,
            columns=columns,
        )

        self.catalog.create_table(table)
        self.storage.create_table(table_name)

        return f"CREATE TABLE {table_name}"

    def drop_table(self, table_name: str) -> str:
        """Drop an existing table."""

        self.storage.drop_table(table_name)
        self.catalog.drop_table(table_name)

        return f"DROP TABLE {table_name}"

    # ------------------------------------------------------------------
    # DML
    # ------------------------------------------------------------------

    def insert(
        self,
        table_name: str,
        row: Row,
    ) -> str:
        """Insert a row into a table."""

        self.storage.insert(
            table_name,
            row,
        )

        return "INSERT 0 1"

    def select_all(
        self,
        table_name: str,
    ) -> List[Row]:
        """Return every row from a table."""

        return self.storage.select_all(table_name)

    def delete_all(
        self,
        table_name: str,
    ) -> str:
        """Delete every row from a table."""

        count = self.storage.delete_all(table_name)

        return f"DELETE {count}"

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def list_tables(self) -> List[str]:
        """Return all tables currently known to the database."""

        return self.catalog.list_tables()

    def describe_table(
        self,
        table_name: str,
    ) -> Dict[str, Any]:
        """Return metadata describing a table."""

        table = self.catalog.get_table(table_name)

        return {
            "name": table.name,
            "columns": [
                {
                    "name": column.name,
                    "data_type": column.data_type,
                    "nullable": column.nullable,
                }
                for column in table.columns
            ],
        }