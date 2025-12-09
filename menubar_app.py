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
        self.work_hours = 9
        self.notification_shown = False
        self.snooze_until = None
        self.snooze_count = 0
        self.max_snoozes = 3
        self.max_overtime_minutes = 60  # 1 hour

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
            self.exit_button,
        ]

        # Start timer
        self.timer = rumps.Timer(self.update_timer, 1)
        self.timer.start()

        # Start session keep-alive timer (every 5 minutes)
        self.session_timer = rumps.Timer(self.keep_session_alive, 300)
        self.session_timer.start()

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

    def keep_session_alive(self, _):
        """Periodically refresh session to prevent timeout."""
        threading.Thread(target=self._refresh_session, daemon=True).start()

    def _refresh_session(self):
        """Background task to refresh session."""
        if self.scraper.is_session_valid():
            self.scraper.refresh_session()
            logging.info("Session keep-alive executed")
        else:
            logging.warning("Session invalid during keep-alive check")

    def clock_in(self, _):
        logging.info("Manual Clock In triggered.")
        self.title = "Keka: Clocking In..."
        threading.Thread(target=self.do_clock_in, daemon=True).start()

    def do_clock_in(self):
        # Check if session is valid
        if not self.scraper.is_session_valid():
            logging.warning("Session invalid, prompting user to relaunch")
            send_notification(
                "Keka Timer",
                "Session Expired",
                "Browser session expired. Please restart the app.",
            )
            self.title = "Keka: Session Expired"
            return

        success = self.scraper.perform_clock_in()
        if success:
            send_notification(
                "Keka Timer", "Clock In", "Clock In successful! Refreshing..."
            )
            self.do_refresh()
        else:
            send_notification(
                "Keka Timer",
                "Clock In Failed",
                "Could not find button or error occurred. Check if you're logged in.",
            )
            self.title = "Keka: Error"

    def clock_out(self, _):
        logging.info("Manual Clock Out triggered.")
        self.title = "Keka: Clocking Out..."
        threading.Thread(target=self.do_clock_out, daemon=True).start()

    def do_clock_out(self):
        # Check if session is valid
        if not self.scraper.is_session_valid():
            logging.warning("Session invalid, prompting user to relaunch")
            send_notification(
                "Keka Timer",
                "Session Expired",
                "Browser session expired. Please restart the app.",
            )
            self.title = "Keka: Session Expired"
            return

        success = self.scraper.perform_clock_out()
        if success:
            send_notification(
                "Keka Timer", "Clock Out", "Clock Out successful! Refreshing..."
            )
            self.do_refresh()
        else:
            send_notification(
                "Keka Timer",
                "Clock Out Failed",
                "Could not find button or error occurred. Check if you're logged in.",
            )
            self.title = "Keka: Error"

    def refresh_data(self, _):
        logging.info("Manual refresh triggered.")
        self.title = "Keka: Refreshing..."
        threading.Thread(target=self.do_refresh, daemon=True).start()

    def do_refresh(self):
        # Check if session is valid, attempt auto-relogin if not
        if not self.scraper.is_session_valid():
            logging.warning(
                "Session invalid during refresh, attempting auto-relogin..."
            )
            self.title = "Keka: Restoring Session..."

            if self.scraper.relaunch_browser():
                logging.info("Auto-relogin successful")
                send_notification(
                    "Keka Timer",
                    "Session Restored",
                    "Browser session has been restored. Please log in if needed.",
                )
                time.sleep(3)  # Give time for page to load
                # Try to fetch clock-in time after relogin
                new_time = self.scraper.get_clock_in_time()
                if new_time:
                    self.clock_in_time = new_time
                    logging.info(f"Refresh after relogin success: {new_time}")
                else:
                    self.clock_in_time = None
                return
            else:
                logging.error("Auto-relogin failed")
                send_notification(
                    "Keka Timer",
                    "Session Expired",
                    "Could not restore session. Please restart the app.",
                )
                self.clock_in_time = None
                self.title = "Keka: Session Expired"
                return

        new_time = self.scraper.get_clock_in_time()
        if new_time:
            self.clock_in_time = new_time
            logging.info(f"Refresh success: {new_time}")
        else:
            logging.info("Refresh: Not clocked in or failed.")
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
                        threading.Thread(
                            target=self.show_completion_dialog, daemon=True
                        ).start()
                        self.notification_shown = True

                overtime = abs(remaining)
                total_seconds = int(overtime.total_seconds())

                # Check for max overtime (1 hour)
                if total_seconds > (self.max_overtime_minutes * 60):
                    logging.info(
                        "Max overtime reached (1 hour). Auto-shutdown initiated."
                    )
                    self.perform_auto_shutdown(
                        "Max Overtime Reached",
                        "You've worked 10+ hours. Closing app for your well-being.",
                    )
                    return

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
            script = """
            display dialog "You've completed 9 hours! Time to clock out?" ¬
            buttons {"Snooze (15 min)", "Dismiss", "Clock Out"} ¬
            default button "Clock Out" ¬
            with title "Keka Timer" ¬
            with icon caution
            """
            result = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True
            )

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
                    self.snooze_count += 1
                    logging.info(
                        f"Snooze clicked. Count: {self.snooze_count}/{self.max_snoozes}"
                    )

                    if self.snooze_count >= self.max_snoozes:
                        logging.info("Max snoozes reached. Auto-shutdown initiated.")
                        self.perform_auto_shutdown(
                            "Max Snoozes Reached",
                            "You've snoozed 3 times. Time to go home! Closing app.",
                        )
                        return

                    self.snooze_until = datetime.now() + timedelta(minutes=15)
                    self.notification_shown = False
                    logging.info(f"Snoozed until {self.snooze_until}")
                    send_notification(
                        "Keka Timer",
                        "Snoozed",
                        f"Reminder snoozed for 15 minutes ({self.snooze_count}/{self.max_snoozes})",
                    )
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

    def perform_auto_shutdown(self, title, message):
        """Attempts to clock out, sends notification, and quits the app."""
        logging.info(f"Auto-shutdown triggered: {title}")

        # Notify user about shutdown initiation
        send_notification("Keka Timer", title, f"{message} Attempting to clock out...")
        time.sleep(2)

        # Attempt to clock out
        try:
            if self.scraper.is_session_valid():
                logging.info("Session valid, attempting auto-clock out...")
                success = self.scraper.perform_clock_out()
                if success:
                    send_notification(
                        "Keka Timer",
                        "Auto-Clock Out",
                        "Successfully clocked out! Shutting down now.",
                    )
                    logging.info("Auto-clock out successful")
                else:
                    send_notification(
                        "Keka Timer",
                        "Auto-Clock Out Failed",
                        "Could not clock out. Shutting down anyway.",
                    )
                    logging.warning("Auto-clock out failed")
            else:
                # Try to restore session one last time
                logging.info("Session invalid, attempting to restore for clock-out...")
                if self.scraper.relaunch_browser():
                    success = self.scraper.perform_clock_out()
                    if success:
                        send_notification(
                            "Keka Timer",
                            "Auto-Clock Out",
                            "Restored session and clocked out! Shutting down.",
                        )
                    else:
                        send_notification(
                            "Keka Timer",
                            "Auto-Clock Out Failed",
                            "Restored session but clock out failed.",
                        )
                else:
                    send_notification(
                        "Keka Timer",
                        "Auto-Clock Out Failed",
                        "Session expired and could not be restored.",
                    )
        except Exception as e:
            logging.error(f"Error during auto-clock out: {e}")
            send_notification(
                "Keka Timer", "Error", "An error occurred during auto-clock out."
            )

        # Give time for final notification
        time.sleep(4)
        self.quit_app(None)
