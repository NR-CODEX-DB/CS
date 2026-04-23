#!/usr/bin/env python3
"""
Auto-extend script for Cloud Labs (gcp.2z2.top)
Keeps the VPS instance alive by extending its lifetime every 14 minutes.
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load configuration from .env file
load_dotenv()

# Configuration - read from environment or .env
INSTANCE_NAME = os.getenv("LABS_INSTANCE_NAME")
DASHBOARD_TOKEN = os.getenv("DASHBOARD_TOKEN")
CF_CLEARANCE = os.getenv("CF_CLEARANCE")
BASE_URL = os.getenv("BASE_URL", "https://gcp.2z2.top")
EXTEND_INTERVAL_MINUTES = int(os.getenv("EXTEND_INTERVAL_MINUTES", "14"))  # seconds before expiry
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def validate_config():
    """Check if all required configuration is present."""
    missing = []
    if not INSTANCE_NAME:
        missing.append("LABS_INSTANCE_NAME")
    if not DASHBOARD_TOKEN:
        missing.append("DASHBOARD_TOKEN")
    if not CF_CLEARANCE:
        missing.append("CF_CLEARANCE")
    if missing:
        logger.error(f"Missing configuration: {', '.join(missing)}")
        logger.error("Please set them in .env file or environment variables.")
        sys.exit(1)

def extend_instance(session, instance_name):
    """
    Call the /api/labs/extend endpoint to add 15 minutes to the instance.
    Returns True if successful, False otherwise.
    """
    url = f"{BASE_URL}/api/labs/extend"
    payload = {"instanceName": instance_name}
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; M2006C3LI Build/QP1A.190711.020) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.7727.55 Mobile Safari/537.36",
        "Origin": BASE_URL,
        "Referer": f"{BASE_URL}/dashboard",
        "Accept": "*/*",
        "X-Requested-With": "mark.via.gp",
    }
    cookies = {
        "dashboard_token": DASHBOARD_TOKEN,
        "cf_clearance": CF_CLEARANCE,
    }

    try:
        response = session.post(
            url,
            json=payload,
            headers=headers,
            cookies=cookies,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        if data.get("success"):
            expires_at = data.get("expiresAt")
            if expires_at:
                # expiresAt is a Unix timestamp in milliseconds
                expiry_time = datetime.fromtimestamp(expires_at / 1000.0)
                logger.info(f"Extended successfully. New expiry: {expiry_time}")
            else:
                logger.info(f"Extended successfully: {data.get('message', 'No message')}")
            return True
        else:
            logger.error(f"Extension failed: {data}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        return False

def main():
    validate_config()
    logger.info("Starting auto-extend script for Cloud Labs")
    logger.info(f"Instance: {INSTANCE_NAME}")
    logger.info(f"Extension interval: {EXTEND_INTERVAL_MINUTES} minutes")

    session = requests.Session()
    # Optional: add retry adapter
    # Retry logic is handled by the loop

    while True:
        success = extend_instance(session, INSTANCE_NAME)
        if success:
            # Wait for interval before next extension
            # Convert minutes to seconds
            wait_seconds = EXTEND_INTERVAL_MINUTES * 60
            logger.info(f"Next extension in {EXTEND_INTERVAL_MINUTES} minutes...")
            time.sleep(wait_seconds)
        else:
            # If extension fails, wait a bit and retry
            logger.warning("Extension failed, retrying in 60 seconds...")
            time.sleep(60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Stopped by user")
        sys.exit(0)