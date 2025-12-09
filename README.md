# Keka Timer ⏳

A native macOS Menu Bar application to track your Keka work hours. It automates logging into Keka, scrapes your clock-in time, and displays a live countdown timer right in your menu bar.

## Features
-   **Menu Bar Integration**: Always visible timer in your macOS menu bar.
-   **Auto-Login**: Automates the login process (supports SSO).
-   **Smart Detection**: Automatically detects when you are clocked in.
-   **Clock In/Out**: Manage your attendance directly from the menu bar.
-   **Auto-Shutdown & Clock Out**: Automatically clocks you out and closes the app if you work >1 hour overtime or snooze 3 times.
-   **Session Keep-Alive**: Prevents session timeouts with automatic background refreshing.
-   **Native Experience**: Built with `rumps` for a seamless macOS feel.

## Installation (For Users)

### Download Pre-built App

1.  **Download** the latest release from [GitHub Releases](https://github.com/veerprakash28/keka-timer/releases)
2.  **Unzip** the downloaded file
3.  **Move** `KekaTimer.app` to your Applications folder
4.  **Bypass Gatekeeper** (first time only):
    -   Go to **System Settings** → **Privacy & Security**
    -   Scroll down to find the message about `KekaTimer`
    -   Click **"Open Anyway"**
    -   Click **"Open"** to confirm
5.  **Launch** the app - Chrome will open to Keka login
6.  **Login** to Keka and the menu bar timer will appear!

### Requirements
-   macOS (Apple Silicon recommended)
-   Chrome browser installed
-   Keka account access

## Development Setup

1.  Clone the repository:
    ```bash
    git clone https://github.com/veerprakash28/keka-timer.git
    cd keka-timer
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the app:
    ```bash
    python main.py
    ```
4.  **Build Standalone App**:
    ```bash
    pyinstaller KekaTimer.spec
    ```
    The app will be available in `dist/KekaTimer.app`.

## "Vibe Coded" Project ✨

This project was built using a **"Vibe Coding"** strategy. It was entirely generated through natural language prompts and an "accept all" approach to AI-generated code, focusing on rapid iteration and intuitive design over manual implementation.

---
*Built with Python, Selenium, and Rumps.*
