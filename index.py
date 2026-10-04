# minipg/index.py

from bisect import bisect_left, bisect_right, insort
from typing import Any, Dict, List


Row = Dict[str, Any]


class BTreeIndex:
    """
    Simple sorted index for a single table column.

    This is an educational implementation inspired by
    the behavior of a B-tree index.

    The index stores:

        column value -> rows having that value

    Example:

        age = 20 -> [row1, row2]
        age = 25 -> [row3]
        age = 30 -> [row4, row5]

    A sorted list of keys allows us to efficiently find
    ranges for operators such as < and >.
    """

    def __init__(
        self,
        table_name: str,
        column_name: str,
    ):
        self.table_name = table_name
        self.column_name = column_name

        # Maps each indexed value to the rows
        # having that value.
        self.entries: Dict[Any, List[Row]] = {}

        # Keep the indexed values sorted.
        #
        # Example:
        # [10, 20, 30, 40]
        self.keys: List[Any] = []

    # ------------------------------------------------------------------
    # Building the index
    # ------------------------------------------------------------------

    def build(self, rows: List[Row]) -> None:
        """
        Build the index from existing table rows.
        """

        self.entries.clear()
        self.keys.clear()

        for row in rows:
            self.insert(row)

    # ------------------------------------------------------------------
    # Insert
    # ------------------------------------------------------------------

    def insert(self, row: Row) -> None:
        """
        Add a row to the index.
        """

        value = row[self.column_name]

        if value not in self.entries:
            self.entries[value] = []

            # Insert the new key while keeping keys sorted.
            insort(self.keys, value)

        self.entries[value].append(row)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(self, row: Row) -> None:
        """
        Remove a row from the index.
        """

        value = row[self.column_name]

        if value not in self.entries:
            return

        rows = self.entries[value]

        if row in rows:
            rows.remove(row)

        # If no rows remain for this value,
        # remove the key completely.
        if not rows:
            del self.entries[value]

            index = bisect_left(self.keys, value)

            if (
                index < len(self.keys)
                and self.keys[index] == value
            ):
                self.keys.pop(index)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        operator: str,
        value: Any,
    ) -> List[Row]:
        """
        Search the index using:

            =
            <
            >

        Returns the matching rows.
        """

        if operator == "=":
            return list(
                self.entries.get(value, [])
            )

        if operator == "<":
            position = bisect_left(
                self.keys,
                value,
            )

            matching_rows = []

            for key in self.keys[:position]:
                matching_rows.extend(
                    self.entries[key]
                )

            return matching_rows

        if operator == ">":
            position = bisect_right(
                self.keys,
                value,
            )

            matching_rows = []

            for key in self.keys[position:]:
                matching_rows.extend(
                    self.entries[key]
                )

            return matching_rows

        raise ValueError(
            f"unsupported index operator: {operator}"
        )

    # ------------------------------------------------------------------
    # Debugging / inspection
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"BTreeIndex("
            f"table='{self.table_name}', "
            f"column='{self.column_name}', "
            f"keys={self.keys}"
            f")"
        )