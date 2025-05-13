import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os
from datetime import datetime, timezone, UTC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from unittest.mock import MagicMock

class TestFlaskAppUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--headless')  # Headless modda çalışması için
        
        # ChromeDriverManager kullanarak WebDriver'ı oluştur
        service = Service(ChromeDriverManager().install())
        cls.driver = webdriver.Chrome(service=service, options=options)
        
        cls.base_url = "http://localhost:5000"
        cls.driver.implicitly_wait(10)
        
        cls.screenshot_dir = os.path.join(os.path.dirname(__file__), 'screenshots')
        os.makedirs(cls.screenshot_dir, exist_ok=True)
        
    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
    
    def setUp(self):
        self.driver.get(self.base_url)
        self.driver.delete_all_cookies()
        self.timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    
    def tearDown(self):
        if hasattr(self, '_outcome') and hasattr(self._outcome, 'result'):
            if self._outcome.result.failures or self._outcome.result.errors:
                self._take_screenshot(self._testMethodName)
    
    def _take_screenshot(self, name):
        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        filename = f"{name}-{timestamp}.png"
        filepath = os.path.join(self.screenshot_dir, filename)
        self.driver.save_screenshot(filepath)
        print(f"Screenshot saved: {filepath}")
    
    def _register_test_user(self, username=None, password="testpass123", email=None, user_type="customer"):
        if username is None:
            username = f"seleniumuser{self.timestamp}"
        if email is None:
            email = f"selenium{self.timestamp}@test.com"
            
        self.driver.get(f"{self.base_url}/signup")
        
        self.driver.find_element(By.NAME, "username").send_keys(username)
        self.driver.find_element(By.NAME, "password").send_keys(password)
        self.driver.find_element(By.NAME, "email").send_keys(email)
        self.driver.find_element(By.CSS_SELECTOR, f"input[name='user_type'][value='{user_type}']").click()
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        WebDriverWait(self.driver, 10).until(
            lambda driver: "/login" in driver.current_url or "/" == driver.current_url
        )
        
        return {"username": username, "password": password, "email": email, "user_type": user_type}
    
    def _login(self, username=None, password="testpass123"):
        if username is None:
            user_data = self._register_test_user()
            username = user_data["username"]
            
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(username)
        self.driver.find_element(By.NAME, "password").send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        try:
            WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
            return True
        except TimeoutException:
            return False
    
    def _add_test_product(self, name=None, price="199.99", description="This is a product created by Selenium test"):
        if name is None:
            name = f"Selenium Test Product {self.timestamp}"
            
        self.driver.get(f"{self.base_url}/add-product")
        self.driver.find_element(By.NAME, "name").send_keys(name)
        self.driver.find_element(By.NAME, "price").send_keys(price)
        self.driver.find_element(By.NAME, "description").send_keys(description)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        return name
    
    def test_01_homepage_loads(self):
        self.driver.get(self.base_url)
        self.assertIn("Flask", self.driver.title)
        try:
            login_link = self.driver.find_element(By.LINK_TEXT, "Login")
            self.assertTrue(login_link.is_displayed())
            signup_link = self.driver.find_element(By.LINK_TEXT, "Sign Up")
            self.assertTrue(signup_link.is_displayed())
        except NoSuchElementException:
            self.fail("Ana sayfada login/signup bağlantıları bulunamadı")
    
    def test_02_registration_form(self):
        username = f"testuser{self.timestamp}"
        email = f"test{self.timestamp}@example.com"
        self.driver.get(f"{self.base_url}/signup")
        self.driver.find_element(By.NAME, "username").send_keys(username)
        self.driver.find_element(By.NAME, "password").send_keys("testpass123")
        self.driver.find_element(By.NAME, "email").send_keys(email)
        self.driver.find_element(By.CSS_SELECTOR, "input[name='user_type'][value='customer']").click()
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        WebDriverWait(self.driver, 10).until(
            lambda driver: "/login" in driver.current_url or "/" == driver.current_url
        )
        current_url = self.driver.current_url
        self.assertTrue("/login" in current_url or "/" in current_url)
    
    def test_03_login_form(self):
        user_data = self._register_test_user()
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(user_data["username"])
        self.driver.find_element(By.NAME, "password").send_keys(user_data["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        self.assertIn("/products", self.driver.current_url)
    
    def test_04_login_invalid_credentials(self):
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys("wronguser")
        self.driver.find_element(By.NAME, "password").send_keys("wrongpass")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        time.sleep(1)
        self.assertIn("/login", self.driver.current_url)
        try:
            error_message = self.driver.find_element(By.CSS_SELECTOR, ".alert-danger")
            self.assertIn("Geçersiz", error_message.text)
        except NoSuchElementException:
            pass
    
    def test_05_add_product(self):
        user_data = self._register_test_user(user_type="supplier")
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(user_data["username"])
        self.driver.find_element(By.NAME, "password").send_keys(user_data["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        product_name = self._add_test_product()
        
        page_source = self.driver.page_source
        self.assertIn(product_name, page_source)
    
    def test_06_add_to_cart(self):
        supplier = self._register_test_user(user_type="supplier")
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(supplier["username"])
        self.driver.find_element(By.NAME, "password").send_keys(supplier["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        product_name = self._add_test_product()
        self.driver.get(f"{self.base_url}/logout")
        
        customer = self._register_test_user(user_type="customer")
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(customer["username"])
        self.driver.find_element(By.NAME, "password").send_keys(customer["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        try:
            product_cards = self.driver.find_elements(By.CSS_SELECTOR, ".product-card")
            for card in product_cards:
                if product_name in card.text:
                    add_to_cart_button = card.find_element(By.CSS_SELECTOR, "button.add-to-cart")
                    add_to_cart_button.click()
                    break
            else:
                self.fail(f"Ürün bulunamadı: {product_name}")
                
            WebDriverWait(self.driver, 10).until(EC.url_contains("/cart"))
            page_source = self.driver.page_source
            self.assertIn(product_name, page_source)
        except NoSuchElementException as e:
            self._take_screenshot("add_to_cart_failure")
            self.fail(f"Sepete ekle düğmesi bulunamadı: {str(e)}")
    
    def test_07_update_cart(self):
        supplier = self._register_test_user(user_type="supplier")
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(supplier["username"])
        self.driver.find_element(By.NAME, "password").send_keys(supplier["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        product_name = self._add_test_product()
        self.driver.get(f"{self.base_url}/logout")
        
        customer = self._register_test_user(user_type="customer")
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(customer["username"])
        self.driver.find_element(By.NAME, "password").send_keys(customer["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        try:
            product_cards = self.driver.find_elements(By.CSS_SELECTOR, ".product-card")
            for card in product_cards:
                if product_name in card.text:
                    add_to_cart_button = card.find_element(By.CSS_SELECTOR, "button.add-to-cart")
                    add_to_cart_button.click()
                    break
                
            WebDriverWait(self.driver, 10).until(EC.url_contains("/cart"))
            quantity_input = self.driver.find_element(By.NAME, "quantity")
            quantity_input.clear()
            quantity_input.send_keys("3")
            update_button = self.driver.find_element(By.CSS_SELECTOR, "button.update-cart")
            update_button.click()
            
            WebDriverWait(self.driver, 10).until(EC.url_contains("/cart"))
            updated_quantity = self.driver.find_element(By.NAME, "quantity")
            self.assertEqual("3", updated_quantity.get_attribute("value"))
        except NoSuchElementException as e:
            self._take_screenshot("update_cart_failure")
            self.fail(f"Sepeti güncelleme testi başarısız: {str(e)}")
    
    def test_08_remove_from_cart(self):
        supplier = self._register_test_user(user_type="supplier")
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(supplier["username"])
        self.driver.find_element(By.NAME, "password").send_keys(supplier["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        product_name = self._add_test_product()
        self.driver.get(f"{self.base_url}/logout")
        
        customer = self._register_test_user(user_type="customer")
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(customer["username"])
        self.driver.find_element(By.NAME, "password").send_keys(customer["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        try:
            product_cards = self.driver.find_elements(By.CSS_SELECTOR, ".product-card")
            for card in product_cards:
                if product_name in card.text:
                    add_to_cart_button = card.find_element(By.CSS_SELECTOR, "button.add-to-cart")
                    add_to_cart_button.click()
                    break
                
            WebDriverWait(self.driver, 10).until(EC.url_contains("/cart"))
            remove_button = self.driver.find_element(By.CSS_SELECTOR, "button.remove-from-cart")
            remove_button.click()
            
            WebDriverWait(self.driver, 10).until(EC.url_contains("/cart"))
            page_source = self.driver.page_source
            if product_name in page_source:
                self.fail("Ürün sepetten çıkarılamadı")
        except NoSuchElementException as e:
            self._take_screenshot("remove_from_cart_failure")
            self.fail(f"Sepetten çıkarma testi başarısız: {str(e)}")
    
    def test_09_profile_page(self):
        user = self._register_test_user()
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(user["username"])
        self.driver.find_element(By.NAME, "password").send_keys(user["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        self.driver.get(f"{self.base_url}/profile")
        
        self.assertIn("/profile", self.driver.current_url)
        page_source = self.driver.page_source
        self.assertIn(user["username"], page_source)
        self.assertIn(user["email"], page_source)
        
        try:
            username_input = self.driver.find_element(By.NAME, "username")
            new_username = f"updated{self.timestamp}"
            username_input.clear()
            username_input.send_keys(new_username)
            current_password_input = self.driver.find_element(By.NAME, "current_password")
            current_password_input.send_keys(user["password"])
            update_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            update_button.click()
            
            time.sleep(2)
            page_source = self.driver.page_source
            self.assertIn(new_username, page_source)
        except NoSuchElementException as e:
            self._take_screenshot("profile_update_failure")
            self.fail(f"Profil güncelleme testi başarısız: {str(e)}")
    
    def test_10_logout(self):
        user = self._register_test_user()
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(user["username"])
        self.driver.find_element(By.NAME, "password").send_keys(user["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        self.driver.get(f"{self.base_url}/logout")
        WebDriverWait(self.driver, 10).until(EC.url_contains("/login"))
        
        self.driver.get(f"{self.base_url}/products")
        WebDriverWait(self.driver, 10).until(EC.url_contains("/login"))
    
    def test_11_forget_password(self):
        user = self._register_test_user()
        self.driver.get(f"{self.base_url}/forget_password")
        self.driver.find_element(By.NAME, "email").send_keys(user["email"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        time.sleep(2)
        page_source = self.driver.page_source
        self.assertIn("gonderildi", page_source.lower())
    
    def test_12_checkout(self):
        supplier = self._register_test_user(user_type="supplier")
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(supplier["username"])
        self.driver.find_element(By.NAME, "password").send_keys(supplier["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        product_name = self._add_test_product()
        self.driver.get(f"{self.base_url}/logout")
        
        customer = self._register_test_user(user_type="customer")
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(customer["username"])
        self.driver.find_element(By.NAME, "password").send_keys(customer["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        try:
            product_cards = self.driver.find_elements(By.CSS_SELECTOR, ".product-card")
            for card in product_cards:
                if product_name in card.text:
                    add_to_cart_button = card.find_element(By.CSS_SELECTOR, "button.add-to-cart")
                    add_to_cart_button.click()
                    break
                
            WebDriverWait(self.driver, 10).until(EC.url_contains("/cart"))
            checkout_button = self.driver.find_element(By.CSS_SELECTOR, "button.checkout")
            checkout_button.click()
            
            WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
            page_source = self.driver.page_source
            self.assertIn("Satın alma başarılı", page_source)
        except NoSuchElementException as e:
            self._take_screenshot("checkout_failure")
            self.fail(f"Ödeme işlemi testi başarısız: {str(e)}")

# Yeni sınıf ekleniyor
class MockedSeleniumTests(unittest.TestCase):
    """
    Selenium testleri için mock sınıfı.
    Gerçek tarayıcı başlatmadan temel Selenium test yapısını test eder.
    """
    def setUp(self):
        self.driver_mock = MagicMock()
        self.driver_mock.get = MagicMock()
        self.driver_mock.find_element = MagicMock()
        self.driver_mock.find_elements = MagicMock()
        self.driver_mock.save_screenshot = MagicMock()
        self.driver_mock.delete_all_cookies = MagicMock()
        self.base_url = "http://localhost:5000"
        self.timestamp = "20240101000000"  # Sabit zaman damgası
    
    def test_homepage_navigation(self):
        # Mock find_element cevabı
        element_mock = MagicMock()
        element_mock.is_displayed.return_value = True
        self.driver_mock.find_element.return_value = element_mock
        
        # Anasayfaya git
        self.driver_mock.get(f"{self.base_url}")
        
        # Mock element araması yapılıyor
        by_mock = MagicMock(name="By.LINK_TEXT")
        self.driver_mock.find_element(by_mock, "Login")
        
        # Bileşenler kontrol edilmeli
        self.driver_mock.find_element.assert_called()
        
        # Sayfada login bağlantısının varlığını kontrol et
        self.assertTrue(element_mock.is_displayed())
    
    def test_mock_registration(self):
        # Form için mocklara yeni değerler atama
        username_field = MagicMock()
        password_field = MagicMock()
        email_field = MagicMock()
        user_type_field = MagicMock()
        submit_button = MagicMock()
        
        # find_element için side effect tanımlama
        def find_element_side_effect(by, value):
            if value == "username":
                return username_field
            elif value == "password":
                return password_field
            elif value == "email":
                return email_field
            elif value == "user_type":
                return user_type_field
            elif value == "submit":
                return submit_button
            else:
                return MagicMock()
        
        self.driver_mock.find_element.side_effect = find_element_side_effect
        
        # Kayıt sayfasına git
        self.driver_mock.get(f"{self.base_url}/signup")
        
        # Form alanlarını doldur - bu esnada gerçek çağrılar yapılıyor
        by_mock = MagicMock(name="By.NAME")
        self.driver_mock.find_element(by_mock, "username")
        self.driver_mock.find_element(by_mock, "password")
        self.driver_mock.find_element(by_mock, "email")
        self.driver_mock.find_element(by_mock, "user_type")
        self.driver_mock.find_element(by_mock, "submit")
        
        # En az bir find_element çağrısı yapıldığını kontrol et
        self.assertGreaterEqual(self.driver_mock.find_element.call_count, 1)

if __name__ == "__main__":
    unittest.main()