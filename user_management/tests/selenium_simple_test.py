import unittest
import sys
from pathlib import Path
import os
import time
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Flask uygulamasını import et
sys.path.append(str(Path(__file__).parent.parent))
from app import app

class TestFlaskAppSimple(unittest.TestCase):
    """Basit Selenium testleri"""
    
    @classmethod
    def setUpClass(cls):
        # Flask uygulamasını başlat
        def run_flask():
            app.run(port=5000)
        
        cls.flask_thread = threading.Thread(target=run_flask, daemon=True)
        cls.flask_thread.start()
        time.sleep(1)  # Uygulamanın başlaması için bekle
        
        try:
            # Chrome opsiyonlarını ayarla
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            # WebDriver'ı başlat
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.base_url = "http://localhost:5000"
        except Exception as e:
            print(f"WebDriver başlatılamadı: {str(e)}")
            sys.exit(1)
    
    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        # Flask thread'i sonlandırma işlemleri burada yapılabilir
    
    def test_homepage_title(self):
        """Ana sayfa başlığını test et"""
        self.driver.get(self.base_url)
        self.assertIn("Login", self.driver.title)

if __name__ == "__main__":
    unittest.main() 