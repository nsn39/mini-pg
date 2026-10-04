# minipg/planner.py

from dataclasses import dataclass
from typing import Any, List

from parser import (
    CreateTable,
    CreateIndex,
    Delete,
    DropTable,
    Insert,
    Select,
    Statement,
)
from catalog import Catalog


# ----------------------------------------------------------------------
# Plan nodes
# ----------------------------------------------------------------------

@dataclass
class CreateTablePlan:
    table_name: str
    columns: list


@dataclass
class DropTablePlan:
    table_name: str


@dataclass
class CreateIndexPlan:
    index_name: str
    table_name: str
    column_name: str


@dataclass
class InsertPlan:
    table_name: str
    row: dict[str, Any]


@dataclass
class SeqScanPlan:
    """
    Sequential scan of every row in a table.

    This is the simplest possible SELECT access method.
    Later MiniPG can add IndexScanPlan.
    """

    table_name: str

@dataclass
class IndexScanPlan:
    """
    Scan rows using an index instead of scanning
    every row in the table.
    """

    table_name: str
    index_name: str
    column: str
    operator: str
    value: str


@dataclass
class FilterPlan:
    """
    Filter rows produced by another plan using a WHERE condition.
    """

    column: str
    operator: str
    value: str
    child: Any


@dataclass
class ProjectionPlan:
    """
    Select specific columns from the rows produced by another plan.
    """

    columns: List[str]
    child: Any


@dataclass
class DeletePlan:
    table_name: str
    where: Any = None

Plan = (
    CreateTablePlan
    | DropTablePlan
    | CreateIndexPlan
    | InsertPlan
    | SeqScanPlan
    | IndexScanPlan
    | FilterPlan
    | ProjectionPlan
    | DeletePlan
)


# ----------------------------------------------------------------------
# Planner
# ----------------------------------------------------------------------

class Planner:
    """
    Converts parser AST nodes into execution plans.

    Parser:
        SQL -> AST

    Planner:
        AST -> Plan

    Executor:
        Plan -> actual database operation
    """

    def __init__(self, catalog: Catalog):
        self.catalog = catalog

    def plan(self, statement: Statement) -> Plan:

        if isinstance(statement, CreateTable):
            return self._plan_create_table(statement)

        if isinstance(statement, DropTable):
            return self._plan_drop_table(statement)

        if isinstance(statement, CreateIndex):
            return self._plan_create_index(statement)

        if isinstance(statement, Insert):
            return self._plan_insert(statement)

        if isinstance(statement, Select):
            return self._plan_select(statement)

        if isinstance(statement, Delete):
            return self._plan_delete(statement)

        raise ValueError(
            f"unsupported statement type: {type(statement).__name__}"
        )

    # ------------------------------------------------------------------
    # CREATE TABLE
    # ------------------------------------------------------------------

    def _plan_create_table(
        self,
        statement: CreateTable,
    ) -> CreateTablePlan:

        return CreateTablePlan(
            table_name=statement.table_name,
            columns=statement.columns,
        )

    # ------------------------------------------------------------------
    # DROP TABLE
    # ------------------------------------------------------------------

    def _plan_drop_table(
        self,
        statement: DropTable,
    ) -> DropTablePlan:

        return DropTablePlan(
            table_name=statement.table_name,
        )

    # ------------------------------------------------------------------
    # CREATE INDEX
    # ------------------------------------------------------------------

    def _plan_create_index(
        self,
        statement: CreateIndex,
    ) -> CreateIndexPlan:

        return CreateIndexPlan(
            index_name=statement.index_name,
            table_name=statement.table_name,
            column_name=statement.column_name,
        )

    # ------------------------------------------------------------------
    # INSERT
    # ------------------------------------------------------------------

    def _plan_insert(
        self,
        statement: Insert,
    ) -> InsertPlan:

        if len(statement.columns) != len(statement.values):
            raise ValueError(
                "number of columns does not match "
                "number of values"
            )

        row = dict(
            zip(
                statement.columns,
                statement.values,
            )
        )

        return InsertPlan(
            table_name=statement.table_name,
            row=row,
        )

    # ------------------------------------------------------------------
    # SELECT
    # ------------------------------------------------------------------

    def _plan_select(
        self,
        statement: Select,
    ) -> Plan:

        # --------------------------------------------------------------
        # Choose the access method
        # --------------------------------------------------------------

        if statement.where is not None:

            where_column = statement.where["column"]

            index = self.catalog.get_index_for_column(
                statement.table_name,
                where_column,
            )

            # Use the index if one exists for the WHERE column.
            if index is not None:
                scan = IndexScanPlan(
                    table_name=statement.table_name,
                    index_name=index.name,
                    column=where_column,
                    operator=statement.where["operator"],
                    value=statement.where["value"],
                )

            # Otherwise use a sequential scan + filter.
            else:
                scan = FilterPlan(
                    column=where_column,
                    operator=statement.where["operator"],
                    value=statement.where["value"],
                    child=SeqScanPlan(
                        table_name=statement.table_name,
                    ),
                )

        else:
            # No WHERE clause → sequential scan.
            scan = SeqScanPlan(
                table_name=statement.table_name,
            )

    # --------------------------------------------------------------
    # Projection
    # --------------------------------------------------------------

    # SELECT *
    if statement.columns == ["*"]:
        return scan

    # SELECT id, name, age
    return ProjectionPlan(
        columns=statement.columns,
        child=scan,
    )

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    def _plan_delete(
        self,
        statement: Delete,
    ) -> DeletePlan:

        return DeletePlan(
            table_name=statement.table_name,
            where=statement.where,
        )