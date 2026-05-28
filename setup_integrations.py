#!/usr/bin/env python3
"""Setup all social platform integrations using Playwright browser automation.
Runs once to log into each platform, then saves credentials for headless use."""

import json, os, shutil, sys, time
from pathlib import Path

VAULT = Path(__file__).parent / "vault_data"

INTEGRATIONS = {
    "LinkedIn": {
        "url": "https://www.linkedin.com/feed/",
        "config": VAULT / "LinkedIn" / "config.json",
        "state_file": VAULT / "LinkedIn" / "playwright_state.json",
        "status_key": "connection_type",
        "status_value": "playwright_browser",
    },
    "Twitter": {
        "url": "https://x.com/home",
        "config": VAULT / "Twitter" / "config.json",
        "state_file": VAULT / "Twitter" / "playwright_state.json",
        "status_key": "connection_type",
        "status_value": "playwright_browser",
    },
    "Facebook_Instagram": {
        "url": "https://www.facebook.com/",
        "config": VAULT / "Facebook_Instagram" / "config.json",
        "state_file": VAULT / "Facebook_Instagram" / "playwright_state.json",
        "status_key": "connection_type",
        "status_value": "playwright_browser",
    },
}

def check_state(platform: str, info: dict) -> bool:
    state_file = info["state_file"]
    if state_file.exists():
        data = json.loads(state_file.read_text())
        return len(data.get("cookies", [])) > 0
    return False

def setup_platform(platform: str, info: dict):
    """Open browser for user to log into the platform."""
    state_file = info["state_file"]
    url = info["url"]

    print(f"\n{'='*60}")
    print(f" Setting up {platform}")
    print(f"{'='*60}")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  ❌ Playwright not installed. Run: pip3 install playwright")
        return False

    with sync_playwright() as p:
        try:
            chrome_data = "/tmp/chrome-browser-data"
            if not os.path.isdir(chrome_data):
                def ignore_singletons(path, names):
                    return [n for n in names if n.startswith("Singleton")]
                shutil.copytree("/home/waleed/.config/google-chrome", chrome_data,
                                dirs_exist_ok=True, ignore=ignore_singletons)

            ctx = p.chromium.launch_persistent_context(
                user_data_dir=chrome_data,
                headless=False,
                executable_path="/opt/google/chrome/chrome",
                args=["--no-sandbox", "--disable-dev-shm-usage"],
                ignore_default_args=["--enable-automation"],
            )
        except Exception as e:
            print(f"  ❌ Could not launch Chrome: {e}")
            return False

        page = ctx.new_page()
        page.goto(url, timeout=30000, wait_until="domcontentloaded")
        print(f"  📋 A browser window should open for {url}")
        print(f"  🔑 Log in if needed, then press Enter here...")
        input("  ⏎ Press Enter after logging in: ")

        current_url = page.url
        logged_in = url.split("/")[2] in current_url and "login" not in current_url

        if logged_in:
            print(f"  ✅ Logged in! Saving session...")
            ctx.storage_state(path=str(state_file))
            print(f"  ✅ Storage state saved to {state_file}")

            def ignore_singletons(path, names):
                return [n for n in names if n.startswith("Singleton")]
            shutil.copytree("/home/waleed/.config/google-chrome", "/tmp/chrome-browser-data",
                            dirs_exist_ok=True, ignore=ignore_singletons)
            print(f"  ✅ Chrome profile copied to /tmp/chrome-browser-data")

            info["config"].parent.mkdir(parents=True, exist_ok=True)
            if info["config"].exists():
                config = json.loads(info["config"].read_text())
            else:
                config = {}
            config[info["status_key"]] = info["status_value"]
            config["status"] = "operational"
            config["playwright_state"] = str(state_file)
            config["last_login"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            info["config"].write_text(json.dumps(config, indent=2))
            print(f"  ✅ Config updated")
        else:
            print(f"  ❌ Doesn't look like login was successful (URL: {current_url})")
            print(f"     Try again with the correct credentials.")

        page.close()
        ctx.close()
        return logged_in


def main():
    print("=" * 60)
    print(" AI Employee - Social Integration Setup")
    print("=" * 60)
    print("\nThis will open browser windows for each platform.")
    print("Log into each one when prompted.")
    print()

    for platform, info in INTEGRATIONS.items():
        if check_state(platform, info):
            print(f"  ✅ {platform} already configured - skipping")
            continue
        setup_platform(platform, info)

    print(f"\n{'='*60}")
    print(" Setup Complete")
    print(f"{'='*60}")
    print("\nCurrent integration status:")
    for platform, info in INTEGRATIONS.items():
        state = check_state(platform, info)
        print(f"  {'✅' if state else '❌'} {platform}")

    print("\nRun: bash start_all.sh  to restart all services")
    print("Or:  opencode \"Post to LinkedIn about our new product\"")


if __name__ == "__main__":
    main()
