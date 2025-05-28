import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from bson.objectid import ObjectId
import jwt
import datetime
import sys
import os

from user_management.repositories.mysql_repository import MySQLUserRepository


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from user_management.app import app, create_token
from user_management.repositories.mongo_repository import MongoProductRepository
from user_management.services.auth_service import AuthService

class FlaskAppBasicTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = '123'
        self.client = app.test_client()
        self.user = {
            'id': 1,
            'username': 'testuser',
            'password': '$2b$12$testpasswordhash',
            'gmail': 'test@example.com',
            'user_type': 'customer'
        }
        self.product = {
            '_id': ObjectId(),
            'name': 'Test Product',
            'price': 10.0,
            'description': 'A test product',
            'user_id': 1,
            'created_by': 'testuser',
            'created_at': datetime.datetime.now(datetime.timezone.utc)
        }
        self.token = create_token(self.user)

    def test_index_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        print("Sayfa yüklendi:", response.data)
        
    def test_login_page_loads(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'form', response.data)
        print("Sayfa yüklendi:", response.data)
        
    def test_signup_page_loads(self):
        response = self.client.get('/signup')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'form', response.data)
        print("Sayfa yüklendi:", response.data)
        
    def test_forget_password_page_loads(self):
        response = self.client.get('/forget_password')
        self.assertEqual(response.status_code, 200)
        print("Sayfa yüklendi:", response.data)
        
    # def test_create_token_invalid_user(self):
    #     with self.assertRaises(ValueError):
    #         create_token({'username': 'invaliduser', 'user_type': 'unknown'})
            
    # def test_create_token_valid_user(self):
    #     token = create_token(self.user)
    #     self.assertIsNotNone(token)
    #     decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    #     self.assertEqual(decoded['username'], self.user['username'])
    #     self.assertEqual(decoded['user_type'], self.user['user_type'])
    #     self.assertIn('exp', decoded)
        
    # def test_create_token_expiration(self):
    #     token = create_token(self.user)
    #     decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    #     expiration_time = datetime.datetime.fromtimestamp(decoded['exp'])
    #     self.assertTrue(expiration_time > datetime.datetime.now(datetime.timezone.utc))
    
    def test_create_token(self):
        token = create_token(self.user)
        self.assertIsNotNone(token)
        decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        self.assertEqual(decoded['username'], self.user['username'])
        self.assertEqual(decoded['user_type'], self.user['user_type'])
        self.assertIn('exp', decoded)

class TestAuthService(unittest.TestCase):
    def setUp(self):
        self.mock_repo = MagicMock()
        self.mock_bcrypt = MagicMock()
        self.mock_mail = MagicMock()
        self.auth_service = AuthService(self.mock_repo, self.mock_bcrypt, self.mock_mail)

    def test_register_success(self):
        self.mock_repo.save.return_value = True
        result = self.auth_service.register("user1", "pass1", "user1@gmail.com")
        self.assertTrue(result)
        self.mock_repo.save.assert_called_once()
    
    def test_login_success(self):
        self.mock_repo.find_by_username.return_value = {'username': 'user1', 'password': 'hashedpass'}
        self.mock_bcrypt.check_password_hash.return_value = True
        user = self.auth_service.login("user1", "pass1")
        self.assertIsNotNone(user)
        self.mock_repo.find_by_username.assert_called_once_with("user1")
        self.mock_bcrypt.check_password_hash.assert_called_once()
    
    def test_login_failure_wrong_password(self):
        self.mock_repo.find_by_username.return_value = {'username': 'user1', 'password': 'hashedpass'}
        self.mock_bcrypt.check_password_hash.return_value = False
        user = self.auth_service.login("user1", "wrongpass")
        self.assertIsNone(user)

    def test_login_failure_no_user(self):
        self.mock_repo.find_by_username.return_value = None
        user = self.auth_service.login("no_user", "pass")
        self.assertIsNone(user)

    def test_update_profile_user_not_found(self):
        self.mock_repo.find_by_id.return_value = None
        success, msg = self.auth_service.update_profile(1, username="newuser")
        self.assertFalse(success)
        self.assertEqual(msg, "Kullanıcı bulunamadı.")

    def test_update_profile_password_mismatch(self):
        self.mock_repo.find_by_id.return_value = {'id': 1, 'username': 'olduser', 'password': 'hashedpass', 'email': 'old@gmail.com'}
        self.mock_bcrypt.check_password_hash.return_value = False
        success, msg = self.auth_service.update_profile(1, current_password="wrong", new_password="newpass")
        self.assertFalse(success)
        self.assertEqual(msg, "Mevcut şifre yanlış.")

    def test_update_profile_username_taken(self):
        self.mock_repo.find_by_id.return_value = {'id': 1, 'username': 'olduser', 'password': 'hashedpass', 'email': 'old@gmail.com'}
        self.mock_bcrypt.check_password_hash.return_value = True
        self.mock_repo.find_by_username.return_value = {'id': 2, 'username': 'newuser'}
        success, msg = self.auth_service.update_profile(1, username="newuser")
        self.assertFalse(success)
        self.assertEqual(msg, "Bu kullanıcı adı zaten kullanılıyor.")

    def test_update_profile_email_taken(self):
        self.mock_repo.find_by_id.return_value = {'id': 1, 'username': 'olduser', 'password': 'hashedpass', 'email': 'old@gmail.com'}
        self.mock_bcrypt.check_password_hash.return_value = True
        self.mock_repo.find_by_username.return_value = None
        self.mock_repo.find_by_email.return_value = {'id': 3, 'gmail': 'new@gmail.com'}
        success, msg = self.auth_service.update_profile(1, email="new@gmail.com")
        self.assertFalse(success)
        self.assertEqual(msg, "Bu e-posta adresi zaten kullanılıyor.")

    def test_update_profile_success(self):
        self.mock_repo.find_by_id.return_value = {'id': 1, 'username': 'olduser', 'password': 'hashedpass', 'email': 'old@gmail.com'}
        self.mock_bcrypt.check_password_hash.return_value = True
        self.mock_repo.find_by_username.return_value = None
        self.mock_repo.find_by_email.return_value = None
        self.mock_bcrypt.generate_password_hash.return_value = b"hashednewpass"
        self.mock_repo.update_user.return_value = True
        success, msg = self.auth_service.update_profile(
            1,
            username="newuser",
            email="new@gmail.com",
            current_password="oldpass",
            new_password="newpass"
        )
        self.assertTrue(success)
        self.assertEqual(msg, "Profil başarıyla güncellendi.")
        
        

class TestMongoProductRepository(unittest.TestCase):
    def setUp(self):
        self.mock_mongo = MagicMock()
        self.mock_collection = MagicMock()
        self.mock_mongo.db.products = self.mock_collection
        self.repo = MongoProductRepository(self.mock_mongo)

    def test_find_all_success(self):
        self.mock_collection.find.return_value = [
            {'name': 'Ürün1', 'price': 100},
            {'name': 'Ürün2', 'price': 200}
        ]
        result = self.repo.find_all()
        self.mock_collection.find.assert_called_once_with({}, {'_id': 0})
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'Ürün1')

    def test_find_all_exception(self):
        self.mock_collection.find.side_effect = Exception("DB hatası")
        result = self.repo.find_all()
        self.assertEqual(result, [])


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
