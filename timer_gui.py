import customtkinter as ctk
import tkinter as tk
from datetime import datetime, timedelta
from utils import calculate_remaining_time

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class FloatingTimerApp(ctk.CTk):
    def __init__(self, clock_in_time=None, work_hours=9, refresh_callback=None):
        super().__init__()

        self.clock_in_time = clock_in_time
        self.work_hours = work_hours
        self.refresh_callback = refresh_callback
        self.is_running = True

        # Window configuration
        self.title("Keka Timer")
        self.geometry("250x120")
        self.overrideredirect(True) # Frameless
        self.attributes("-topmost", True) # Always on top
        self.resizable(False, False)

        # Draggable window logic
        self.x_offset = 0
        self.y_offset = 0
        self.bind("<ButtonPress-1>", self.start_move)
        self.bind("<ButtonRelease-1>", self.stop_move)
        self.bind("<B1-Motion>", self.do_move)

        # UI Elements
        self.create_widgets()
        
        # Start timer loop
        self.update_timer()
        
        # Auto-refresh after 1 second
        self.after(1000, self.refresh_timer)

    def create_widgets(self):
        # Main Frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Timer Label
        self.timer_label = ctk.CTkLabel(
            self.main_frame, 
            text="00:00:00", 
            font=("Roboto", 32, "bold"),
            text_color="#FFFFFF"
        )
        self.timer_label.pack(pady=(15, 5))

        # Status/Info Label
        self.info_label = ctk.CTkLabel(
            self.main_frame,
            text=f"Target: {self.work_hours}h",
            font=("Roboto", 12),
            text_color="#AAAAAA"
        )
        self.info_label.pack(pady=(0, 10))

        # Buttons Frame
        self.button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.button_frame.pack(fill="x", padx=10, pady=5)

        # Close Button
        self.close_btn = ctk.CTkButton(
            self.button_frame, 
            text="✕", 
            width=30, 
            height=30,
            fg_color="#FF5555", 
            hover_color="#CC0000",
            command=self.close_app
        )
        self.close_btn.pack(side="right")

        # Minimize/Hide Button (Optional, maybe just a toggle)
        # For now, just Close is fine as per requirements "cancel it".
        
        # Reset/Refresh Button (Placeholder for now)
        self.refresh_btn = ctk.CTkButton(
            self.button_frame,
            text="⟳",
            width=30,
            height=30,
            fg_color="#444444",
            hover_color="#666666",
            command=self.refresh_timer
        )
        self.refresh_btn.pack(side="left")

    def start_move(self, event):
        self.x_offset = event.x
        self.y_offset = event.y

    def stop_move(self, event):
        self.x_offset = None
        self.y_offset = None

    def do_move(self, event):
        deltax = event.x - self.x_offset
        deltay = event.y - self.y_offset
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")

    def update_timer(self):
        if not self.is_running:
            return

        if self.clock_in_time:
            remaining = calculate_remaining_time(self.clock_in_time, self.work_hours)
            
            if remaining.total_seconds() > 0:
                # Format: HH:MM:SS
                total_seconds = int(remaining.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
                self.timer_label.configure(text=time_str, text_color="#FFFFFF")
            else:
                # Overtime
                overtime = abs(remaining)
                total_seconds = int(overtime.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                time_str = f"+ {hours:02}:{minutes:02}:{seconds:02}"
                self.timer_label.configure(text=time_str, text_color="#55FF55") # Green for overtime
        else:
            self.timer_label.configure(text="00:00:00", text_color="#AAAAAA")

        # Schedule next update
        self.after(1000, self.update_timer)

    def refresh_timer(self):
        if self.refresh_callback:
            print("Refreshing data...")
            self.timer_label.configure(text="Refreshing...")
            # Run in a separate thread to avoid freezing UI? 
            # For simplicity, we'll do it synchronously or let the callback handle threading if needed.
            # But Tkinter doesn't like long running tasks on main thread.
            # Let's assume the callback is fast or threaded.
            new_time = self.refresh_callback()
            if new_time:
                self.clock_in_time = new_time
                print(f"Refreshed time: {new_time}")
            else:
                print("Refresh failed or no time found.")
        else:
            print("No refresh callback provided.")

    def close_app(self):
        self.is_running = False
        self.destroy()

if __name__ == "__main__":
    # Test with a dummy clock-in time (e.g., 9 hours ago)
    dummy_time = datetime.now() - timedelta(hours=4, minutes=30)
    app = FloatingTimerApp(clock_in_time=dummy_time)
    app.mainloop()
