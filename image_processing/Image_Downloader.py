import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import pandas as pd
from pathlib import Path
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import string
import logging
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from product_extraction.common.progress_utils import load_json_state, save_json_state


ROOT_DIR = Path(__file__).resolve().parent.parent
CANONICAL_STATE_FILE = ROOT_DIR / "runtime" / "state" / "download_state.json"

DEFAULT_DOWNLOAD_STATE = {
    'completed_pages': [],
    'failed_images': {},
    'no_image_pages': [],
    'last_page': 0,
    'session_folder': None,
}

class AdvancedImageDownloader:
    def __init__(self, excel_path, output_folder, use_selenium=False, max_retries=3, proxy=None):
        self.excel_path = excel_path
        self.output_folder = str(Path(output_folder).resolve())
        self.use_selenium = use_selenium
        self.max_retries = max_retries
        self.proxy = proxy
        self.driver = None
        self.sku_map = {}

        Path(self.output_folder).mkdir(parents=True, exist_ok=True)

        self.state_file = str(CANONICAL_STATE_FILE)
        self.state = self.load_state_early()

        if self.state.get('session_folder') and os.path.isdir(self.state['session_folder']):
            self.session_folder = self.state['session_folder']
        else:
            # If resuming and there are existing session folders under output_folder,
            # prefer the most recently modified session folder so resumed downloads go
            # into the same folder rather than creating a new one.
            parent = Path(self.output_folder)
            existing_sessions = [p for p in parent.iterdir() if p.is_dir()]
            if existing_sessions and os.environ.get('IMG_MODE') == 'resume':
                latest = max(existing_sessions, key=lambda p: p.stat().st_mtime)
                self.session_folder = str(latest)
                self.state['session_folder'] = self.session_folder
                self._save_state_raw()
            else:
                session_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                self.session_folder = os.path.join(self.output_folder, session_name)
                Path(self.session_folder).mkdir(parents=True, exist_ok=True)
                self.state['session_folder'] = self.session_folder
                self._save_state_raw()

        self.setup_logging()
        self.logger.info(f"[FOLDER] Session folder: {self.session_folder}")

        if use_selenium:
            self.setup_selenium()
        # Register signal handlers to save state on termination
        try:
            import signal
            def _handle_exit(sig, frame):
                try:
                    self.logger.info('[SIG] Saving downloader state before exit')
                    self._save_state_to_targets()
                except Exception:
                    pass
                try:
                    if self.driver:
                        self.driver.quit()
                except Exception:
                    pass
                self.logger.info('[SIG] Exiting')
                sys.exit(1)

            signal.signal(signal.SIGINT, _handle_exit)
            signal.signal(signal.SIGTERM, _handle_exit)
        except Exception:
            pass

    def load_state_early(self):
        candidate = Path(self.state_file)
        if candidate.exists():
            try:
                return load_json_state(candidate, DEFAULT_DOWNLOAD_STATE)
            except Exception:
                pass
        return load_json_state(Path(self.state_file), DEFAULT_DOWNLOAD_STATE)

    def _save_state_to_targets(self):
        try:
            save_json_state(Path(self.state_file), self.state)
        except Exception:
            pass

    def _save_state_raw(self):
        self._save_state_to_targets()

    def extract_sku(self, product_name):
        import re
        match = re.search(r'کد\s*(\d+)', product_name)
        if match:
            return match.group(1)
        numbers = re.findall(r'\d+', product_name)
        if numbers:
            return numbers[0]
        return None

    def setup_logging(self):
        log_file = os.path.join(self.session_folder, f'download_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("="*60)
        self.logger.info("IMAGE DOWNLOADER - Started")
        self.logger.info("="*60)

    def load_state(self):
        if os.path.exists(self.state_file):
            try:
                state = load_json_state(self.state_file, DEFAULT_DOWNLOAD_STATE)
                self.logger.info(f"[DONE] Previous state loaded: {len(state.get('completed_pages', []))} pages completed")
                return state
            except Exception as e:
                self.logger.warning(f"Error loading state: {e}")
        return load_json_state(self.state_file, DEFAULT_DOWNLOAD_STATE)

    def save_state(self):
        try:
            self._save_state_to_targets()
        except Exception as e:
            self.logger.error(f"Error saving state: {e}")

    def setup_selenium(self):
        try:
            from selenium.webdriver.chrome.service import Service
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--ignore-ssl-errors')
            chrome_options.add_argument('--log-level=3')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            chrome_options.page_load_strategy = 'eager'

            service = Service(r'C:\drivers\chromedriver.exe')
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(45)

            self.driver.execute_cdp_cmd('Network.enable', {})
            self.driver.execute_cdp_cmd('Network.setBlockedURLs', {"urls": [
                "*google-analytics.com*", "*googletagmanager.com*", "*gtm.js*",
                "*analytics.js*", "*facebook.net*", "*doubleclick.net*",
            ]})
            self.logger.info("[DONE] Selenium initialized")
        except Exception as e:
            self.logger.error(f"Error initializing Selenium: {e}")
            raise

    def get_images_beautifulsoup(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            seen_urls = set()
            carousel_images = []
            carousel_wrap = soup.select_one('.wd-carousel-wrap')
            if carousel_wrap:
                for item in carousel_wrap.select('.wd-carousel-item'):
                    img = item.select_one('img')
                    if img:
                        img_url = (img.get('data-large_image') or img.get('data-src')
                                   or img.get('data-lazy-src') or img.get('src'))
                        if img_url:
                            full_url = urljoin(url, img_url)
                            if full_url not in seen_urls and self.is_valid_image(full_url):
                                carousel_images.append(full_url)
                                seen_urls.add(full_url)
                self.logger.info(f"  [IMG] Carousel items found: {len(carousel_images)}")
            else:
                self.logger.warning("  [WARN] .wd-carousel-wrap not found on page")
            return carousel_images
        except Exception as e:
            self.logger.error(f"Error fetching images from {url}: {e}")
            return []

    def find_main_product_image(self, soup, base_url):
        priority_selectors = [
            '.wd-carousel-item.wd-active figure.woocommerce-product-gallery__image img',
            'figure.woocommerce-product-gallery__image img',
            '.woocommerce-product-gallery__image--featured img',
            '.woocommerce-product-gallery__image:first-child img',
            '.wp-post-image', 'img[class*="featured"]', 'img[class*="primary"]',
            'img[id*="featured"]', 'img[id*="main"]', '.featured-image img',
            '.main-image img', '.primary-image img', 'img[class*="product-image-main"]',
            'img[class*="product-main"]', 'img[id*="main-image"]', 'img[id*="product-image"]',
            '.product-image img', '.product-main-image img', '.product-single__photo img',
            '.product__main-photos img', '.product-featured-img img', '.gallery-main img',
            '.product-gallery-main img',
        ]
        for selector in priority_selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    img_url = (element.get('data-large_image') or element.get('data-src')
                               or element.get('data-lazy-src') or element.get('src'))
                    if img_url and self.is_valid_image(urljoin(base_url, img_url)):
                        return urljoin(base_url, img_url)
            except:
                continue
        try:
            meta_og = soup.select_one('meta[property="og:image"]')
            if meta_og:
                img_url = meta_og.get('content')
                if img_url and self.is_valid_image(img_url):
                    return urljoin(base_url, img_url)
        except:
            pass
        return None

    def sort_by_image_size(self, image_urls):
        def estimate_size(url):
            import re
            size_match = re.search(r'(\d+)x(\d+)', url)
            if size_match:
                width, height = map(int, size_match.groups())
                return width * height
            if 'thumb' in url.lower() or 'small' in url.lower():
                return 1
            elif 'medium' in url.lower():
                return 2
            elif 'large' in url.lower() or 'big' in url.lower():
                return 4
            return 3
        return sorted(image_urls, key=estimate_size, reverse=True)

    def get_images_selenium(self, url):
        try:
            self.logger.info(f"  Loading page with Selenium...")
            self.driver.get(url)
            time.sleep(5)
            image_urls = self.driver.execute_script("""
                var results = [];
                var seen = {};
                var wrap = document.querySelector('.wd-carousel-wrap');
                if (!wrap) return results;
                var items = wrap.querySelectorAll('.wd-carousel-item');
                items.forEach(function(item) {
                    var img = item.querySelector('img');
                    if (!img) return;
                    var src = img.getAttribute('data-large_image')
                              || img.getAttribute('data-src')
                              || img.getAttribute('data-lazy-src')
                              || img.getAttribute('src');
                    if (src && !seen[src]) {
                        seen[src] = true;
                        results.push(src);
                    }
                });
                return results;
            """)
            carousel_images = []
            for img_url in (image_urls or []):
                full_url = urljoin(url, img_url)
                if self.is_valid_image(full_url):
                    carousel_images.append(full_url)
            if not image_urls:
                self.logger.warning("  [WARN] .wd-carousel-wrap not found on page")
            self.logger.info(f"  [IMG] Carousel items found: {len(carousel_images)}")
            return carousel_images
        except Exception as e:
            self.logger.error(f"Error fetching images with Selenium from {url}: {e}")
            return []

    def find_main_image_selenium(self):
        priority_selectors = [
            '.wd-carousel-item.wd-active figure.woocommerce-product-gallery__image img',
            'figure.woocommerce-product-gallery__image img',
            '.woocommerce-product-gallery__image--featured img',
            '.woocommerce-product-gallery__image:first-child img',
            '.wp-post-image', 'img[class*="featured"]', 'img[class*="primary"]',
            'img[id*="featured"]', 'img[class*="product-image-main"]',
            'img[class*="main-image"]', 'img[id*="main-image"]',
            '.featured-image img', '.product-image img', '.main-image img',
            '.product-single__photo img', '.product__main-photos img', '.product-featured-img img',
        ]
        for selector in priority_selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                img_url = (element.get_attribute('data-large_image') or element.get_attribute('data-src')
                           or element.get_attribute('data-lazy-src') or element.get_attribute('src'))
                if img_url and self.is_valid_image(img_url):
                    return img_url
            except:
                continue
        return None

    def is_valid_image(self, url):
        invalid_patterns = [
            'placeholder', 'icon', 'logo', 'data:image', '1x1', 'spacer',
            'badge', 'sprite', 'button', 'arrow', 'star', 'rating',
            'thumbnail-', '-thumb', '_thumb', '-small', '_small',
            '-icon', '_icon', 'favicon', 'avatar', 'emoji'
        ]
        url_lower = url.lower()
        video_extensions = ['.mp4', '.webm', '.ogg', '.mov', '.avi', '.mkv', '.m4v']
        if any(url_lower.endswith(ext) or ext + '?' in url_lower for ext in video_extensions):
            return False
        if any(pattern in url_lower for pattern in invalid_patterns):
            return False
        import re
        if not re.search(r'\.(jpg|jpeg|png|gif|webp|bmp|svg)(\?|$)', url_lower):
            parsed = urlparse(url)
            if '.' not in os.path.basename(parsed.path):
                return False
        return True

    def download_image(self, image_url, save_path, retry_count=0):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(image_url, headers=headers, timeout=15, stream=True)
            response.raise_for_status()
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                f.flush()
                os.fsync(f.fileno())
            if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                return True, None
            else:
                return False, "File is empty or not created"
        except Exception as e:
            error_msg = str(e)
            if retry_count < self.max_retries:
                self.logger.warning(f"   Retry {retry_count + 1}/{self.max_retries} for: {os.path.basename(save_path)}")
                time.sleep(2 * (retry_count + 1))
                return self.download_image(image_url, save_path, retry_count + 1)
            else:
                self.logger.error(f"   Download failed after {self.max_retries} retries: {error_msg}")
                return False, error_msg

    def generate_image_name(self, page_num, image_num):
        if image_num < 26:
            letter = string.ascii_lowercase[image_num]
        else:
            letter = string.ascii_lowercase[image_num // 26 - 1] + string.ascii_lowercase[image_num % 26]
        sku = self.sku_map.get(page_num, str(page_num))
        return f"{sku}{letter}"

    def process_single_page(self, page_num, url):
        """Process a single product page"""
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Processing page {page_num}: {url}")
        self.logger.info(f"{'='*60}")

        image_urls = self.get_images_beautifulsoup(url)
        if not image_urls and self.use_selenium:
            self.logger.info("  [BS4] No images via BeautifulSoup — trying Selenium...")
            image_urls = self.get_images_selenium(url)

        # ── FIX 1: No image found → goes to no_image_pages, not completed ──
        if not image_urls:
            self.logger.warning(f"   No images found on page — marking as No Images Found (will retry later)")
            if page_num not in self.state['no_image_pages']:
                self.state['no_image_pages'].append(page_num)
            # Remove from completed if it was mistakenly added before
            if page_num in self.state['completed_pages']:
                self.state['completed_pages'].remove(page_num)
            self.save_state()
            return None, []

        self.logger.info(f"   Total images: {len(image_urls)}")

        downloaded_paths = []
        failed_images = []

        for img_num, img_url in enumerate(image_urls):
            base_name = self.generate_image_name(page_num, img_num)
            parsed = urlparse(img_url)
            ext = os.path.splitext(parsed.path)[1]
            if not ext or ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                ext = '.jpg'
            file_name = f"{base_name}{ext}"
            save_path = os.path.join(self.session_folder, file_name)

            if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                self.logger.info(f"  [DONE] Already exists: {file_name}")
                downloaded_paths.append(save_path)
                continue

            self.logger.info(f"   Downloading: {file_name}")
            success, error = self.download_image(img_url, save_path)

            if success:
                downloaded_paths.append(save_path)
                self.logger.info(f"  [DONE] Downloaded: {file_name}")
            else:
                failed_images.append({
                    'page_num': page_num,
                    'img_num': img_num,
                    'url': img_url,
                    'filename': file_name,
                    'error': error
                })
                self.logger.error(f"   Download failed: {file_name} - {error}")

            time.sleep(0.5)

        # ── FIX 2: Only mark completed if there were no errors ──
        if not failed_images:
            if page_num not in self.state['completed_pages']:
                self.state['completed_pages'].append(page_num)
            # Remove from no_image_pages if it was there before
            if page_num in self.state.get('no_image_pages', []):
                self.state['no_image_pages'].remove(page_num)
            self.logger.info(f"  [OK] Page {page_num} completed successfully")
        else:
            # ── FIX 3: Remove incomplete product from completed ──
            if page_num in self.state['completed_pages']:
                self.state['completed_pages'].remove(page_num)
            self.state['failed_images'][str(page_num)] = failed_images
            self.logger.warning(f"   Page {page_num} incomplete: {len(failed_images)} failed images")

        self.save_state()
        return downloaded_paths, failed_images

    def retry_failed_images(self, df, per_image_retries=3):
        """retry for undownloaded images (download error)"""
        if not self.state.get('failed_images'):
            return 0, 0

        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"[RELOAD] Retrying failed images (up to {per_image_retries} attempts each)")
        self.logger.info(f"{'='*60}")

        total_success = 0
        total_still_failed = 0

        for page_num_str, failed_list in list(self.state['failed_images'].items()):
            page_num = int(page_num_str)
            self.logger.info(f"\n[RELOAD] Page {page_num}: {len(failed_list)} failed images")
            remaining_failed = []

            for failed_img in failed_list:
                img_url = failed_img['url']
                file_name = failed_img['filename']
                save_path = os.path.join(self.session_folder, file_name)

                success = False
                error = None
                for attempt in range(1, per_image_retries + 1):
                    self.logger.info(f"  [RELOAD] Attempt {attempt}/{per_image_retries}: {file_name}")
                    success, error = self.download_image(img_url, save_path)
                    if success:
                        break
                    if attempt < per_image_retries:
                        wait = attempt * 3
                        self.logger.warning(f"    Failed, waiting {wait}s before next attempt...")
                        time.sleep(wait)

                if success:
                    self.logger.info(f"  [DONE] Success: {file_name}")
                    total_success += 1
                    row_idx = page_num - 1
                    if row_idx < len(df):
                        current_paths = df.at[row_idx, 'Image_Paths']
                        if pd.isna(current_paths) or current_paths == '':
                            df.at[row_idx, 'Image_Paths'] = save_path
                        elif save_path not in str(current_paths):
                            df.at[row_idx, 'Image_Paths'] = str(current_paths) + '|' + save_path
                else:
                    self.logger.error(f"    Gave up: {file_name} — {error}")
                    total_still_failed += 1
                    remaining_failed.append(failed_img)

            row_idx = page_num - 1
            if row_idx < len(df):
                if not remaining_failed:
                    df.at[row_idx, 'Download_Status'] = 'OK'
                    df.at[row_idx, 'Failed_Images'] = ''
                    if page_num not in self.state['completed_pages']:
                        self.state['completed_pages'].append(page_num)
                    del self.state['failed_images'][page_num_str]
                else:
                    df.at[row_idx, 'Download_Status'] = f'Failed ({len(remaining_failed)} images)'
                    df.at[row_idx, 'Failed_Images'] = '; '.join([f['filename'] for f in remaining_failed])
                    self.state['failed_images'][page_num_str] = remaining_failed

        self.save_state()
        self.logger.info(f"\n[DONE] Retry round complete — success: {total_success}, still failed: {total_still_failed}")
        return total_success, total_still_failed

    def retry_no_image_pages(self, df, urls):
        """
        retry for products where no image was extracted at all.
        Goes back to the page and tries again to find an image.
        """
        no_image = self.state.get('no_image_pages', [])
        if not no_image:
            self.logger.info("[INFO] No 'No Images Found' products to retry.")
            return

        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"[RELOAD] Retrying {len(no_image)} products with no images")
        self.logger.info(f"{'='*60}")

        for page_num in list(no_image):
            url = urls[page_num - 1]
            self.logger.info(f"\n[RELOAD] Re-fetching page {page_num}: {url}")
            downloaded_paths, failed_images = self.process_single_page(page_num, url)

            row_idx = page_num - 1
            if downloaded_paths is None:
                df.at[row_idx, 'Download_Status'] = 'No Images Found'
                df.at[row_idx, 'Image_Paths'] = ''
            elif failed_images:
                df.at[row_idx, 'Image_Paths'] = '|'.join(downloaded_paths)
                df.at[row_idx, 'Download_Status'] = f'Incomplete ({len(failed_images)} failed)'
                df.at[row_idx, 'Failed_Images'] = '; '.join([f['filename'] for f in failed_images])
                self.state['failed_images'][str(page_num)] = failed_images
            else:
                df.at[row_idx, 'Image_Paths'] = '|'.join(downloaded_paths)
                df.at[row_idx, 'Download_Status'] = 'OK'
                df.at[row_idx, 'Failed_Images'] = ''

        self.save_state()

    def _get_existing_paths_for_page(self, page_num):
        sku = self.sku_map.get(page_num, str(page_num))
        existing = []
        try:
            for f in sorted(os.listdir(self.session_folder)):
                name = os.path.splitext(f)[0]
                if name.startswith(sku) and len(name) > len(sku) and name[len(sku)].isalpha():
                    full_path = os.path.join(self.session_folder, f)
                    if os.path.getsize(full_path) > 0:
                        existing.append(full_path)
        except Exception as e:
            self.logger.warning(f"  Could not scan session folder for page {page_num}: {e}")
        return existing

    def _build_sku_map(self, df):
        if 'Product URL' in df.columns and 'Product Name' in df.columns:
            for idx, row in df.iterrows():
                page_num = idx + 1
                sku = self.extract_sku(str(row['Product Name']))
                if sku:
                    self.sku_map[page_num] = sku
                else:
                    self.sku_map[page_num] = str(page_num)
        else:
            for i in range(1, len(df) + 1):
                self.sku_map[i] = str(i)

    def _ensure_columns(self, df):
        for col, default in [('Image_Paths', ''), ('Download_Status', 'Pending'), ('Failed_Images', '')]:
            if col not in df.columns:
                df[col] = default

    def _save_final_excel(self, df, excel_base_name):
        output_excel = os.path.join(self.output_folder, f'{excel_base_name}_with_paths.xlsx')
        with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='All Products', index=False)

            # Sheet of incomplete products (partial or full download failure)
            still_failed = {k: v for k, v in self.state.get('failed_images', {}).items() if v}
            if still_failed:
                failed_rows = []
                for page_num_str, failed_list in still_failed.items():
                    row_idx = int(page_num_str) - 1
                    if row_idx < len(df):
                        row_data = df.iloc[row_idx].to_dict()
                        row_data['Failed_Image_URLs'] = '; '.join([f['url'] for f in failed_list])
                        row_data['Failed_Filenames'] = '; '.join([f['filename'] for f in failed_list])
                        failed_rows.append(row_data)
                if failed_rows:
                    pd.DataFrame(failed_rows).to_excel(writer, sheet_name='Failed Downloads', index=False)
                    self.logger.info(f"  [SHEET] Failed Downloads sheet: {len(failed_rows)} products")

            # Sheet of products where no image was found at all
            no_img = self.state.get('no_image_pages', [])
            if no_img:
                no_img_rows = []
                for page_num in no_img:
                    row_idx = page_num - 1
                    if row_idx < len(df):
                        no_img_rows.append(df.iloc[row_idx].to_dict())
                if no_img_rows:
                    pd.DataFrame(no_img_rows).to_excel(writer, sheet_name='No Images Found', index=False)
                    self.logger.info(f"  [SHEET] No Images Found sheet: {len(no_img_rows)} products")

        return output_excel

    def process_urls(self):
        """Full processing of all URLs"""
        # Support optional manifest to process only new products
        manifest_path = os.environ.get('IMG_MANIFEST')
        if manifest_path:
            try:
                df_manifest = pd.read_csv(manifest_path, encoding='utf-8-sig')
                # Expect columns: sku, url, name (url preferred)
                if 'url' in df_manifest.columns:
                    urls = df_manifest['url'].tolist()
                elif 'Product URL' in df_manifest.columns:
                    urls = df_manifest['Product URL'].tolist()
                else:
                    urls = []
                # Build a minimal dataframe for compatibility
                df = pd.DataFrame({'Product URL': urls})
                self.logger.info(f"[MANIFEST] Processing {len(df)} products from manifest: {manifest_path}")
            except Exception as e:
                self.logger.error(f"[MANIFEST] Could not read manifest {manifest_path}: {e}")
                df = pd.read_excel(self.excel_path)
        else:
            df = pd.read_excel(self.excel_path)
        self._build_sku_map(df)
        self._ensure_columns(df)

        urls = df['Product URL'].tolist() if 'Product URL' in df.columns else df[df.columns[0]].tolist()

        excel_base_name = os.path.splitext(os.path.basename(self.excel_path))[0]
        temp_excel = os.path.join(self.output_folder, f'{excel_base_name}_temp.xlsx')

        resume_mode = os.environ.get("IMG_RESUME", "fresh")
        resume = False

        if self.state['completed_pages'] or self.state.get('no_image_pages') or self.state.get('failed_images'):
            completed_count = len(self.state['completed_pages'])
            failed_count = len(self.state.get('failed_images', {}))
            no_img_count = len(self.state.get('no_image_pages', []))

            if resume_mode == "resume":
                resume = True
                self.logger.info(f"[>] Resuming — completed: {completed_count}, "
                                 f"failed products: {failed_count}, no-image: {no_img_count}")
            else:
                self.state = {
                    'completed_pages': [],
                    'failed_images': {},
                    'no_image_pages': [],
                    'last_page': 0,
                    'session_folder': self.session_folder
                }
                self.save_state()
                self.logger.info("[>] Starting fresh from the beginning")
        else:
            self.logger.info(f"[>] Starting fresh: {len(urls)} products to process")

        # ── Processing products ──
        # Products that need to be processed:
        # In resume mode: everything not completed and not (no_image and not scheduled for retry)
        # In fresh mode: everything
        for page_num in range(1, len(urls) + 1):
            url = urls[page_num - 1]

            if resume and page_num in self.state['completed_pages']:
                self.logger.info(f"[SKIP] Page {page_num} already completed")
                row_idx = page_num - 1
                existing_paths = self._get_existing_paths_for_page(page_num)
                if existing_paths:
                    df.at[row_idx, 'Image_Paths'] = '|'.join(existing_paths)
                    df.at[row_idx, 'Download_Status'] = 'OK'
                else:
                    df.at[row_idx, 'Image_Paths'] = ''
                    df.at[row_idx, 'Download_Status'] = 'No Images Found'
                continue

            downloaded_paths, failed_images = self.process_single_page(page_num, url)
            row_idx = page_num - 1

            if downloaded_paths is None:
                df.at[row_idx, 'Image_Paths'] = ''
                df.at[row_idx, 'Download_Status'] = 'No Images Found'
                df.at[row_idx, 'Failed_Images'] = ''
            elif failed_images:
                df.at[row_idx, 'Image_Paths'] = '|'.join(downloaded_paths)
                df.at[row_idx, 'Download_Status'] = f'Incomplete ({len(failed_images)} failed)'
                df.at[row_idx, 'Failed_Images'] = '; '.join([f['filename'] for f in failed_images])
                self.state['failed_images'][str(page_num)] = failed_images
            else:
                df.at[row_idx, 'Image_Paths'] = '|'.join(downloaded_paths)
                df.at[row_idx, 'Download_Status'] = 'OK'
                df.at[row_idx, 'Failed_Images'] = ''

            self.state['last_page'] = page_num
            self.save_state()
            df.to_excel(temp_excel, index=False)

        # ── Automatic retry after processing all products ──
        if self.state.get('failed_images'):
            failed_count = sum(len(v) for v in self.state['failed_images'].values())
            self.logger.info(f"\n[RELOAD] Final retry: {failed_count} failed images...")
            self.retry_failed_images(df, per_image_retries=3)

        if self.state.get('no_image_pages'):
            self.logger.info(f"\n[RELOAD] Retrying {len(self.state['no_image_pages'])} no-image products...")
            self.retry_no_image_pages(df, urls)

        output_excel = self._save_final_excel(df, excel_base_name)

        self.state['session_folder'] = None
        self.save_state()

        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"[OK] Download Complete")
        total_failed = sum(len(v) for v in self.state.get('failed_images', {}).values())
        self.logger.info(f"  Completed: {len(self.state['completed_pages'])}/{len(urls)}")
        self.logger.info(f"  Still failed images: {total_failed}")
        self.logger.info(f"  No images found: {len(self.state.get('no_image_pages', []))}")
        self.logger.info(f"  Excel: {output_excel}")

        if self.use_selenium and self.driver:
            self.driver.quit()

        return output_excel

    def retry_only(self):
        """Only retries incomplete and imageless products"""
        has_failed = bool(self.state.get('failed_images'))
        has_no_image = bool(self.state.get('no_image_pages'))

        if not has_failed and not has_no_image:
            self.logger.info("[INFO] No failed or no-image products — nothing to retry.")
            print("\n  Nothing to retry.")
            return

        df = pd.read_excel(self.excel_path)
        self._build_sku_map(df)
        self._ensure_columns(df)
        urls = df['Product URL'].tolist() if 'Product URL' in df.columns else df[df.columns[0]].tolist()

        # Rebuild Image_Paths for completed products
        for page_num in self.state.get('completed_pages', []):
            row_idx = page_num - 1
            if row_idx < len(df):
                existing = self._get_existing_paths_for_page(page_num)
                if existing:
                    df.at[row_idx, 'Image_Paths'] = '|'.join(existing)
                    df.at[row_idx, 'Download_Status'] = 'OK'

        if has_failed:
            failed_count = sum(len(v) for v in self.state['failed_images'].values())
            self.logger.info(f"\n[RELOAD] Retry failed downloads: {failed_count} images across "
                             f"{len(self.state['failed_images'])} products")
            self.retry_failed_images(df, per_image_retries=3)

        if has_no_image:
            self.logger.info(f"\n[RELOAD] Retry no-image products: {len(self.state['no_image_pages'])} products")
            self.retry_no_image_pages(df, urls)

        excel_base_name = os.path.splitext(os.path.basename(self.excel_path))[0]
        output_excel = self._save_final_excel(df, excel_base_name)

        self.logger.info(f"\n[OK] Retry complete — Excel: {output_excel}")

        if self.use_selenium and self.driver:
            self.driver.quit()

        return output_excel

    def download_incomplete_only(self):
        """
        Downloads from scratch only the products whose status is
        Incomplete, Failed, or No Images Found — without touching OK products.
        """
        df = pd.read_excel(self.excel_path)
        self._build_sku_map(df)
        self._ensure_columns(df)
        urls = df['Product URL'].tolist() if 'Product URL' in df.columns else df[df.columns[0]].tolist()

        # Determine which products should be downloaded
        target_pages = []
        for idx, row in df.iterrows():
            page_num = idx + 1
            status = str(row.get('Download_Status', ''))
            if status in ('Pending', 'No Images Found', '') or \
               status.startswith('Incomplete') or status.startswith('Failed') or \
               pd.isna(row.get('Download_Status')):
                target_pages.append(page_num)

        self.logger.info(f"[>] Incomplete-only mode: {len(target_pages)} products to process")

        excel_base_name = os.path.splitext(os.path.basename(self.excel_path))[0]
        temp_excel = os.path.join(self.output_folder, f'{excel_base_name}_temp.xlsx')

        for page_num in target_pages:
            url = urls[page_num - 1]
            downloaded_paths, failed_images = self.process_single_page(page_num, url)
            row_idx = page_num - 1

            if downloaded_paths is None:
                df.at[row_idx, 'Image_Paths'] = ''
                df.at[row_idx, 'Download_Status'] = 'No Images Found'
                df.at[row_idx, 'Failed_Images'] = ''
            elif failed_images:
                df.at[row_idx, 'Image_Paths'] = '|'.join(downloaded_paths)
                df.at[row_idx, 'Download_Status'] = f'Incomplete ({len(failed_images)} failed)'
                df.at[row_idx, 'Failed_Images'] = '; '.join([f['filename'] for f in failed_images])
                self.state['failed_images'][str(page_num)] = failed_images
            else:
                df.at[row_idx, 'Image_Paths'] = '|'.join(downloaded_paths)
                df.at[row_idx, 'Download_Status'] = 'OK'
                df.at[row_idx, 'Failed_Images'] = ''

            self.save_state()
            df.to_excel(temp_excel, index=False)

        # automatic retry
        if self.state.get('failed_images'):
            self.retry_failed_images(df, per_image_retries=3)
        if self.state.get('no_image_pages'):
            self.retry_no_image_pages(df, urls)

        output_excel = self._save_final_excel(df, excel_base_name)
        self.logger.info(f"\n[OK] Incomplete-only download complete — Excel: {output_excel}")

        if self.use_selenium and self.driver:
            self.driver.quit()

        return output_excel


# ──────────────────────────────────────────────
#  Usage
# ──────────────────────────────────────────────
if __name__ == "__main__":
    EXCEL_FILE    = os.environ.get("IMG_EXCEL",    "extracted_products.xlsx")
    OUTPUT_FOLDER = os.environ.get("IMG_OUTPUT",   "downloaded_images")
    USE_SELENIUM  = os.environ.get("IMG_SELENIUM", "1") == "1"
    MAX_RETRIES   = int(os.environ.get("IMG_RETRIES", "3"))

    print("="*60)
    print("ADVANCED IMAGE DOWNLOADER")
    print("="*60)
    print(f"[FILE]   Excel File    : {EXCEL_FILE}")
    print(f"[FOLDER] Output Folder : {OUTPUT_FOLDER}")
    print(f"[METHOD] Method        : {'Selenium' if USE_SELENIUM else 'BeautifulSoup'}")
    print(f"[RETRY]  Max Retries   : {MAX_RETRIES}")
    print("="*60)

    downloader = AdvancedImageDownloader(
        excel_path=EXCEL_FILE,
        output_folder=OUTPUT_FOLDER,
        use_selenium=USE_SELENIUM,
        max_retries=MAX_RETRIES
    )

    # Run modes:
    #   full             — full download of all products
    #   resume           — continue from where it stopped
    #   retry_only       — only retry incomplete/imageless products
    #   incomplete_only  — only download products that are not OK
    run_mode = os.environ.get("IMG_MODE", "full")

    if run_mode == "retry_only":
        output_file = downloader.retry_only()
    elif run_mode == "incomplete_only":
        output_file = downloader.download_incomplete_only()
    elif run_mode == "resume":
        os.environ["IMG_RESUME"] = "resume"
        output_file = downloader.process_urls()
    else:  # full
        os.environ["IMG_RESUME"] = "fresh"
        output_file = downloader.process_urls()

    if output_file:
        print(f"\n[OK] Done! Output file: {output_file}")
