import os
import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
from datetime import datetime
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


def test_profile_update(browser):
    if "/products" not in browser.current_url:
        browser.get("http://localhost:5000/products")

    logger.info(f"Mevcut URL (profile test öncesi): {browser.current_url}")

    try:
        profile_btn = WebDriverWait(browser, 5).until(
            EC.element_to_be_clickable((By.ID, "profile-btn"))
        )
        profile_btn.click()
        logger.info("Profil butonuna tıklandı.")

        WebDriverWait(browser, 5).until(
            EC.url_contains("/profile")
        )
        logger.info(f"Yönlendirme sonrası URL: {browser.current_url}")

        username_input = WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        email_input = browser.find_element(By.NAME, "email")

        old_username = username_input.get_attribute("value")
        new_username = old_username + "_test"

        username_input.clear()
        username_input.send_keys(new_username)
        
        save_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        save_button.click()
        logger.info("Profil güncelleme formu submit edildi.")

        WebDriverWait(browser, 5).until(
            EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Profil başarıyla güncellendi")
        )
        logger.info("Profil güncelleme testi başarılı.")
        save_screenshot(browser, "profile_update_success")

    except Exception as e:
        logger.exception(f"Profil güncelleme testinde hata oluştu: {e}")
        save_screenshot(browser, "profile_update_exception")
        
#şifre günclleme testi
