# minipg/transaction.py

import shutil
from pathlib import Path


class TransactionManager:
    """
    Primitive transaction manager for MiniPG.

    Phase 1 implementation:
        BEGIN    -> save a snapshot of the database
        COMMIT   -> discard the snapshot
        ROLLBACK -> restore the snapshot

    This is intentionally simple and is not a WAL/MVCC
    implementation.
    """

    def __init__(
        self,
        storage,
    ):
        self.storage = storage
        self.active = False

        self.snapshot_dir = (
            self.storage.data_dir.parent
            / ".transaction_snapshot"
        )

    def begin(self) -> str:
        """Start a new transaction."""

        if self.active:
            raise RuntimeError(
                "transaction already active"
            )

        if self.snapshot_dir.exists():
            shutil.rmtree(self.snapshot_dir)

        self.snapshot_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Copy the current database files.
        for path in self.storage.data_dir.iterdir():
            if path.is_file():
                shutil.copy2(
                    path,
                    self.snapshot_dir / path.name,
                )

        self.active = True

        return "BEGIN"

    def commit(self) -> str:
        """Commit the current transaction."""

        if not self.active:
            raise RuntimeError(
                "no active transaction"
            )

        self._remove_snapshot()

        self.active = False

        return "COMMIT"

    def rollback(self) -> str:
        """Rollback the current transaction."""

        if not self.active:
            raise RuntimeError(
                "no active transaction"
            )

        # Remove the current database files.
        for path in self.storage.data_dir.iterdir():
            if path.is_file():
                path.unlink()

        # Restore the snapshot.
        for path in self.snapshot_dir.iterdir():
            if path.is_file():
                shutil.copy2(
                    path,
                    self.storage.data_dir / path.name,
                )

        # Rebuild in-memory indexes from the restored data.
        self.storage.rebuild_indexes()

        self._remove_snapshot()

        self.active = False

        return "ROLLBACK"

    def _remove_snapshot(self) -> None:
        """Delete the transaction snapshot."""

        if self.snapshot_dir.exists():
            shutil.rmtree(self.snapshot_dir)