import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class KekaScraper:
    def __init__(self, url="https://shipthis.keka.com"):
        self.url = url
        self.driver = None

    def launch_browser(self):
        """Launches the Chrome browser."""
        options = Options()
        # options.add_argument("--headless") # Keep headful for manual login
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # This keeps the browser open even if the script finishes (useful for debugging, 
        # but we'll manage the driver lifecycle explicitly)
        options.add_experimental_option("detach", True) 

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.driver.get(self.url)

    def wait_for_login(self):
        """
        Waits for the user to log in manually.
        Detects login by checking for 'dashboard' in the URL or presence of dashboard elements.
        """
        import logging
        logging.info("Waiting for user to log in...")
        print("Waiting for user to log in...")
        
        start_time = time.time()
        timeout = 300 # 5 minutes
        
        while time.time() - start_time < timeout:
            try:
                # Check URL first - fastest and most reliable for "dashboard"
                current_url = self.driver.current_url
                if "dashboard" in current_url.lower():
                    logging.info(f"Login detected via URL: {current_url}")
                    return True
                
                # Check for elements as backup
                elements = self.driver.find_elements(By.XPATH, "//span[contains(text(), 'Time Today')] | //div[contains(text(), 'Web Clock-in')]")
                if elements:
                    logging.info("Login detected via DOM elements.")
                    return True
                
                time.sleep(1)
            except Exception as e:
                logging.warning(f"Error checking login status: {e}")
                time.sleep(1)
                
        logging.error("Login timeout.")
        return False

    def get_clock_in_time(self):
        """
        Scrapes the clock-in time from the dashboard.
        Returns a datetime object or None if not found/not clocked in.
        """
        import logging
        try:
            # Navigate to logs for reliable data
            # self.driver.get(f"{self.url}/#/time/attendance/logs") 
            # NOTE: Navigating changes the page, which might confuse the user if they are looking at it.
            # But we minimized it.
            # Let's check if we are already on logs or dashboard.
            
            logging.info("Scraping clock-in time...")
            
            # Use a less intrusive check if possible, or just go to logs.
            # Going to logs is safest for data.
            if "logs" not in self.driver.current_url:
                self.driver.get(f"{self.url}/#/time/attendance/logs")
                time.sleep(2)
            
            # Wait for the table to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            time.sleep(1)

            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            from utils import find_clock_in_time_in_text
            clock_in_time = find_clock_in_time_in_text(body_text)
            
            if clock_in_time:
                logging.info(f"Found clock-in time: {clock_in_time}")
                return clock_in_time
            else:
                logging.info("Could not find clock-in time in logs.")
                # Fallback: Check Dashboard "Actions" card
                self.driver.get(f"{self.url}/#/home/dashboard")
                time.sleep(3)
                body_text = self.driver.find_element(By.TAG_NAME, "body").text
                clock_in_time = find_clock_in_time_in_text(body_text)
                if clock_in_time:
                    logging.info(f"Found clock-in time on dashboard: {clock_in_time}")
                    return clock_in_time
                
                return None

        except Exception as e:
            logging.error(f"Error scraping clock-in time: {e}")
            return None

    def minimize_window(self):
        """Minimizes the browser window."""
        import logging
        if self.driver:
            try:
                self.driver.minimize_window()
            except Exception as e:
                logging.warning(f"Failed to minimize window (ignoring): {e}")

    def close_browser(self):
        if self.driver:
            self.driver.quit()

if __name__ == "__main__":
    # Test the scraper
    scraper = KekaScraper()
    scraper.launch_browser()
    if scraper.wait_for_login():
        print("Logged in!")
        text = scraper.get_clock_in_time()
        print(f"Page text sample: {text[:500]}...") # Print first 500 chars to debug
        # In a real run, we would parse 'text' to find the time.
    # scraper.close_browser()
