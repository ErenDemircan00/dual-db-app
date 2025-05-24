import os
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
from datetime import datetime
import time
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

def test_signup_success(browser):

    browser.get(f"{BASE_URL}/signup")

    browser.find_element(By.NAME, "username").send_keys("testuser_ui_supplier")
    browser.find_element(By.NAME, "email").send_keys("testuser_ui_supplier@example.com")
    browser.find_element(By.NAME, "password").send_keys("testpass123")

    browser.find_element(By.CSS_SELECTOR, "input[name='user_type'][value='supplier']").click()
    browser.find_element(By.TAG_NAME, "button").click()

    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    page_source = browser.page_source

    if "error" in page_source or "kayıt başarısız" in page_source:
        logger.error("Signup success test failed: hata mesajı bulundu.")
        save_screenshot(browser, "test_signup_success")
    elif "Başarıyla kayıt oldunuz" in page_source or "Hoş geldiniz" in page_source:
        logger.info("Signup success test passed.")
    else:
        logger.error("Signup success test failed: başarı veya hata mesajı bulunamadı.")
        save_screenshot(browser, "test_signup_success")


def test_signup_missing_fields(browser):
    browser.get(f"{BASE_URL}/signup")

    browser.find_element(By.NAME, "email").send_keys("eksik@example.com")

    browser.find_element(By.TAG_NAME, "button").click()

    try:
        WebDriverWait(browser, 5).until(
            EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Bu alan zorunludur")
        )
        logger.info("Signup missing fields test passed: zorunlu alan uyarısı gösteriliyor.")
    except:
        logger.error("Signup missing fields test failed: zorunlu alan uyarısı yok.")
        save_screenshot(browser, "test_signup_missing_fields")

def test_signup_duplicate_email(browser):
    browser.get(f"{BASE_URL}/signup")

    browser.find_element(By.NAME, "username").send_keys("testuser_ui_supplier")
    browser.find_element(By.NAME, "email").send_keys("testuser_ui_supplier@example.com")
    browser.find_element(By.NAME, "password").send_keys("testpass123")
    browser.find_element(By.CSS_SELECTOR, "input[name='user_type'][value='supplier']").click()
    browser.find_element(By.TAG_NAME, "button").click()

    try:
        WebDriverWait(browser, 5).until(
            EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Bu email zaten kayıtlı")
        )
        logger.info("Signup duplicate email test passed: duplicate email uyarısı gösteriliyor.")
    except:
        logger.error("Signup duplicate email test failed: duplicate email uyarısı yok.")
        save_screenshot(browser, "test_signup_duplicate_email")
        
def test_login_success(browser):
    browser.get(f"{BASE_URL}/login")
    browser.find_element(By.NAME, "username").send_keys("testuser_ui_supplier")
    browser.find_element(By.NAME, "password").send_keys("testpass123")
    browser.find_element(By.TAG_NAME, "button").click()
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    
    if "/products" in browser.current_url or "Hoşgeldiniz" in browser.page_source:
        logger.info("Login test passed.")
        save_screenshot(browser, "test_login_success.png")
    else:
        logger.error("Login test failed: Giriş başarısız veya yönlendirme yok.")
        save_screenshot(browser,"test_login_fail.png")




