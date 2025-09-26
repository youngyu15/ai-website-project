#!/usr/bin/env python3
import argparse
import json
import sys
import time
from pathlib import Path

import requests


def die(msg, resp=None):
    if resp is not None:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        print(f"\n{msg}\nStatus={resp.status_code}\nResponse={detail}", file=sys.stderr)
    else:
        print(f"\n{msg}", file=sys.stderr)
    sys.exit(1)


def pretty(o):
    print(json.dumps(o, indent=2, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser(description="E2E: login → upload → prediction → wait for result")
    p.add_argument("--api", default="http://127.0.0.1:8000", help="API base URL (default: %(default)s)")
    p.add_argument("--email", required=True, help="Login email")
    p.add_argument("--password", required=True, help="Login password")
    p.add_argument("--image", required=True, help="Path to image to upload")
    p.add_argument("--timeout", type=int, default=120, help="Seconds to wait for prediction (default: 120)")
    p.add_argument("--interval", type=float, default=2.0, help="Polling interval seconds (default: 2.0)")
    args = p.parse_args()

    api = args.api.rstrip("/")
    img_path = Path(args.image)
    if not img_path.exists():
        die(f"Image not found: {img_path}")

    # 1) LOGIN
    login_url = f"{api}/v1/auth/login"
    login_body = {"email": args.email, "password": args.password}
    try:
        r = requests.post(login_url, json=login_body, timeout=15)
    except requests.RequestException as e:
        die(f"Login request failed: {e}")
    if r.status_code != 200:
        die("Login failed", r)
    try:
        token = r.json()["access_token"]
    except Exception:
        die("Login response missing access_token", r)

    headers = {"Authorization": f"Bearer {token}"}
    print("✓ Logged in")

    # 2) UPLOAD
    img = Path(args.image); 
    r = requests.post(f"{args.api}/v1/uploads", headers=headers,
                      json={"content_type": "image/jpeg", "file_bytes": img.stat().st_size}, timeout=15)
    if r.status_code not in (200,201): die("create/presign failed", r)
    up = r.json()
    upload_url = up["upload_url"]; file_id = up["file_id"]

    img_file = {"file": (img_path.name, img_path.open("rb"))}
    try:
        r = requests.put(upload_url, headers={"Content-Type": up["content_type"]}, files=img_file)
    except requests.RequestException as e:
        die(f"Upload request failed: {e}")
    if r.status_code != 200 and r.status_code != 201:
        die("Upload failed", r)

    print("✓ Image uploaded")
    print(json.dumps(r.json, indent=2))

    # 3) CREATE PREDICTION
    pred_url = f"{api}/v1/predictions"
    body = {"file_id": file_id}
    try:
        r = requests.post(pred_url, headers=headers, json=body, timeout=15)
    except requests.RequestException as e:
        die(f"Create prediction request failed: {e}")
    if r.status_code not in (200, 201):
        die("Create prediction failed", r)

    pred = r.json()
    pred_id = pred.get("id")
    if not pred_id:
        die("Prediction response missing id", r)
    print(f"✓ Created prediction id={pred_id} (status={pred.get('status')})")

    # 4) POLL UNTIL DONE
    show_once = True
    deadline = time.time() + args.timeout
    get_url = f"{api}/v1/predictions/{pred_id}"

    while True:
        try:
            r = requests.get(get_url, headers=headers, timeout=15)
        except requests.RequestException as e:
            die(f"Poll request failed: {e}")
        if r.status_code != 200:
            die("Polling failed", r)

        data = r.json()
        status = data.get("status", "").lower()

        if show_once:
            print("Polling…")
            show_once = False

        if status in {"succeeded", "failed"}:
            print(f"✓ Finished with status={status}")
            pretty(data)
            # optionally exit nonzero on failure
            sys.exit(0 if status == "succeeded" else 2)

        if time.time() > deadline:
            print("Timed out waiting for prediction. Last response was:")
            pretty(data)
            sys.exit(3)

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
