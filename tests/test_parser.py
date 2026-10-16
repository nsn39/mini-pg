
import pytest

from parser import (
    parse,
    CreateTable,
    CreateIndex,
    DropTable,
    Insert,
    Select,
    Delete,
    Begin,
    Commit,
    Rollback,
)


def test_parse_create_table():
    """Parse a simple table definition."""
    sql = "CREATE TABLE users (id INT, username TEXT)"

    statement = parse(sql)

    assert statement is not None


def test_parse_create_table_with_multiple_columns():
    """Parse a table with multiple columns."""
    sql = "CREATE TABLE orders (order_id INT, user_id INT, total REAL)"

    statement = parse(sql)

    assert statement is not None


def test_parse_create_table_case_insensitive():
    """SQL keywords should accept different letter cases."""
    statement = parse("create table products (id INT, name TEXT)")

    assert statement is not None


def test_parse_create_table_with_whitespace():
    """Leading/trailing whitespace and a trailing semicolon are accepted."""
    statement = parse("  CREATE TABLE users (id INT);  ")

    assert statement is not None


def test_parse_empty_sql():
    """Empty SQL should raise ValueError."""
    with pytest.raises(ValueError, match="empty SQL statement"):
        parse("")


def test_parse_whitespace_only_sql():
    """Whitespace-only SQL should raise ValueError."""
    with pytest.raises(ValueError, match="empty SQL statement"):
        parse("   ")


def test_parse_unsupported_statement():
    """Unsupported SQL keywords should raise ValueError."""
    with pytest.raises(ValueError, match="unsupported SQL statement"):
        parse("UPDATE users SET id = 1")


def test_parse_incomplete_create_table():
    """An incomplete CREATE TABLE statement should be rejected."""
    with pytest.raises(ValueError):
        parse("CREATE TABLE")


def test_parse_begin():
    """Parse a transaction BEGIN statement."""
    statement = parse("BEGIN")

    assert statement is not None


def test_parse_commit():
    """Parse a transaction COMMIT statement."""
    statement = parse("COMMIT;")

    assert statement is not None


def test_parse_rollback():
    """Parse a transaction ROLLBACK statement."""
    statement = parse("ROLLBACK")

    assert statement is not None


def test_create_table_not_null():
    statement = parse(
        "CREATE TABLE users (id INT NOT NULL, name TEXT)"
    )

    assert isinstance(statement, CreateTable)
    assert statement.table_name == "users"
    assert statement.columns[0].nullable is False
    assert statement.columns[1].nullable is True


def test_create_index():
    statement = parse("CREATE INDEX idx_users ON users (id)")

    assert isinstance(statement, CreateIndex)
    assert statement.index_name == "idx_users"
    assert statement.table_name == "users"
    assert statement.column_name == "id"


def test_invalid_create_index():
    with pytest.raises(ValueError, match="invalid CREATE INDEX"):
        parse("CREATE INDEX idx_users ON")


def test_drop_table():
    statement = parse("DROP TABLE users")

    assert isinstance(statement, DropTable)
    assert statement.table_name == "users"


def test_invalid_drop_table():
    with pytest.raises(ValueError, match="invalid DROP TABLE"):
        parse("DROP TABLE users extra")


def test_insert_multiple_value_types():
    statement = parse(
        "INSERT INTO users (id, name, score, active, note) "
        "VALUES (42, 'Alice', 9.5, TRUE, NULL)"
    )

    assert isinstance(statement, Insert)
    assert statement.table_name == "users"
    assert statement.columns == ["id", "name", "score", "active", "note"]
    assert statement.values == [42, "Alice", 9.5, True, None]


def test_insert_negative_integer_and_false():
    statement = parse(
        "INSERT INTO records (id, active) VALUES (-5, FALSE)"
    )

    assert isinstance(statement, Insert)
    assert statement.values == [-5, False]


def test_insert_string_containing_comma():
    statement = parse(
        "INSERT INTO users (id, city) VALUES (1, 'New York, NY')"
    )

    assert isinstance(statement, Insert)
    assert statement.values == [1, "New York, NY"]


def test_insert_mismatched_columns_and_values():
    with pytest.raises(
        ValueError,
        match="number of columns does not match number of values",
    ):
        parse("INSERT INTO users (id, name) VALUES (1)")


def test_insert_unsupported_value():
    with pytest.raises(ValueError, match="unsupported value"):
        parse("INSERT INTO users (id) VALUES (unknown)")


def test_insert_invalid_syntax():
    with pytest.raises(ValueError, match="invalid INSERT"):
        parse("INSERT users VALUES (1)")


def test_select_all_columns():
    statement = parse("SELECT * FROM users")

    assert isinstance(statement, Select)
    assert statement.columns == ["*"]
    assert statement.table_name == "users"
    assert statement.where is None


def test_select_specific_columns():
    statement = parse("SELECT id, name FROM users")

    assert isinstance(statement, Select)
    assert statement.columns == ["id", "name"]
    assert statement.where is None


@pytest.mark.parametrize(
    ("operator", "value"),
    [
        ("=", "10"),
        ("<", "20"),
        (">", "5"),
    ],
)
def test_select_where_operators(operator, value):
    statement = parse(
        "SELECT id FROM users WHERE age " + operator + " " + value
    )

    assert isinstance(statement, Select)
    assert statement.where == {
        "column": "age",
        "operator": operator,
        "value": value,
    }


def test_invalid_select():
    with pytest.raises(ValueError, match="invalid SELECT"):
        parse("SELECT FROM users")


def test_delete_all_rows():
    statement = parse("DELETE FROM users")

    assert isinstance(statement, Delete)
    assert statement.table_name == "users"
    assert statement.where is None


@pytest.mark.parametrize(
    ("operator", "value"),
    [
        ("=", "7"),
        ("<", "10"),
        (">", "2"),
    ],
)
def test_delete_where_operators(operator, value):
    statement = parse(
        "DELETE FROM users WHERE id " + operator + " " + value
    )

    assert isinstance(statement, Delete)
    assert statement.where == {
        "column": "id",
        "operator": operator,
        "value": value,
    }


def test_invalid_delete():
    with pytest.raises(ValueError, match="invalid DELETE"):
        parse("DELETE users")


def test_transaction_statements():
    assert isinstance(parse("BEGIN"), Begin)
    assert isinstance(parse("COMMIT"), Commit)
    assert isinstance(parse("ROLLBACK"), Rollback)


def test_keyword_case_insensitive():
    assert isinstance(parse("begin"), Begin)
    assert isinstance(parse("commit"), Commit)
    assert isinstance(parse("rollback"), Rollback)


def test_create_table_invalid_column_definition():
    with pytest.raises(ValueError, match="invalid column definition"):
        parse("CREATE TABLE users (id)")
