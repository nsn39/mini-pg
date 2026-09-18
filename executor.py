# minipg/executor.py

from typing import Any, Dict, List

from .catalog import Catalog, Column, Table
from .planner import (
    CreateTablePlan,
    DeletePlan,
    DropTablePlan,
    InsertPlan,
    Plan,
    ProjectionPlan,
    SeqScanPlan,
)
from .storage import Row, Storage


class Executor:
    """
    Executes database plans against the catalog and storage engine.

    The execution pipeline is:

        SQL
         ↓
        Parser
         ↓
        AST
         ↓
        Planner
         ↓
        Execution Plan
         ↓
        Executor
         ↓
        Storage

    The executor does not understand SQL syntax. It only understands
    execution plans produced by planner.py.
    """

    def __init__(self):
        self.catalog = Catalog()
        self.storage = Storage(self.catalog)

    # ------------------------------------------------------------------
    # Main execution entry point
    # ------------------------------------------------------------------

    def execute(self, plan: Plan) -> Any:
        """
        Execute an execution plan.

        The plan determines which operation should be performed.
        """

        if isinstance(plan, CreateTablePlan):
            return self._execute_create_table(plan)

        if isinstance(plan, DropTablePlan):
            return self._execute_drop_table(plan)

        if isinstance(plan, InsertPlan):
            return self._execute_insert(plan)

        if isinstance(plan, SeqScanPlan):
            return self._execute_seq_scan(plan)

        if isinstance(plan, ProjectionPlan):
            return self._execute_projection(plan)

        if isinstance(plan, DeletePlan):
            return self._execute_delete(plan)

        raise ValueError(
            f"unsupported plan type: {type(plan).__name__}"
        )

    # ------------------------------------------------------------------
    # DDL
    # ------------------------------------------------------------------

    def _execute_create_table(
        self,
        plan: CreateTablePlan,
    ) -> str:
        """Execute CREATE TABLE."""

        table = Table(
            name=plan.table_name,
            columns=[
                Column(
                    name=column.name,
                    data_type=column.data_type,
                    nullable=column.nullable,
                )
                for column in plan.columns
            ],
        )

        self.catalog.create_table(table)
        self.storage.create_table(plan.table_name)

        return f"CREATE TABLE {plan.table_name}"

    def _execute_drop_table(
        self,
        plan: DropTablePlan,
    ) -> str:
        """Execute DROP TABLE."""

        self.storage.drop_table(plan.table_name)
        self.catalog.drop_table(plan.table_name)

        return f"DROP TABLE {plan.table_name}"

    # ------------------------------------------------------------------
    # DML
    # ------------------------------------------------------------------

    def _execute_insert(
        self,
        plan: InsertPlan,
    ) -> str:
        """Execute INSERT."""

        self.storage.insert(
            plan.table_name,
            plan.row,
        )

        return "INSERT 0 1"

    def _execute_seq_scan(
        self,
        plan: SeqScanPlan,
    ) -> List[Row]:
        """
        Execute a sequential table scan.

        A sequential scan simply reads every row in the table.
        """

        return self.storage.select_all(
            plan.table_name
        )

    def _execute_projection(
        self,
        plan: ProjectionPlan,
    ) -> List[Row]:
        """
        Execute a projection.

        Example:

            SELECT name, age FROM users

        The child SeqScan produces:

            [
                {"id": 1, "name": "Nishan", "age": 25},
                {"id": 2, "name": "Alice", "age": 30},
            ]

        Projection reduces this to:

            [
                {"name": "Nishan", "age": 25},
                {"name": "Alice", "age": 30},
            ]
        """

        rows = self.execute(plan.child)

        if not rows:
            return []

        # Validate that requested columns exist.
        table = self.catalog.get_table(
            plan.child.table_name
        )

        valid_columns = {
            column.name
            for column in table.columns
        }

        for column in plan.columns:
            if column not in valid_columns:
                raise ValueError(
                    f"column '{column}' does not exist "
                    f"in table '{table.name}'"
                )

        return [
            {
                column: row[column]
                for column in plan.columns
            }
            for row in rows
        ]

    def _execute_delete(
        self,
        plan: DeletePlan,
    ) -> str:
        """Execute DELETE."""

        count = self.storage.delete_all(
            plan.table_name
        )

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
