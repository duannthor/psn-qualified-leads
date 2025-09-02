import os
from tenacity import retry, wait_fixed, stop_after_attempt
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv


from .db import record_played_game


load_dotenv()


SELENIUM_REMOTE_URL = os.getenv("SELENIUM_REMOTE_URL", "http://selenium:4444")
LOGIN_URL = os.getenv("LOGIN_URL", "https://my.playstation.com/profile")
SUCCESS_SELECTOR = os.getenv("SUCCESS_SELECTOR", "section[aria-label='Games']")


@retry(wait=wait_fixed(2), stop=stop_after_attempt(5))
def make_driver():
    # IMPORTANT: do NOT enable headless when you want to drive it via noVNC (port 7900)
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1366,900")
    # options.add_argument("--headless=new") # leave commented for manual login via noVNC
    return webdriver.Remote(command_executor=SELENIUM_REMOTE_URL, options=options)


def wait_for_manual_login(driver, login_url: str, success_selector: str):
    """
    Navigate to the login URL and wait until the user has manually logged in.
    Blocks until `success_selector` is found in the DOM (up to 10 minutes).
    """
    print(f"Navigate to {login_url} and log in manually (using http://localhost:7900)...")
    driver.get(login_url)


    wait = WebDriverWait(driver, 600) # 10 minutes
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, success_selector)))
    print("Login successful. Proceeding with scraping...")


def scrape_played_games(driver):
    # Ensure user has logged in manually first
    wait_for_manual_login(driver, LOGIN_URL, SUCCESS_SELECTOR)


    # TODO: Navigate to the actual games page and collect titles
    titles = [
        "ELDEN RING",
        "Ghost of Tsushima",
        "Gran Turismo 7",
    ]


for t in titles:
    print(f"Recording: {t}")
    record_played_game(t)


if __name__ == "__main__":
    driver = make_driver()
    try:
        scrape_played_games(driver)
    finally:
        driver.quit()