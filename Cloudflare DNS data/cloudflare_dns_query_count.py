"""
Cloudflare DNS Query Counter (token-based, no hardcoded credentials).

環境變數：
- CF_API_TOKEN      （必填）只需授權：Zone:Read、DNS Analytics:Read
- CF_ACCOUNT_ID     （選填）若提供，僅列出該 Account 的 zones
- CF_ZONES          （選填）以逗號分隔的 zone 名稱清單，只查這些 zone

輸出：
- 產生 CSV：cloudflare_dns_query_count_<timestamp>.csv
  欄位：account_id,zone_name,zone_id,since,until,total_query_count
"""

import os
import sys
import time
import json
import datetime
import requests
from typing import List, Optional, Dict


API_BASE = "https://api.cloudflare.com/client/v4"
RUN_TS = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def get_env(name: str, required: bool = False) -> Optional[str]:
    val = os.getenv(name)
    if required and not val:
        print(f"[ERROR] Missing env: {name}")
        sys.exit(1)
    return val


class SkipZone(Exception):
    """Non-fatal skip for a zone (e.g., plan not eligible)."""


def backoff_retry(func, retries=3, base=2, first_wait=1):
    for attempt in range(retries):
        try:
            return func()
        except Exception as e:
            if attempt == retries - 1:
                raise
            wait = first_wait * (base ** attempt)
            print(f"[WARN] {e}, retry in {wait}s...")
            time.sleep(wait)


def build_headers(entry: Dict) -> Dict:
    """Return auth headers for either API Token (Bearer) or Global API Key."""
    api_token = entry.get("token") or entry.get("api_token")
    api_key = entry.get("api_key")
    email = entry.get("email")
    use_global = entry.get("use_global")

    # If explicitly told to use global, or we have email+api_key but no api_token, use Global API Key
    if use_global or (email and api_key and not api_token):
        return {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Content-Type": "application/json",
        }

    # Otherwise treat as token (Bearer). If only api_key provided (no email), allow as token.
    bearer = api_token or api_key
    return {
        "Authorization": f"Bearer {bearer}",
        "Content-Type": "application/json",
    }


def get_zones(headers: Dict, account_id: Optional[str], filter_names: List[str]) -> List[Dict]:
    zones = []
    page = 1
    per_page = 50
    while True:
        params = {"page": page, "per_page": per_page}
        if account_id:
            params["account.id"] = account_id

        def _call():
            resp = requests.get(f"{API_BASE}/zones", headers=headers, params=params, timeout=30)
            if resp.status_code != 200:
                raise Exception(f"list zones http {resp.status_code}")
            data = resp.json()
            if not data.get("success"):
                raise Exception(f"list zones api error: {data.get('errors')}")
            return data

        data = backoff_retry(_call, retries=3)
        result = data.get("result", [])
        if filter_names:
            result = [z for z in result if z.get("name") in filter_names]
        zones.extend(result)
        if len(data.get("result", [])) < per_page:
            break
        page += 1
        time.sleep(0.3)  # avoid rate limit
    return zones


def fetch_dns_query_count(headers: Dict, zone_id: str, since: str, until: str) -> int:
    params = {
        "metrics": "queryCount",
        "dimensions": "date",
        "since": since,
        "until": until,
    }

    def _call():
        resp = requests.get(
            f"{API_BASE}/zones/{zone_id}/dns_analytics/report",
            headers=headers,
            params=params,
            timeout=60,
        )
        if resp.status_code == 403:
            raise SkipZone("dns analytics 403 (no permission)")
        if resp.status_code == 400:
            raise SkipZone("dns analytics 400 (plan not eligible or bad params)")
        if resp.status_code != 200:
            raise Exception(f"dns analytics http {resp.status_code}")
        data = resp.json()
        if not data.get("success"):
            raise Exception(f"dns analytics api error: {data.get('errors')}")
        return data

    data = backoff_retry(_call, retries=3)
    rows = data.get("result", {}).get("data", [])
    total = 0
    for row in rows:
        # row example: {"dimensions":{"date":"2025-02-01"},"metrics":{"queryCount":123}}
        metrics = row.get("metrics", {})
        total += int(metrics.get("queryCount", 0))
    return total


def save_partial(results: List[Dict], failures: List[Dict], final: bool = False):
    """Persist incremental results to CSV to avoid loss on long runs."""
    if not results and not failures:
        return
    suffix = "" if final else "_partial"
    out_file = f"cloudflare_dns_query_count_{RUN_TS}{suffix}.csv"
    fail_file = f"cloudflare_dns_query_failures_{RUN_TS}{suffix}.csv"
    try:
        import pandas as pd
        if results:
            pd.DataFrame(results).to_csv(out_file, index=False, encoding="utf-8-sig")
        if failures:
            pd.DataFrame(failures).to_csv(fail_file, index=False, encoding="utf-8-sig")
        print(f"[INFO] saved batch -> {out_file}" + (f", {fail_file}" if failures else ""))
    except Exception as e:
        print(f"[WARN] batch save failed: {e}")
        if results:
            print("[RESULTS]", json.dumps(results, ensure_ascii=False, indent=2))
        if failures:
            print("[FAILURES]", json.dumps(failures, ensure_ascii=False, indent=2))


def run_single(headers: Dict, account_id: Optional[str], filter_names: List[str], since: str, until: str):
    """Run counting for one token/account. Yields batches every batch_size."""
    zones = get_zones(headers, account_id, filter_names)
    if not zones:
        print("[WARN] No zones found.")
        return

    print(f"[INFO] Zones to process: {len(zones)}")
    results = []
    failures = []
    batch_size = 10
    for idx, z in enumerate(zones, 1):
        zone_id = z.get("id")
        name = z.get("name")
        acct_id = z.get("account", {}).get("id", "")
        print(f"[{idx}/{len(zones)}] zone={name} ({zone_id}) ...")
        try:
            total = fetch_dns_query_count(headers, zone_id, since, until)
            results.append(
                {
                    "account_id": acct_id,
                    "zone_name": name,
                    "zone_id": zone_id,
                    "since": since,
                    "until": until,
                    "total_query_count": total,
                }
            )
        except SkipZone as e:
            msg = str(e)
            print(f"[SKIP] zone {name}: {msg}")
            failures.append({"zone_name": name, "zone_id": zone_id, "error": msg, "account_id": acct_id})
        except Exception as e:
            msg = str(e)
            print(f"[ERROR] zone {name}: {msg}")
            failures.append({"zone_name": name, "zone_id": zone_id, "error": msg, "account_id": acct_id})
        time.sleep(0.3)
        # write batch every 10 successes+failures to avoid loss on long runs
        if (len(results) + len(failures)) % batch_size == 0:
            yield results, failures
            results, failures = [], []
    # yield remaining
    if results or failures:
        yield results, failures


def main():
    accounts_json = get_env("CF_ACCOUNTS_JSON", required=False)
    token = get_env("CF_API_TOKEN", required=False)
    account_id = get_env("CF_ACCOUNT_ID", required=False)
    zone_filter_raw = get_env("CF_ZONES", required=False)
    filter_names = []
    if zone_filter_raw:
        filter_names = [z.strip() for z in zone_filter_raw.split(",") if z.strip()]

    end_date = datetime.datetime.utcnow().date()
    start_date = end_date - datetime.timedelta(days=30)
    since = f"{start_date}T00:00:00Z"
    until = f"{end_date}T00:00:00Z"

    print(f"[INFO] Date range: {since} ~ {until}")
    print(f"[INFO] Filter zones: {filter_names if filter_names else 'ALL'}")

    # Decide account list
    account_entries = []
    if accounts_json:
        try:
            data = json.loads(accounts_json)
            if isinstance(data, list):
                account_entries = data
            else:
                print("[WARN] CF_ACCOUNTS_JSON is not a list, ignored.")
        except Exception as e:
            print(f"[WARN] CF_ACCOUNTS_JSON parse failed: {e}")

    # If no list, fall back to single env vars
    if not account_entries:
        if not token:
            print("[ERROR] Missing env: CF_API_TOKEN")
            sys.exit(1)
        account_entries = [
            {
                "email": "",
                "api_key": token,
                "account_id": account_id or "",
            }
        ]

    all_results = []
    all_failures = []
    for idx, entry in enumerate(account_entries, 1):
        token_val = entry.get("api_key") or entry.get("token") or entry.get("api_token")
        acct_id_val = entry.get("account_id") or ""
        email = entry.get("email") or f"#account_{idx}"

        if not token_val and not entry.get("api_key"):
            print(f"[WARN] skip entry {email}: missing api_key/token")
            continue

        headers = build_headers(entry)
        print(f"[INFO] ==== Account {idx}/{len(account_entries)}: {email} (acct={acct_id_val or 'N/A'}) ====")
        try:
            for batch_results, batch_failures in run_single(headers, acct_id_val, filter_names, since, until):
                for r in batch_results:
                    r["account_email"] = email
                for f in batch_failures:
                    f["account_email"] = email
                all_results.extend(batch_results)
                all_failures.extend(batch_failures)
                save_partial(all_results, all_failures)
        except Exception as e:
            print(f"[ERROR] account {email}: {e}")
            continue

    # final save
    save_partial(all_results, all_failures, final=True)


if __name__ == "__main__":
    main()

