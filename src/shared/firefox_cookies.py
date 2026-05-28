import logging
import sqlite3
import tempfile
import shutil
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

logger = logging.getLogger("FirefoxCookies")

FIREFOX_PROFILES = [
    Path.home() / "snap/firefox/common/.mozilla/firefox/ft170i2b.default",
    Path.home() / "snap/firefox/common/.mozilla/firefox/wGHUz1uq.Profile 1",
]

PLATFORM_COOKIES = {
    "linkedin": [".www.linkedin.com", ".linkedin.com", ".pk.linkedin.com"],
    "instagram": [".instagram.com"],
    "facebook": [".facebook.com"],
    "twitter": [".x.com", ".twitter.com"],
}

AUTH_COOKIES = {
    "li_at", "JSESSIONID", "bscookie", "li_rm", "liap",
    "sessionid", "ds_user_id", "csrftoken", "ig_did",
    "c_user", "xs", "sb", "datr", "fr",
    "auth_token", "ct0", "twid",
}


def find_firefox_profile():
    for profile in FIREFOX_PROFILES:
        if profile.is_dir() and (profile / "cookies.sqlite").exists():
            return profile
    return None


def _patch_compat_ini(profile_dir):
    compat_ini = profile_dir / "compatibility.ini"
    if not compat_ini.exists():
        return
    content = compat_ini.read_text()
    content = re.sub(
        r'LastVersion=[\d.]+_[^/]+/[^\n]+',
        'LastVersion=146.0.1_20260000000000/20260000000000',
        content,
    )
    compat_ini.write_text(content)

    for f in profile_dir.glob("parentlock*"):
        f.unlink(missing_ok=True)
    for f in profile_dir.glob(".parentlock*"):
        f.unlink(missing_ok=True)


def get_playwright_cookies(platform=None):
    profile = find_firefox_profile()
    if not profile:
        logger.error("No Firefox profile found")
        return []

    db_path = profile / "cookies.sqlite"
    if not db_path.exists():
        logger.error(f"Cookies database not found at {db_path}")
        return []

    domains = []
    if platform and platform in PLATFORM_COOKIES:
        domains = PLATFORM_COOKIES[platform]
    else:
        for d in PLATFORM_COOKIES.values():
            domains.extend(d)

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute(
        "SELECT name, value, host, path, expiry, isSecure, isHttpOnly "
        "FROM moz_cookies WHERE host IN ({})".format(
            ",".join("?" for _ in domains)
        ),
        domains,
    )
    rows = cur.fetchall()
    conn.close()

    pw_cookies = []
    for c in rows:
        name, value, host, path, expiry, isSecure, isHttpOnly = c
        if platform:
            if name not in AUTH_COOKIES:
                continue
        unix_expiry = int(expiry / 1000) if expiry > 9999999999 else expiry
        cookie = {
            "name": name,
            "value": value,
            "domain": host.lstrip("."),
            "path": path,
            "expires": unix_expiry if unix_expiry > 0 else -1,
            "secure": bool(isSecure),
            "httpOnly": bool(isHttpOnly),
            "sameSite": "Lax",
        }
        pw_cookies.append(cookie)

    logger.info(f"Extracted {len(pw_cookies)} cookies for platform={platform or 'all'}")
    return pw_cookies


def create_authenticated_context(platform=None, headless=True):
    profile = find_firefox_profile()
    p = sync_playwright().start()

    if profile:
        tmpdir = tempfile.mkdtemp(prefix="ff-profile-")
        shutil.copytree(str(profile), tmpdir, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("lock", "parentlock", ".parentlock", "cache2", "thumbnails"))
        _patch_compat_ini(Path(tmpdir))

        ctx = p.firefox.launch_persistent_context(
            user_data_dir=tmpdir,
            headless=headless,
            args=["--no-sandbox"],
        )
        ctx._tmpdir = tmpdir
    else:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=tempfile.mkdtemp(prefix="pw-cookies-"),
            headless=headless,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        )
        cookies = get_playwright_cookies(platform)
        if cookies:
            try:
                ctx.add_cookies(cookies)
                logger.info(f"Injected {len(cookies)} cookies into Chromium")
            except Exception as e:
                logger.warning(f"Cookie injection issue: {e}")

    ctx._playwright_instance = p
    return ctx


def close_context(ctx):
    try:
        tmpdir = getattr(ctx, "_tmpdir", None)
        p = getattr(ctx, "_playwright_instance", None)
        ctx.close()
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)
        if p:
            p.stop()
    except Exception as e:
        logger.warning(f"Error closing context: {e}")
