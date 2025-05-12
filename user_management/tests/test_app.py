import unittest
from unittest.mock import patch, MagicMock
import json
import datetime
from bson.objectid import ObjectId
from flask import Flask
import jwt
from dotenv import load_dotenv
import sys
import os
from user_management.services.product_services import product_service
from user_management.services.product_services import product_service

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'user_management')))



# Ana uygulama dosyasını import edin
from app import app, bcrypt, auth_service, user_repository, product_repository, products_collection, cart_collection

load_dotenv()  # .env dosyasını yükler

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

class TestApp(unittest.TestCase):
    
    
    def setUp(self):
        """Her test öncesi çalışacak metod"""
        self.app = app.test_client()
        self.app.testing = True
        self.app_ctx = app.app_context()
        self.app_ctx.push()
        # Test için örnek kullanıcı, ürün ve sepet öğeleri
        self.test_user = {
            'id': 1,
            'username': 'testuser',
            'email': 'test@example.com',
            'user_type': 'customer',
            'password': bcrypt.generate_password_hash('password123').decode('utf-8')
        }
        self.test_product = {
            '_id': ObjectId('507f1f77bcf86cd799439011'),
            'name': 'Test Product',
            'price': 100.0,
            'description': 'This is a test product',
            'user_id': 1,
            'created_by': 'testuser',
            'created_at': datetime.datetime.utcnow()
        }
        self.test_cart_item = {
            '_id': ObjectId('507f1f77bcf86cd799439012'),
            'user_id': 1,
            'product_id': '507f1f77bcf86cd799439011',
            'name': 'Test Product',
            'price': 100.0,
            'quantity': 1,
            'added_at': datetime.datetime.utcnow()
        }
        # Mock veritabanı işlemleri
        self._setup_mocks()
        
    def tearDown(self):
        """Her test sonrası çalışacak metod"""
        self.app_ctx.pop()

    def _setup_mocks(self):
        """Mock veritabanı işlemlerini ayarla"""
        # User repository mock
        self.user_repo_patcher = patch('app.user_repository')
        self.mock_user_repo = self.user_repo_patcher.start()
        self.mock_user_repo.find_by_username.return_value = self.test_user
        self.mock_user_repo.find_by_id.return_value = self.test_user
        self.mock_user_repo.get_user_mail.return_value = self.test_user
        
        # Product repository mock
        self.product_repo_patcher = patch('app.product_repository')
        self.mock_product_repo = self.product_repo_patcher.start()
        
        # MongoDB collections mock
        self.products_patcher = patch('app.products_collection')
        self.mock_products = self.products_patcher.start()
        self.mock_products.find.return_value = [self.test_product]
        self.mock_products.find_one.return_value = self.test_product
        self.mock_products.insert_one.return_value = MagicMock(inserted_id=self.test_product['_id'])
        
        self.cart_patcher = patch('app.cart_collection')
        self.mock_cart = self.cart_patcher.start()
        self.mock_cart.find.return_value = [self.test_cart_item]
        self.mock_cart.find_one.return_value = self.test_cart_item
        
        # Mail sender mock
        self.mail_patcher = patch('app.mail')
        self.mock_mail = self.mail_patcher.start()
        
        # Jwt mock
        self.jwt_patcher = patch('app.jwt')
        self.mock_jwt = self.jwt_patcher.start()
        self.mock_jwt.encode.return_value = "test.jwt.token"
        self.mock_jwt.decode.return_value = {'user_id': 1, 'username': 'testuser', 'user_type': 'customer'}
        
        # Bcrypt mock
        self.bcrypt_patcher = patch('app.bcrypt')
        self.mock_bcrypt = self.bcrypt_patcher.start()
        self.mock_bcrypt.check_password_hash.return_value = True
        
        # Auth service mock
        self.auth_service_patcher = patch('app.auth_service')
        self.mock_auth_service = self.auth_service_patcher.start()
        self.mock_auth_service.login.return_value = self.test_user
        self.mock_auth_service.register.return_value = True
        self.mock_auth_service.update_profile.return_value = (True, "Profil güncellendi")
        
    def _get_mock_token_cookie(self):
        """Test için mock token oluştur"""
        return {'token': 'test.jwt.token'}
    
    # TEST METHODS
        
    def test_index_route(self):
        """Anasayfa testi"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_signup_get(self):
        """Kayıt sayfası GET isteği testi"""
        response = self.app.get('/signup')
        self.assertEqual(response.status_code, 200)
    
    def test_signup_post_success(self):
        """Başarılı kayıt testi"""
        self.mock_auth_service.register.return_value = True
        response = self.app.post('/signup', data={
            'username': 'newuser',
            'password': 'password123',
            'email': 'new@example.com',
            'user_type': 'customer'
        })
        self.assertEqual(response.status_code, 302)  # Yönlendirme kodu
        self.assertTrue('/login' in response.location or '/' in response.location)
    
    def test_login_get(self):
        """Giriş sayfası GET isteği testi"""
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
    
    def test_login_post_success(self):
        """Başarılı giriş testi"""
        response = self.app.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)  # Yönlendirme kodu
        self.assertTrue('/products' in response.location)
    
    def test_login_post_failure(self):
        """Başarısız giriş testi"""
        self.mock_auth_service.login.return_value = None
        response = self.app.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)  # Sayfada kalır
        self.assertIn(b'Ge', response.data)  # Hata mesajı içeriyor
    
    def test_login_api_success(self):
        """API üzerinden başarılı giriş testi"""
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/login', 
                                data=json.dumps({
                                    'username': 'testuser',
                                    'password': 'password123'
                                }),
                                headers=headers)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('token', data)
    
    def test_products_list_with_token(self):
        """Token ile ürün listesi görüntüleme testi"""
        with self.app.session_transaction() as sess:
            sess['username'] = 'testuser'
            sess['user_type'] = 'customer'
        
        response = self.app.get('/products', 
                               cookies=self._get_mock_token_cookie())
        self.assertEqual(response.status_code, 200)
    
    def test_products_list_without_token(self):
        """Token olmadan ürün listesi görüntüleme testi"""
        response = self.app.get('/products')
        self.assertEqual(response.status_code, 302)  # Yönlendirme kodu
        self.assertTrue('/login' in response.location)
    
    def test_add_product_get(self):
        """Ürün ekleme sayfası GET isteği testi"""
        response = self.app.get('/add-product', 
                               cookies=self._get_mock_token_cookie())
        self.assertEqual(response.status_code, 200)
    
    def test_add_product_post(self):
        """Ürün ekleme POST isteği testi"""
        response = self.app.post('/add-product', 
                                data={
                                    'name': 'New Product',
                                    'price': '199.99',
                                    'description': 'A new test product'
                                },
                                cookies=self._get_mock_token_cookie())
        self.assertEqual(response.status_code, 302)  # Yönlendirme kodu
        self.assertTrue('/products' in response.location)
    
    def test_api_add_product(self):
        """API üzerinden ürün ekleme testi"""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test.jwt.token'
        }
        response = self.app.post('/api/products', 
                                data=json.dumps({
                                    'name': 'API Product',
                                    'price': 299.99,
                                    'description': 'Product added via API'
                                }),
                                headers=headers)
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('product_id', data)
    
    def test_add_to_cart(self):
        """Sepete ürün ekleme testi"""
        response = self.app.post(f'/add-to-cart/{self.test_product["_id"]}', 
                                cookies=self._get_mock_token_cookie())
        self.assertEqual(response.status_code, 302)  # Yönlendirme kodu
        self.assertTrue('/cart' in response.location)
    
    def test_view_cart(self):
        """Sepeti görüntüleme testi"""
        response = self.app.get('/cart', 
                               cookies=self._get_mock_token_cookie())
        self.assertEqual(response.status_code, 200)
    
    def test_remove_from_cart(self):
        """Sepetten ürün çıkarma testi"""
        response = self.app.post(f'/remove-from-cart/{self.test_cart_item["_id"]}', 
                                cookies=self._get_mock_token_cookie())
        self.assertEqual(response.status_code, 302)  # Yönlendirme kodu
        self.assertTrue('/cart' in response.location)
    
    def test_update_cart(self):
        """Sepet güncelleme testi"""
        response = self.app.post(f'/update-cart/{self.test_cart_item["_id"]}', 
                                data={'quantity': '2'},
                                cookies=self._get_mock_token_cookie())
        self.assertEqual(response.status_code, 302)  # Yönlendirme kodu
        self.assertTrue('/cart' in response.location)
    
    def test_checkout(self):
        """Checkout işlemi testi"""
        with patch('app.flash') as mock_flash:
            response = self.app.post('/checkout', 
                                   cookies=self._get_mock_token_cookie())
            self.assertEqual(response.status_code, 302)  # Yönlendirme kodu
            self.assertTrue('/products' in response.location)
    
    def test_profile_get(self):
        """Profil sayfası GET isteği testi"""
        response = self.app.get('/profile', 
                               cookies=self._get_mock_token_cookie())
        self.assertEqual(response.status_code, 200)
    
    def test_profile_post(self):
        """Profil güncelleme testi"""
        response = self.app.post('/profile', 
                                data={
                                    'username': 'updateduser',
                                    'email': 'updated@example.com',
                                    'current_password': 'password123',
                                    'new_password': 'newpassword123'
                                },
                                cookies=self._get_mock_token_cookie())
        self.assertEqual(response.status_code, 200)
    
    def test_forget_password_get(self):
        """Şifre sıfırlama sayfası GET isteği testi"""
        response = self.app.get('/forget_password')
        self.assertEqual(response.status_code, 200)
    
    def test_forget_password_post(self):
        """Şifre sıfırlama POST isteği testi"""
        response = self.app.post('/forget_password', 
                                data={'email': 'test@example.com'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)
    
    def test_logout(self):
        """Çıkış yapma testi"""
        response = self.app.get('/logout')
        self.assertEqual(response.status_code, 302)  # Yönlendirme kodu
        self.assertTrue('/login' in response.location)
        self.assertEqual(response.cookies.get('token'), '')  # Token temizlendi


class TestAuthService(unittest.TestCase):
    def setUp(self):
        """Her test öncesi çalışacak metod"""
        # Mock user repository
        self.mock_user_repo = MagicMock()
        self.mock_user_repo.find_by_username.return_value = {
            'id': 1,
            'username': 'testuser',
            'email': 'test@example.com',
            'password': bcrypt.generate_password_hash('password123').decode('utf-8'),
            'user_type': 'customer'
        }
        
        # Mock bcrypt
        self.mock_bcrypt = MagicMock()
        self.mock_bcrypt.check_password_hash.return_value = True
        self.mock_bcrypt.generate_password_hash.return_value = b'hashedpassword'
        
        # Mock mail
        self.mock_mail = MagicMock()
        
        self.auth_service = auth_service
        self.auth_service.user_repository = self.mock_user_repo
        self.auth_service.bcrypt = self.mock_bcrypt
        self.auth_service.mail = self.mock_mail
    
    def test_login_success(self):
        """Başarılı giriş testi"""
        result = self.auth_service.login('testuser', 'password123')
        self.assertIsNotNone(result)
        self.assertEqual(result['username'], 'testuser')
    
    def test_login_failure_wrong_password(self):
        """Yanlış şifre ile giriş başarısız olmalı"""
        self.mock_bcrypt.check_password_hash.return_value = False
        result = self.auth_service.login('testuser', 'wrongpassword')
        self.assertIsNone(result)
    
    def test_login_failure_user_not_found(self):
        """Olmayan kullanıcı ile giriş başarısız olmalı"""
        self.mock_user_repo.find_by_username.return_value = None
        result = self.auth_service.login('nonexistentuser', 'password123')
        self.assertIsNone(result)


class TestProductService(unittest.TestCase):
    def setUp(self):
        """Her test öncesi çalışacak metod"""
        # Mock product repository
        self.mock_product_repo = MagicMock()
        self.test_product = {
            '_id': ObjectId('507f1f77bcf86cd799439011'),
            'name': 'Test Product',
            'price': 100.0,
            'description': 'This is a test product',
            'user_id': 1,
            'created_by': 'testuser',
            'created_at': datetime.datetime.utcnow()
        }
        self.mock_product_repo.get_all_products.return_value = [self.test_product]
        self.mock_product_repo.get_product_by_id.return_value = self.test_product
        
        self.product_service = product_service
        self.product_service.product_repository = self.mock_product_repo
    
    def test_get_all_products(self):
        """Tüm ürünleri getirme testi"""
        result = self.product_service.get_all_products()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'Test Product')
    
    def test_get_product_by_id(self):
        """ID ile ürün getirme testi"""
        result = self.product_service.get_product_by_id('507f1f77bcf86cd799439011')
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'Test Product')


if __name__ == '__main__':
    unittest.main()
    app.secret_key='benimgizliSecretkeyim'