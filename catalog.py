# minipg/catalog.py

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Column:
    name: str
    data_type: str
    nullable: bool = True


@dataclass
class Table:
    name: str
    columns: List[Column] = field(default_factory=list)


@dataclass
class Index:
    name: str
    table_name: str
    column_name: str


class Catalog:
    """
    System catalog for MiniPG.

    The catalog keeps track of the structure of the database:

        database
            ├── tables
            │       └── columns
            │
            └── indexes

    Catalog metadata is persisted to:

        data/catalog.json
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.catalog_path = self.data_dir / "catalog.json"

        self.tables: Dict[str, Table] = {}
        self.indexes: Dict[str, Index] = {}

        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load the catalog from disk if it exists."""

        if not self.catalog_path.exists():
            return

        with self.catalog_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        # --------------------------------------------------------------
        # Load tables
        # --------------------------------------------------------------

        for table_data in data.get("tables", {}).values():

            columns = [
                Column(
                    name=column["name"],
                    data_type=column["data_type"],
                    nullable=column.get("nullable", True),
                )
                for column in table_data.get("columns", [])
            ]

            table = Table(
                name=table_data["name"],
                columns=columns,
            )

            self.tables[table.name] = table

        # --------------------------------------------------------------
        # Load indexes
        # --------------------------------------------------------------

        for index_data in data.get("indexes", {}).values():

            index = Index(
                name=index_data["name"],
                table_name=index_data["table_name"],
                column_name=index_data["column_name"],
            )

            self.indexes[index.name] = index

    def _save(self) -> None:
        """Persist the current catalog to disk."""

        data = {
            "tables": {
                table.name: asdict(table)
                for table in self.tables.values()
            },
            "indexes": {
                index.name: asdict(index)
                for index in self.indexes.values()
            },
        }

        # Write to a temporary file first.
        # This prevents leaving a partially-written catalog
        # if the program crashes during the write.
        temp_path = self.catalog_path.with_suffix(".tmp")

        with temp_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                indent=2,
            )

        temp_path.replace(self.catalog_path)

    # ------------------------------------------------------------------
    # Table management
    # ------------------------------------------------------------------

    def create_table(self, table: Table) -> None:
        """Add a table to the catalog."""

        if table.name in self.tables:
            raise ValueError(
                f"table '{table.name}' already exists"
            )

        self.tables[table.name] = table

        self._save()

    def drop_table(self, table_name: str) -> None:
        """Remove a table from the catalog."""

        if table_name not in self.tables:
            raise ValueError(
                f"table '{table_name}' does not exist"
            )

        del self.tables[table_name]

        self._save()

    # ------------------------------------------------------------------
    # Index management
    # ------------------------------------------------------------------

    def create_index(self, index: Index) -> None:
        """Add an index to the catalog."""

        if index.name in self.indexes:
            raise ValueError(
                f"index '{index.name}' already exists"
            )

        table = self.get_table(index.table_name)

        valid_columns = {
            column.name
            for column in table.columns
        }

        if index.column_name not in valid_columns:
            raise ValueError(
                f"column '{index.column_name}' does not exist "
                f"in table '{index.table_name}'"
            )

        self.indexes[index.name] = index

        self._save()

    def get_index(self, index_name: str) -> Index:
        """Return index metadata."""

        try:
            return self.indexes[index_name]
        except KeyError:
            raise ValueError(
                f"index '{index_name}' does not exist"
            )

    def list_indexes(self) -> List[str]:
        """Return all index names."""

        return list(self.indexes.keys())

    def get_index_for_column(
        self,
        table_name: str,
        column_name: str,
    ) -> Optional[Index]:
        """Return an index on a specific table column, if one exists."""

        for index in self.indexes.values():
            if (
                index.table_name == table_name
                and index.column_name == column_name
            ):
                return index

        return None

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get_table(self, table_name: str) -> Table:
        """Return table metadata."""

        try:
            return self.tables[table_name]
        except KeyError:
            raise ValueError(
                f"table '{table_name}' does not exist"
            )

    def table_exists(self, table_name: str) -> bool:
        """Check whether a table exists."""

        return table_name in self.tables

    def list_tables(self) -> List[str]:
        """Return all table names."""

        return list(self.tables.keys())