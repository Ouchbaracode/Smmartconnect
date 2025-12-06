import unittest
from unittest.mock import MagicMock, patch
import db
from datetime import datetime

class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        # Create a mock for the Firestore client
        self.mock_db_client = MagicMock()

        # Patch the db.db object with our mock
        self.original_db = db.db.db
        db.db.db = self.mock_db_client

        # Reset the mock for each test
        self.mock_db_client.reset_mock()

    def tearDown(self):
        # Restore the original db object
        db.db.db = self.original_db

    def test_hash_password(self):
        password = "password123"
        hashed = db.db.hash_password(password)
        # SHA-256 hash of "password123"
        expected_hash = "ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f"
        self.assertEqual(hashed, expected_hash)

    def test_login_success(self):
        # Mock the query result
        mock_stream = MagicMock()
        mock_doc = MagicMock()
        mock_doc.id = "user123"
        mock_doc.to_dict.return_value = {
            "username": "testuser",
            "password": db.db.hash_password("password"),
            "active": True,
            "full_name": "Test User"
        }
        mock_doc.exists = True
        mock_stream.stream.return_value = [mock_doc]

        # Configure the mock chain
        self.mock_db_client.collection.return_value.where.return_value.where.return_value.where.return_value.limit.return_value = mock_stream

        # Call the login function
        user = db.db.login("testuser", "password")

        # Assertions
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], "testuser")
        self.assertEqual(user['id'], "user123")

        # Verify last login update
        self.mock_db_client.collection.return_value.document.assert_called_with("user123")
        self.mock_db_client.collection.return_value.document.return_value.update.assert_called()

    def test_login_failure_wrong_password(self):
         # Mock the query result (empty for wrong credentials)
        mock_stream = MagicMock()
        mock_stream.stream.return_value = []

        # Configure the mock chain
        self.mock_db_client.collection.return_value.where.return_value.where.return_value.where.return_value.limit.return_value = mock_stream

        # Call the login function
        user = db.db.login("testuser", "wrongpassword")

        # Assertions
        self.assertIsNone(user)

    def test_create_user_success(self):
        # Mock that user doesn't exist
        mock_stream = MagicMock()
        mock_stream.stream.return_value = []
        self.mock_db_client.collection.return_value.where.return_value.limit.return_value = mock_stream

        # Mock the add operation
        mock_doc_ref = MagicMock()
        self.mock_db_client.collection.return_value.add.return_value = mock_doc_ref

        # Call create_user
        result = db.db.create_user("newuser", "New User", "password", "admin", 1)

        # Assertions
        self.assertTrue(result)
        self.mock_db_client.collection.return_value.add.assert_called()
        args, _ = self.mock_db_client.collection.return_value.add.call_args
        self.assertEqual(args[0]['username'], "newuser")
        self.assertEqual(args[0]['role'], "admin")

    def test_create_user_already_exists(self):
        # Mock that user exists
        mock_stream = MagicMock()
        mock_doc = MagicMock()
        mock_stream.stream.return_value = [mock_doc]
        self.mock_db_client.collection.return_value.where.return_value.limit.return_value = mock_stream

        # Call create_user
        result = db.db.create_user("existinguser", "Existing User", "password", "admin", 1)

        # Assertions
        self.assertFalse(result)
        self.mock_db_client.collection.return_value.add.assert_not_called()

    def test_get_all_employees(self):
        # Mock users
        mock_user1 = MagicMock()
        mock_user1.id = "u1"
        mock_user1.to_dict.return_value = {
            "full_name": "User One", "username": "u1", "role": "admin", "department_id": "1", "active": True
        }
        mock_user1.exists = True

        mock_user2 = MagicMock()
        mock_user2.id = "u2"
        mock_user2.to_dict.return_value = {
            "full_name": "User Two", "username": "u2", "role": "technician", "department_id": "2", "active": False
        }
        mock_user2.exists = True

        self.mock_db_client.collection.return_value.stream.return_value = [mock_user1, mock_user2]

        # Mock departments
        mock_dept_doc = MagicMock()
        mock_dept_doc.exists = True
        mock_dept_doc.to_dict.return_value = {"name": "IT"}
        self.mock_db_client.collection.return_value.document.return_value.get.return_value = mock_dept_doc

        # Call function
        employees = db.db.get_all_employees()

        # Assertions
        self.assertEqual(len(employees), 2)
        self.assertEqual(employees[0]['name'], "User One")
        self.assertEqual(employees[0]['department'], "IT")
        self.assertEqual(employees[0]['status'], "ACTIVE")
        self.assertEqual(employees[1]['status'], "INACTIVE")

if __name__ == '__main__':
    unittest.main()
