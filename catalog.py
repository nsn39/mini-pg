# minipg/catalog.py

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Column:
    name: str
    data_type: str
    nullable: bool = True


@dataclass
class Table:
    name: str
    columns: List[Column] = field(default_factory=list)


class Catalog:
    """
    System catalog for MiniPG.

    The catalog keeps track of the structure of the database:
        database -> tables -> columns

    For now, everything lives in memory.
    """

    def __init__(self):
        self.tables: Dict[str, Table] = {}

    def create_table(self, table: Table) -> None:
        """Add a table to the catalog."""
        if table.name in self.tables:
            raise ValueError(f"table '{table.name}' already exists")

        self.tables[table.name] = table

    def drop_table(self, table_name: str) -> None:
        """Remove a table from the catalog."""
        if table_name not in self.tables:
            raise ValueError(f"table '{table_name}' does not exist")

        del self.tables[table_name]

    def get_table(self, table_name: str) -> Table:
        """Return table metadata."""
        try:
            return self.tables[table_name]
        except KeyError:
            raise ValueError(f"table '{table_name}' does not exist")

    def table_exists(self, table_name: str) -> bool:
        """Check whether a table exists."""
        return table_name in self.tables

    def list_tables(self) -> List[str]:
        """Return all table names."""
        return list(self.tables.keys())