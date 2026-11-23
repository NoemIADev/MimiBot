"""Run with: python -m unittest discover -s app/tests -v.

No external services, credentials, or LLM calls are used by these tests.
"""
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch


class HealthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = MagicMock()
        cls.rag = MagicMock()
        spec = importlib.util.spec_from_file_location(
            "health_test_main", Path(__file__).resolve().parents[1] / "main.py"
        )
        cls.main = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"db": cls.db, "rag": cls.rag}), patch("dotenv.load_dotenv"):
            spec.loader.exec_module(cls.main)

    def setUp(self):
        self.db.reset_mock()
        self.rag.reset_mock()
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.cursor.fetchone.return_value = (1,)
        self.main.get_db_connection = MagicMock(return_value=self.conn)

    def tearDown(self):
        self.assertEqual(self.rag.mock_calls, [], "Health checks must never call the RAG pipeline")
        self.db.save_qa_history.assert_not_called()
        self.db.get_recent_qa_history.assert_not_called()

    def test_healthy_database(self):
        response = self.main.health()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.body), {"status": "ok", "api": "ok", "database": "ok"})
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.cursor.execute.assert_any_call("SELECT 1")
        self.conn.close.assert_called_once()

    def test_database_connection_failure_is_503_without_secrets(self):
        self.main.get_db_connection.side_effect = RuntimeError('postgres://secret-credentials')
        response = self.main.health()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(json.loads(response.body)['database'], 'unavailable')
        self.assertNotIn(b'secret', response.body)

    def test_query_timeout_closes_connection(self):
        self.cursor.execute.side_effect = RuntimeError('statement timeout')
        response = self.main.health()
        self.assertEqual(response.status_code, 503)
        self.conn.close.assert_called_once()

    def test_unexpected_query_result_is_unavailable(self):
        self.cursor.fetchone.return_value = None
        self.assertEqual(self.main.health().status_code, 503)
        self.conn.close.assert_called_once()

    def test_health_route_is_registered(self):
        route = next(route for route in self.main.app.routes if route.path == '/health')
        self.assertIn('GET', route.methods)
        self.assertIs(route.endpoint, self.main.health)


if __name__ == '__main__':
    unittest.main()
