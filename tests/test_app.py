import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from bson.objectid import ObjectId
import jwt
import datetime
import mongomock
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from user_management.app import app, create_token, bcrypt
from user_management.repositories.mysql_repository import MySQLUserRepository
from user_management.repositories.mongo_repository import MongoProductRepository
from user_management.services.auth_service import AuthService
from user_management.utils.email_service import send_cart_update_email

class FlaskAppBasicTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        self.client = app.test_client()
        self.user = {
            'id': 1,
            'username': 'testuser',
            'password': '$2b$12$testpasswordhash',
            'email': 'test@example.com',
            'user_type': 'customer'
        }
        self.product = {
            '_id': ObjectId(),
            'name': 'Test Product',
            'price': 10.0,
            'description': 'A test product',
            'user_id': 1,
            'created_by': 'testuser',
            'created_at': datetime.datetime.now(datetime.UTC)
        }
        self.token = create_token(self.user)

    # Basit sayfaların yüklenmesi testleri
    def test_index_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_login_page_loads(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'form', response.data)

    def test_signup_page_loads(self):
        response = self.client.get('/signup')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'form', response.data)
        
    def test_forget_password_page_loads(self):
        response = self.client.get('/forget_password')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'email', response.data)
    
    # Token oluşturma işlemi testi
    def test_create_token(self):
        token = create_token(self.user)
        self.assertTrue(token)
        # Token'ı doğrulama
        decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        self.assertEqual(decoded['user_id'], self.user['id'])
        self.assertEqual(decoded['username'], self.user['username'])

class FlaskAppMockTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        self.client = app.test_client()
        self.user = {
            'id': 1,
            'username': 'testuser',
            'password': '$2b$12$testpasswordhash',
            'email': 'test@example.com',
            'user_type': 'customer'
        }
        
    # Kullanıcı girişi testi
    @patch('user_management.app.auth_service.login')
    def test_login_with_valid_credentials(self, mock_login):
        # Mock AuthService.login fonksiyonunun dönüş değerini ayarla
        mock_login.return_value = self.user
        
        # Login isteği yap
        response = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        }, follow_redirects=True)
        
        # Sonuçları doğrula
        self.assertEqual(response.status_code, 200)
        mock_login.assert_called_once_with('testuser', 'password123')
        
    # Geçersiz kimlik bilgileriyle giriş testi
    @patch('user_management.app.auth_service.login')
    def test_login_with_invalid_credentials(self, mock_login):
        # Mock AuthService.login fonksiyonunun dönüş değerini ayarla
        mock_login.return_value = None
        
        # Login isteği yap
        response = self.client.post('/login', data={
            'username': 'wronguser',
            'password': 'wrongpass'
        })
        
        # Sonuçları doğrula
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)  # Geçersiz kimlik bilgileri gösteriliyor
        mock_login.assert_called_once_with('wronguser', 'wrongpass')

class MongoDBTests(unittest.TestCase):
    def setUp(self):
        # MongoClient'ı mongomock ile oluştur
        self.mongo_client = mongomock.MongoClient()
        
        # Flask-PyMongo sınıfını taklit eden bir mock oluştur
        class MockPyMongo:
            def __init__(self, mongo_client):
                self.db = mongo_client['shop']  # MongoProductRepository'nin beklediği db adı
                
        # Mock PyMongo nesnesini oluştur
        self.mock_pymongo = MockPyMongo(self.mongo_client)
        
        # Test verileri
        self.test_products = [
            {
                '_id': ObjectId(),
                'name': 'Test Product 1',
                'price': 10.0,
                'description': 'A test product 1',
                'user_id': 1,
                'created_by': 'testuser',
                'created_at': datetime.datetime.now(datetime.UTC)
            },
            {
                '_id': ObjectId(),
                'name': 'Test Product 2',
                'price': 20.0,
                'description': 'A test product 2',
                'user_id': 2,
                'created_by': 'anotheruser',
                'created_at': datetime.datetime.now(datetime.UTC)
            }
        ]
        
        # Verileri koleksiyona ekle
        self.mongo_client['shop']['products'].insert_many(self.test_products)
        
        # MongoProductRepository nesnesi oluştur
        self.product_repo = MongoProductRepository(self.mock_pymongo)
        
    def test_find_all_products(self):
        # Repository üzerinden tüm ürünleri bul
        products = self.product_repo.find_all()
        
        # En az 2 ürün olmalı
        self.assertGreaterEqual(len(products), 2)
    
    def test_mongo_insert_and_find(self):
        # Yeni ürün ekle
        new_product = {
            'name': 'New Product',
            'price': 30.0,
            'description': 'A new product',
            'user_id': 3,
            'created_by': 'newuser',
            'created_at': datetime.datetime.now(datetime.UTC)
        }
        
        # Ürünü koleksiyona ekle
        result = self.mongo_client['shop']['products'].insert_one(new_product)
        self.assertTrue(result.inserted_id)
        
        # Eklenen ürünü bul
        found_product = self.mongo_client['shop']['products'].find_one({'_id': result.inserted_id})
        self.assertEqual(found_product['name'], 'New Product')
        self.assertEqual(found_product['price'], 30.0)
        
        # İsme göre arama
        found_by_name = list(self.mongo_client['shop']['products'].find({'name': 'New Product'}))
        self.assertEqual(len(found_by_name), 1)
        self.assertEqual(found_by_name[0]['price'], 30.0)

if __name__ == '__main__':
    unittest.main() 