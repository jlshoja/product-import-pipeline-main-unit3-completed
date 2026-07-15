from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
import os
import sys
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin

import time
import re

# Enable direct-script execution (python scrapers/spec_scraper.py)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ─── Shared Excel utilities (Unit 3) ───────────────────────────────
from common.excel_utils import read_excel, excel_writer, write_dataframe
from common.file_registry import get_file
from common.file_utils import safe_delete
from common.progress_utils import load_json_state, save_json_state
from common.color_utils import collect_unique_normalized_colors
from common.price_utils import clean_price_text as _clean_price_text
from common.path_registry import ARCHIVES_DIR, INPUTS_DIR, OUTPUTS_DIR, INTERMEDIATE_DIR, ROOT_DIR, RUNTIME_REPORTS_DIR, resolve_existing_path

PROGRESS_FILE = str(ROOT_DIR / "runtime" / "state" / get_file('scraper_progress'))

# Module-level progress trackers for graceful shutdown
CURRENT_PROGRESS_INDEX = 0
TOTAL_PRODUCTS = 0

import signal

def _spec_handle_exit(sig, frame):
    try:
        print('\n[SIG] Received termination signal — saving progress...')
        sys.stdout.flush()
        # Save current progress
        try:
            save_progress(CURRENT_PROGRESS_INDEX, TOTAL_PRODUCTS)
        except Exception:
            pass
    finally:
        print('[SIG] Exiting now')
        sys.stdout.flush()
        sys.exit(1)

signal.signal(signal.SIGINT, _spec_handle_exit)
signal.signal(signal.SIGTERM, _spec_handle_exit)

# ✅ Import ColorManager for final standardization
try:
    from color_manager import ColorManager
    HAS_COLOR_MANAGER = True
except ImportError:
    HAS_COLOR_MANAGER = False
    print("⚠️ color_manager.py not found. Using fallback ColorParser only.")
    sys.stdout.flush()


class ColorParser:
    """کلاس برای تبدیل رنگ‌ها به فرمت استاندارد سایت"""
    
    def __init__(self):
        # Standardized colors سایت (دقیقاً مطابق لیست شما)
        self.standard_colors = [
            'آبی', 'آبی آسمانی', 'برنزی', 'بژ', 'بنفش', 'خردلی', 'زرد', 'سبز', 
            'سبز تیره', 'سرمه‌ای', 'سفید', 'سفید شیری', 'شرابی', 'شکلاتی', 
            'صورتی', 'طلایی', 'طوسی', 'فیروزه‌ای', 'قرمز', 'قهوه‌ای', 
            'قهوه‌ای تیره', 'کرم', 'مشکی', 'نارنجی', 'نارنجی سوخته', 'نقره‌ای'
        ]
        
        # نقشه تبدیل رنگ‌های غیراستاندارد به استاندارد
        self.color_mapping = {
            # مشکی و سیاه
            'مشکی': 'مشکی', 'سیاه': 'مشکی', 'black': 'مشکی',
            
            # سفید و مشتقات
            'سفید': 'سفید', 'white': 'سفید',
            'سفید شیری': 'سفید شیری', 'شیری': 'سفید شیری', 'استخوانی': 'سفید شیری',
            
            # کرم و بژ
            'کرم': 'کرم', 'کرمی': 'کرم', 'cream': 'کرم', 'کرم روشن': 'کرم',
            'بژ': 'بژ', 'beige': 'بژ',
            
            # قهوه‌ای و مشتقات (مهم: نسکافه به قهوه‌ای)
            'قهوه‌ای': 'قهوه‌ای', 'قهوه ای': 'قهوه‌ای', 'قهوهای': 'قهوه‌ای', 'brown': 'قهوه‌ای',
            'نسکافه': 'قهوه‌ای', 'نسکافه‌ای': 'قهوه‌ای', 'نسکافه ای': 'قهوه‌ای',
            'عسلی': 'قهوه‌ای', 'کاراملی': 'قهوه‌ای', 'کارامل': 'قهوه‌ای',
            'قهوه ای روشن': 'قهوه‌ای', 'قهوه‌ای روشن': 'قهوه‌ای',
            'قهوه ای تیره': 'قهوه‌ای تیره', 'قهوه‌ای تیره': 'قهوه‌ای تیره',
            'شکلاتی': 'شکلاتی', 'شکلات': 'شکلاتی', 'chocolate': 'شکلاتی',
            
            # طوسی و خاکستری
            'طوسی': 'طوسی', 'خاکستری': 'طوسی', 'grey': 'طوسی', 'gray': 'طوسی',
            'طوسی روشن': 'طوسی', 'طوسی تیره': 'طوسی', 'خاکستری روشن': 'طوسی',
            
            # آبی و مشتقات (مهم: سورمه‌ای به سرمه‌ای)
            'آبی': 'آبی', 'ابی': 'آبی', 'blue': 'آبی', 'آبی تیره': 'آبی',
            'سرمه‌ای': 'سرمه‌ای', 'سرمه ای': 'سرمه‌ای', 
            'سورمه‌ای': 'سرمه‌ای', 'سورمه ای': 'سرمه‌ای', 'سورمه': 'سرمه‌ای',
            'آبی کاربنی': 'سرمه‌ای', 'navy': 'سرمه‌ای',
            'آبی آسمانی': 'آبی آسمانی', 'آسمانی': 'آبی آسمانی', 'آبی روشن': 'آبی آسمانی',
            'فیروزه‌ای': 'فیروزه‌ای', 'فیروزه ای': 'فیروزه‌ای', 'فیروزه': 'فیروزه‌ای', 'turkis': 'فیروزه‌ای', 'turquoise': 'فیروزه‌ای',
            
            # سبز و مشتقات
            'سبز': 'سبز', 'green': 'سبز', 'سبز روشن': 'سبز',
            'سبز تیره': 'سبز تیره', 'خاکی': 'سبز تیره', 'ارتشی': 'سبز تیره',
            'سبز یشمی': 'سبز', 'یشمی': 'سبز', 'سدری': 'سبز', 'سبز سدری': 'سبز',
            
            # قرمز و شرابی
            'قرمز': 'قرمز', 'red': 'قرمز',
            'شرابی': 'شرابی', 'زرشکی': 'شرابی', 'زرشگی': 'شرابی',
            'مارون': 'شرابی', 'maroon': 'شرابی', 'wine': 'شرابی', 'بوردو': 'شرابی',
            
            # صورتی و بنفش
            'صورتی': 'صورتی', 'pink': 'صورتی', 'گلبهی': 'صورتی',
            'بنفش': 'بنفش', 'purple': 'بنفش', 'یاسی': 'بنفش', 'violet': 'بنفش',
            
            # زرد و مشتقات
            'زرد': 'زرد', 'yellow': 'زرد', 'زرد روشن': 'زرد',
            'خردلی': 'خردلی', 'خردل': 'خردلی', 'mustard': 'خردلی',
            
            # طلایی و نقره‌ای
            'طلایی': 'طلایی', 'طلائی': 'طلایی', 'gold': 'طلایی',
            'نقره‌ای': 'نقره‌ای', 'نقره ای': 'نقره‌ای', 'نقره': 'نقره‌ای', 'silver': 'نقره‌ای',
            
            # نارنجی
            'نارنجی': 'نارنجی', 'orange': 'نارنجی', 'نارنجی روشن': 'نارنجی',
            'نارنجی سوخته': 'نارنجی سوخته', 'burnt orange': 'نارنجی سوخته',
            
            # برنزی
            'برنزی': 'برنزی', 'برنز': 'برنزی', 'bronze': 'برنزی', 'مسی': 'برنزی',
        }
        
        # الگوهای برای حذف کلمات اضافی
        self.remove_patterns = [
            r'\s*ساده\s*', r'\s*طرح\s*\d+', r'\s*\d+\s*', r'لویی\s*ویتون',
            r'پوست\s*ماری', r'داغی', r'طرح\s*دار', r'طرح‌دار', r'دراگون'
        ]
    
    def normalize_color(self, color_text):
        """تبدیل رنگ به فرمت استاندارد"""
        if not color_text:
            return None
        
        # پاکسازی اولیه
        color_clean = color_text.strip()
        
        # حذف کلمات اضافی
        for pattern in self.remove_patterns:
            color_clean = re.sub(pattern, '', color_clean, flags=re.IGNORECASE).strip()
        
        # تبدیل به lowercase برای مقایسه
        color_lower = color_clean.lower()
        
        # جستجو مستقیم در mapping
        if color_lower in self.color_mapping:
            return self.color_mapping[color_lower]
        
        # جستجو با حذف ی و ه های آخر
        color_variants = [
            color_lower,
            color_lower.rstrip('ی').rstrip('ه'),
            color_lower.replace('ی', 'ي'),
        ]
        
        for variant in color_variants:
            if variant in self.color_mapping:
                return self.color_mapping[variant]
        
        # بررسی اگر خود رنگ استاندارد باشد
        for std_color in self.standard_colors:
            if color_lower == std_color.lower():
                return std_color
        
        # تطبیق جزئی - اگر رنگ استاندارد در متن باشد
        for std_color in self.standard_colors:
            if std_color.lower() in color_lower:
                return std_color
        
        # اگر رنگ ترکیبی است، فقط کلمه اول را بگیر
        if ' ' in color_clean:
            first_word = color_clean.split()[0].lower()
            if first_word in self.color_mapping:
                return self.color_mapping[first_word]
            for std_color in self.standard_colors:
                if first_word == std_color.lower() or first_word in std_color.lower():
                    return std_color
        
        # اگر هیچ تطبیقی نشد، همان رنگ اصلی را برگردان
        return color_clean.strip()
    
    def parse_colors(self, colors_list):
        """تبدیل لیست رنگ‌ها به فرمت استاندارد"""
        return collect_unique_normalized_colors(colors_list, self.normalize_color)


def setup_driver():
    """Setup Chrome driver with optimized settings"""
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--lang=fa')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument('--headless=new')
    chrome_options.page_load_strategy = 'eager'

    try:
        driver = webdriver.Chrome(
            service=Service(r"C:\drivers\chromedriver.exe"),
            options=chrome_options
        )
        driver.maximize_window()
        driver.set_page_load_timeout(45)

        # بلاک کردن سرویس‌های آنالیتیکس که در ایران فیلتر هستند و باعث timeout می‌شوند
        driver.execute_cdp_cmd('Network.enable', {})
        driver.execute_cdp_cmd('Network.setBlockedURLs', {"urls": [
            "*google-analytics.com*",
            "*googletagmanager.com*",
            "*gtm.js*",
            "*analytics.js*",
            "*facebook.net*",
            "*doubleclick.net*",
        ]})
        print("  ✓ Blocked analytics/tracking scripts (GTM, GA, etc.)")
        print("  ✓ Browser ready")
        sys.stdout.flush()
        return driver
    except Exception as e:
        print(f"  ✗ Error: {e}")
        sys.stdout.flush()
        return None

def wait_for_page_load(driver, timeout=15):
    """Wait until page fully loads"""
    try:
        # Wait until JavaScript completes
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        print("  ✓ Page loaded")
        sys.stdout.flush()
        return True
    except Exception as e:
        print(f"  ⚠ Timeout: {e}")
        sys.stdout.flush()
        return False

def clean_price(price_text):
    """استخراج قیمت و حذف کاما و تومان"""
    return _clean_price_text(price_text)

def extract_price_smart(driver):
    """استخراج قیمت با روش‌های مختلف و هوشمند"""
    price_data = {'قیمت_اصلی': '', 'قیمت_فروش': ''}

    try:
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.woocommerce-Price-amount'))
            )
        except:
            pass

        # ══════════════════════════════════════════════════════
        # روش اصلی: خواندن مستقیم از المان قیمت WooCommerce
        # ساختار: <span class="woocommerce-Price-amount amount"><bdi>727,000&nbsp;<span class="woocommerce-Price-currencySymbol">تومان</span></bdi></span>
        # ══════════════════════════════════════════════════════
        try:
            def get_elem_text(elem):
                """خواندن متن المان با JavaScript - برای حل مشکل bdi"""
                text = driver.execute_script("return arguments[0].innerText;", elem) or ''
                if not text.strip():
                    text = elem.text or ''
                return text.strip()

            # قیمت خط‌خورده (قیمت اصلی بدون تخفیف)
            del_price_elem = driver.find_elements(By.CSS_SELECTOR, 'del .woocommerce-Price-amount, del .amount')
            # قیمت فروش
            ins_price_elem = driver.find_elements(By.CSS_SELECTOR, 'ins .woocommerce-Price-amount, ins .amount')

            if del_price_elem and ins_price_elem:
                # دو قیمت: خط‌خورده = اصلی، ins = فروش
                price_data['قیمت_اصلی'] = clean_price(get_elem_text(del_price_elem[0]))
                price_data['قیمت_فروش'] = clean_price(get_elem_text(ins_price_elem[0]))
                print(f"  ✓ Two prices: original={price_data['قیمت_اصلی']}, sale={price_data['قیمت_فروش']}")
                sys.stdout.flush()
                return price_data

            # یک قیمت: با JavaScript مستقیم از bdi بخوان
            price_via_js = driver.execute_script("""
                var selectors = [
                    'p.price .woocommerce-Price-amount bdi',
                    'p.price .woocommerce-Price-amount',
                    '.summary p.price bdi',
                    '.summary .woocommerce-Price-amount bdi',
                    '.woocommerce-Price-amount bdi',
                    '.woocommerce-Price-amount'
                ];
                for (var i = 0; i < selectors.length; i++) {
                    var el = document.querySelector(selectors[i]);
                    if (el) {
                        var text = el.innerText || el.textContent || '';
                        text = text.trim();
                        if (text) return text;
                    }
                }
                return '';
            """)

            if price_via_js and price_via_js.strip():
                cleaned = clean_price(price_via_js)
                if cleaned:
                    price_data['قیمت_اصلی'] = cleaned
                    print(f"  ✓ Price via JS: {price_data['قیمت_اصلی']}")
                    sys.stdout.flush()
                    return price_data

            # fallback: همه .woocommerce-Price-amount را بخوان با JS
            all_prices_js = driver.execute_script("""
                var elems = document.querySelectorAll('.woocommerce-Price-amount.amount');
                var results = [];
                elems.forEach(function(el) {
                    var text = el.innerText || el.textContent || '';
                    text = text.trim();
                    if (text) results.push(text);
                });
                return results;
            """)

            if all_prices_js:
                price_data['قیمت_اصلی'] = clean_price(all_prices_js[0])
                print(f"  ✓ Price from JS fallback: {price_data['قیمت_اصلی']}")
                sys.stdout.flush()
                return price_data

        except Exception as e:
            print(f"  ⚠ Error extracting price via CSS: {e}")
            sys.stdout.flush()

        # ══════════════════════════════════════════════════════
        # روش پشتیبان: regex در متن صفحه - محدود به منطقه summary
        # ══════════════════════════════════════════════════════
        try:
            # سعی کن فقط از بخش summary بخوان
            try:
                summary = driver.find_element(By.CSS_SELECTOR, '.summary, .product-summary, .entry-summary')
                search_text = summary.text
            except:
                search_text = driver.find_element(By.TAG_NAME, 'body').text

            # الگو: عدد (با کاما یا بدون) + تومان
            price_patterns = [
                r'([۰-۹\d][۰-۹\d,،٬\s]*[۰-۹\d])\s*تومان',
                r'قیمت[:\s]*([۰-۹\d][۰-۹\d,،٬\s]*[۰-۹\d])',
            ]

            found_prices = []
            for pattern in price_patterns:
                matches = re.findall(pattern, search_text)
                for match in matches:
                    cleaned = clean_price(match)
                    if cleaned and len(cleaned) >= 4:
                        found_prices.append(cleaned)

            # فقط قیمت‌های منحصربه‌فرد
            found_prices = list(dict.fromkeys(found_prices))

            if found_prices:
                if len(found_prices) >= 2:
                    # بزرگتر = اصلی، کوچکتر = فروش
                    sorted_prices = sorted(found_prices, key=lambda x: int(x) if x else 0, reverse=True)
                    price_data['قیمت_اصلی'] = sorted_prices[0]
                    price_data['قیمت_فروش'] = sorted_prices[1]
                else:
                    price_data['قیمت_اصلی'] = found_prices[0]

        except Exception as e:
            print(f"  ⚠ Error extracting price via regex: {e}")
            sys.stdout.flush()

    except Exception as e:
        print(f"  ⚠ Error extracting price: {e}")
        sys.stdout.flush()

    return price_data

def extract_colors_all(driver, color_parser, max_retries=3):
    """استخراج رنگ‌های موجود - فقط wd-enabled، بدون استانداردسازی"""
    for color_attempt in range(1, max_retries + 1):
      try:
        try:
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.wd-swatches-product'))
            )
        except:
            pass

        if color_attempt > 1:
            print(f"  → Color extraction attempt {color_attempt}/{max_retries}...")
        else:
            print("  → Starting color extraction...")
        sys.stdout.flush()

        # ══════════════════════════════════════════════════════
        # روش اصلی: فقط اولین div.wd-swatches-product
        # (جلوگیری از تکراری بخاطر container های مخفی)
        # فقط wd-enabled → wd-disabled نادیده گرفته می‌شود
        # ══════════════════════════════════════════════════════
        colors = []
        try:
            # صبر کن تا swatches لود بشن
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.wd-swatches-product div.wd-swatch'))
                )
            except:
                pass

            # فقط اولین container را بگیر
            container = driver.find_element(By.CSS_SELECTOR, 'div.wd-swatches-product')

            # همه swatch ها را بگیر (enabled و disabled)
            all_swatches = container.find_elements(By.CSS_SELECTOR, 'div.wd-swatch')
            enabled_swatches = [s for s in all_swatches
                                if 'wd-disabled' not in (s.get_attribute('class') or '')]

            print(f"  ✓ Found {len(all_swatches)} total swatches, {len(enabled_swatches)} enabled")
            sys.stdout.flush()

            # ── تشخیص: همه رنگ‌ها ناموجود (ضربدر) ──
            if all_swatches and not enabled_swatches:
                print(f"  ℹ All {len(all_swatches)} color(s) are out of stock — marking as OUT_OF_STOCK")
                sys.stdout.flush()
                return ['OUT_OF_STOCK']

            for swatch in enabled_swatches:
                color_name = swatch.get_attribute('data-title') or ''
                if not color_name:
                    try:
                        span = swatch.find_element(By.CSS_SELECTOR, 'span.wd-swatch-text')
                        color_name = span.text.strip()
                    except:
                        color_name = swatch.text.strip()
                if color_name:
                    colors.append(color_name.strip())

            print(f"  → Raw colors: {colors}")
            sys.stdout.flush()

        except Exception as e:
            print(f"  ⚠ wd-swatch method failed: {e}")
            sys.stdout.flush()

        # ══════════════════════════════════════════════════════
        # روش پشتیبان: از <select> - option های enabled
        # ══════════════════════════════════════════════════════
        if not colors:
            print("  → Trying select fallback...")
            sys.stdout.flush()
            try:
                color_selects = driver.find_elements(
                    By.CSS_SELECTOR,
                    'select[name*="رنگ"], select[id*="رنگ"], select[data-attribute_name*="رنگ"]'
                )
                all_option_count = 0
                for sel in color_selects:
                    options = sel.find_elements(By.CSS_SELECTOR, 'option')
                    for opt in options:
                        val = opt.get_attribute('value') or ''
                        text = opt.text.strip()
                        if val and text and text not in ['یک گزینه را انتخاب کنید', 'انتخاب کنید']:
                            all_option_count += 1
                            if not opt.get_attribute('disabled'):
                                colors.append(text)
                if all_option_count > 0 and not colors:
                    print(f"  ℹ All {all_option_count} option(s) are disabled — marking as OUT_OF_STOCK")
                    sys.stdout.flush()
                    return ['OUT_OF_STOCK']
                if colors:
                    print(f"  ✓ Colors from select: {colors}")
                    sys.stdout.flush()
            except Exception as e:
                print(f"  ⚠ Select fallback error: {e}")
                sys.stdout.flush()

        if colors:
            print(f"  ✓ Final colors ({len(colors)}): {colors}")
            sys.stdout.flush()
            return colors
        else:
            print(f"  ⚠ No colors found (attempt {color_attempt}/{max_retries})")
            sys.stdout.flush()
            if color_attempt < max_retries:
                print(f"  → Retrying color extraction in 3 seconds...")
                sys.stdout.flush()
                time.sleep(3)
                try:
                    driver.refresh()
                    wait_for_page_load(driver)
                except:
                    pass
            else:
                return []

      except Exception as e:
        print(f"  ✗ Error in extract_colors_all (attempt {color_attempt}): {str(e)}")
        sys.stdout.flush()
        if color_attempt < max_retries:
            time.sleep(3)
        else:
            return []
    return []


def extract_text_by_label(driver, label):
    """استخراج مقدار یک برچسب خاص با روش‌های متعدد"""
    try:
        # روش 1: XPath های مختلف
        xpaths = [
            f"//*[contains(text(), '{label}')]/following-sibling::*[1]",
            f"//th[contains(text(), '{label}')]/..//td",
            f"//td[contains(text(), '{label}')]/following-sibling::td",
            f"//span[contains(text(), '{label}')]/following-sibling::span",
            f"//div[contains(text(), '{label}')]/following-sibling::div",
            f"//label[contains(text(), '{label}')]/following-sibling::*",
            f"//dt[contains(text(), '{label}')]/following-sibling::dd[1]",
        ]
        
        for xpath in xpaths:
            try:
                elem = driver.find_element(By.XPATH, xpath)
                text = elem.text.strip()
                if text and text != label and len(text) < 200:  # محدودیت طول
                    return text
            except:
                continue
        
        # روش 2: جستجو در attributes table
        try:
            attr_rows = driver.find_elements(By.CSS_SELECTOR, 
                '.woocommerce-product-attributes-item, .product-attributes tr, table.shop_attributes tr')
            for row in attr_rows:
                row_text = row.text
                if label in row_text:
                    # جدا کردن label و value
                    parts = row_text.split('\n')
                    if len(parts) >= 2:
                        for i, part in enumerate(parts):
                            if label in part and i + 1 < len(parts):
                                value = parts[i + 1].strip()
                                if value and value != label:
                                    return value
                    # یا با : جدا شده باشد
                    if ':' in row_text:
                        parts = row_text.split(':', 1)
                        if label in parts[0]:
                            value = parts[1].strip()
                            if value:
                                return value
        except:
            pass
        
        # روش 3: جستجو در متن صفحه با regex patterns مختلف
        try:
            body_text = driver.find_element(By.TAG_NAME, 'body').text
            
            patterns = [
                f"{label}[:\\s]+([^\n]+)",  # label: value
                f"{label}\\s*:\\s*([^\n]+)",  # label : value
                f"{label}\\s+([^\n]+)",  # label value
                f"{re.escape(label)}[:\\s]+(.+?)(?:\n|$)",  # escape special chars
            ]
            
            for pattern in patterns:
                match = re.search(pattern, body_text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    # فیلتر کردن مقادیر نامعتبر
                    if value and value != label and len(value) < 200:
                        # حذف کلمات اضافی معمول
                        value = value.replace('انتخاب کنید', '').replace('پاک کردن', '').strip()
                        if value:
                            return value
        except:
            pass
        
        # روش 4: جستجو در meta tags
        try:
            meta_selectors = [
                f'meta[property*="{label}"]',
                f'meta[name*="{label}"]',
            ]
            for selector in meta_selectors:
                try:
                    elem = driver.find_element(By.CSS_SELECTOR, selector)
                    content = elem.get_attribute('content')
                    if content:
                        return content.strip()
                except:
                    continue
        except:
            pass
            
    except Exception as e:
        print(f"    ⚠ Error in extract_text_by_label for '{label}': {e}")
        sys.stdout.flush()
    
    return ''

def extract_product_details(driver, product_url, color_parser):
    """Extract complete product details with smart waiting"""
    print(f"\n  → {product_url}")
    sys.stdout.flush()
    
    product_data = {
        'شماره': '', 'نام_محصول': '', 'sku': '', 'مدل': '', 'دسته_بندی': '',
        'قیمت_اصلی': '', 'قیمت_فروش': '', 'رنگ': '', 'موجودی': '', 'وضعیت': 'OK',
        'تعداد_عکس_گالری': '', 'کاربرد': '', 'محفظه_های_کیف': '',
        'نوع_کیف': '', 'نحوه_بسته_شدن_کیف': '', 'جنس_آستر': '',
        'بند_بلند': '', 'تعداد_جیب_داخلی': '', 'تعداد_جیب_بیرونی': '',
        'تعداد_بند': '', 'جنس_رویه': '', 'مناسب_برای': '',
        'طول': '', 'عرض': '', 'کف': '',
        'توضیحات_کوتاه': '', 'توضیحات_کامل': ''
    }
    
    try:
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                driver.get(product_url)
                print("  → Loading page...")
                sys.stdout.flush()
                
                # Wait until page fully loads
                wait_for_page_load(driver)
                break  # Success
                
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    print(f"  ❌ Failed after {max_retries} attempts")
                    raise
                print(f"  ⚠ Connection error, retrying ({retry_count}/{max_retries})...")
                sys.stdout.flush()
                time.sleep(5)
        
        # Extract product title
        try:
            title_selectors = ['h1', '.product-title', '.entry-title', '.product_title', '[class*="product-name"]']
            for selector in title_selectors:
                try:
                    title = driver.find_element(By.CSS_SELECTOR, selector)
                    product_data['نام_محصول'] = title.text.strip()
                    if product_data['نام_محصول']:
                        break
                except:
                    continue
            
            # Extract model code from title
            # حالت‌های مختلف: "کد 9360"، "مدل 9360"، یا عدد در انتهای نام بدون کلمه کد
            if product_data['نام_محصول']:
                model_match = re.search(r'(?:کد|مدل)\s*([A-Za-z]?\d{3,})\s*$', product_data['نام_محصول'])
                if not model_match:
                    # fallback: هر عدد ۳+ رقمی در انتهای نام
                    model_match = re.search(r'([A-Za-z]?\d{3,})\s*$', product_data['نام_محصول'])
                if model_match:
                    product_data['مدل'] = model_match.group(1)
                    product_data['sku'] = model_match.group(1)
        except Exception as e:
            print(f"    ⚠ Error extracting title: {e}")
            sys.stdout.flush()
        
        # Extract category
        try:
            breadcrumb = driver.find_elements(By.CSS_SELECTOR, '.breadcrumb a, .woocommerce-breadcrumb a')
            if len(breadcrumb) > 1:
                product_data['دسته_بندی'] = breadcrumb[-1].text.strip()
        except:
            pass
        
        # Extract price
        price_data = extract_price_smart(driver)
        product_data['قیمت_اصلی'] = price_data['قیمت_اصلی']
        product_data['قیمت_فروش'] = price_data['قیمت_فروش']
        
        # Extract colors
        colors = extract_colors_all(driver, color_parser)
        if colors == ['OUT_OF_STOCK']:
            product_data['رنگ'] = 'OUT_OF_STOCK'
            product_data['موجودی'] = 'ناموجود'
            product_data['وضعیت'] = 'OUT_OF_STOCK'
        elif colors:
            product_data['رنگ'] = ' | '.join(colors)
        
        # Count gallery images
        try:
            gallery_selectors = [
                '.woocommerce-product-gallery__image',
                '.product-gallery img',
                '.product-images img',
                '[class*="gallery"] img'
            ]
            max_count = 0
            for selector in gallery_selectors:
                try:
                    images = driver.find_elements(By.CSS_SELECTOR, selector)
                    max_count = max(max_count, len(images))
                except:
                    continue
            product_data['تعداد_عکس_گالری'] = max_count if max_count > 0 else ''
            # Also collect image URLs from the gallery selectors (prioritise large images)
            image_urls = []
            try:
                for selector in gallery_selectors:
                    try:
                        elems = driver.find_elements(By.CSS_SELECTOR, selector)
                        for el in elems:
                            img_url = ''
                            try:
                                img_url = el.get_attribute('data-large_image') or el.get_attribute('data-src') or el.get_attribute('data-lazy-src') or el.get_attribute('src')
                            except:
                                try:
                                    img = el.find_element(By.TAG_NAME, 'img')
                                    img_url = img.get_attribute('data-large_image') or img.get_attribute('data-src') or img.get_attribute('src')
                                except:
                                    img_url = ''
                            if img_url:
                                full = urljoin(product_url, img_url)
                                if full not in image_urls:
                                    image_urls.append(full)
                    except:
                        continue
            except Exception:
                image_urls = []

            if image_urls:
                # Limit to first 12 images to avoid huge manifests
                product_data['image_urls'] = '|'.join(image_urls[:12])
            else:
                product_data['image_urls'] = ''
        except:
            pass
        
        # استخراج مشخصات
        print("  → Extracting specifications...")
        sys.stdout.flush()
        
        # ابتدا دکمه "نمایش بیشتر" را کلیک کن (اگر وجود دارد)
        try:
            try:
                show_more_btn = driver.find_element(By.XPATH, "//button[contains(., 'نمایش') and contains(., 'بیشتر')]")
                driver.execute_script("arguments[0].scrollIntoView(true);", show_more_btn)
                time.sleep(0.5)
                show_more_btn.click()
                time.sleep(1)
            except:
                try:
                    show_more_btn = driver.find_element(By.CSS_SELECTOR, 'button.text-zinc-600')
                    driver.execute_script("arguments[0].scrollIntoView(true);", show_more_btn)
                    time.sleep(0.5)
                    show_more_btn.click()
                    time.sleep(1)
                except:
                    pass
        except:
            pass
        
        # ══════════════════════════════════════════════════════
        # استخراج ابعاد از جدول woocommerce-product-attributes
        # ساختار: <td>35 × 11 × 25 سانتیمتر</td>
        # ══════════════════════════════════════════════════════
        try:
            dim_selectors = [
                'tr.woocommerce-product-attributes-item--dimensions td.woocommerce-product-attributes-item__value',
                '.woocommerce-product-attributes-item--dimensions .woocommerce-product-attributes-item__value',
                'tr.woocommerce-product-attributes-item--dimensions td',
            ]
            for dim_sel in dim_selectors:
                try:
                    dim_elem = driver.find_element(By.CSS_SELECTOR, dim_sel)
                    dim_text = dim_elem.text.strip()
                    if not dim_text:
                        dim_text = (dim_elem.get_attribute('data-o_content') or '').strip()
                    if dim_text:
                        print(f"  → Raw dimensions: {dim_text}")
                        sys.stdout.flush()
                        dim_clean = dim_text.replace('سانتیمتر', '').replace('cm', '').strip()
                        parts = re.split(r'\s*[×x×]\s*', dim_clean)
                        parts = [p.strip() for p in parts if p.strip()]
                        if len(parts) >= 3:
                            product_data['طول'] = parts[0] + 'cm'
                            product_data['کف']  = parts[1] + 'cm'
                            product_data['عرض'] = parts[2] + 'cm'
                            print(f"  ✓ Dimensions: L={product_data['طول']}, D={product_data['کف']}, W={product_data['عرض']}")
                            sys.stdout.flush()
                        elif len(parts) == 2:
                            product_data['طول'] = parts[0] + 'cm'
                            product_data['عرض'] = parts[1] + 'cm'
                        break
                except:
                    continue
        except Exception as e:
            print(f"  ⚠ Error extracting dimensions: {e}")
            sys.stdout.flush()

        specs_mapping = {
            'طول': ['طول', 'length', 'طول کیف', 'طول محصول'],
            'عرض': ['عرض', 'width', 'عرض کیف', 'عرض محصول'],
            'کف': ['کف', 'depth', 'ارتفاع', 'کف کیف'],
            'کاربرد': ['کاربرد', 'usage', 'نوع استفاده', 'کاربری'],
            'محفظه_های_کیف': ['محفظه', 'محفظه های کیف', 'تعداد محفظه', 'محفظه ها'],
            'نوع_کیف': ['نوع کیف', 'نوع', 'مدل کیف'],
            'نحوه_بسته_شدن_کیف': ['نحوه بسته شدن', 'بسته شدن', 'نوع بسته شدن', 'قفل'],
            'جنس_آستر': ['جنس آستر', 'آستر', 'جنس داخل', 'آستر کیف'],
            'بند_بلند': ['بند بلند'],
            'تعداد_جیب_داخلی': ['تعداد جیب داخلی', 'جیب داخلی'],
            'تعداد_جیب_بیرونی': ['تعداد جیب بیرونی', 'جیب بیرونی'],
            'تعداد_بند': ['تعداد بند'],
            'جنس_رویه': ['جنس رویه', 'رویه', 'جنس خارجی', 'جنس بیرونی', 'جنس'],
            'مناسب_برای': ['مناسب برای', 'مناسب', 'کاربری', 'استفاده برای']
        }
        
        page_text = driver.find_element(By.TAG_NAME, 'body').text
        
        # 🔥 روش 0: استخراج از ساختار خاص سایت (با CSS Selector)
        try:
            # پیدا کردن همه p های که شامل span.font-semibold هستند
            spec_paragraphs = driver.find_elements(By.CSS_SELECTOR, 'p.py-1')
            
            for para in spec_paragraphs:
                try:
                    # پیدا کردن label (span.font-semibold)
                    label_elem = para.find_element(By.CSS_SELECTOR, 'span.font-semibold')
                    label_text = label_elem.text.strip()
                    
                    # روش 1: پیدا کردن value از span.mr-1
                    value_elems = para.find_elements(By.CSS_SELECTOR, 'span.mr-1')
                    value_text = ''
                    
                    if value_elems:
                        # جمع کردن همه مقادیر (بعضی فیلدها چند span دارند)
                        values = [v.text.strip() for v in value_elems if v.text.strip()]
                        value_text = ' , '.join(values) if values else ''
                    
                    # روش 2: اگر span.mr-1 نبود، کل متن paragraph را بگیر و label را حذف کن
                    if not value_text:
                        full_text = para.text.strip()
                        # حذف label و :
                        value_text = full_text.replace(label_text, '').replace(':', '').strip()
                    
                    # اگر مقدار پیدا شد
                    if value_text:
                        # تطبیق با کلیدها
                        for key, labels in specs_mapping.items():
                            if not product_data[key]:
                                for label in labels:
                                    # تطبیق با case-insensitive و trim
                                    if label.strip().lower() == label_text.strip().lower():
                                        product_data[key] = value_text
                                        break
                                    # تطبیق جزئی (label در label_text باشد)
                                    elif label.strip().lower() in label_text.strip().lower():
                                        product_data[key] = value_text
                                        break
                except Exception as e:
                    continue
            
        except Exception as e:
            pass
        
        # روش 1: استفاده از تابع extract_text_by_label
        for key, labels in specs_mapping.items():
            if not product_data[key]:
                for label in labels:
                    value = extract_text_by_label(driver, label)
                    if value:
                        product_data[key] = value
                        break
        
        # روش 2: استخراج با regex patterns مستقیم از متن صفحه
        regex_patterns = {
            'طول': [
                r'طول\s*:\s*(\d+)\s*cm',
                r'طول[:\s]*(\d+)',
            ],
            'عرض': [
                r'عرض\s*:\s*(\d+)\s*cm',
                r'عرض[:\s]*(\d+)',
            ],
            'کف': [
                r'کف\s*:\s*(\d+)\s*cm',
                r'کف[:\s]*(\d+)',
            ],
            'نحوه_بسته_شدن_کیف': [
                r'نحوه بسته شدن\s*:\s*([^\n]+)',
                r'بسته شدن\s*:\s*([^\n]+)',
            ],
            'جنس_آستر': [
                r'جنس آستر\s*:\s*([^\n]+)',
                r'آستر\s*:\s*(ساتن|پارچه|چرم|ندارد|پارچه ای)',
            ],
            'جنس_رویه': [
                r'جنس رویه\s*:\s*([^\n]+)',
                r'رویه\s*:\s*([^\n]+)',
            ],
            'بند_بلند': [
                r'بند بلند\s*:\s*([^\n]+)',
                r'بند بلند\s*:\s*(دارد|ندارد)',
            ],
            'تعداد_جیب_داخلی': [
                r'تعداد جیب داخلی\s*:\s*(\d+)',
                r'جیب داخلی\s*:\s*(\d+)',
            ],
            'تعداد_جیب_بیرونی': [
                r'تعداد جیب بیرونی\s*:\s*(\d+)',
                r'جیب بیرونی\s*:\s*(\d+)',
            ],
            'تعداد_بند': [
                r'تعداد بند\s*:\s*(\d+)',
            ],
            'مناسب_برای': [
                r'مناسب برای\s*:\s*([^\n]+)',
                r'مناسب\s*:\s*([^\n]+)',
            ],
            'محفظه_های_کیف': [
                r'محفظه\s*:\s*(\d+)',
                r'تعداد محفظه\s*:\s*(\d+)',
            ],
            'کاربرد': [
                r'کاربرد\s*:\s*([^\n]+)',
            ],
        }
        
        for key, patterns in regex_patterns.items():
            if not product_data[key]:
                for pattern in patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        try:
                            value = match.group(1).strip()
                            value = value.replace('انتخاب کنید', '').replace(':', '').strip()
                            if value and len(value) < 100:
                                product_data[key] = value
                                break
                        except:
                            value = match.group(0).strip()
                            if value and len(value) < 100:
                                product_data[key] = value
                                break
        
        # روش 3: جستجو در جداول مشخصات
        try:
            spec_tables = driver.find_elements(By.CSS_SELECTOR, 
                'table.shop_attributes, .woocommerce-product-attributes, table.product-attributes, .specifications table')
            
            for table in spec_tables:
                rows = table.find_elements(By.CSS_SELECTOR, 'tr')
                for row in rows:
                    try:
                        cells = row.find_elements(By.CSS_SELECTOR, 'th, td')
                        if len(cells) >= 2:
                            label_text = cells[0].text.strip().lower()
                            value_text = cells[1].text.strip()
                            
                            for key, labels in specs_mapping.items():
                                if not product_data[key]:
                                    for label in labels:
                                        if label.lower() in label_text:
                                            product_data[key] = value_text
                                            break
                    except:
                        continue
        except:
            pass
        
        # روش 4: جستجوی خط‌به‌خط
        try:
            lines = page_text.split('\n')
            for i, line in enumerate(lines):
                line_clean = line.strip()
                
                if 'بند بلند' in line_clean and not product_data['بند_بلند']:
                    if ':' in line_clean:
                        parts = line_clean.split(':', 1)
                        if len(parts) == 2:
                            product_data['بند_بلند'] = parts[1].strip()
                    elif i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and len(next_line) < 50:
                            product_data['بند_بلند'] = next_line
                
                if 'تعداد بند' in line_clean and not product_data['تعداد_بند']:
                    if ':' in line_clean:
                        parts = line_clean.split(':', 1)
                        if len(parts) == 2:
                            product_data['تعداد_بند'] = parts[1].strip()
                    elif i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and next_line.isdigit():
                            product_data['تعداد_بند'] = next_line
                
                if 'تعداد جیب داخلی' in line_clean and not product_data['تعداد_جیب_داخلی']:
                    if ':' in line_clean:
                        parts = line_clean.split(':', 1)
                        if len(parts) == 2:
                            product_data['تعداد_جیب_داخلی'] = parts[1].strip()
                    elif i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and next_line.isdigit():
                            product_data['تعداد_جیب_داخلی'] = next_line
                
                if 'تعداد جیب بیرونی' in line_clean and not product_data['تعداد_جیب_بیرونی']:
                    if ':' in line_clean:
                        parts = line_clean.split(':', 1)
                        if len(parts) == 2:
                            product_data['تعداد_جیب_بیرونی'] = parts[1].strip()
                    elif i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and next_line.isdigit():
                            product_data['تعداد_جیب_بیرونی'] = next_line
                
                if 'مناسب برای' in line_clean and not product_data['مناسب_برای']:
                    if ':' in line_clean:
                        parts = line_clean.split(':', 1)
                        if len(parts) == 2:
                            product_data['مناسب_برای'] = parts[1].strip()
                    elif i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and len(next_line) < 100:
                            product_data['مناسب_برای'] = next_line
        except:
            pass
        
        # اضافه کردن واحد cm به ابعاد اگر ندارند
        for dim in ['طول', 'عرض', 'کف']:
            if product_data[dim] and 'cm' not in product_data[dim].lower():
                if product_data[dim].replace('.', '').isdigit():
                    product_data[dim] = product_data[dim] + 'cm'
        
        # 🔧 پاکسازی و تبدیل جداکننده‌ها به |
        # فیلدهایی که ممکن است چند مقدار داشته باشند
        multi_value_fields = [
            'کاربرد', 'مناسب_برای', 'نحوه_بسته_شدن_کیف'
            # حذف 'رنگ' از اینجا چون قبلاً پردازش شده
        ]
        
        for field in multi_value_fields:
            if product_data[field]:
                value = product_data[field]
                # بررسی اینکه value یک string است
                if isinstance(value, str):
                    # تبدیل , به |
                    value = value.replace(' , ', '|').replace(',', '|')
                    # حذف فاصله‌های اضافی
                    parts = [p.strip() for p in value.split('|') if p.strip()]
                    # حذف تکراری‌ها
                    unique_parts = []
                    for p in parts:
                        if p not in unique_parts:
                            unique_parts.append(p)
                    # ترکیب با |
                    product_data[field] = ' | '.join(unique_parts) if unique_parts else value
                elif isinstance(value, list):
                    # اگر لیست است، مستقیماً به string تبدیل کن
                    product_data[field] = ' | '.join(value)
        
        # استخراج توضیحات کوتاه
        try:
            short_desc_selectors = [
                '.woocommerce-product-details__short-description',
                '.short-description',
                '[class*="short-desc"]'
            ]
            for selector in short_desc_selectors:
                try:
                    elem = driver.find_element(By.CSS_SELECTOR, selector)
                    product_data['توضیحات_کوتاه'] = elem.text.strip()
                    if product_data['توضیحات_کوتاه']:
                        break
                except:
                    continue
        except:
            pass
        
        # استخراج توضیحات کامل
        try:
            full_desc_selectors = [
                '.woocommerce-Tabs-panel--description',
                '#tab-description',
                '.product-description',
                '[class*="full-desc"]'
            ]
            for selector in full_desc_selectors:
                try:
                    elem = driver.find_element(By.CSS_SELECTOR, selector)
                    product_data['توضیحات_کامل'] = elem.text.strip()
                    if product_data['توضیحات_کامل']:
                        break
                except:
                    continue
        except:
            pass
        
        print(f"  ✓ Extracted: {product_data['نام_محصول']}")
        sys.stdout.flush()
        
        return product_data
        
    except Exception as e:
        print(f"  ✗ Error extracting product: {str(e)}")
        sys.stdout.flush()
        import traceback
        print(f"    Details: {traceback.format_exc()[:200]}")
        return product_data


# ========================================
# Progress Management Functions
# ========================================

def save_progress(current_index, total, output_file='progress.json'):
    """Save current progress to resume later"""
    progress_data = {
        'last_processed_index': current_index,
        'total_products': total,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'output_file': output_file
    }
    try:
        save_json_state(PROGRESS_FILE, progress_data)
        print(f"  💾 Progress saved: {current_index}/{total}")
    except Exception as e:
        print(f"  ⚠ Could not save progress: {e}")
        sys.stdout.flush()

def load_progress():
    """Load progress from previous run"""
    try:
        if not os.path.exists(PROGRESS_FILE):
            return None
        progress_data = load_json_state(PROGRESS_FILE)
        print(f"\n📂 Found previous progress:")
        sys.stdout.flush()
        print(f"   Last processed: {progress_data['last_processed_index']}/{progress_data['total_products']}")
        sys.stdout.flush()
        print(f"   Timestamp: {progress_data['timestamp']}")
        return progress_data
    except Exception as e:
        print(f"  ⚠ Could not load progress: {e}")
        sys.stdout.flush()
        return None

def clear_progress():
    """Clear progress file after completion"""
    try:
        if safe_delete(PROGRESS_FILE, missing_ok=False):
            print("\n🗑️  Progress file cleared")
    except:
        pass

def load_existing_results(output_file):
    """Load existing results from output file"""
    try:
        if os.path.exists(output_file):
            df = read_excel(output_file, dtype={'sku': str, 'مدل': str, 'شماره': str})
            # strip whitespace from string columns to avoid matching issues
            for col in ['sku', 'مدل', 'شماره']:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
            print(f"\n📊 Found existing results: {len(df)} products")
            sys.stdout.flush()
            return df
        return None
    except Exception as e:
        print(f"  ⚠ Could not load existing results: {e}")
        sys.stdout.flush()
        return None

def save_incremental_results(all_products, output_file, failed_products=None, preserve_failed_sheet=False):
    """Save results incrementally (after each product).
    
    preserve_failed_sheet=True: if failed_products is empty, reads the previous
    failed sheet from the file and preserves it so it is not wiped during retry.
    """
    try:
        columns_order = [
            'شماره', 'نام_محصول', 'sku', 'مدل', 'دسته_بندی', 'قیمت_اصلی', 'قیمت_فروش',
            'رنگ', 'موجودی', 'وضعیت', 'تعداد_عکس_گالری', 'کاربرد', 'محفظه_های_کیف',
            'نوع_کیف', 'نحوه_بسته_شدن_کیف', 'جنس_آستر', 'بند_بلند',
            'تعداد_جیب_داخلی', 'تعداد_جیب_بیرونی', 'تعداد_بند', 'جنس_رویه',
            'مناسب_برای', 'طول', 'عرض', 'کف', 'توضیحات_کوتاه', 'توضیحات_کامل'
        ]
        
        df_output = pd.DataFrame(all_products)
        if 'وضعیت' not in df_output.columns:
            df_output['وضعیت'] = 'OK'
        df_output = df_output[columns_order]
        
        if failed_products is not None:
            # if failed list is empty but sheet must be preserved, read from file
            if not failed_products and preserve_failed_sheet and os.path.exists(output_file):
                try:
                    xl = pd.ExcelFile(output_file)
                    if 'محصولات_ناموفق' in xl.sheet_names:
                        df_prev_failed = read_excel(output_file, sheet_name='محصولات_ناموفق')
                        if not df_prev_failed.empty:
                            failed_products = df_prev_failed.to_dict('records')
                except Exception:
                    pass

            with excel_writer(output_file) as writer:
                df_output.to_excel(writer, sheet_name='محصولات', index=False)
                if failed_products:
                    df_failed = pd.DataFrame(failed_products)
                    df_failed.to_excel(writer, sheet_name='محصولات_ناموفق', index=False)
        else:
            write_dataframe(df_output, output_file)
    except Exception as e:
        print(f"  ⚠ Could not save incremental results: {e}")
        sys.stdout.flush()


# =============================================================================
# CHANGES NEEDED in product_spec_scraper_RESUME.py
# =============================================================================

# 1️⃣ Replace the main() function (from line 998 to end):

def load_failed_products(output_file):
    """Load failed products from the 'محصولات_ناموفق' sheet in the output file"""
    try:
        if os.path.exists(output_file):
            xl = pd.ExcelFile(output_file)
            if 'محصولات_ناموفق' in xl.sheet_names:
                df_failed = read_excel(output_file, sheet_name='محصولات_ناموفق')
                if not df_failed.empty and 'URL' in df_failed.columns:
                    print(f"\n⚠ Found {len(df_failed)} failed product(s) from previous run")
                    sys.stdout.flush()
                    return df_failed
        return None
    except Exception as e:
        print(f"  ⚠ Could not load failed products: {e}")
        sys.stdout.flush()
        return None


def upsert_product(all_products, product_data, num):
    """اگر محصول با همین شماره قبلاً وجود دارد جایگزین کن، وگرنه اضافه کن.
    
    وضعیت‌های ناقص (No Color / Failed) همیشه جایگزین می‌شوند تا داده‌ی
    تازه و کامل نگه داشته شود.
    """
    for idx_p, p in enumerate(all_products):
        if p.get('شماره') == num:
            prev_status = str(p.get('وضعیت', ''))
            new_status  = str(product_data.get('وضعیت', 'OK'))
            # همیشه با داده‌ی جدید جایگزین کن
            all_products[idx_p] = product_data
            print(f"  ↺ Replaced product #{num} (prev: {prev_status} → new: {new_status})")
            sys.stdout.flush()
            return
    all_products.append(product_data)


def main():
    """Main function with Resume capability - وضعیت از ستون اکسل خونده می‌شه"""
    # ── مسیرها ────────────────────────────────────────────────────────────
    REPORTS_DIR  = str(RUNTIME_REPORTS_DIR)
    os.makedirs(REPORTS_DIR, exist_ok=True)

    timestamp   = datetime.now().strftime('%Y%m%d_%H%M%S')
    input_file  = str(INTERMEDIATE_DIR / get_file('extracted_products'))
    output_file = str(OUTPUTS_DIR / get_file('product_details'))

    print("=" * 70)
    print("Product Details Extractor - Resume Enabled")
    sys.stdout.flush()
    print("=" * 70)

    existing_results     = load_existing_results(output_file)
    failed_from_previous = load_failed_products(output_file)

    has_results = existing_results is not None and not existing_results.empty
    has_failed  = failed_from_previous is not None and not failed_from_previous.empty

    # ── تعیین شماره‌های پردازش‌شده از ستون وضعیت ──
    # شماره همیشه به int تبدیل می‌شه تا مقایسه با product_numbers (که int هستند) درست باشه
    completed_numbers = set()
    if has_results and 'شماره' in existing_results.columns:
        for _, row in existing_results.iterrows():
            st = str(row.get('وضعیت', 'OK'))
            if st in ('OK', 'OUT_OF_STOCK'):
                try:
                    completed_numbers.add(int(row['شماره']))
                except (ValueError, TypeError):
                    pass

    retry_failed_only = False
    start_index = 0
    all_products = []
    retry_urls = retry_numbers = retry_names = None

    # Automatic mode: never prompt. But support resume if AUTO_RESUME is set.
    auto_mode = os.getenv('AUTO_MODE') == '1'
    auto_resume = os.getenv('AUTO_RESUME') == '1'

    if auto_mode and (has_results or has_failed):
        if auto_resume and has_results:
            # Auto resume: continue from where we left off
            all_products = existing_results.to_dict('records') if has_results else []
            for p in all_products:
                try:
                    p['شماره'] = int(p['شماره'])
                except (ValueError, TypeError):
                    pass
            completed_numbers = set()
            if 'شماره' in existing_results.columns:
                for _, row in existing_results.iterrows():
                    st = str(row.get('وضعیت', 'OK'))
                    if st in ('OK', 'OUT_OF_STOCK'):
                        try:
                            completed_numbers.add(int(row['شماره']))
                        except (ValueError, TypeError):
                            pass
            print(f"\n[AUTO] Automatic mode with resume - skipping {len(completed_numbers)} already processed")
            sys.stdout.flush()
        else:
            # Auto mode without resume: start fresh
            all_products      = []
            completed_numbers = set()
            clear_progress()
            print("\n[AUTO] Automatic mode - starting fresh (full scan), no prompts")
            sys.stdout.flush()
    elif has_results or has_failed:
        print(f"\n{'='*70}")
        print("📊 Previous run status:")

        if has_results:
            ok_count  = len([r for r in existing_results.to_dict('records')
                             if str(r.get('وضعیت', 'OK')) in ('OK', 'OUT_OF_STOCK')])
            oos_count = len([r for r in existing_results.to_dict('records')
                             if str(r.get('وضعیت', '')) == 'OUT_OF_STOCK'])
            print(f"   ✔ {ok_count} products processed ({oos_count} out of stock)")
        if has_failed:
            print(f"   ⚠ {len(failed_from_previous)} failed product(s):")
            for _, row in failed_from_previous.iterrows():
                print(f"      • {row.get('نام_محصول', 'Unknown')} — {row.get('علت', '?')}")

        print(f"{'='*70}")

        options = {}
        menu_lines = ["\n❓ What would you like to do?"]

        if completed_numbers:
            options['1'] = 'resume'
            menu_lines.append(f"   1 — Resume (skip {len(completed_numbers)} already processed)")
        if has_failed:
            options['2'] = 'retry'
            menu_lines.append(f"   2 — Retry {len(failed_from_previous)} failed product(s) only")
        options['3'] = 'fresh'
        menu_lines.append("   3 — Start from scratch (full scan)")

        valid = list(options.keys())
        menu_lines.append(f"\n   Your choice ({'/'.join(valid)}): ")

        print('\n'.join(menu_lines), end='')
        sys.stdout.flush()

        choice = input().strip()
        while choice not in valid:
            print(f"   ⚠ Please enter one of: {'/'.join(valid)}: ", end='')
            sys.stdout.flush()
            choice = input().strip()

        action = options[choice]

        if action == 'resume':
            all_products = existing_results.to_dict('records') if has_results else []
            # شماره رو به int نرمال کن تا upsert_product درست مقایسه کنه
            for p in all_products:
                try:
                    p['شماره'] = int(p['شماره'])
                except (ValueError, TypeError):
                    pass
            print(f"\n✓ Resume mode — {len(completed_numbers)} products will be skipped")

        elif action == 'retry':
            retry_failed_only = True
            all_products = existing_results.to_dict('records') if has_results else []
            # شماره رو به int نرمال کن
            for p in all_products:
                try:
                    p['شماره'] = int(p['شماره'])
                except (ValueError, TypeError):
                    pass
            retry_urls    = failed_from_previous['URL'].tolist()
            retry_numbers = failed_from_previous.get('شماره', pd.Series(range(len(retry_urls)))).tolist()
            retry_names   = failed_from_previous.get('نام_محصول', pd.Series(['']*len(retry_urls))).tolist()
            print(f"\n✓ Retry mode: {len(retry_urls)} failed product(s) will be re-scanned")

        else:  # fresh
            all_products      = []
            completed_numbers = set()
            clear_progress()
            print("\n✓ Starting fresh — full scan")

        sys.stdout.flush()
    
    # Initialize ColorParser
    color_manager = None
    if HAS_COLOR_MANAGER:
        try:
            color_manager = ColorManager(
                str(resolve_existing_path(
                    ROOT_DIR / get_file('color_mapping'),
                    ARCHIVES_DIR / get_file('color_mapping'),
                )),
                auto_create=True,
            )
            print(f"🎨 ColorManager: {len(color_manager.get_all_colors())} colors loaded")
        except:
            pass
    
    color_parser = ColorParser()
    
    print("\n→ Starting browser...")
    sys.stdout.flush()
    driver = setup_driver()
    
    if not driver:
        print("\n✗ Failed to start browser")
        sys.stdout.flush()
        return
    
    try:
        # ── حالت retry: فقط محصولات ناموفق ─────────────────────────────────
        if retry_failed_only:
            product_urls = retry_urls
            product_numbers = retry_numbers
            product_names_list = retry_names
            df_input = None
            print(f"\n🔄 Retry mode: processing {len(product_urls)} failed products only")
            sys.stdout.flush()
        else:
            print(f"\n→ Reading {input_file}...")
            sys.stdout.flush()
            df_input = read_excel(input_file)
        
        if not retry_failed_only:
            # Find URL column
            url_column = None
            for col in df_input.columns:
                if any(x in col.lower() for x in ['url', 'link', 'لینک']):
                    url_column = col
                    break
            
            if not url_column:
                print("✗ URL column not found!")
                sys.stdout.flush()
                driver.quit()
                return
            
            product_urls = df_input[url_column].tolist()
            product_numbers = list(range(1, len(product_urls) + 1))
            product_names_list = None
            remaining = len(product_urls) - len(completed_numbers)
            print(f"✓ Total: {len(product_urls)} products | Already done: {len(completed_numbers)} | Remaining: {remaining}")
            sys.stdout.flush()
        
        # لیست محصولاتی که رنگ نداشتن یا خطا داشتن
        failed_color_products = []
        
        # Process products
        for idx, url in enumerate(product_urls):
            i = product_numbers[idx]
            # update module-level progress
            try:
                CURRENT_PROGRESS_INDEX = i
                TOTAL_PRODUCTS = len(product_urls)
            except Exception:
                pass
            
            if not retry_failed_only and i in completed_numbers:
                print(f"[SKIP] Product #{i} already processed (وضعیت: OK/OUT_OF_STOCK)")
                sys.stdout.flush()
                continue
                
            if pd.notna(url) and str(url).strip():
                url = str(url).strip()
                
                total = len(product_urls)
                progress_pct = int(((idx + 1) / total) * 100)
                print(f"\n{'='*70}")
                print(f"Processing product {idx+1}/{total} ({progress_pct}%) [#: {i}]")
                sys.stdout.flush()
                
                # Get product name
                try:
                    if retry_failed_only:
                        product_name = product_names_list[idx] if product_names_list else url.split('/')[-1][:50]
                    elif df_input is not None:
                        if 'Product Name' in df_input.columns:
                            product_name = df_input.iloc[idx]['Product Name']
                        elif 'نام محصول' in df_input.columns:
                            product_name = df_input.iloc[idx]['نام محصول']
                        else:
                            product_name = url.split('/')[-1][:50]
                    else:
                        product_name = url.split('/')[-1][:50]
                except:
                    product_name = 'Unknown'
                
                print(f"Product: {product_name}")
                sys.stdout.flush()
                
                try:
                    product_data = extract_product_details(driver, url, color_parser)
                    product_data['شماره'] = i
                    
                    upsert_product(all_products, product_data, i)
                    
                    # ردیابی محصولاتی که رنگ نداشتن
                    if not product_data.get('رنگ'):
                        product_data['وضعیت'] = 'No Color'
                        failed_color_products.append({
                            'شماره': i,
                            'نام_محصول': product_data.get('نام_محصول', product_name),
                            'URL': url,
                            'علت': 'No color found'
                        })
                        print(f"  ⚠ Added to failed list: no color found")
                        sys.stdout.flush()
                    elif product_data.get('وضعیت') == 'OUT_OF_STOCK':
                        print(f"  ℹ Product #{i} all colors out of stock — not added to failed list")
                        sys.stdout.flush()

                    # وضعیت رو در completed_numbers ثبت کن (فقط OK و OUT_OF_STOCK)
                    if product_data.get('وضعیت') in ('OK', 'OUT_OF_STOCK'):
                        completed_numbers.add(i)

                    print(f"✓ Product {i} completed — وضعیت: {product_data.get('وضعیت', 'OK')}")
                    sys.stdout.flush()

                    # Save results (بدون JSON)
                    save_incremental_results(all_products, output_file, failed_color_products,
                                             preserve_failed_sheet=retry_failed_only)
                    
                    if idx + 1 < len(product_urls):
                        time.sleep(2)
                        
                except Exception as e:
                    print(f"\n❌ Error on product {i}: {e}")
                    sys.stdout.flush()
                    failed_color_products.append({
                        'شماره': i,
                        'نام_محصول': product_name,
                        'URL': url,
                        'علت': f'Error: {str(e)[:120]}'
                    })
                    # محصول خطادار رو با وضعیت Failed در لیست اضافه کن
                    error_stub = {k: '' for k in [
                        'شماره', 'نام_محصول', 'sku', 'مدل', 'دسته_بندی',
                        'قیمت_اصلی', 'قیمت_فروش', 'رنگ', 'موجودی', 'وضعیت',
                        'تعداد_عکس_گالری', 'کاربرد', 'محفظه_های_کیف',
                        'نوع_کیف', 'نحوه_بسته_شدن_کیف', 'جنس_آستر', 'بند_بلند',
                        'تعداد_جیب_داخلی', 'تعداد_جیب_بیرونی', 'تعداد_بند', 'جنس_رویه',
                        'مناسب_برای', 'طول', 'عرض', 'کف', 'توضیحات_کوتاه', 'توضیحات_کامل'
                    ]}
                    error_stub['شماره'] = i
                    error_stub['نام_محصول'] = product_name
                    error_stub['وضعیت'] = 'Failed'
                    upsert_product(all_products, error_stub, i)
                    save_incremental_results(all_products, output_file, failed_color_products,
                                             preserve_failed_sheet=retry_failed_only)
                    print(f"  ⚠ Skipped. Continuing with next product...")
                    sys.stdout.flush()
                    time.sleep(3)
        
        # ── راند retry برای محصولات fail‌شده ──────────────────────────────
        # فقط محصولاتی که به‌خاطر خطا (نه فقط رنگ ندارند) fail شدند را retry می‌کنیم
        hard_failed = [p for p in failed_color_products if p.get('علت', '').startswith('Error')]
        if hard_failed:
            print(f"\n{'='*70}")
            print(f"🔄 Retry round: {len(hard_failed)} failed products")
            print(f"{'='*70}")
            sys.stdout.flush()

            still_failed_after_retry = []
            for failed_item in hard_failed:
                f_url = failed_item['URL']
                f_num = failed_item['شماره']
                f_name = failed_item['نام_محصول']
                print(f"\n→ Retrying product {f_num}: {f_name}")
                sys.stdout.flush()

                success = False
                for attempt in range(1, 4):  # 3 بار تلاش
                    print(f"  Attempt {attempt}/3...")
                    sys.stdout.flush()
                    try:
                        product_data = extract_product_details(driver, f_url, color_parser)
                        product_data['شماره'] = f_num
                        upsert_product(all_products, product_data, f_num)
                        print(f"  ✓ Success on attempt {attempt}")
                        sys.stdout.flush()
                        success = True
                        break
                    except Exception as retry_e:
                        print(f"  ✗ Attempt {attempt} failed: {str(retry_e)[:80]}")
                        sys.stdout.flush()
                        if attempt < 3:
                            time.sleep(attempt * 3)

                if not success:
                    print(f"  ✗ Gave up after 3 attempts")
                    sys.stdout.flush()
                    still_failed_after_retry.append(failed_item)

            # به‌روزرسانی لیست fail‌شده‌ها
            # حذف موارد retry‌شده و نگه‌داشتن موارد بدون رنگ + موارد هنوز fail
            color_only_failed = [p for p in failed_color_products if not p.get('علت', '').startswith('Error')]
            failed_color_products = color_only_failed + still_failed_after_retry

            print(f"\n✓ Retry complete — success: {len(hard_failed) - len(still_failed_after_retry)}, still failed: {len(still_failed_after_retry)}")
            sys.stdout.flush()

        # Final save
        print("\n" + "="*70)
        if all_products:
            columns_order = [
                'شماره', 'نام_محصول', 'sku', 'مدل', 'دسته_بندی', 'قیمت_اصلی', 'قیمت_فروش',
                'رنگ', 'موجودی', 'وضعیت', 'تعداد_عکس_گالری', 'کاربرد', 'محفظه_های_کیف',
                'نوع_کیف', 'نحوه_بسته_شدن_کیف', 'جنس_آستر', 'بند_بلند',
                'تعداد_جیب_داخلی', 'تعداد_جیب_بیرونی', 'تعداد_بند', 'جنس_رویه',
                'مناسب_برای', 'طول', 'عرض', 'کف', 'توضیحات_کوتاه', 'توضیحات_کامل'
            ]
            # مرتب‌سازی بر اساس شماره
            all_products_sorted = sorted(all_products, key=lambda x: x.get('شماره', 0))
            df_output = pd.DataFrame(all_products_sorted)[columns_order]
            
            # تعیین لیست نهایی ناموفق‌ها (قبل از باز کردن فایل برای نوشتن)
            final_failed = failed_color_products
            # در حالت retry اگه لیست جدید خالیه، شیت قبلی رو حفظ کن
            if retry_failed_only and not final_failed and os.path.exists(output_file):
                try:
                    xl = pd.ExcelFile(output_file)
                    if 'محصولات_ناموفق' in xl.sheet_names:
                        df_prev = read_excel(output_file, sheet_name='محصولات_ناموفق')
                        final_failed = df_prev.to_dict('records') if not df_prev.empty else []
                except Exception:
                    pass

            with excel_writer(output_file) as writer:
                df_output.to_excel(writer, sheet_name='محصولات', index=False)

                if final_failed:
                    df_failed = pd.DataFrame(final_failed)
                    df_failed.to_excel(writer, sheet_name='محصولات_ناموفق', index=False)
                    print(f"⚠ {len(final_failed)} products saved to 'Failed Products' sheet")
                    sys.stdout.flush()
            
            print(f"✓ Extracted {len(all_products)} products")
            sys.stdout.flush()
            print(f"✓ File saved: {output_file}")
            sys.stdout.flush()
            
            # ── ذخیره دو نسخه تاریخ‌دار ──────────────────────────────
            import shutil
            dated_name = f'product_details_{timestamp}.xlsx'

            # کپی تاریخ‌دار فقط در پوشه reports
            report_dated = os.path.join(REPORTS_DIR, dated_name)
            shutil.copy2(output_file, report_dated)
            print(f'✓ Reports dated file: {report_dated}')
            sys.stdout.flush()

            # Show sample
            print("\n📋 Sample:")
            sample = df_output[['شماره', 'نام_محصول', 'قیمت_اصلی', 'رنگ']].head(3)
            print(sample.to_string(index=False))
        
        print("="*70)
        
        # Clear progress file when complete
        if retry_failed_only:
            retry_success = len([p for p in failed_color_products]) 
            still_failed = len(failed_color_products)
            retried_count = len(retry_urls)
            success_count = retried_count - still_failed
            print(f"\n✅ Retry complete: {success_count}/{retried_count} products fixed")
            if still_failed == 0:
                print("🎉 All previously failed products are now successful!")
            sys.stdout.flush()
        elif len(all_products) >= len(product_urls):
            clear_progress()
            print("\n✅ All products processed successfully!")
            sys.stdout.flush()
        
    except FileNotFoundError:
        print(f"\n✗ File not found: {input_file}")
        sys.stdout.flush()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.stdout.flush()
        import traceback
        print(traceback.format_exc()[:500])
    finally:
        print("\n→ Closing browser...")
        sys.stdout.flush()
        try:
            driver.quit()
            print("✓ Done")
            sys.stdout.flush()
        except:
            pass


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║     Product Extractor - FIXED Resume Version                      ║
    ║     Data preservation issue resolved ✓                            ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    required = ['selenium', 'pandas', 'openpyxl']
    missing = [pkg for pkg in required
               if not __import__('importlib').util.find_spec(pkg)]

    if missing:
        print("⚠ Missing packages:")
        sys.stdout.flush()
        for pkg in missing:
            print(f"  - {pkg}")
        print(f"\nInstall: pip install {' '.join(missing)}")
    else:
        print("✓ All packages installed\n")
        sys.stdout.flush()
        main()

