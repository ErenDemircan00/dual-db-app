import unittest
from unittest.mock import MagicMock, patch
from user_management.repositories.mysql_repository import MySQLUserRepository

class TestMySQLUserRepository(unittest.TestCase):
    
    def setUp(self):
        # Sahte MySQL bağlantısı oluştur
        self.mysql_mock = MagicMock()
        self.connection_mock = MagicMock()
        self.cursor_mock = MagicMock()
        self.mysql_mock.connection = self.connection_mock
        self.connection_mock.cursor.return_value = self.cursor_mock
        
        self.repo = MySQLUserRepository(self.mysql_mock)
    
    def test_save_success(self):
        user_data = {
            'username': 'testuser',
            'password': 'hashedpw',
            'email': 'test@example.com',
            'user_type': 'müsteri'
        }
        
        result = self.repo.save(user_data)
        self.assertTrue(result)
        self.cursor_mock.execute.assert_any_call(
            "INSERT INTO users (username, password, email, user_type) VALUES (%s, %s, %s, %s)",
            ('testuser', 'hashedpw', 'test@example.com', 'müsteri')  # Fixed: 'normal' -> 'müsteri'
        )
    
    def test_find_by_username_found(self):
        self.cursor_mock.fetchone.return_value = (1, 'testuser', 'hashedpw', 'test@example.com', 'normal')
        
        result = self.repo.find_by_username('testuser')
        self.assertIsNotNone(result)
        self.assertEqual(result['username'], 'testuser')
    
    def test_find_by_username_not_found(self):
        self.cursor_mock.fetchone.return_value = None
        result = self.repo.find_by_username('unknown')
        self.assertIsNone(result)
    
    def test_update_password_success(self):
        result = self.repo.update_password(1, 'newhashedpw')
        self.assertTrue(result)
        self.cursor_mock.execute.assert_any_call("USE user_management")
        self.cursor_mock.execute.assert_any_call(
            "UPDATE users SET password = %s WHERE id = %s",
            ('newhashedpw', 1)
        )
    
    def test_find_by_id_found(self):
        self.cursor_mock.fetchone.return_value = (1, 'user', 'pass', 'email', 'normal')
        result = self.repo.find_by_id(1)
        self.assertEqual(result['id'], 1)
    
    def test_find_by_id_not_found(self):
        self.cursor_mock.fetchone.return_value = None
        result = self.repo.find_by_id(999)
        self.assertIsNone(result)
    
    def test_update_user_success(self):
        update_data = {'email': 'new@example.com', 'user_type': 'premium'}
        result = self.repo.update_user(1, update_data)
        self.assertTrue(result)
        expected_sql = "UPDATE users SET email = %s, user_type = %s WHERE id = %s"
        self.cursor_mock.execute.assert_called_with(expected_sql, ['new@example.com', 'premium', 1])

if __name__ == '__main__':
    unittest.main()