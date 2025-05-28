import os
import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
from datetime import datetime
import time

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
    

def test_supplier_can_add_product(browser):
    if"/products" not in browser.current_url:
        browser.get(f"{BASE_URL}/products")
        
    logger.info(f"Mevcut URL (Signup test öncesi): {browser.current_url}")
    try:
        add_product_button = WebDriverWait(browser, 5).until(
            EC.element_to_be_clickable((By.ID, "add-product-button"))
        )
        add_product_button.click()
        logger.info("Add product butonuna tıklandı.")
        
        WebDriverWait(browser, 5).until(
            EC.url_contains("/add-product")
        )
        logger.info(f"Yönlendirme sonrası URL: {browser.current_url}")
        
        product_name_input = WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.NAME, "name"))
        )
        product_price_input = browser.find_element(By.NAME, "price")
        product_description_input = browser.find_element(By.NAME, "description")
        product_name_input.send_keys("Test Product")
        product_price_input.send_keys("100")
        product_description_input.send_keys("This is a test product.")
        submit_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        print("Here 10")
        page_source = browser.page_source
        if"/products" not in browser.current_url:
            logger.info("Ürün ekleme testi başarılı.")
            save_screenshot(browser, "test_supplier_can_add_product")
        else:
            logger.error("Ürün ekleme testi başarısız: Başarı mesajı bulunamadı.")
            save_screenshot(browser, "test_supplier_can_add_product_failed")
    except Exception as e:
        logger.error(f"Add product butonuna tıklanamadı: {e}")
        save_screenshot(browser, "test_supplier_can_add_product_error")
        raise e

def test_supplier_can_remove_product(browser):
    if "/products" not in browser.current_url:
        browser.get(f"{BASE_URL}/products")
        
    logger.info(f"Mevcut URL (Remove product test öncesi): {browser.current_url}")
    
    try:
        product_cards = WebDriverWait(browser, 5).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "product-card"))
        )
        
        if len(product_cards) == 0:
            logger.error("Hiç ürün bulunamadı.")
            save_screenshot(browser, "no_products_found")
            return
        
        first_product = product_cards[0]
        remove_button = first_product.find_element(By.CLASS_NAME, "delete-product")
        remove_button.click()
        
        WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        logger.info("Başkasına ait ürün silme testi silinemedi.")
        save_screenshot(browser, "test_supplier_can_remove_product")
    except Exception as e:
        logger.error(f"Ürün silme testinde hata oluştu: {e}")
        save_screenshot(browser, "test_supplier_can_remove_product_error")
        raise e

def test_supplier_can_remove_self_product(browser):
    if "/products" not in browser.current_url:
        browser.get(f"{BASE_URL}/products")
        
    logger.info(f"Mevcut URL (Remove product test öncesi): {browser.current_url}")

    try:
        product_cards = WebDriverWait(browser, 5).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "product-card"))
        )
        if len(product_cards) == 0:
            logger.error("Hiç ürün bulunamadı.")
            save_screenshot(browser, "no_products_found")
            return
        logger.info(f"{len(product_cards)} adet ürün bulundu.")
        logger.info("Ürün silme testi başlatılıyor.")
        
        browser.find_element(By.ID,"search").send_keys("Test Product")
        logger.info("Ürün arama kutusuna 'Test Product' yazıldı.")
        browser.find_element(By.ID, "filter-button").click()
        logger.info("Filtreleme butonuna tıklandı.")
        logger.info("Filtreleme sonrası sayfa yüklendi.")
        logger.info("Ürün kartları tekrar alınıyor.")
        WebDriverWait(browser, 5).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "product-card"))
        )
        logger.info("Ürün kartları alındı.")
        logger.info("Ürün kartları filtreleniyor.")
        product_cards = WebDriverWait(browser, 5).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "product-card"))
        )
        
        first_product = product_cards[0]
        remove_button = first_product.find_element(By.CLASS_NAME, "delete-product")
        remove_button.click()
        logger.info("Ürün silme butonuna tıklandı.")
        
        WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        product_cards = WebDriverWait(browser, 5).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "product-card"))
        )

        filter_cards = [card for card in product_cards if "Test Product" in card.text]
        if len(filter_cards) == 0:
            logger.info("Ürün silme testi başarılı.")
            save_screenshot(browser, "test_supplier_can_remove_self_product")
        else:
            logger.error("Ürün silme testi başarısız: Ürün hala listede.")
            save_screenshot(browser, "test_supplier_can_remove_self_product_failed")
    except Exception as e:
        logger.error(f"Ürün silme testinde hata oluştu: {e}")
        save_screenshot(browser, "test_supplier_can_remove_self_product_error")
        raise e
