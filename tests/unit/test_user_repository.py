import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import MagicMock, patch
from user_management.repositories.mysql_repository import MySQLUserRepository


class TestMySQLUserRepository(unittest.TestCase):
    def setUp(self):
        self.mysql_mock = MagicMock()
        self.connection_mock = MagicMock()
        self.cursor_mock = MagicMock()
        self.mysql_mock.connection = self.connection_mock
        self.connection_mock.cursor.return_value = self.cursor_mock
        self.connection_mock.commit = MagicMock()
        self.connection_mock.close = MagicMock()
        
        self.repo = MySQLUserRepository(self.mysql_mock)
    
    def test_save_success(self):
        user_data = {
            'username': 'testuser',
            'password': 'hashedpw',
            'email': 'test@example.com',
            'user_type': 'customer'
        }
        
        result = self.repo.save(user_data)
        self.assertTrue(result)
        self.cursor_mock.execute.assert_called_with(
            "INSERT INTO users (username, password, email, user_type) VALUES (%s, %s, %s, %s)",
            ('testuser', 'hashedpw', 'test@example.com', 'customer')
        )
        self.cursor_mock.close.assert_called_once()
        self.connection_mock.commit.assert_called_once()
    
    def test_save_db_error(self):
        user_data = {
            'username': 'testuser',
            'password': 'hashedpw',
            'email': 'test@example.com',
            'user_type': 'customer'
        }
        self.cursor_mock.execute.side_effect = Exception("DB Error")
        
        result = self.repo.save(user_data)
        self.assertFalse(result)
        self.cursor_mock.close.assert_not_called()
        self.connection_mock.commit.assert_not_called()
    
    def test_find_by_username_found(self):
        self.cursor_mock.fetchone.return_value = (1, 'testuser', 'hashedpw', 'test@example.com', 'customer')
        
        result = self.repo.find_by_username('testuser')
        self.assertIsNotNone(result)
        self.assertEqual(result['username'], 'testuser')
        self.assertEqual(result['user_type'], 'customer')
        self.cursor_mock.close.assert_called_once()
        self.connection_mock.commit.assert_not_called()
    
    def test_find_by_username_not_found(self):
        self.cursor_mock.fetchone.return_value = None
        result = self.repo.find_by_username('unknown')
        self.assertIsNone(result)
        self.cursor_mock.close.assert_called_once()
        self.connection_mock.commit.assert_not_called()
    
    def test_update_password_success(self):
        result = self.repo.update_password(1, 'newhashedpassword')
        self.assertTrue(result)
        self.cursor_mock.execute.assert_any_call("USE user_management")
        self.cursor_mock.execute.assert_any_call(
            "UPDATE users SET password = %s WHERE id = %s",
            ('newhashedpassword', 1)
        )
        self.cursor_mock.close.assert_called_once()
        self.connection_mock.commit.assert_called_once()
    
    def test_update_password_db_error(self):
        self.cursor_mock.execute.side_effect = Exception("DB Error")
        result = self.repo.update_password(1, 'newhashedpassword')
        self.assertFalse(result)
        self.cursor_mock.close.assert_not_called()
        self.connection_mock.commit.assert_not_called()
    
    def test_find_by_id_found(self):
        self.cursor_mock.fetchone.return_value = (1, 'testuser', 'hashedpassword', 'test@example.com', 'customer')
        result = self.repo.find_by_id(1)
        self.assertEqual(result['id'], 1)
        self.assertEqual(result['username'], 'testuser')
        self.cursor_mock.close.assert_called_once()
        self.connection_mock.commit.assert_not_called()
    
    def test_find_by_id_not_found(self):
        self.cursor_mock.fetchone.return_value = None
        result = self.repo.find_by_id(999)
        self.assertIsNone(result)
        self.cursor_mock.close.assert_called_once()
        self.connection_mock.commit.assert_not_called()
    
    def test_update_user_success(self):
        update_data = {'email': 'new@example.com', 'user_type': 'supplier'}
        result = self.repo.update_user(1, update_data)
        self.assertTrue(result)
        expected_sql = "UPDATE users SET email = %s, user_type = %s WHERE id = %s"
        self.cursor_mock.execute.assert_called_with(expected_sql, ['new@example.com', 'supplier', 1])
        self.cursor_mock.close.assert_called_once()
        self.connection_mock.commit.assert_called_once()
    
    def test_update_user_db_error(self):
        update_data = {'email': 'new@example.com', 'user_type': 'supplier'}
        self.cursor_mock.execute.side_effect = Exception("DB Error")
        result = self.repo.update_user(1, update_data)
        self.assertFalse(result)
        self.cursor_mock.close.assert_not_called()
        self.connection_mock.commit.assert_not_called()
