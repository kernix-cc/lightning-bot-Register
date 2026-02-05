# Account Auto-Generator Bot
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import time
import requests
import json
import os
import random
from datetime import datetime

ACCOUNTS_FILE = "accounts.json"
CONFIG_FILE = "config.json"

# ============ CONFIG MANAGEMENT ============

def load_config():
    """Load configuration (prefix, password pattern)"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_config(config):
    """Save configuration to JSON"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"✅ Config saved to {CONFIG_FILE}")

def setup_config():
    """Setup initial configuration from user input"""
    config = load_config()
    
    if config:
        print(f"\n📋 Existing Configuration Found:")
        print(f"   Prefix: {config['prefix']}")
        print(f"   Password Pattern: {config['password_pattern']}")
        use_existing = input("\nUse existing config? (y/n): ").strip().lower()
        if use_existing == 'y':
            return config
    
    print("\n" + "="*70)
    print("⚙️  SETUP: Configure Account Generation")
    print("="*70)
    
    prefix = input("\n📝 Enter username prefix (e.g., kernix, user, bot): ").strip()
    if not prefix:
        prefix = "kernix"
    
    print("\n🔑 Password Pattern Examples:")
    print("   - Pass{num}@2025     (Pass001@2025, Pass002@2025, ...)")
    print("   - Password{num}!     (Password001!, Password002!, ...)")
    print("   - Pwd{num}123        (Pwd001123, Pwd002123, ...)")
    
    password_pattern = input("\nEnter password pattern: ").strip()
    if not password_pattern:
        password_pattern = "Pass{num}@2025"
    
    config = {
        "prefix": prefix,
        "password_pattern": password_pattern
    }
    
    save_config(config)
    return config

# ============ ACCOUNT MANAGEMENT ============

def load_accounts():
    """Load list of previously created accounts"""
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"accounts": [], "last_number": 0}

def save_accounts(data):
    """Save account information to JSON"""
    with open(ACCOUNTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_next_username(config, data):
    """Generate next username (user001, user002, ...)"""
    next_num = data["last_number"] + 1
    username = f"{config['prefix']}{next_num:03d}"
    return username, next_num

def get_password_for_username(config, num):
    """Generate password based on pattern"""
    pattern = config['password_pattern']
    password = pattern.replace("{num}", f"{num:03d}")
    return password

# ============ SPOOFING ============

def get_random_user_agent():
    """Return random User-Agent (spoofing)"""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    ]
    return random.choice(user_agents)

def inject_fingerprint_spoof(driver):
    """Spoof WebDriver fingerprint"""
    spoofing_script = """
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });
    
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5]
    });
    
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en']
    });
    
    window.chrome = {
        runtime: {}
    };
    
    Object.defineProperty(navigator, 'permissions', {
        get: () => ({
            query: () => Promise.resolve({ state: 'granted' })
        })
    });
    """
    driver.execute_cdp_command('Page.addScriptToEvaluateOnNewDocument', {
        "source": spoofing_script
    })

# ============ HELPER FUNCTIONS ============

def _try_select(driver, selectors):
    """Try selector list in order, return element or None"""
    for by, sel in selectors:
        try:
            el = driver.find_element(by, sel)
            return el
        except Exception:
            continue
    return None

def wait_for_recaptcha_solution(driver, timeout=300, poll_interval=2):
    """Wait for user to solve reCAPTCHA"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            textarea = driver.find_element(By.CSS_SELECTOR, "textarea.g-recaptcha-response")
            val = textarea.get_attribute("value")
            if val and len(val.strip()) > 10:
                print("✅ reCAPTCHA token detected")
                return True
        except NoSuchElementException:
            pass
        time.sleep(poll_interval)
    return False

def inject_recaptcha_token(driver, token):
    """Inject reCAPTCHA token into page"""
    script = """
    (function(token){
      var el = document.querySelector('textarea.g-recaptcha-response');
      if(!el){
        el = document.createElement('textarea');
        el.className = 'g-recaptcha-response';
        el.name = 'g-recaptcha-response';
        el.style.display = 'none';
        document.body.appendChild(el);
      }
      el.value = token;
    })(arguments[0]);
    """
    driver.execute_script(script, token)
    time.sleep(1)

# ============ SIGNUP FUNCTION ============

def signup_with_selenium(config, username, password, base_url="https://lightning-bot.com", headless=False, captcha_solver=None):
    """
    Main signup function
    captcha_solver: None (manual solve) or {"type":"2captcha","api_key":"KEY"}
    """
    options = webdriver.ChromeOptions()
    
    # User-Agent spoofing
    user_agent = get_random_user_agent()
    options.add_argument(f"user-agent={user_agent}")
    print(f"🎭 User-Agent: {user_agent[:70]}...")
    
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # Fingerprint spoofing
    try:
        inject_fingerprint_spoof(driver)
        print("🎭 Fingerprint spoofing applied")
    except:
        print("⚠️  Fingerprint spoofing skipped (CDP not available)")
    
    wait = WebDriverWait(driver, 15)

    try:
        signup_url = base_url.rstrip("/") + "/signup"
        driver.get(signup_url)
        print(f"📱 Opened {signup_url}")

        # --- Form field selectors ---
        username_sel = [
            (By.CSS_SELECTOR, "input[name='username']"),
            (By.CSS_SELECTOR, "input[placeholder*='Username']"),
            (By.CSS_SELECTOR, "input[placeholder*='username']"),
            (By.XPATH, "//input[@type='text']"),
        ]
        password_sel = [
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.CSS_SELECTOR, "input[name='password']"),
            (By.CSS_SELECTOR, "input[placeholder*='Password']"),
        ]
        # Terms checkbox - MUST check
        checkbox_sel = [
            (By.XPATH, "//input[@type='checkbox']"),
            (By.CSS_SELECTOR, "input[type='checkbox']"),
            (By.XPATH, "//input[@type='checkbox' and (contains(@name,'terms') or contains(@id,'terms'))]"),
            (By.XPATH, "//label[contains(.,'agree') or contains(.,'Agree') or contains(.,'terms') or contains(.,'Terms')]/preceding::input[@type='checkbox'][1]"),
        ]
        # Submit button
        submit_sel = [
            (By.XPATH, "//button[contains(., 'Register')]"),
            (By.XPATH, "//button[contains(., 'Sign Up')]"),
            (By.XPATH, "//button[contains(., 'Create account')]"),
            (By.XPATH, "//button[contains(., 'signup')]"),
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//button[@type='submit']"),
        ]

        # Fill form fields
        if username:
            u = _try_select(driver, username_sel)
            if u:
                u.clear()
                u.send_keys(username)
                print(f"✓ Username filled: {username}")
        if password:
            p = _try_select(driver, password_sel)
            if p:
                p.clear()
                p.send_keys(password)
                print(f"✓ Password filled")

        # Click terms checkbox
        cb = _try_select(driver, checkbox_sel)
        if cb:
            try:
                if not cb.is_selected():
                    cb.click()
                    print("✓ Terms & Conditions checkbox checked")
                else:
                    print("✓ Terms & Conditions checkbox already checked")
            except Exception as e:
                print(f"⚠️  Warning: Could not click checkbox: {e}")
        else:
            print("⚠️  Warning: Could not find terms checkbox on page")

        # --- reCAPTCHA detection ---
        has_recaptcha = False
        try:
            driver.find_element(By.CSS_SELECTOR, ".grecaptcha-badge")
            has_recaptcha = True
            print("✓ reCAPTCHA badge detected")
        except NoSuchElementException:
            try:
                driver.find_element(By.CSS_SELECTOR, "iframe[title='reCAPTCHA']")
                has_recaptcha = True
                print("✓ reCAPTCHA iframe detected")
            except NoSuchElementException:
                try:
                    driver.find_element(By.CSS_SELECTOR, ".g-recaptcha")
                    has_recaptcha = True
                    print("✓ reCAPTCHA container detected")
                except NoSuchElementException:
                    print("✓ No reCAPTCHA detected")

        if has_recaptcha:
            print("\n🔐 reCAPTCHA detected on page")
            if captcha_solver and captcha_solver.get("type") == "2captcha":
                # 2Captcha integration
                site_key = None
                try:
                    elem = driver.find_element(By.CSS_SELECTOR, "[data-sitekey]")
                    site_key = elem.get_attribute("data-sitekey")
                except:
                    try:
                        site_key = driver.execute_script("return window.grecaptchaKey || document.querySelector('[data-sitekey]')?.getAttribute('data-sitekey')")
                    except:
                        pass

                if not site_key:
                    print("⚠️  2captcha: Could not extract sitekey — proceeding with manual solve")
                else:
                    s_key = captcha_solver["api_key"]
                    req = requests.post("http://2captcha.com/in.php", data={
                        "key": s_key,
                        "method": "userrecaptcha",
                        "googlekey": site_key,
                        "pageurl": driver.current_url,
                        "json": 1
                    }).json()
                    if req.get("status") == 1:
                        captcha_id = req["request"]
                        for _ in range(60):
                            time.sleep(5)
                            res = requests.get("http://2captcha.com/res.php", params={
                                "key": s_key, "action": "get", "id": captcha_id, "json": 1
                            }).json()
                            if res.get("status") == 1:
                                token = res["request"]
                                inject_recaptcha_token(driver, token)
                                print("✓ Injected token from 2captcha")
                                break
                        else:
                            print("⚠️  2captcha: Timed out waiting for result")
            else:
                print("👤 Please solve the reCAPTCHA in the browser window...")
                print("⏳ Waiting up to 5 minutes...")
                solved = wait_for_recaptcha_solution(driver, timeout=300)
                if not solved:
                    print("❌ Timed out waiting for reCAPTCHA solve")
                    return False

        # Click Register button
        time.sleep(1)
        print("\n🔍 Looking for Register button...")
        submit_btn = _try_select(driver, submit_sel)
        
        if submit_btn:
            try:
                button_text = submit_btn.text
                print(f"✓ Found button: '{button_text}'")
                
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable(submit_btn))
                print("✓ Button is clickable, clicking now...")
                
                driver.execute_script("arguments[0].click();", submit_btn)
                print("✅ CLICKED REGISTER BUTTON!")
                time.sleep(2)
                
            except Exception as e:
                print(f"⚠️  JavaScript click failed: {e}")
                try:
                    submit_btn.click()
                    print("✓ Clicked with standard method")
                    time.sleep(2)
                except Exception as e2:
                    print(f"❌ Could not click button: {e2}")
                    return False
        else:
            print("❌ Register button NOT found!")
            try:
                all_buttons = driver.find_elements(By.TAG_NAME, "button")
                print(f"Found {len(all_buttons)} buttons on page:")
                for i, btn in enumerate(all_buttons):
                    print(f"  [{i}] {btn.text} - {btn.get_attribute('type')}")
            except:
                pass
            return False

        # Wait for URL change
        try:
            WebDriverWait(driver, 15).until(EC.url_changes(signup_url))
            print("✓ URL changed after submit — signup succeeded")
        except TimeoutException:
            print("⚠️  No URL change detected; check for errors on page")

        return True

    finally:
        driver.quit()

# ============ MAIN PROGRAM ============

if __name__ == "__main__":
    print("="*70)
    print("🚀 ACCOUNT AUTO-GENERATOR BOT")
    print("="*70)
    
    # Setup configuration
    config = setup_config()
    
    # Load existing accounts
    accounts_data = load_accounts()
    print(f"\n📋 Previous Accounts Created: {len(accounts_data['accounts'])}")
    if accounts_data['accounts']:
        print(f"   Last: {accounts_data['accounts'][-1]}")
    
    print("\n" + "="*70)
    print("🚀 STARTING INFINITE ACCOUNT GENERATION!")
    print("="*70)
    print("⏹  Press Ctrl+C to stop\n")
    
    account_count = 0
    
    try:
        while True:
            # Generate next username
            username, num = get_next_username(config, accounts_data)
            password = get_password_for_username(config, num)
            account_count += 1
            
            print(f"\n{'='*70}")
            print(f"📍 [{account_count}] {datetime.now().strftime('%H:%M:%S')} - {username}")
            print(f"{'='*70}")
            
            # Start signup
            success = signup_with_selenium(
                config,
                username=username,
                password=password,
                base_url="https://lightning-bot.com",
                headless=False,
            )
            
            if success:
                # Save if successful
                accounts_data['accounts'].append(username)
                accounts_data['last_number'] = num
                save_accounts(accounts_data)
                print(f"\n✅ Success! {username} created")
                print(f"📝 Total accounts created: {len(accounts_data['accounts'])}")
                
                # Wait before next account
                print("⏳ Waiting 3 seconds before next account...")
                time.sleep(3)
            else:
                print(f"\n❌ Failed! {username} signup failed")
                print("Will retry with same number on next run")
                print("⏳ Waiting 5 seconds...")
                time.sleep(5)
                
    except KeyboardInterrupt:
        print(f"\n\n{'='*70}")
        print("🛑 PROGRAM STOPPED!")
        print(f"{'='*70}")
        print(f"✅ Total Accounts Created: {len(accounts_data['accounts'])}")
        if accounts_data['accounts']:
            print(f"📝 Last 5 accounts: {', '.join(accounts_data['accounts'][-5:])}")
        print(f"💾 Saved to {ACCOUNTS_FILE}")
        print(f"⚙️  Config saved to {CONFIG_FILE}")
        print("="*70)
