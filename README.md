# Keka Timer ⏳

A native macOS Menu Bar application to track your Keka work hours. It automates logging into Keka, scrapes your clock-in time, and displays a live countdown timer right in your menu bar.

## Features
-   **Menu Bar Integration**: Always visible timer in your macOS menu bar.
-   **Auto-Login**: Automates the login process (supports SSO).
-   **Smart Detection**: Automatically detects when you are clocked in.
-   **Native Experience**: Built with `rumps` for a seamless macOS feel.

## Installation

1.  Clone the repository.
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
