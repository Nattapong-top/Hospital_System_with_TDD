# tests/conftest.py

# ประกาศให้ Pytest รู้ว่าให้ไปดึง Fixture ทั้งหมดมาจากไฟล์เหล่านี้
pytest_plugins = [
    "tests.fixtures.fixture_db",
    "tests.fixtures.fixture_domain",
    "tests.fixtures.fixture_api",
    "tests.fixtures.fixture_repo",
    "tests.fixtures.fixture_sqlalchemy",
]
