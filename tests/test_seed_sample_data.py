"""Tests for safe, repeatable synthetic-data seeding."""

from copy import deepcopy
from unittest.mock import patch

import pytest

from scripts.seed_sample_data import seed


class FakeSeedDatabase:
    def __init__(self) -> None:
        self.tables: dict[str, dict[str, dict]] = {}
        self.current_table = ""

    def table(self, name: str) -> "FakeSeedDatabase":
        self.current_table = name
        return self

    def upsert(self, row: dict, *, on_conflict: str) -> "FakeSeedDatabase":
        assert on_conflict == "id"
        self.tables.setdefault(self.current_table, {})[row["id"]] = dict(row)
        return self

    def execute(self) -> None:
        return None


def test_sample_seed_requires_explicit_test_database_confirmation() -> None:
    with patch("scripts.seed_sample_data.get_db") as get_db:
        with pytest.raises(SystemExit, match="--confirm-test-database"):
            seed()

    get_db.assert_not_called()


def test_sample_seed_rerun_upserts_the_same_fake_records() -> None:
    db = FakeSeedDatabase()

    seed(confirm_test_database=True, db=db)
    first_seed = deepcopy(db.tables)
    seed(confirm_test_database=True, db=db)

    assert db.tables == first_seed
    assert len(db.tables["courses"]) == 2
    assert len(db.tables["students"]) == 3
    assert len(db.tables["enrollments"]) == 6
