#!/usr/bin/env python3

import os
import time
import logging
import requests
from datetime import datetime

# =========================
# CONFIG FROM ENV / SECRETS
# =========================
INSTANCE_NAME = os.getenv("LABS_INSTANCE_NAME")
DASHBOARD_TOKEN = os.getenv("DASHBOARD_TOKEN")
CF_CLEARANCE = os.getenv("CF_CLEARANCE")
BASE_URL = os.getenv("BASE_URL", "https://gcp.2z2.top")
INTERVAL = int(os.getenv("EXTEND_INTERVAL_MINUTES", "10"))
TIMEOUT = 30

# =========================
# LOGGING
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# =========================
# CHECK CONFIG
# =========================
if not INSTANCE_NAME or not DASHBOARD_TOKEN or not CF_CLEARANCE:
    print("Missing ENV values")
    exit()

# =========================
# REQUEST FUNCTION
# =========================
def extend():
    url = f"{BASE_URL}/api/labs/extend"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": BASE_URL,
        "Referer": f"{BASE_URL}/dashboard"
    }

    cookies = {
        "dashboard_token": DASHBOARD_TOKEN,
        "cf_clearance": CF_CLEARANCE
    }

    payload = {
        "instanceName": INSTANCE_NAME
    }

    try:
        r = requests.post(
            url,
            json=payload,
            headers=headers,
            cookies=cookies,
            timeout=TIMEOUT
        )

        print("Status Code:", r.status_code)

        # Show first response lines for debug
        print("Response:", r.text[:300])

        if r.status_code != 200:
            return False

        try:
            data = r.json()
        except:
            print("JSON Decode Failed")
            return False

        if data.get("success") == True:
            exp = data.get("expiresAt")

            if exp:
                dt = datetime.fromtimestamp(exp / 1000)
                print("Extended Success:", dt)

            else:
                print("Extended Success")

            return True

        else:
            print("Failed:", data)
            return False

    except Exception as e:
        print("Error:", e)
        return False

# =========================
# LOOP
# =========================
print("Starting Auto Extend")
print("Instance:", INSTANCE_NAME)

while True:
    ok = extend()

    if ok:
        print(f"Next run after {INTERVAL} minutes")
        time.sleep(INTERVAL * 60)
    else:
        print("Retry after 60 sec")
        time.sleep(60)
