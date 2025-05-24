import os
import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
from datetime import datetime
from db_utils import cleanup_test_users
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


BASE_URL = "http://localhost:5000"

logger = logging.getLogger("ui_tests")
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("test_ui.log", mode='a', encoding='utf-8')
file_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
   
def save_screenshot(browser, test_name):
    screenshots_dir = "screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{screenshots_dir}/{test_name}_{timestamp}.png"
    browser.save_screenshot(filename)
    logger.info(f"Ekran görüntüsü kaydedildi: {filename}")
    
@pytest.fixture(scope="session", autouse=True)
def cleanup_after_tests():
    yield
    cleanup_test_users()

def test_logout(browser):
    if "/products" not in browser.current_url:
        browser.get("http://localhost:5000/products")
    logger.info(f"Mevcut URL (Logout test öncesi): {browser.current_url}")
    try:
        logout_button = WebDriverWait(browser, 5).until(
            EC.element_to_be_clickable((By.ID, "logout-button"))
        )
        logout_button.click()
        logging.info("Logout butonuna tıklandı.")
        time.sleep(1)

        current_url = browser.current_url
        logging.info(f"Çıkış sonrası yönlendirilen URL: {current_url}")
        if "/login" not in current_url:
            logging.error("Logout sonrası beklenen URL'ye yönlendirilmedi.")
            save_screenshot(browser, "logout_test_failed")

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        save_screenshot(browser,f"logout_test_{timestamp}")

    except Exception as e:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        browser.save_screenshot(f"screenshots/logout_exception_{timestamp}.png")
        logging.error(f"Logout testinde hata oluştu: {str(e)}")
        raise




