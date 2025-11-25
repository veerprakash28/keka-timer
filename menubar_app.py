import rumps
import threading
import time
import logging
import subprocess
from datetime import datetime, timedelta
from utils import calculate_remaining_time

def send_notification(title, subtitle, message):
    """Sends a native macOS notification using AppleScript."""
    try:
        script = f'display notification "{message}" with title "{title}" subtitle "{subtitle}"'
        subprocess.run(["osascript", "-e", script])
    except Exception as e:
        logging.error(f"Failed to send notification: {e}")

class KekaTimerApp(rumps.App):
    def __init__(self, scraper):
        super(KekaTimerApp, self).__init__("Keka: Loading...", quit_button=None)
        self.scraper = scraper
        self.clock_in_time = None
        self.work_hours = 9
        self.notification_shown = False
        self.snooze_until = None
        
        # Menu Items
        self.clock_in_button = rumps.MenuItem("Clock In", callback=self.clock_in)
        self.clock_out_button = rumps.MenuItem("Clock Out", callback=self.clock_out)
        self.refresh_button = rumps.MenuItem("Refresh", callback=self.refresh_data)
        self.exit_button = rumps.MenuItem("Quit", callback=self.quit_app)
        
        self.menu = [
            self.clock_in_button,
            self.clock_out_button,
            rumps.separator,
            self.refresh_button,
            rumps.separator,
            self.exit_button
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

    def clock_in(self, _):
        logging.info("Manual Clock In triggered.")
        self.title = "Keka: Clocking In..."
        threading.Thread(target=self.do_clock_in, daemon=True).start()

    def do_clock_in(self):
        success = self.scraper.perform_clock_in()
        if success:
            send_notification("Keka Timer", "Clock In", "Clock In attempt finished. Refreshing...")
            self.do_refresh()
        else:
            send_notification("Keka Timer", "Clock In Failed", "Could not find button or error occurred.")
            self.title = "Keka: Error"

    def clock_out(self, _):
        logging.info("Manual Clock Out triggered.")
        self.title = "Keka: Clocking Out..."
        threading.Thread(target=self.do_clock_out, daemon=True).start()

    def do_clock_out(self):
        success = self.scraper.perform_clock_out()
        if success:
            send_notification("Keka Timer", "Clock Out", "Clock Out attempt finished. Refreshing...")
            self.do_refresh()
        else:
            send_notification("Keka Timer", "Clock Out Failed", "Could not find button or error occurred.")
            self.title = "Keka: Error"

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

    def quit_app(self, _):
        logging.info("Quitting app and closing browser...")
        if self.scraper:
            self.scraper.perform_logout()
            self.scraper.close_browser()
        rumps.quit_application()

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
                # Overtime - check if we should show notification
                if not self.notification_shown:
                    # Check if snooze period has passed
                    if self.snooze_until is None or datetime.now() >= self.snooze_until:
                        threading.Thread(target=self.show_completion_dialog, daemon=True).start()
                        self.notification_shown = True
                
                overtime = abs(remaining)
                total_seconds = int(overtime.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                time_str = f"+ {hours:02}:{minutes:02}:{seconds:02}"
                self.title = f"Keka: {time_str}"
        else:
            self.title = "Keka: Not Clocked In"

    def show_completion_dialog(self):
        """Shows a dialog when 9 hours are completed."""
        try:
            script = '''
            display dialog "You've completed 9 hours! Time to clock out?" ¬
            buttons {"Snooze (15 min)", "Dismiss", "Clock Out"} ¬
            default button "Clock Out" ¬
            with title "Keka Timer" ¬
            with icon caution
            '''
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            
            # Parse the button clicked
            if result.returncode == 0:
                button_clicked = result.stdout.strip()
                logging.info(f"Completion dialog: User clicked '{button_clicked}'")
                
                if "Clock Out" in button_clicked:
                    # Trigger clock out
                    logging.info("User chose to clock out from completion dialog")
                    self.do_clock_out()
                elif "Snooze" in button_clicked:
                    # Snooze for 15 minutes
                    self.snooze_until = datetime.now() + timedelta(minutes=15)
                    self.notification_shown = False
                    logging.info(f"Snoozed until {self.snooze_until}")
                    send_notification("Keka Timer", "Snoozed", "Reminder snoozed for 15 minutes")
                elif "Dismiss" in button_clicked:
                    # Dismissed - don't show again
                    logging.info("User dismissed completion notification")
                    # notification_shown remains True
            else:
                # User cancelled dialog
                logging.info("User cancelled completion dialog")
                self.notification_shown = False
        except Exception as e:
            logging.error(f"Error showing completion dialog: {e}")
            self.notification_shown = False
