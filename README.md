README — Account Auto-Generator Bot (English)

Overview
--------
This repository contains a simple Selenium-based automation script (index.py) that attempts to register accounts on a configurable website.

Use this tool responsibly and only on sites where you have explicit permission to create accounts automatically. Automating account creation at scale can violate terms of service and local laws. The author provides this code for educational and development use only.

Quick facts
-----------
• Script file: index.py
• Config file: config.json (created when first run)
• Saved accounts: accounts.json
• Main dependencies: Python 3.8+; selenium; webdriver-manager; requests

Important: ChromeDriver
-----------------------
Download the ChromeDriver build referenced by this project and place it in `C:\` on Windows.

ChromeDriver download (example):
https://storage.googleapis.com/chrome-for-testing-public/145.0.7632.46/win64/chromedriver-win64.zip

Steps to install ChromeDriver on Windows:
1. Open the URL above in your browser and download the ZIP file.
2. Extract the zip and copy `chromedriver.exe` to `C:\` (i.e., `C:\chromedriver.exe`).
3. Ensure `C:\` is in your PATH or that your environment can locate `chromedriver.exe` when launching Selenium.

Dependencies
------------
Install required Python packages (recommended in a virtual environment):

```bash
python -m pip install -U pip
python -m pip install selenium webdriver-manager requests
```

Files
-----
• index.py — Main automation script. Contains configuration setup, account management, and the Selenium signup routine.
• config.json — Saved configuration (username prefix and password pattern). Created on first run.
• accounts.json — Stores created account usernames and last number used.

Configuration
-------------
When you run `index.py` the first time, the script prompts for:
• username prefix (e.g., `kernix`)
• password pattern (use `{num}` as placeholder for sequential number; example: `Pass{num}@2025`)

Example config.json:

```json
{
  "prefix": "kernix",
  "password_pattern": "Pass{num}@2025"
}
```

How it works (short)
--------------------
• The script loads/saves a `config.json` and `accounts.json` file.
• It generates usernames sequentially (`prefix001`, `prefix002`, ...).
• For each account the script opens the site signup page (default: `https://lightning-bot.com/signup`), attempts to fill username and password fields, checks a terms checkbox if available, and clicks the submit button.
• The script includes rudimentary fingerprint spoofing (navigator.webdriver removal, fake plugins/languages, etc.) and rotates user-agents.
• If reCAPTCHA is detected the script will either wait for manual solving in the opened browser or try to use the 2Captcha API if configured.

Running the script
------------------
From the repository folder run:

```bash
python index.py
```

The program will prompt to set up or confirm a configuration, then enter an infinite loop creating accounts until you press `Ctrl+C`.

Options and notes
-----------------
• headless mode: The script sets `headless=False` by default. You can modify the `signup_with_selenium` call in the main loop to run in headless mode by passing `headless=True`.
• CAPTCHA: The script supports manual solving or 2Captcha integration. To use 2Captcha, modify the code where `captcha_solver` is provided and pass `{"type":"2captcha","api_key":"YOUR_KEY"}`.
• ChromeDriver: By default the script uses `webdriver-manager` to install a ChromeDriver. If you want to use a local ChromeDriver (for example, the one you put into `C:\chromedriver.exe`), modify the `Service` call in `signup_with_selenium` and provide the path to your driver executable.

Troubleshooting
---------------
• ChromeDriver not found: Make sure `chromedriver.exe` is in `C:\` and that your environment can access it. If using `webdriver-manager`, ensure your network allows downloads.
• Element not found / different page layout: The script probes multiple common selectors but may fail on custom pages. Inspect the target site and update selectors in `index.py`.
• reCAPTCHA: If reCAPTCHA appears and you don't provide an API solver, the script will pause and wait for manual completion in the browser window.

Ethics & Legal
--------------
Automating account creation can be used for legitimate testing or research but may also enable abuse. Do not deploy this script against third-party services without permission. Respect site terms of service and applicable laws.

License
-------
Provided as-is for educational purposes. No warranty. Use at your own risk.

Contact
-------
If you need a modified README or a different format (e.g., markdown or a downloadable `.txt`), tell me and I will provide it.
