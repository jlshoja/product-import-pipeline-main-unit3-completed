#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration File - Version 9.0
تنظیمات جامع برای سیستم مدیریت عکس
"""

from pathlib import Path

# ======================
# تنظیمات پوشه‌ها و URL
# ======================

# ======================
# پوشه منبع عکس‌ها
# ======================
# مسیر پایه‌ای که زیرپوشه‌های تاریخ‌دار در آن ذخیره می‌شوند
# فرمت زیرپوشه‌ها: 2026-06-11_11-52-23
SOURCE_IMAGES_BASE = r"C:\Users\Jalil Shojazade\Desktop\Luxbaz_product_import\3_Imagetools\output"

# تابع پیدا کردن آخرین پوشه تاریخ‌دار
def get_latest_images_folder():
    """
    آخرین زیرپوشه تاریخ‌دار را در SOURCE_IMAGES_BASE پیدا می‌کند
    فرمت: 2026-06-11_11-52-23
    اگر پوشه‌ای پیدا نشد، همان مسیر پایه را برمی‌گرداند
    """
    import os, re
    base = SOURCE_IMAGES_BASE

    if not os.path.exists(base):
        return base

    pattern = re.compile(r'^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$')
    dated_folders = [
        f for f in os.listdir(base)
        if os.path.isdir(os.path.join(base, f)) and pattern.match(f)
    ]

    if not dated_folders:
        return base

    latest = sorted(dated_folders)[-1]   # مرتب‌سازی رشته‌ای کافی است (فرمت ISO)
    return os.path.join(base, latest)

# مسیر نهایی عکس‌ها — همیشه از این متغیر استفاده کنید
SOURCE_IMAGES_FOLDER = get_latest_images_folder()

# سال/ماه جاری — بر اساس تاریخ اجرای برنامه (به‌صورت خودکار به‌روز می‌شود)
from datetime import datetime as _datetime
_CURRENT_YEAR_MONTH = _datetime.now().strftime("%Y/%m")

# پوشه مقصد در سرور (کپی نهایی عکس‌ها)
DESTINATION_IMAGES_FOLDER = f"/home/luxbazco/public_html/wp-content/uploads/{_CURRENT_YEAR_MONTH}"

# URL پایه برای دسترسی به عکس‌ها
BASE_IMAGES_URL = f"https://luxbaz.com/wp-content/uploads/{_CURRENT_YEAR_MONTH}/"

# ======================
# تنظیمات نام‌گذاری عکس‌ها
# ======================

# الگوی نام‌گذاری منبع
# {index} = شماره محصول (1, 2, 3, ...)
# {letter} = حرف (a, b, c, ...)
SOURCE_IMAGE_PATTERN = "{index}{letter}"

# الگوی نام‌گذاری مقصد
# {product} = نام محصول انگلیسی
# {model} = مدل
# {color} = رنگ
# {type} = نوع (main, general)
TARGET_IMAGE_PATTERN = "{product}-{model}-{color}.jpg"

# ======================
# منطق تخصیص عکس‌ها
# ======================

# عکس اول (1a, 2a, ...) = عکس اصلی (main)
FIRST_IMAGE_TYPE = "main"

# عکس‌های بعدی = رنگ‌ها
# مثال: 1b=red, 1c=black, 1d=blue

# عکس‌های اضافی (بیشتر از رنگ‌ها) = general
EXTRA_IMAGE_TYPE = "general"

# فرمت شماره‌گذاری general (01, 02, 03, ...)
GENERAL_IMAGE_FORMAT = "general-{number:02d}"

# ======================
# تنظیمات فرمت فایل
# ======================

# پسوندهای مجاز برای عکس‌های منبع
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']

# پسوند پیش‌فرض برای عکس‌های خروجی
DEFAULT_OUTPUT_EXTENSION = '.jpg'

# ======================
# تنظیمات CSV
# ======================

# ستون‌های مربوط به عکس در CSV خروجی
CSV_IMAGE_COLUMNS = {
    'main': 'images',
    'gallery': 'gallery_images',
    'filename': 'image_filename'
}

# ======================
# تنظیمات پیشرفته
# ======================

# آیا عکس‌های موجود را جایگزین کنیم؟
OVERWRITE_EXISTING_IMAGES = True

# آیا عکس‌ها رو رِسایز کنیم؟
RESIZE_IMAGES = False
RESIZE_MAX_WIDTH = 1920
RESIZE_MAX_HEIGHT = 1920
RESIZE_QUALITY = 85

# آیا Watermark اضافه کنیم؟
ADD_WATERMARK = False
WATERMARK_IMAGE = r"E:\Luxbaz\watermark.png"
WATERMARK_POSITION = "bottom-right"  # top-left, top-right, bottom-left, bottom-right, center
WATERMARK_OPACITY = 0.7

# ======================
# تنظیمات تبدیل به WEBP
# ======================

# آیا عکس‌ها رو به WEBP تبدیل کنیم؟
CONVERT_TO_WEBP = True  # ✅ عکس‌های منبع webp هستند

# کیفیت WEBP (1-100)
WEBP_QUALITY = 85

# حذف فایل‌های اصلی بعد از تبدیل؟
DELETE_ORIGINALS_AFTER_WEBP = False

# پسوند خروجی (اگر CONVERT_TO_WEBP فعال باشد)
OUTPUT_IMAGE_EXTENSION = '.webp' if CONVERT_TO_WEBP else '.jpg'

# ======================
# تنظیمات لاگ و گزارش
# ======================

# نمایش پیشرفت
SHOW_PROGRESS = True

# ذخیره لاگ در فایل
SAVE_LOG_FILE = True
LOG_FILE_PATH = str(Path(__file__).resolve().parent.parent / "runtime" / "logs" / "image_processing_log.txt")

# ======================
# تنظیمات Terminal
# ======================

# زبان منوها در Terminal
TERMINAL_LANGUAGE = "en"  # "en" or "fa"

# پیام‌های انگلیسی
MESSAGES_EN = {
    'welcome': "🚀 WooCommerce Product Generator - Version 9.0",
    'menu_title': "Main Menu:",
    'option_1': "Create sample input file",
    'option_2': "Process products (Excel → CSV)",
    'option_3': "Process images (Rename & Upload)",
    'option_4': "Complete workflow (Excel → CSV → Images)",
    'option_5': "Generate AI descriptions",
    'option_6': "Exit",
    'select': "Select option (1-6): ",
    'processing': "Processing...",
    'success': "✅ Success!",
    'error': "❌ Error:",
    'file_not_found': "File not found:",
    'stats_title': "Statistics:",
}

# پیام‌های فارسی
MESSAGES_FA = {
    'welcome': "🚀 تولیدکننده محصولات ووکامرس - نسخه 9.0",
    'menu_title': "منوی اصلی:",
    'option_1': "ساخت فایل نمونه",
    'option_2': "پردازش محصولات (Excel ← CSV)",
    'option_3': "پردازش عکس‌ها (تغییر نام و آپلود)",
    'option_4': "فرآیند کامل (Excel ← CSV ← عکس‌ها)",
    'option_5': "تولید توضیحات با AI",
    'option_6': "خروج",
    'select': "انتخاب کنید (1-6): ",
    'processing': "در حال پردازش...",
    'success': "✅ موفق!",
    'error': "❌ خطا:",
    'file_not_found': "فایل پیدا نشد:",
    'stats_title': "آمار:",
}

# ======================
# توابع کمکی
# ======================

def get_message(key):
    """دریافت پیام بر اساس زبان تنظیم شده"""
    if TERMINAL_LANGUAGE == "en":
        return MESSAGES_EN.get(key, key)
    else:
        return MESSAGES_FA.get(key, key)

def validate_config():
    """بررسی صحت تنظیمات"""
    errors = []
    import os

    # بررسی پوشه پایه
    if not os.path.exists(SOURCE_IMAGES_BASE):
        errors.append(f"Base images folder not found: {SOURCE_IMAGES_BASE}")
    else:
        # بررسی پوشه نهایی (آخرین تاریخ‌دار)
        if not os.path.exists(SOURCE_IMAGES_FOLDER):
            errors.append(f"Latest images folder not found: {SOURCE_IMAGES_FOLDER}")

    # بررسی URL
    if not BASE_IMAGES_URL.startswith('http'):
        errors.append(f"Invalid URL: {BASE_IMAGES_URL}")

    if errors:
        print("\n⚠️  Configuration Errors:")
        for error in errors:
            print(f"  ❌ {error}")
        return False

    return True

# ======================
# نمایش تنظیمات
# ======================

def print_config():
    """نمایش تنظیمات فعلی"""
    import os
    print("\n" + "="*70)
    print("⚙️  Current Configuration - Version 9.0")
    print("="*70)
    print(f"\n📁 Images Base Folder : {SOURCE_IMAGES_BASE}")
    print(f"📂 Active Images Folder: {SOURCE_IMAGES_FOLDER}")

    # تعداد عکس‌ها
    if os.path.exists(SOURCE_IMAGES_FOLDER):
        exts = [e.lower() for e in ALLOWED_IMAGE_EXTENSIONS]
        count = sum(
            1 for f in os.listdir(SOURCE_IMAGES_FOLDER)
            if os.path.splitext(f)[1].lower() in exts
        )
        print(f"🖼️  Images Found        : {count} files")
    else:
        print(f"⚠️  Folder not found!")

    print(f"\n📂 Destination Folder  : {DESTINATION_IMAGES_FOLDER}")
    print(f"🔗 Base URL            : {BASE_IMAGES_URL}")
    print(f"\n🎨 Image Naming:")
    print(f"   Source Pattern: {SOURCE_IMAGE_PATTERN}")
    print(f"   Target Pattern: {TARGET_IMAGE_PATTERN}")
    print(f"\n🌐 Terminal Language: {TERMINAL_LANGUAGE.upper()}")
    print(f"🔧 Overwrite Existing: {OVERWRITE_EXISTING_IMAGES}")
    print(f"📏 Resize Images: {RESIZE_IMAGES}")
    print(f"💧 Add Watermark: {ADD_WATERMARK}")
    print("="*70)

if __name__ == "__main__":
    print_config()
    
    print("\n🔍 Validating configuration...")
    if validate_config():
        print("✅ Configuration is valid!")
    else:
        print("❌ Please fix configuration errors!")
