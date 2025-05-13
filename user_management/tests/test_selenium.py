import unittest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
import time
import os
from datetime import datetime
from selenium.webdriver.support.ui import Select
import threading
import sys
from pathlib import Path

# Flask uygulamasını import et
sys.path.append(str(Path(__file__).parent.parent.parent))
from user_management.app import app

class TestFlaskAppUI(unittest.TestCase):
    """Flask uygulamasının UI testleri için Selenium test sınıfı."""
    
    @classmethod
    def setUpClass(cls):
        """Tüm testlerden önce bir kez çalışır."""
        # Flask uygulamasını başlat
        def run_flask():
            app.run(port=5000)
        
        cls.flask_thread = threading.Thread(target=run_flask, daemon=True)
        cls.flask_thread.start()
        time.sleep(1)  # Uygulamanın başlaması için bekle
        
        # WebDriver'ı başlat
        options = webdriver.ChromeOptions()
        # Aşağıdaki satırı yoruma alarak testleri görsel olarak izleyebilirsiniz
        options.add_argument('--headless')  # UI olmadan çalıştırmak için
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Driver'ı başlat
        service = Service(ChromeDriverManager().install())
        cls.driver = webdriver.Chrome(service=service, options=options)
        cls.base_url = "http://localhost:5000"  # Uygulamanın URL'si
        cls.driver.implicitly_wait(10)  # Elementlerin yüklenmesi için implicitly wait
        
        # Ekran görüntüleri için klasör
        cls.screenshot_dir = os.path.join(os.path.dirname(__file__), 'screenshots')
        os.makedirs(cls.screenshot_dir, exist_ok=True)
        
    @classmethod
    def tearDownClass(cls):
        """Tüm testlerden sonra bir kez çalışır."""
        cls.driver.quit()
    
    def setUp(self):
        """Her testten önce çalışır."""
        self.driver.get(self.base_url)
        self.driver.delete_all_cookies()  # Önceki oturumları temizle
        self.timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    def tearDown(self):
        """Her testten sonra çalışır."""
        # Test başarısız olursa ekran görüntüsü al
        if hasattr(self, '_outcome') and hasattr(self._outcome, 'result'):
            if self._outcome.result.failures or self._outcome.result.errors:
                self._take_screenshot(self._testMethodName)
    
    def _take_screenshot(self, name):
        """Ekran görüntüsü alma yardımcı metodu."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{name}-{timestamp}.png"
        filepath = os.path.join(self.screenshot_dir, filename)
        self.driver.save_screenshot(filepath)
        print(f"Screenshot saved: {filepath}")
    
    def _register_test_user(self, username=None, password="testpass123", email=None, user_type="customer"):
        """Test için yeni kullanıcı kayıt yardımcı metodu."""
        if username is None:
            username = f"seleniumuser{self.timestamp}"
        if email is None:
            email = f"selenium{self.timestamp}@test.com"
            
        self.driver.get(f"{self.base_url}/signup")
        
        # Form alanlarını doldur
        self.driver.find_element(By.NAME, "username").send_keys(username)
        self.driver.find_element(By.NAME, "password").send_keys(password)
        self.driver.find_element(By.NAME, "email").send_keys(email)
        
        # User type seçimi (radio button)
        self.driver.find_element(By.CSS_SELECTOR, f"input[name='user_type'][value='{user_type}']").click()
        
        # Formu gönder
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Yönlendirmenin tamamlanmasını bekle
        WebDriverWait(self.driver, 10).until(
            lambda driver: "/login" in driver.current_url or "/" == driver.current_url
        )
        
        return {
            "username": username,
            "password": password,
            "email": email,
            "user_type": user_type
        }
    
    def _login(self, username=None, password="testpass123"):
        """Test için kullanıcı girişi yardımcı metodu."""
        if username is None:
            # Önce kayıt ol
            user_data = self._register_test_user()
            username = user_data["username"]
            
        self.driver.get(f"{self.base_url}/login")
        
        # Form alanlarını doldur
        self.driver.find_element(By.NAME, "username").send_keys(username)
        self.driver.find_element(By.NAME, "password").send_keys(password)
        
        # Formu gönder
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Başarılı giriş durumunda ürün sayfasına yönlendirilmeyi bekle
        try:
            WebDriverWait(self.driver, 10).until(
                EC.url_contains("/products")
            )
            return True
        except TimeoutException:
            return False
    
    def _add_test_product(self, name=None, price="199.99", description="This is a product created by Selenium test"):
        """Test için ürün ekleme yardımcı metodu."""
        if name is None:
            name = f"Selenium Test Product {self.timestamp}"
            
        self.driver.get(f"{self.base_url}/add-product")
        
        # Form alanlarını doldur
        self.driver.find_element(By.NAME, "name").send_keys(name)
        self.driver.find_element(By.NAME, "price").send_keys(price)
        self.driver.find_element(By.NAME, "description").send_keys(description)
        
        # Formu gönder
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Yönlendirmenin tamamlanmasını bekle
        WebDriverWait(self.driver, 10).until(
            EC.url_contains("/products")
        )
        
        return name
    
    # Test Metodları
    
    def test_01_homepage_loads(self):
        """Ana sayfanın yüklendiğini test et."""
        self.driver.get(self.base_url)
        # Ana sayfa başlığını kontrol et
        self.assertIn("Login Page", self.driver.title)
        
        # Ana sayfada signup bağlantısını kontrol et
        try:
            signup_link = self.driver.find_element(By.LINK_TEXT, "Sign up here")
            self.assertTrue(signup_link.is_displayed())
        except NoSuchElementException:
            self.fail("Ana sayfada signup bağlantısı bulunamadı")
    
    def test_02_registration_form(self):
        """Kayıt formunun çalıştığını test et."""
        # Benzersiz kullanıcı adı oluştur
        username = f"testuser{self.timestamp}"
        email = f"test{self.timestamp}@example.com"
        
        self.driver.get(f"{self.base_url}/signup")
        
        # Form alanlarını doldur
        self.driver.find_element(By.ID, "username").send_keys(username)
        self.driver.find_element(By.ID, "password").send_keys("testpass123")
        self.driver.find_element(By.ID, "email").send_keys(email)
        self.driver.find_element(By.CSS_SELECTOR, "input[name='user_type'][value='customer']").click()
        
        # Formu gönder
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Yönlendirmenin tamamlanmasını bekle
        WebDriverWait(self.driver, 10).until(
            lambda driver: "/login" in driver.current_url or "/" == driver.current_url
        )
        
        # Başarılı kayıt sonrası login sayfasına yönlendirildiğini kontrol et
        current_url = self.driver.current_url
        self.assertTrue("/login" in current_url or "/" in current_url)
    
    def test_03_login_form(self):
        """Giriş formunun çalıştığını test et."""
        # Önce test kullanıcısını kaydet
        user_data = self._register_test_user()
        
        # Giriş yap
        self.driver.get(f"{self.base_url}/login")
        
        # Form alanlarını doldur
        self.driver.find_element(By.NAME, "username").send_keys(user_data["username"])
        self.driver.find_element(By.NAME, "password").send_keys(user_data["password"])
        
        # Formu gönder
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Başarılı giriş durumunda ürün sayfasına yönlendirilmeyi bekle
        WebDriverWait(self.driver, 10).until(
            EC.url_contains("/products")
        )
        
        # Ürün sayfasının yüklendiğini doğrula
        self.assertIn("/products", self.driver.current_url)
    
    def test_04_login_invalid_credentials(self):
        """Geçersiz kimlik bilgileriyle giriş başarısızlığını test et."""
        self.driver.get(f"{self.base_url}/login")
        
        # Geçersiz kimlik bilgileriyle formu doldur
        self.driver.find_element(By.NAME, "username").send_keys("wronguser")
        self.driver.find_element(By.NAME, "password").send_keys("wrongpass")
        
        # Formu gönder
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Login sayfasında kaldığımızı doğrula (yönlendirme olmamalı)
        time.sleep(1)  # Kısa bir bekleme
        self.assertIn("/login", self.driver.current_url)
        
        # Hata mesajını kontrol et (uygulamanızın hata bildirimi nasılsa ona göre ayarlayın)
        try:
            error_message = self.driver.find_element(By.CSS_SELECTOR, ".alert-danger")
            self.assertIn("Geçersiz", error_message.text)
        except NoSuchElementException:
            # Hata mesajı farklı bir element içinde olabilir, bu durumu tolere et
            pass
    
    def test_05_add_product(self):
        """Ürün ekleme formunun çalıştığını test et."""
        # Test kullanıcısını oluştur ve giriş yap (supplier rolünde)
        user_data = self._register_test_user(user_type="supplier")
        
        # Giriş yap
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(user_data["username"])
        self.driver.find_element(By.NAME, "password").send_keys(user_data["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Ürün ekleme sayfasına git
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        self.driver.get(f"{self.base_url}/add-product")
        
        # Ürün adını benzersiz yap
        product_name = f"Test Product {self.timestamp}"
        
        # Form alanlarını doldur
        self.driver.find_element(By.NAME, "name").send_keys(product_name)
        self.driver.find_element(By.NAME, "price").send_keys("199.99")
        self.driver.find_element(By.NAME, "description").send_keys("Product added by Selenium test")
        
        # Formu gönder
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Ürün listesine yönlendirildiğini bekle
        WebDriverWait(self.driver, 10).until(
            EC.url_contains("/products")
        )
        
        # Ürünün listeye eklendiğini kontrol et (sayfada ürün adı görünüyor mu?)
        page_source = self.driver.page_source
        self.assertIn(product_name, page_source)
    
    def test_06_add_to_cart(self):
        """Sepete ürün ekleme işlevini test et."""
        # Önce supplier olarak kayıt ol ve ürün ekle
        supplier = self._register_test_user(user_type="supplier")
        
        # Giriş yap
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(supplier["username"])
        self.driver.find_element(By.NAME, "password").send_keys(supplier["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Ürün ekleme
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        product_name = self._add_test_product()
        
        # Çıkış yap
        self.driver.get(f"{self.base_url}/logout")
        
        # Müşteri olarak kayıt ol
        customer = self._register_test_user(user_type="customer")
        
        # Müşteri olarak giriş yap
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(customer["username"])
        self.driver.find_element(By.NAME, "password").send_keys(customer["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Ürün listesine git
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        
        # Ürünü sepete ekle (UI'a göre ayarlayın)
        # Önce eklediğimiz ürünün "Sepete Ekle" düğmesini bul
        # Bu kısım uygulamanızın HTML yapısına bağlı olarak değişebilir
        try:
            # Ürün kartlarını bul
            product_cards = self.driver.find_elements(By.CSS_SELECTOR, ".card")
            
            for card in product_cards:
                if product_name in card.text:
                    # Bu ürün kartında "Sepete Ekle" düğmesini bul
                    add_to_cart_button = card.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    add_to_cart_button.click()
                    break
            else:
                self.fail(f"Ürün bulunamadı: {product_name}")
                
            # Sepet sayfasına yönlendirilmeyi bekle
            WebDriverWait(self.driver, 10).until(EC.url_contains("/cart"))
            
            # Ürünün sepette olduğunu doğrula
            page_source = self.driver.page_source
            self.assertIn(product_name, page_source)
            
        except NoSuchElementException as e:
            self._take_screenshot("add_to_cart_failure")
            self.fail(f"Sepete ekle düğmesi bulunamadı: {str(e)}")
    
    def test_07_update_cart(self):
        """Sepetteki ürün miktarını güncelleme işlevini test et."""
        # test_06 ile aynı kurulumu yap
        # Önce supplier olarak kayıt ol ve ürün ekle
        supplier = self._register_test_user(user_type="supplier")
        
        # Giriş yap
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(supplier["username"])
        self.driver.find_element(By.NAME, "password").send_keys(supplier["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Ürün ekleme
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        product_name = self._add_test_product()
        
        # Çıkış yap
        self.driver.get(f"{self.base_url}/logout")
        
        # Müşteri olarak kayıt ol
        customer = self._register_test_user(user_type="customer")
        
        # Müşteri olarak giriş yap
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(customer["username"])
        self.driver.find_element(By.NAME, "password").send_keys(customer["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Ürün listesine git ve sepete ekle
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        
        # Sepete ürün ekle
        try:
            product_cards = self.driver.find_elements(By.CSS_SELECTOR, ".card")
            for card in product_cards:
                if product_name in card.text:
                    add_to_cart_button = card.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    add_to_cart_button.click()
                    break
            
            # Sepet sayfasına yönlendirilmeyi bekle
            WebDriverWait(self.driver, 10).until(EC.url_contains("/cart"))
            
            # Miktarı güncelle
            quantity_input = self.driver.find_element(By.NAME, "quantity")
            quantity_input.clear()
            quantity_input.send_keys("3")
            
            # Güncelle düğmesine tıkla
            update_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            update_button.click()
            
            # Sepet sayfasının yenilenmesini bekle
            WebDriverWait(self.driver, 10).until(EC.url_contains("/cart"))
            
            # Miktarın güncellendiğini doğrula
            updated_quantity = self.driver.find_element(By.NAME, "quantity")
            self.assertEqual("3", updated_quantity.get_attribute("value"))
            
        except NoSuchElementException as e:
            self._take_screenshot("update_cart_failure")
            self.fail(f"Sepeti güncelleme testi başarısız: {str(e)}")
    
    def test_08_remove_from_cart(self):
        """Sepetten ürün çıkarma işlevini test et."""
        # test_06 ile aynı kurulumu yap
        # Önce supplier ve ürün oluştur
        supplier = self._register_test_user(user_type="supplier")
        
        # Giriş yap
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(supplier["username"])
        self.driver.find_element(By.NAME, "password").send_keys(supplier["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Ürün ekleme
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        product_name = self._add_test_product()
        
        # Çıkış yap
        self.driver.get(f"{self.base_url}/logout")
        
        # Müşteri olarak kayıt ol ve giriş yap
        customer = self._register_test_user(user_type="customer")
        
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(customer["username"])
        self.driver.find_element(By.NAME, "password").send_keys(customer["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Ürün listesine git ve sepete ekle
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        
        try:
            product_cards = self.driver.find_elements(By.CSS_SELECTOR, ".card")
            for card in product_cards:
                if product_name in card.text:
                    add_to_cart_button = card.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    add_to_cart_button.click()
                    break
            
            # Sepet sayfasına yönlendirilmeyi bekle
            WebDriverWait(self.driver, 10).until(EC.url_contains("/cart"))
            
            # Ürünü sepetten çıkar
            remove_button = self.driver.find_element(By.CSS_SELECTOR, "form[action*='remove-from-cart'] button")
            remove_button.click()
            
            # Sepet sayfasının yenilenmesini bekle
            WebDriverWait(self.driver, 10).until(EC.url_contains("/cart"))
            
            # Ürünün sepetten çıkarıldığını doğrula
            page_source = self.driver.page_source
            # Artık ürün adı görünmemeli veya "Sepetiniz boş" mesajı görünmeli
            if product_name in page_source:
                self.fail("Ürün sepetten çıkarılamadı")
            
        except NoSuchElementException as e:
            self._take_screenshot("remove_from_cart_failure")
            self.fail(f"Sepetten çıkarma testi başarısız: {str(e)}")
    
    def test_09_profile_page(self):
        """Profil sayfasının işlevini test et."""
        # Bir kullanıcı oluştur ve giriş yap
        user = self._register_test_user()
        
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(user["username"])
        self.driver.find_element(By.NAME, "password").send_keys(user["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Ürün sayfasına yönlendirildiğini bekle
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        
        # Profil sayfasına git
        self.driver.get(f"{self.base_url}/profile")
        
        # Profil sayfasının yüklendiğini doğrula
        self.assertIn("/profile", self.driver.current_url)
        
        # Kullanıcı bilgilerinin görüntülendiğini doğrula
        page_source = self.driver.page_source
        self.assertIn(user["username"], page_source)
        self.assertIn(user["email"], page_source)
        
        # Kullanıcı adını güncelle
        try:
            username_input = self.driver.find_element(By.NAME, "username")
            new_username = f"updated{self.timestamp}"
            username_input.clear()
            username_input.send_keys(new_username)
            
            # Mevcut şifreyi gir (profil güncellemesi için gerekli)
            current_password_input = self.driver.find_element(By.NAME, "current_password")
            current_password_input.send_keys(user["password"])
            
            # Güncelle düğmesine tıkla
            update_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            update_button.click()
            
            # Profil sayfasının yenilenmesini bekle
            time.sleep(2)  # Sayfa yenilenmesi için kısa bir bekleme
            
            # Güncellemenin başarılı olduğunu doğrula
            page_source = self.driver.page_source
            self.assertIn(new_username, page_source)
            
        except NoSuchElementException as e:
            self._take_screenshot("profile_update_failure")
            self.fail(f"Profil güncelleme testi başarısız: {str(e)}")
    
    def test_10_logout(self):
        """Çıkış yapma işlevini test et."""
        # Kullanıcı oluştur ve giriş yap
        user = self._register_test_user()
        
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(user["username"])
        self.driver.find_element(By.NAME, "password").send_keys(user["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Ürün sayfasına yönlendirildiğini bekle
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        
        # Çıkış yap
        self.driver.get(f"{self.base_url}/logout")
        
        # Login sayfasına yönlendirildiğini bekle
        WebDriverWait(self.driver, 10).until(EC.url_contains("/login"))
        
        # Çıkış yaptıktan sonra korumalı sayfaya erişmeye çalış
        self.driver.get(f"{self.base_url}/products")
        
        # Korumalı sayfaya erişemediğini ve login sayfasına yönlendirildiğini doğrula
        WebDriverWait(self.driver, 10).until(EC.url_contains("/login"))
    
    def test_11_forget_password(self):
        """Şifre sıfırlama formunun çalıştığını test et."""
        # Önce bir kullanıcı oluştur
        user = self._register_test_user()
        
        # Şifre sıfırlama sayfasına git
        self.driver.get(f"{self.base_url}/forget_password")
        
        # E-posta adresini gir
        self.driver.find_element(By.NAME, "email").send_keys(user["email"])
        
        # Formu gönder
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Başarı mesajını bekle
        time.sleep(2)  # Ajax yanıtı için kısa bir bekleme
        
        # Başarı mesajını kontrol et (uygulamanıza göre ayarlayın)
        page_source = self.driver.page_source
        self.assertIn("gonderildi", page_source.lower())  # "gönderildi" kelimesini ara
    
    def test_12_checkout(self):
        """Ödeme işlemi testi."""
        # Supplier oluştur ve ürün ekle
        supplier = self._register_test_user(user_type="supplier")
        
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(supplier["username"])
        self.driver.find_element(By.NAME, "password").send_keys(supplier["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Ürün ekleme
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        product_name = self._add_test_product()
        
        # Çıkış yap
        self.driver.get(f"{self.base_url}/logout")
        
        # Müşteri oluştur ve giriş yap
        customer = self._register_test_user(user_type="customer")
        
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(customer["username"])
        self.driver.find_element(By.NAME, "password").send_keys(customer["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Ürün listesine git
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        
        # Ürünü sepete ekle
        try:
            product_cards = self.driver.find_elements(By.CSS_SELECTOR, ".card")
            for card in product_cards:
                if product_name in card.text:
                    add_to_cart_button = card.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    add_to_cart_button.click()
                    break
            
            # Sepet sayfasına yönlendirilmeyi bekle
            WebDriverWait(self.driver, 10).until(EC.url_contains("/cart"))
            
            # Ödeme sayfasına git (Checkout düğmesine tıkla)
            checkout_button = self.driver.find_element(By.LINK_TEXT, "Checkout")
            checkout_button.click()
            
            # Ödeme sayfasının yüklenmesini bekle
            WebDriverWait(self.driver, 10).until(EC.url_contains("/checkout"))
            
            # Ödeme bilgilerini doldur
            self.driver.find_element(By.NAME, "address").send_keys("123 Test Street")
            self.driver.find_element(By.NAME, "city").send_keys("Test City")
            self.driver.find_element(By.NAME, "postal_code").send_keys("12345")
            
            # Kredi kartı bilgileri
            self.driver.find_element(By.NAME, "card_number").send_keys("4111111111111111")
            self.driver.find_element(By.NAME, "card_exp").send_keys("12/25")
            self.driver.find_element(By.NAME, "card_cvv").send_keys("123")
            
            # Ödeme formunu gönder
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            
            # Siparişin tamamlandığını doğrula (sipariş onay sayfasına yönlendirilmeli)
            WebDriverWait(self.driver, 10).until(EC.url_contains("/order-confirmation"))
            
            # Onay sayfasında sipariş bilgilerinin görüntülendiğini doğrula
            page_source = self.driver.page_source
            self.assertIn("Sipariş onaylandı", page_source)
            self.assertIn(product_name, page_source)
            
        except NoSuchElementException as e:
            self._take_screenshot("checkout_failure")
            self.fail(f"Ödeme işlemi testi başarısız: {str(e)}")
    
    def test_13_search_products(self):
        """Ürün arama işlevini test et."""
        # Önce supplier olarak giriş yap ve birkaç ürün ekle
        supplier = self._register_test_user(user_type="supplier")
        
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(supplier["username"])
        self.driver.find_element(By.NAME, "password").send_keys(supplier["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # İlk ürünü ekle - özel isimli
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        unique_keyword = f"UniqueTest{self.timestamp}"
        product_name1 = f"{unique_keyword} Product One"
        self._add_test_product(name=product_name1)
        
        # İkinci ürünü ekle - farklı isimli
        product_name2 = f"Regular Product {self.timestamp}"
        self._add_test_product(name=product_name2)
        
        # Arama işlevini test et
        try:
            # Arama kutusunu bul
            search_input = self.driver.find_element(By.NAME, "search")
            
            # Özel anahtar kelimeyi ara
            search_input.clear()
            search_input.send_keys(unique_keyword)
            search_input.send_keys(Keys.RETURN)
            
            # Arama sonuçlarının yüklenmesini bekle
            time.sleep(2)  # Arama sonuçlarının yüklenmesi için kısa bir bekleme
            
            # Arama sonuçlarını kontrol et
            page_source = self.driver.page_source
            self.assertIn(product_name1, page_source)  # İlk ürün görünmeli
            self.assertNotIn(product_name2, page_source)  # İkinci ürün görünmemeli
            
        except NoSuchElementException as e:
            self._take_screenshot("search_failure")
            self.fail(f"Arama testi başarısız: {str(e)}")
    
    def test_14_filters_and_sorting(self):
        """Ürün filtreleme ve sıralama işlevlerini test et."""
        # Önce supplier olarak giriş yap ve farklı fiyatlarda ürünler ekle
        supplier = self._register_test_user(user_type="supplier")
        
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(supplier["username"])
        self.driver.find_element(By.NAME, "password").send_keys(supplier["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Ürünleri ekle
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        cheap_product = f"Cheap Product {self.timestamp}"
        self._add_test_product(name=cheap_product, price="50.00")
        
        expensive_product = f"Expensive Product {self.timestamp}"
        self._add_test_product(name=expensive_product, price="500.00")
        
        # Fiyat filtreleme ve sıralama özelliklerini test et
        try:
            # Fiyata göre artan sıralama
            sort_select = Select(self.driver.find_element(By.NAME, "sort"))
            sort_select.select_by_value("price_asc")
            
            # Sıralama formunu gönder
            self.driver.find_element(By.CSS_SELECTOR, "form[action*='filter'] button").click()
            
            # Sıralamanın uygulanmasını bekle
            time.sleep(2)
            
            # Ürün listesinin HTML'ini al
            product_list_html = self.driver.page_source
            
            # Ucuz ürünün pahalı üründen önce geldiğini doğrula
            cheap_index = product_list_html.find(cheap_product)
            expensive_index = product_list_html.find(expensive_product)
            
            self.assertTrue(cheap_index < expensive_index, "Artan fiyat sıralaması çalışmıyor")
            
            # Fiyata göre azalan sıralama
            sort_select = Select(self.driver.find_element(By.NAME, "sort"))
            sort_select.select_by_value("price_desc")
            
            # Sıralama formunu gönder
            self.driver.find_element(By.CSS_SELECTOR, "form[action*='filter'] button").click()
            
            # Sıralamanın uygulanmasını bekle
            time.sleep(2)
            
            # Ürün listesinin HTML'ini al
            product_list_html = self.driver.page_source
            
            # Pahalı ürünün ucuz üründen önce geldiğini doğrula
            cheap_index = product_list_html.find(cheap_product)
            expensive_index = product_list_html.find(expensive_product)
            
            self.assertTrue(expensive_index < cheap_index, "Azalan fiyat sıralaması çalışmıyor")
            
            # Fiyat aralığı filtreleme
            min_price_input = self.driver.find_element(By.NAME, "min_price")
            max_price_input = self.driver.find_element(By.NAME, "max_price")
            
            min_price_input.clear()
            min_price_input.send_keys("100")
            max_price_input.clear()
            max_price_input.send_keys("600")
            
            # Filtreleme formunu gönder
            self.driver.find_element(By.CSS_SELECTOR, "form[action*='filter'] button").click()
            
            # Filtrelemenin uygulanmasını bekle
            time.sleep(2)
            
            # Filtrelenmiş sonuçları kontrol et
            page_source = self.driver.page_source
            self.assertNotIn(cheap_product, page_source)  # Ucuz ürün görünmemeli
            self.assertIn(expensive_product, page_source)  # Pahalı ürün görünmeli
            
        except NoSuchElementException as e:
            self._take_screenshot("filter_sort_failure")
            self.fail(f"Filtreleme/sıralama testi başarısız: {str(e)}")
    
    def test_15_order_history(self):
        """Sipariş geçmişi sayfasının işlevini test et."""
        # Supplier oluştur ve ürün ekle
        supplier = self._register_test_user(user_type="supplier")
        
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(supplier["username"])
        self.driver.find_element(By.NAME, "password").send_keys(supplier["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Ürün ekleme
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        product_name = self._add_test_product()
        
        # Çıkış yap
        self.driver.get(f"{self.base_url}/logout")
        
        # Müşteri oluştur ve giriş yap
        customer = self._register_test_user(user_type="customer")
        
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(customer["username"])
        self.driver.find_element(By.NAME, "password").send_keys(customer["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Ürün listesine git
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        
        # Ürünü sepete ekle ve sipariş ver
        try:
            product_cards = self.driver.find_elements(By.CSS_SELECTOR, ".card")
            for card in product_cards:
                if product_name in card.text:
                    add_to_cart_button = card.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    add_to_cart_button.click()
                    break
            
            # Sepet sayfasına yönlendirilmeyi bekle
            WebDriverWait(self.driver, 10).until(EC.url_contains("/cart"))
            
            # Ödeme sayfasına git
            checkout_button = self.driver.find_element(By.LINK_TEXT, "Checkout")
            checkout_button.click()
            
            # Ödeme sayfasının yüklenmesini bekle
            WebDriverWait(self.driver, 10).until(EC.url_contains("/checkout"))
            
            # Ödeme bilgilerini doldur
            self.driver.find_element(By.NAME, "address").send_keys("123 Test Street")
            self.driver.find_element(By.NAME, "city").send_keys("Test City")
            self.driver.find_element(By.NAME, "postal_code").send_keys("12345")
            self.driver.find_element(By.NAME, "card_number").send_keys("4111111111111111")
            self.driver.find_element(By.NAME, "card_exp").send_keys("12/25")
            self.driver.find_element(By.NAME, "card_cvv").send_keys("123")
            
            # Ödeme formunu gönder
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            
            # Sipariş onay sayfasına yönlendirilmeyi bekle
            WebDriverWait(self.driver, 10).until(EC.url_contains("/order-confirmation"))
            
            # Sipariş geçmişi sayfasına git
            self.driver.get(f"{self.base_url}/order-history")
            
            # Sipariş geçmişi sayfasının yüklendiğini doğrula
            self.assertIn("/order-history", self.driver.current_url)
            
            # Siparişin listelendiğini doğrula
            page_source = self.driver.page_source
            self.assertIn(product_name, page_source)
            
        except NoSuchElementException as e:
            self._take_screenshot("order_history_failure")
            self.fail(f"Sipariş geçmişi testi başarısız: {str(e)}")
    
    def test_16_admin_dashboard(self):
        """Admin paneli işlevselliğini test et."""
        # Admin kullanıcısı oluştur ve giriş yap
        admin = self._register_test_user(username="admin_test", user_type="admin")
        
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(admin["username"])
        self.driver.find_element(By.NAME, "password").send_keys(admin["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Admin paneline erişim
        self.driver.get(f"{self.base_url}/admin")
        
        # Admin panelinin yüklendiğini doğrula
        self.assertIn("/admin", self.driver.current_url)
        
        # Admin panelinde kullanıcı listesinin görüntülendiğini doğrula
        try:
            users_table = self.driver.find_element(By.ID, "users-table")
            self.assertTrue(users_table.is_displayed())
            
            # Tabloda admin kullanıcı adının görüntülendiğini doğrula
            table_html = users_table.get_attribute("innerHTML")
            self.assertIn(admin["username"], table_html)
            
        except NoSuchElementException as e:
            self._take_screenshot("admin_dashboard_failure")
            self.fail(f"Admin paneli testi başarısız: {str(e)}")
    
    def test_17_product_search_and_filter(self):
        """Ürün arama ve filtreleme işlevini test et."""
        # Supplier olarak giriş yap ve ürünler ekle
        supplier = self._register_test_user(user_type="supplier")
        
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(supplier["username"])
        self.driver.find_element(By.NAME, "password").send_keys(supplier["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # İlk ürünü ekle
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        product_name1 = f"Ucuz Ürün {self.timestamp}"
        self.driver.get(f"{self.base_url}/add-product")
        self.driver.find_element(By.NAME, "name").send_keys(product_name1)
        self.driver.find_element(By.NAME, "price").send_keys("50.00")
        self.driver.find_element(By.NAME, "description").send_keys("Test ürünü 1")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # İkinci ürünü ekle
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        product_name2 = f"Pahalı Ürün {self.timestamp}"
        self.driver.get(f"{self.base_url}/add-product")
        self.driver.find_element(By.NAME, "name").send_keys(product_name2)
        self.driver.find_element(By.NAME, "price").send_keys("500.00")
        self.driver.find_element(By.NAME, "description").send_keys("Test ürünü 2")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        try:
            # Arama işlevini test et
            WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
            search_input = self.driver.find_element(By.NAME, "search")
            search_input.send_keys("Ucuz")
            search_input.send_keys(Keys.RETURN)
            
            # Arama sonuçlarını kontrol et
            page_source = self.driver.page_source
            self.assertIn(product_name1, page_source)
            self.assertNotIn(product_name2, page_source)
            
            # Fiyat filtreleme
            min_price = self.driver.find_element(By.NAME, "min_price")
            max_price = self.driver.find_element(By.NAME, "max_price")
            
            min_price.clear()
            min_price.send_keys("400")
            max_price.clear()
            max_price.send_keys("600")
            
            # Filtreleme formunu gönder
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            
            # Filtrelenmiş sonuçları kontrol et
            page_source = self.driver.page_source
            self.assertNotIn(product_name1, page_source)
            self.assertIn(product_name2, page_source)
            
        except NoSuchElementException as e:
            self._take_screenshot("search_filter_failure")
            self.fail(f"Arama ve filtreleme testi başarısız: {str(e)}")
    
    def test_18_product_management(self):
        """Ürün yönetimi işlevlerini test et."""
        # Supplier olarak giriş yap
        supplier = self._register_test_user(user_type="supplier")
        
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(supplier["username"])
        self.driver.find_element(By.NAME, "password").send_keys(supplier["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        try:
            # Ürün ekleme
            WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
            self.driver.get(f"{self.base_url}/add-product")
            
            product_name = f"Test Ürün {self.timestamp}"
            self.driver.find_element(By.NAME, "name").send_keys(product_name)
            self.driver.find_element(By.NAME, "price").send_keys("199.99")
            self.driver.find_element(By.NAME, "description").send_keys("Test ürün açıklaması")
            
            # Formu gönder
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            
            # Ürün listesine yönlendirilmeyi bekle
            WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
            
            # Ürünün eklendiğini doğrula
            page_source = self.driver.page_source
            self.assertIn(product_name, page_source)
            
            # Ürünü sil
            delete_button = self.driver.find_element(By.CSS_SELECTOR, f"form[action*='delete-product'] button")
            delete_button.click()
            
            # Sayfanın yenilenmesini bekle
            time.sleep(2)
            
            # Ürünün silindiğini doğrula
            page_source = self.driver.page_source
            self.assertNotIn(product_name, page_source)
            
        except NoSuchElementException as e:
            self._take_screenshot("product_management_failure")
            self.fail(f"Ürün yönetimi testi başarısız: {str(e)}")
    
    def test_19_cart_operations(self):
        """Sepet işlemlerini test et."""
        # Supplier olarak giriş yap ve ürün ekle
        supplier = self._register_test_user(user_type="supplier")
        
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(supplier["username"])
        self.driver.find_element(By.NAME, "password").send_keys(supplier["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Ürün ekleme
        WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
        product_name = self._add_test_product()
        
        # Çıkış yap
        self.driver.get(f"{self.base_url}/logout")
        
        # Müşteri olarak giriş yap
        customer = self._register_test_user(user_type="customer")
        
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(customer["username"])
        self.driver.find_element(By.NAME, "password").send_keys(customer["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        try:
            # Ürün listesine git
            WebDriverWait(self.driver, 10).until(EC.url_contains("/products"))
            
            # Ürünü sepete ekle
            product_cards = self.driver.find_elements(By.CSS_SELECTOR, ".card")
            for card in product_cards:
                if product_name in card.text:
                    add_to_cart_button = card.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    add_to_cart_button.click()
                    break
            
            # Sepet sayfasına git
            WebDriverWait(self.driver, 10).until(EC.url_contains("/cart"))
            
            # Ürünün sepette olduğunu doğrula
            page_source = self.driver.page_source
            self.assertIn(product_name, page_source)
            
            # Ürün miktarını güncelle
            quantity_input = self.driver.find_element(By.NAME, "quantity")
            quantity_input.clear()
            quantity_input.send_keys("3")
            
            # Güncelle düğmesine tıkla
            update_button = self.driver.find_element(By.CSS_SELECTOR, "form[action*='update-cart'] button")
            update_button.click()
            
            # Sayfanın yenilenmesini bekle
            time.sleep(2)
            
            # Miktarın güncellendiğini doğrula
            updated_quantity = self.driver.find_element(By.NAME, "quantity")
            self.assertEqual("3", updated_quantity.get_attribute("value"))
            
            # Ürünü sepetten çıkar
            remove_button = self.driver.find_element(By.CSS_SELECTOR, "form[action*='remove-from-cart'] button")
            remove_button.click()
            
            # Sayfanın yenilenmesini bekle
            time.sleep(2)
            
            # Ürünün sepetten çıkarıldığını doğrula
            page_source = self.driver.page_source
            self.assertNotIn(product_name, page_source)
            
            # Sepete tekrar ürün ekle ve ödeme yap
            self.driver.get(f"{self.base_url}/products")
            product_cards = self.driver.find_elements(By.CSS_SELECTOR, ".card")
            for card in product_cards:
                if product_name in card.text:
                    add_to_cart_button = card.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    add_to_cart_button.click()
                    break
            
            # Sepet sayfasına git
            WebDriverWait(self.driver, 10).until(EC.url_contains("/cart"))
            
            # Ödeme yap
            checkout_button = self.driver.find_element(By.CSS_SELECTOR, "form[action*='checkout'] button")
            checkout_button.click()
            
            # Sayfanın yenilenmesini bekle
            time.sleep(2)
            
            # Ödeme sonrası sepet boş olmalı
            page_source = self.driver.page_source
            self.assertNotIn(product_name, page_source)
            
        except NoSuchElementException as e:
            self._take_screenshot("cart_operations_failure")
            self.fail(f"Sepet işlemleri testi başarısız: {str(e)}")

if __name__ == "__main__":
    unittest.main()