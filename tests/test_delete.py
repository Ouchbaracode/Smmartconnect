import unittest
from unittest.mock import MagicMock
import db

class TestDeleteFunctions(unittest.TestCase):
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

    def test_delete_vehicle_available(self):
        # Mock vehicle doc
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"status": "AVAILABLE"}

        self.mock_db_client.collection.return_value.document.return_value.get.return_value = mock_doc

        result = db.delete_vehicle("v1")

        self.assertTrue(result)
        self.mock_db_client.collection.return_value.document.return_value.delete.assert_called()

    def test_delete_vehicle_in_use(self):
        # Mock vehicle doc
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"status": "IN_USE"}

        self.mock_db_client.collection.return_value.document.return_value.get.return_value = mock_doc

        result = db.delete_vehicle("v1")

        self.assertFalse(result)
        self.mock_db_client.collection.return_value.document.return_value.delete.assert_not_called()

    def test_delete_tool_unused(self):
        # Mock tool doc
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"total_quantity": 10, "available_quantity": 10}

        self.mock_db_client.collection.return_value.document.return_value.get.return_value = mock_doc

        result = db.delete_tool("t1")

        self.assertTrue(result)
        self.mock_db_client.collection.return_value.document.return_value.delete.assert_called()

    def test_delete_tool_in_use(self):
        # Mock tool doc
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"total_quantity": 10, "available_quantity": 5}

        self.mock_db_client.collection.return_value.document.return_value.get.return_value = mock_doc

        result = db.delete_tool("t1")

        self.assertFalse(result)
        self.mock_db_client.collection.return_value.document.return_value.delete.assert_not_called()

    def test_delete_employee(self):
        result = db.delete_employee("u1")

        self.assertTrue(result)
        self.mock_db_client.collection.return_value.document.assert_called_with("u1")
        # Should now call delete instead of update
        self.mock_db_client.collection.return_value.document.return_value.delete.assert_called()

    def test_delete_mission(self):
        # Mock mission resources release logic - complex to test thoroughly without mocking sub-calls,
        # but we can verify delete is called on the document

        # We need to mock _release_mission_resources or its internal calls if we want to isolate it,
        # but here we mainly care that db.collection(...).document(...).delete() is called.

        # Mock get for release resources
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"vehicle_id": "v1"}
        self.mock_db_client.collection.return_value.document.return_value.get.return_value = mock_doc

        result = db.delete_mission("m1")

        self.assertTrue(result)
        # Verify delete was called on the mission document
        # Note: Depending on how mocks are reused, we might need specific assert.
        # Since _release_mission_resources does other calls, we just want to ensure delete() happened eventually.
        self.mock_db_client.collection.return_value.document.return_value.delete.assert_called()

if __name__ == '__main__':
    unittest.main()
