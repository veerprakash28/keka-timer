import threading
import time
import logging
import os
from keka_scraper import KekaScraper
from timer_gui import FloatingTimerApp

# Setup logging
log_file = os.path.expanduser("~/keka_timer.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def main():
    logging.info("Starting Keka Timer App...")
    print("Starting Keka Timer App...") # Keep print for terminal users
    
    # Initialize Scraper
    scraper = KekaScraper()
    
    # Launch Browser
    logging.info("Launching browser...")
    print("Launching browser...")
    scraper.launch_browser()
    
    # Wait for Login
    if scraper.wait_for_login():
        logging.info("Login successful!")
        print("Login successful!")
        
        # Minimize browser so user sees the app
        scraper.minimize_window()
        
        # Launch Menu Bar App
        logging.info("Launching Menu Bar App...")
        print("Launching Menu Bar App...")
        
        from menubar_app import KekaTimerApp
        app = KekaTimerApp(scraper)
        app.run()
        
    else:
        logging.error("Login failed or timed out.")
        print("Login failed or timed out.")
        scraper.close_browser()

if __name__ == "__main__":
    main()
