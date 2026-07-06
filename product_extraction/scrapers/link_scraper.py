# Fix Windows console encoding
import sys
import codecs
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'replace')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import os
from pathlib import Path
from datetime import datetime

# Enable direct-script execution (python scrapers/link_scraper.py)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ─── Shared Excel utilities (Unit 3) ───────────────────────────────
from common.excel_utils import read_excel, write_dataframe
from common.file_utils import safe_delete
from common.progress_utils import load_json_state, save_json_state

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────
PROGRESS_FILE   = 'link_scraper_progress.json'    # full run state
CHECKPOINT_FILE = 'checkpoint.xlsx'  # incremental checkpoint after each URL
ERROR_LOG_FILE  = 'errors.log'       # all errors
INPUT_FILE      = 'archive_urls.xlsx'
OUTPUT_FILE     = 'extracted_products.xlsx'

# Run modes
MODE_FRESH        = '1'  # start fresh
MODE_RESUME       = '2'  # continue where left off
MODE_RETRY_FAILED = '3'  # only failed URLs

# in-memory errors for final summary
_error_records: list = []

DEFAULT_PROGRESS_STATE = {
    'completed_urls': [],
    'failed_urls': [],
    'failed_products': [],
    'all_products': [],
}


# ─────────────────────────────────────────────
# Progress management
# ─────────────────────────────────────────────

def load_progress() -> dict:
    """
    Structure of link_scraper_progress.json:
    {
      "completed_urls": [...],    # URLs fully processed
      "failed_urls":    [...],    # URLs that returned zero products (page-level fail)
      "failed_products": [        # individual products that failed inside a URL
          {"url": "...", "product": "...", "reason": "..."},
          ...
      ],
      "all_products": [...]       # all successfully extracted products so far
    }
    """
    return load_json_state(PROGRESS_FILE, DEFAULT_PROGRESS_STATE)


def save_progress(state: dict):
    save_json_state(PROGRESS_FILE, state)
    if state['all_products']:
        df = pd.DataFrame(state['all_products']).drop_duplicates(subset=['Product URL'], keep='first')
        df.insert(0, 'No', range(1, len(df) + 1))
        write_dataframe(df, CHECKPOINT_FILE)


def log_error(archive_url: str, product_name: str, reason: str):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] URL: {archive_url} | Product: {product_name} | Reason: {reason}\n")
    _error_records.append({
        'archive_url': archive_url, 'product': product_name,
        'reason': reason, 'time': timestamp
    })


# ─────────────────────────────────────────────
# Run-mode selection
# ─────────────────────────────────────────────

def choose_run_mode() -> str:
    progress = load_progress()
    has_progress = bool(progress['completed_urls'])
    has_failed   = bool(progress['failed_urls']) or bool(progress['failed_products'])

    print("\n" + "─" * 60)
    print("  Select run mode:")
    print()
    print(f"  [{MODE_FRESH}]  Fresh start  (all previous data will be deleted)")

    if has_progress:
        done  = len(progress['completed_urls'])
        prods = len(progress['all_products'])
        print(f"  [{MODE_RESUME}]  Resume from last position  "
              f"({done} URL(s) done, {prods} product(s) so far)")
    else:
        print(f"  [{MODE_RESUME}]  Resume from last position  (no previous run found)")

    if has_failed:
        fu = len(progress['failed_urls'])
        fp = len(progress['failed_products'])
        print(f"  [{MODE_RETRY_FAILED}]  Retry failed items only  "
              f"({fu} URL(s) with no products, {fp} product(s) with errors)")
    else:
        print(f"  [{MODE_RETRY_FAILED}]  Retry failed items only  (no failures recorded)")

    print("─" * 60)

    while True:
        choice = input("  Choice (1/2/3): ").strip()
        if choice == MODE_FRESH:
            confirm = input("  ⚠ All previous data will be deleted. Are you sure? (y/n): ").strip().lower()
            if confirm == 'y':
                for f in [PROGRESS_FILE, CHECKPOINT_FILE, ERROR_LOG_FILE]:
                    safe_delete(f)
                print("  ✓ Previous files deleted.\n")
                return MODE_FRESH
        elif choice == MODE_RESUME:
            if not has_progress:
                print("  ✗ No previous run found. Please select option 1.")
                continue
            return MODE_RESUME
        elif choice == MODE_RETRY_FAILED:
            if not has_failed:
                print("  ✗ No failures recorded in the previous run.")
                continue
            return MODE_RETRY_FAILED
        else:
            print("  ✗ Please enter 1, 2, or 3.")


# ─────────────────────────────────────────────
# Browser setup
# ─────────────────────────────────────────────

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--lang=fa')
    chrome_options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36'
    )
    CHROMEDRIVER_PATH = r'C:\drivers\chromedriver.exe'
    chrome_options.page_load_strategy = 'eager'

    try:
        print("  → Starting browser...")
        sys.stdout.flush()
        driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=chrome_options)
        driver.maximize_window()
        driver.set_page_load_timeout(45)
        driver.execute_cdp_cmd('Network.enable', {})
        driver.execute_cdp_cmd('Network.setBlockedURLs', {"urls": [
            "*google-analytics.com*", "*googletagmanager.com*",
            "*gtm.js*", "*analytics.js*", "*facebook.net*", "*doubleclick.net*",
        ]})
        print("  ✓ Browser is ready")
        sys.stdout.flush()
        return driver
    except Exception as e:
        print(f"  ✗ Error setting up browser: {e}")
        sys.stdout.flush()
        return None


def restart_driver(driver):
    print("  → Restarting browser...")
    sys.stdout.flush()
    try:
        driver.quit()
    except Exception:
        pass
    time.sleep(3)
    return setup_driver()


# ─────────────────────────────────────────────
# Click the load-more button
# ─────────────────────────────────────────────

def click_load_more(driver, max_clicks=50):
    print("  → Looking for load more button...")
    sys.stdout.flush()
    click_count = 0
    for _ in range(max_clicks):
        try:
            btn = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a.wd-load-more'))
            )
            if not btn.is_displayed():
                print("  OK All products loaded (button hidden)")
                sys.stdout.flush()
                break
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", btn)
            click_count += 1
            print(f"  → Clicked load more ({click_count})")
            sys.stdout.flush()
            time.sleep(3)
        except Exception:
            print(f"  OK No more load-more button ({click_count} clicks)")
            sys.stdout.flush()
            break
    return click_count


# ─────────────────────────────────────────────
# Extract products from one archive page
# ─────────────────────────────────────────────

def extract_products_from_archive(driver, archive_url: str) -> tuple[list, list]:
    """
    Returns: (products_ok, failed_items)
    - products_ok  : list of successfully extracted product dicts
    - failed_items : list of {'product', 'reason'} dicts for failures
    """
    products_ok   = []
    failed_items  = []

    try:
        print(f"  → Opening page...")
        sys.stdout.flush()
        driver.get(archive_url)
        time.sleep(4)

        click_load_more(driver)
        time.sleep(2)

        print("  → Extracting products from cards...")
        sys.stdout.flush()

        cards = driver.find_elements(By.CSS_SELECTOR, 'div.wd-product')
        print(f"  → Found {len(cards)} product cards")
        sys.stdout.flush()

        seen_urls = set()
        skipped_oos = 0

        for card in cards:
            product_name = '(unknown)'
            try:
                if card.find_elements(By.CSS_SELECTOR, 'span.out-of-stock'):
                    skipped_oos += 1
                    continue

                title_link   = card.find_element(By.CSS_SELECTOR, 'h3.wd-entities-title a')
                href         = title_link.get_attribute('href')
                product_name = title_link.text.strip()

                price = ''
                try:
                    ins = card.find_elements(By.CSS_SELECTOR, 'ins .woocommerce-Price-amount bdi')
                    if ins:
                        price = ins[0].text.strip()
                    else:
                        price = card.find_element(
                            By.CSS_SELECTOR, 'span.woocommerce-Price-amount bdi'
                        ).text.strip()
                    price = price.replace('تومان', '').replace('\xa0', '').strip()
                except Exception as e:
                    log_error(archive_url, product_name, f"Price not found: {e}")
                    # no price, but keep the product

                if href and product_name and href not in seen_urls:
                    products_ok.append({
                        'Product Name': product_name,
                        'Product URL':  href,
                        'Price':        price,
                    })
                    seen_urls.add(href)
                else:
                    reason = f"Missing href={href!r} or empty name"
                    log_error(archive_url, product_name, reason)
                    failed_items.append({'product': product_name, 'reason': reason})

            except Exception as e:
                log_error(archive_url, product_name, str(e))
                failed_items.append({'product': product_name, 'reason': str(e)})

        print(f"  ✓ OK: {len(products_ok)}  |  "
              f"out-of-stock: {skipped_oos}  |  failed: {len(failed_items)}")
        sys.stdout.flush()

        if not products_ok:
            with open('page_source.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("  → page_source.html saved for debugging")
            sys.stdout.flush()

        return products_ok, failed_items

    except Exception as e:
        print(f"  ✗ Page-level error: {e}")
        sys.stdout.flush()
        log_error(archive_url, '(page level)', str(e))
        return [], [{'product': '(page level)', 'reason': str(e)}]


# ─────────────────────────────────────────────
# Final summary report
# ─────────────────────────────────────────────

def print_failure_summary(total_ok: int):
    print("\n" + "=" * 60)
    print("📋 FAILURE SUMMARY")
    print("=" * 60)

    if not _error_records:
        print("  ✓ No failures — all products extracted successfully.")
        return

    by_type: dict = {}
    for r in _error_records:
        key = r['reason'].split(':')[0].strip()
        by_type.setdefault(key, []).append(r)

    fail_rate = len(_error_records) / max(total_ok + len(_error_records), 1) * 100
    print(f"  Total failed : {len(_error_records)}")
    print(f"  Successful   : {total_ok}")
    print(f"  Failure rate : {fail_rate:.1f}%")
    print()
    print("  By error type:")
    for t, recs in sorted(by_type.items(), key=lambda x: -len(x[1])):
        print(f"    [{len(recs):>3}x]  {t}")
    print()

    product_fails = [r for r in _error_records
                     if r['product'] not in ('(page level)', '(driver)', '(unknown)')]
    if product_fails:
        print(f"  Failed products ({len(product_fails)}):")
        for r in product_fails:
            print(f"    ✗ {r['product']}")
            print(f"      → {r['reason'][:80]}")
        print()

    print(f"  Full log: {ERROR_LOG_FILE}")
    print("=" * 60)


# ─────────────────────────────────────────────
# Process a list of archive URLs
# ─────────────────────────────────────────────

def process_urls(driver, urls_to_run: list, state: dict, label: str = ''):
    """
    urls_to_run : list of archive URLs to process
    state       : shared progress dict (updated and saved inside this function)
    label       : optional tag shown in log lines (e.g. "retry")
    """
    total = len(urls_to_run)
    for i, url in enumerate(urls_to_run, 1):
        print(f"\n[{i}/{total}]{' [' + label + ']' if label else ''} {url}")
        sys.stdout.flush()

        max_retries = 2
        products_ok, failed_items = [], []

        for attempt in range(1, max_retries + 1):
            try:
                products_ok, failed_items = extract_products_from_archive(driver, url)
                break
            except Exception as e:
                print(f"  ✗ Attempt {attempt} failed: {e}")
                sys.stdout.flush()
                if attempt < max_retries:
                    driver = restart_driver(driver)
                    if not driver:
                        log_error(url, '(driver)', 'Browser restart failed')
                        failed_items = [{'product': '(driver)', 'reason': 'Browser restart failed'}]
                        break

        # --- update state ---

        # remove from failed_urls if this is a retry
        if url in state['failed_urls']:
            state['failed_urls'].remove(url)
        # remove stale failed_products entries for this URL
        state['failed_products'] = [
            fp for fp in state['failed_products'] if fp.get('archive_url') != url
        ]

        if products_ok:
            # replace any previously stored products for this URL
            # (retry may return a different set)
            existing_urls = {p['Product URL'] for p in products_ok}
            state['all_products'] = [
                p for p in state['all_products']
                if p.get('Product URL') not in existing_urls
            ]
            state['all_products'].extend(products_ok)
            print(f"  ✓ Extracted {len(products_ok)} products")
        else:
            print(f"  ✗ No products — URL marked as failed")
            if url not in state['failed_urls']:
                state['failed_urls'].append(url)

        for fi in failed_items:
            if fi['product'] not in ('(page level)', '(driver)'):
                state['failed_products'].append({
                    'archive_url': url,
                    'product': fi['product'],
                    'reason':  fi['reason'],
                })

        if url not in state['completed_urls']:
            state['completed_urls'].append(url)

        save_progress(state)
        print(f"  → Checkpoint saved ({len(state['all_products'])} products total)")
        sys.stdout.flush()

        if i < total:
            print("  → Waiting...")
            sys.stdout.flush()
            time.sleep(3)

    return driver   # may have been restarted


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Product Extractor v3 — Resume / Retry / Fresh")
    print("=" * 60)
    sys.stdout.flush()

    mode = choose_run_mode()

    # load state (after possible wipe in FRESH mode)
    state = load_progress()

    print("\n→ Starting Chrome browser...")
    sys.stdout.flush()
    driver = setup_driver()
    if not driver:
        print("✗ Cannot continue. Chrome not available.")
        sys.stdout.flush()
        return

    try:
        # --- determine which URLs to process ---
        if mode == MODE_RETRY_FAILED:
            # URLs that had a page-level failure
            urls_to_run = list(state['failed_urls'])
            label = 'retry-url'

            # also include archive URLs that had individual product failures
            extra = list({fp['archive_url'] for fp in state['failed_products']
                          if fp['archive_url'] not in urls_to_run})
            if extra:
                print(f"\n  + {len(extra)} archive URL(s) with individual product failures will also be retried.")
                urls_to_run += extra

            if not urls_to_run:
                print("✓ Nothing to retry.")
                return

            print(f"\n→ Retrying {len(urls_to_run)} URL(s)...\n")
            sys.stdout.flush()

        else:
            # FRESH or RESUME: read archive URLs from input file
            print(f"\n→ Reading {INPUT_FILE}...")
            sys.stdout.flush()
            df_input = read_excel(INPUT_FILE)
            if 'URL' in df_input.columns:
                all_archive_urls = df_input['URL'].dropna().astype(str).str.strip().tolist()
            elif 'url' in df_input.columns:
                all_archive_urls = df_input['url'].dropna().astype(str).str.strip().tolist()
            else:
                all_archive_urls = df_input.iloc[:, 0].dropna().astype(str).str.strip().tolist()

            if mode == MODE_RESUME:
                urls_to_run = [u for u in all_archive_urls if u not in state['completed_urls']]
                print(f"  → {len(state['completed_urls'])} already done, "
                      f"{len(urls_to_run)} remaining")
            else:
                urls_to_run = all_archive_urls

            label = ''

        # --- main run ---
        driver = process_urls(driver, urls_to_run, state, label=label)

        # --- save final output ---
        print("\n" + "=" * 60)
        if state['all_products']:
            df_out = pd.DataFrame(state['all_products'])
            df_out = df_out.drop_duplicates(subset=['Product URL'], keep='first')
            df_out.insert(0, 'No', range(1, len(df_out) + 1))
            write_dataframe(df_out, OUTPUT_FILE)

            print(f"✓ {len(df_out)} unique products saved → {OUTPUT_FILE}")
            sys.stdout.flush()

            # clean up temp files only when everything succeeded
            all_done = not state['failed_urls'] and not state['failed_products']
            if all_done and mode != MODE_RETRY_FAILED:
                for f in [PROGRESS_FILE, CHECKPOINT_FILE]:
                    if os.path.exists(f):
                        os.remove(f)
                print("✓ Temporary files cleaned up")
            else:
                remaining = len(state['failed_urls']) + len(state['failed_products'])
                if remaining:
                    print(f"  ℹ {remaining} failed item(s) still in link_scraper_progress.json — "
                          f"run again and choose option 3 to retry.")

            print("\n📋 Sample:")
            print(df_out.head(10).to_string(index=False))
            print_failure_summary(len(df_out))
        else:
            print("✗ No products found.")
            print_failure_summary(0)

    except FileNotFoundError:
        print(f"\n✗ {INPUT_FILE} not found!")
        print("  Create an Excel file with a column named 'URL'.")
        sys.stdout.flush()

    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.stdout.flush()
        import traceback
        print(traceback.format_exc())

    finally:
        print("\n→ Closing browser...")
        sys.stdout.flush()
        try:
            driver.quit()
        except Exception:
            pass
        print("✓ Done")
        sys.stdout.flush()


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║   Product Extractor v3 — Resume / Retry Failed / Fresh  ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    import importlib.util
    missing = [p for p in ('selenium', 'pandas', 'openpyxl')
               if importlib.util.find_spec(p) is None]
    if missing:
        print(f"⚠ Missing packages: {', '.join(missing)}")
        print(f"  pip install {' '.join(missing)}")
    else:
        print("✓ All packages installed\n")
        sys.stdout.flush()
        main()
