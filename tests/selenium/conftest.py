import os

import pytest
from selenium import webdriver

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
SHOTS = os.getenv("SHOTS_DIR", "shots")


@pytest.fixture
def driver():
    opts = webdriver.ChromeOptions()
    for a in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--window-size=1280,900"):
        opts.add_argument(a)
    d = webdriver.Chrome(options=opts)
    d.implicitly_wait(5)
    yield d
    d.quit()


@pytest.fixture
def base_url():
    return BASE_URL


@pytest.fixture
def shot(driver):
    os.makedirs(SHOTS, exist_ok=True)
    return lambda name: driver.save_screenshot(os.path.join(SHOTS, f"selenium_{name}.png"))
