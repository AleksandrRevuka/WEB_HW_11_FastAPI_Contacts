import unittest

from src.database.db import DatabaseSessionManager, get_db


class TestdConnectDB(unittest.IsolatedAsyncioTestCase):
    def test_database_session_manager(self):
        test_db_url = "sqlite+aiosqlite:///:memory:"
        database_session_manager = DatabaseSessionManager(test_db_url)

        session = database_session_manager.session()

        self.assertIsNotNone(session)

    async def test_get_db(self):
        res = get_db()
        self.assertIsNotNone(res)


if __name__ == "__main__":
    unittest.main()
