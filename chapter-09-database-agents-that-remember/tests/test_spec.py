from src.database.executor import validate_sql
def test_sql_safety():
    assert validate_sql('SELECT * FROM orders')['ok']
    assert not validate_sql('DELETE FROM orders')['ok']
    assert not validate_sql('SELECT 1; DELETE FROM orders')['ok']
