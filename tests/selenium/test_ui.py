"""Selenium end-to-end tests for the ShopLite UI (headless Chrome)."""
import json
import os

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

FLAGS_FILE = os.getenv("FLAGS_FILE_PATH")


def set_flags(flags):
    with open(FLAGS_FILE, "w", encoding="utf-8") as f:
        json.dump(flags, f)


def test_home_page_loads(driver, base_url, shot):
    driver.get(base_url + "/?user=tester")
    assert driver.title == "ShopLite"
    assert driver.find_element(By.ID, "title").text == "ShopLite"
    shot("01_home")


def test_product_list_shows_four_products(driver, base_url):
    driver.get(base_url)
    products = driver.find_elements(By.CSS_SELECTOR, ".product h3")
    assert [p.text for p in products] == ["Laptop Stand", "Wireless Mouse", "USB-C Hub", "Mechanical Keyboard"]


def test_add_to_cart_updates_counter(driver, base_url, shot):
    driver.get(base_url)
    for b in driver.find_elements(By.CSS_SELECTOR, "button.add")[:3]:
        b.click()
    assert driver.find_element(By.ID, "cart-count").text == "3"
    shot("02_cart")


@pytest.mark.parametrize("enabled, version", [(False, "v1"), (True, "v2")])
def test_checkout_follows_feature_flag(driver, base_url, shot, enabled, version):
    set_flags({"new_checkout": enabled, "dark_mode": enabled, "recommendations": {"enabled": True, "rollout": 50}})
    driver.get(base_url + "/?user=tester")
    driver.find_element(By.ID, "checkout-btn").click()
    box = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID, "result")))
    assert box.get_attribute("data-version") == version
    assert ("dark" in driver.find_element(By.TAG_NAME, "body").get_attribute("class")) == enabled
    shot(f"03_checkout_{version}")


def test_recommendation_banner_percentage_rollout(driver, base_url):
    set_flags({"recommendations": {"enabled": True, "rollout": 50}})
    shown = 0
    for i in range(20):
        driver.get(f"{base_url}/?user=visitor{i}")
        shown += len(driver.find_elements(By.ID, "recommend"))
    assert 3 <= shown <= 17, f"banner shown to {shown}/20 users"
