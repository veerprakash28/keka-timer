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
        Scrapes the clock-in time from the logs page by parsing 'Since Last Login'.
        Returns a datetime object or None if not found/not clocked in.
        """
        import logging
        import re
        from datetime import datetime, timedelta
        
        try:
            logging.info("Scraping clock-in time from logs page...")
            
            # Navigate to logs page (where "Since Last Login" text is located)
            self.driver.get(f"{self.url}/#/me/attendance/logs")
            time.sleep(3)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(1)
            
            # Get page text
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            logging.info("Searching for 'Since Last Login' text...")
            
            # Look for pattern: "0h:1m Since Last Login" or "1h:30m Since Last Login"
            # Pattern matches: Xh:Ym or Xh Ym or X hours Y minutes, etc.
            patterns = [
                r'(\d+)h[:\s]*(\d+)m\s*Since Last Login',
                r'(\d+)\s*h[:\s]*(\d+)\s*m\s*Since Last Login',
                r'(\d+)\s*hours?\s*(\d+)\s*min',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, body_text, re.IGNORECASE)
                if match:
                    hours = int(match.group(1))
                    minutes = int(match.group(2))
                    logging.info(f"Found 'Since Last Login': {hours}h:{minutes}m")
                    
                    # Calculate clock-in time by subtracting from current time
                    now = datetime.now()
                    clock_in_time = now - timedelta(hours=hours, minutes=minutes)
                    
                    logging.info(f"Calculated clock-in time: {clock_in_time}")
                    return clock_in_time
            
            # If no "Since Last Login" found, user is not clocked in
            logging.info("No 'Since Last Login' text found. User may not be clocked in.")
            return None

        except Exception as e:
            logging.error(f"Error scraping clock-in time: {e}")
            return None


    def perform_clock_in(self):
        """Attempts to clock in from dashboard."""
        import logging
        try:
            logging.info("Attempting to Clock In...")
            self.driver.get(f"{self.url}/#/home/dashboard")
            time.sleep(3)
            
            # Look for "Web Clock-in" button in Actions section
            # Use case-insensitive matching since button text might be "Web Clock-In" or "Web Clock-in"
            buttons = self.driver.find_elements(By.XPATH, 
                "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'web clock-in') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'clock-in')]")
            if buttons:
                buttons[0].click()
                logging.info("Clicked 'Web Clock-in' button.")
                time.sleep(2)
                
                # Handle potential confirmation dialog
                confirm_buttons = self.driver.find_elements(By.XPATH, "//button[contains(., 'Confirm') or contains(., 'Clock In')]")
                if confirm_buttons:
                    visible_buttons = [b for b in confirm_buttons if b.is_displayed()]
                    if visible_buttons:
                        visible_buttons[0].click()
                        logging.info("Clicked confirmation button.")
                        time.sleep(2)
                
                logging.info("Clock-in completed.")
                return True
            else:
                logging.warning("Could not find 'Web Clock-in' button.")
                return False
        except Exception as e:
            logging.error(f"Error during Clock In: {e}")
            return False


    def perform_clock_out(self):
        """Attempts to clock out with two-step confirmation."""
        import logging
        try:
            logging.info("Attempting to Clock Out...")
            self.driver.get(f"{self.url}/#/home/dashboard")
            time.sleep(3)
            
            # Look for "Clock-out" button (could be on dashboard or logs page)
            # Use case-insensitive matching
            buttons = self.driver.find_elements(By.XPATH, 
                "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'clock-out') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'web clock-out')]")
            if buttons:
                # First click - shows hours logged
                buttons[0].click()
                logging.info("Clicked 'Clock-out' button (first click - showing hours).")
                time.sleep(2)
                
                # Second click - confirm clock-out
                # Look for confirmation button in modal/dialog
                # Could be "Clock Out", "Confirm", "Yes", or similar
                confirm_buttons = self.driver.find_elements(By.XPATH, 
                    "//button[contains(., 'Clock Out') or contains(., 'Clock-out') or contains(., 'Confirm') or contains(., 'Yes')]")
                
                if confirm_buttons:
                    # Filter for visible buttons (modal buttons)
                    visible_buttons = [b for b in confirm_buttons if b.is_displayed()]
                    if visible_buttons:
                        # Click the confirmation button
                        visible_buttons[0].click()
                        logging.info("Clicked confirmation button (second click - confirming clock-out).")
                        time.sleep(3)
                        
                        # Verify clock-out by checking if button changed or disappeared
                        # After clock-out, the "Clock-out" button should disappear or change to "Clock-in"
                        clock_in_buttons = self.driver.find_elements(By.XPATH, "//button[contains(., 'Clock-in') or contains(., 'Web Clock-in')]")
                        if clock_in_buttons:
                            logging.info("Clock-out confirmed - Clock-in button now visible.")
                            return True
                        else:
                            logging.warning("Clock-out button clicked but could not confirm.")
                            return True  # Still return True since we clicked
                    else:
                        logging.warning("No visible confirmation button found after first click.")
                        return False
                else:
                    logging.warning("No confirmation button found after first click. Clock-out might have failed.")
                    return False
            else:
                logging.warning("Could not find 'Clock-out' button. User may not be clocked in.")
                return False
        except Exception as e:
            logging.error(f"Error during Clock Out: {e}")
            return False


    def perform_logout(self):
        """Attempts to log out."""
        import logging
        try:
            logging.info("Attempting to Log Out...")
            if not self.driver:
                return

            # 1. Try to find and click Logout button directly
            try:
                logout_btns = self.driver.find_elements(By.XPATH, "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'log out')] | //button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'log out')]")
                if logout_btns:
                    for btn in logout_btns:
                        if btn.is_displayed():
                            btn.click()
                            logging.info("Clicked Logout button.")
                            time.sleep(2)
                            return
            except Exception:
                pass

            # 2. Try to click User Profile then Logout
            try:
                # Common selectors for profile dropdown
                profile_selectors = [
                    "//div[contains(@class, 'profile')]",
                    "//img[contains(@class, 'avatar')]",
                    "//div[contains(@class, 'user')]"
                ]
                for selector in profile_selectors:
                    profiles = self.driver.find_elements(By.XPATH, selector)
                    for profile in profiles:
                        if profile.is_displayed():
                            profile.click()
                            time.sleep(1)
                            # Look for logout in dropdown
                            logout_dropdown = self.driver.find_elements(By.XPATH, "//a[contains(., 'Log out')] | //li[contains(., 'Log out')]")
                            if logout_dropdown:
                                logout_dropdown[0].click()
                                logging.info("Clicked Logout in dropdown.")
                                time.sleep(2)
                                return
            except Exception:
                pass

            # 3. Fallback: Delete all cookies
            logging.info("Could not find Logout button, deleting cookies to ensure logout.")
            self.driver.delete_all_cookies()
            
        except Exception as e:
            logging.error(f"Error during Logout: {e}")

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
