import rumps
import threading
import time
import logging
from datetime import datetime, timedelta
from utils import calculate_remaining_time

class KekaTimerApp(rumps.App):
    def __init__(self, scraper):
        super(KekaTimerApp, self).__init__("Keka: Loading...")
        self.scraper = scraper
        self.clock_in_time = None
        self.work_hours = 9
        
        # Menu Items
        self.refresh_button = rumps.MenuItem("Refresh", callback=self.refresh_data)
        self.menu = [
            self.refresh_button,
            rumps.separator,
            # "Quit" is added automatically by rumps
        ]
        
        # Start timer
        self.timer = rumps.Timer(self.update_timer, 1)
        self.timer.start()
        
        # Initial data fetch
        threading.Thread(target=self.initial_fetch, daemon=True).start()

    def initial_fetch(self):
        logging.info("Fetching initial data...")
        time.sleep(1)
        self.clock_in_time = self.scraper.get_clock_in_time()
        if self.clock_in_time:
            logging.info(f"Initial fetch success: {self.clock_in_time}")
        else:
            logging.info("Initial fetch: Not clocked in or failed.")

    def refresh_data(self, _):
        logging.info("Manual refresh triggered.")
        self.title = "Keka: Refreshing..."
        threading.Thread(target=self.do_refresh, daemon=True).start()

    def do_refresh(self):
        new_time = self.scraper.get_clock_in_time()
        if new_time:
            self.clock_in_time = new_time
            logging.info(f"Refresh success: {new_time}")
        else:
            logging.info("Refresh: Not clocked in or failed.")
            # We don't clear clock_in_time if refresh fails, unless we want to reset.
            # But if user logged out, maybe we should?
            # For now, let's keep the old time if refresh fails, or set to None if we confirm logout.
            # Scraper returns None if not found.
            self.clock_in_time = None

    def update_timer(self, _):
        if self.clock_in_time:
            remaining = calculate_remaining_time(self.clock_in_time, self.work_hours)
            
            if remaining.total_seconds() > 0:
                # Format: HH:MM:SS
                total_seconds = int(remaining.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
                self.title = f"Keka: {time_str}"
            else:
                # Overtime
                overtime = abs(remaining)
                total_seconds = int(overtime.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                time_str = f"+ {hours:02}:{minutes:02}:{seconds:02}"
                self.title = f"Keka: {time_str}" # Maybe add color or icon if possible? Rumps is limited.
        else:
            self.title = "Keka: Not Clocked In"
