import os
import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
from datetime import datetime

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

def test_add_product_to_cart(browser):
    browser.get("http://localhost:5000/products")

    try:
        WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "product-card"))
        )
        product_cards = browser.find_elements(By.CLASS_NAME, "product-card")

        if len(product_cards) == 0:
            logger.error("Hiç ürün bulunamadı.")
            save_screenshot(browser, "no_products_found")
            return

        logger.info(f"{len(product_cards)} adet ürün bulundu.")
        first_product = product_cards[0]
        add_button = first_product.find_element(By.CLASS_NAME, "add-to-cart")
        add_button.click()

        time.sleep(1) 

        logger.info("Sepete ekleme butonuna tıklandı.")
        save_screenshot(browser, "add_to_cart_clicked")

        browser.get("http://localhost:5000/cart")
        WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        page_source = browser.page_source

        if "Sepetiniz boş" in page_source or "sepet boş" in page_source.lower():
            logger.error("Ürün sepete eklenemedi.")
            save_screenshot(browser, "add_to_cart_failed")
        else:
            logger.info("Ürün başarıyla sepete eklendi.")

    except Exception as e:
        logger.exception(f"Sepete ürün ekleme testinde hata oluştu: {e}")
        save_screenshot(browser, "add_to_cart_error")
        
def test_remove_product_from_cart(browser):
    if "/cart" not in browser.current_url:
        browser.get("http://localhost:5000/cart")
        
    try:
        WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "cart-container"))
        )
        WebDriverWait(browser, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "cart-item"))
        )
        cart_items = browser.find_elements(By.CLASS_NAME, "cart-item")
        if not cart_items:
            logger.warning("Sepet boş, silinecek ürün yok.")
            save_screenshot(browser, "remove_cart_empty")
            return

        logger.info(f"Sepette {len(cart_items)} ürün bulundu. Silme işlemi başlatılıyor.")
        first_item = cart_items[0]
        forms = first_item.find_elements(By.TAG_NAME, "form")

        found = False
        for form in forms:
            action_url = form.get_attribute("action")
            logger.info(f"Form action: {action_url}")
            if action_url and "remove-from-cart" in action_url:
                delete_button = form.find_element(By.CLASS_NAME, "remove-btn")
                delete_button.click()
                found = True
                break

        if not found:
            logger.error("Silme formu bulunamadı.")
            save_screenshot(browser, "remove_form_not_found")
            return

        WebDriverWait(browser, 5).until(EC.staleness_of(first_item))

        WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "cart-container"))
        )
        updated_cart_items = browser.find_elements(By.CLASS_NAME, "cart-item")
        if len(updated_cart_items) < len(cart_items):
            logger.info("Ürün başarıyla sepetten silindi.")
            save_screenshot(browser, "remove_from_cart_success")
        else:
            logger.error("Silme işlemi başarısız.")
            save_screenshot(browser, "remove_from_cart_failed")

    except Exception as e:
        logger.exception(f"Sepetten ürün silme testinde hata oluştu: {e}")
        save_screenshot(browser, "remove_from_cart_exception")

        




