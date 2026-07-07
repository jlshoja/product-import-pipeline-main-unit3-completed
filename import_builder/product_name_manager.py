#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Product Name Manager Module - Version 9.1
مدیریت نام محصولات با ترجمه کامل به انگلیسی
"""

import pandas as pd
import os
import sys
import re
from pathlib import Path

# Add src to path if running standalone
sys.path.insert(0, os.path.dirname(__file__))

try:
    from paths import MISSING_PRODUCTS_LOG as _LOG_PATH
    _DEFAULT_LOG = _LOG_PATH
except ImportError:
    _DEFAULT_LOG = str(Path(__file__).resolve().parent.parent / 'runtime' / 'logs' / 'missing_products.log')

try:
    from paths import PRODUCT_NAMES_FILE as _DEFAULT_PRODUCT_NAMES_FILE
except ImportError:
    _DEFAULT_PRODUCT_NAMES_FILE = 'product_names.xlsx'

# ===========================
# ترجمه پیش‌فرض نام محصولات
# ===========================

DEFAULT_PRODUCT_TRANSLATION = {
    # کیف‌ها
    'کیف': 'bag',
    'کیف زنانه': 'women-bag',
    'کیف مردانه': 'men-bag',
    'کیف دستی': 'handbag',
    'کیف دستی زنانه': 'women-handbag',
    'کیف پاسپورتی': 'passport-bag',
    'کیف پول': 'wallet',
    'کیف کمری': 'waist-bag',
    'کیف دوشی': 'shoulder-bag',
    'کیف چرمی': 'leather-bag',
    
    # کوله‌پشتی‌ها
    'کوله': 'backpack',
    'کوله پشتی': 'backpack',
    'کوله‌پشتی': 'backpack',
    'کوله دانشجویی': 'student-backpack',
    'کوله مدرسه': 'school-backpack',
    'کوله ورزشی': 'sport-backpack',
    
    # چمدان و ساک
    'چمدان': 'suitcase',
    'چمدان چرخدار': 'wheeled-suitcase',
    'ساک': 'duffle-bag',
    'ساک ورزشی': 'sport-duffle',
    'ساک مسافرتی': 'travel-duffle',
    
    # جاکارتی
    'جاکارتی': 'card-holder',
    'جا کارتی': 'card-holder',
    'جاکارتی چرمی': 'leather-card-holder',
    
    # سایر
    'پوشت': 'clutch',
    'کلاچ': 'clutch',
}

# ===========================
# تابع کمکی transliterate فارسی به انگلیسی
# ===========================

PERSIAN_TO_ENGLISH_MAP = {
    'آ': 'a', 'ا': 'a', 'ب': 'b', 'پ': 'p', 'ت': 't', 'ث': 's', 'ج': 'j',
    'چ': 'ch', 'ح': 'h', 'خ': 'kh', 'د': 'd', 'ذ': 'z', 'ر': 'r', 'ز': 'z',
    'ژ': 'zh', 'س': 's', 'ش': 'sh', 'ص': 's', 'ض': 'z', 'ط': 't', 'ظ': 'z',
    'ع': 'a', 'غ': 'gh', 'ف': 'f', 'ق': 'gh', 'ک': 'k', 'ك': 'k', 'گ': 'g',
    'ل': 'l', 'م': 'm', 'ن': 'n', 'و': 'o', 'ه': 'h', 'ی': 'i', 'ي': 'i', 'ى': 'i',
    'ئ': 'i', 'ة': 'e', 'أ': 'a', 'إ': 'e', 'ؤ': 'o',
    '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
    '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
    '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
    '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
}

def transliterate_persian(text):
    """تبدیل کامل متن فارسی به انگلیسی"""
    if not text:
        return ''
    
    # نرمال‌سازی
    text = text.strip()
    
    # تبدیل هر کاراکتر
    result = ''
    for char in text:
        if char in PERSIAN_TO_ENGLISH_MAP:
            result += PERSIAN_TO_ENGLISH_MAP[char]
        elif char.isascii() and (char.isalnum() or char in '-_'):
            result += char.lower()
        elif char in ' \u200c':  # فاصله و نیم‌فاصله
            result += '-'
    
    # پاکسازی نهایی
    result = re.sub(r'-+', '-', result)  # حذف خط تیره‌های متوالی
    result = result.strip('-')  # حذف خط تیره از ابتدا و انتها
    
    return result

# ===========================
# Product Name Manager Class
# ===========================

class ProductNameManager:
    """مدیر نام محصولات با قابلیت خواندن از Excel"""
    
    def __init__(self, excel_path=_DEFAULT_PRODUCT_NAMES_FILE, auto_create=True):
        """
        مقداردهی اولیه
        
        Args:
            excel_path: مسیر فایل Excel نام محصولات
            auto_create: ساخت خودکار فایل در صورت عدم وجود
        """
        self.excel_path = excel_path
        self.auto_create = auto_create
        self.product_dict = {}
        self.missing_products = []
        self.load_products()
    
    def load_products(self):
        """بارگذاری نام محصولات از Excel یا استفاده از پیش‌فرض"""
        
        if not os.path.exists(self.excel_path):
            if self.auto_create:
                print(f"📝 فایل {self.excel_path} وجود ندارد. در حال ساخت...")
                self.create_default_excel()
            else:
                print(f"⚠️ فایل {self.excel_path} یافت نشد. استفاده از نام‌های پیش‌فرض...")
                self.product_dict = DEFAULT_PRODUCT_TRANSLATION.copy()
                return
        
        try:
            df = pd.read_excel(self.excel_path, sheet_name='Products')
            
            self.product_dict = {}
            for _, row in df.iterrows():
                persian = str(row['Persian']).strip()
                english = str(row['English']).strip()
                if persian and english and persian != 'nan' and english != 'nan':
                    self.product_dict[persian] = english
            
            print(f"✅ {len(self.product_dict)} نام محصول از {self.excel_path} بارگذاری شد")
            
        except Exception as e:
            print(f"⚠️ خطا در خواندن فایل Excel: {e}")
            print(f"   استفاده از نام‌های پیش‌فرض...")
            self.product_dict = DEFAULT_PRODUCT_TRANSLATION.copy()
    
    def create_default_excel(self):
        """ساخت فایل Excel با نام محصولات پیش‌فرض"""
        try:
            df = pd.DataFrame([
                {'Persian': persian, 'English': english, 'Notes': ''}
                for persian, english in DEFAULT_PRODUCT_TRANSLATION.items()
            ])
            
            with pd.ExcelWriter(self.excel_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Products', index=False)
                
                worksheet = writer.sheets['Products']
                worksheet.column_dimensions['A'].width = 30
                worksheet.column_dimensions['B'].width = 30
                worksheet.column_dimensions['C'].width = 40
                
                from openpyxl.styles import Font, PatternFill, Alignment
                
                header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
                header_font = Font(color='FFFFFF', bold=True, size=12)
                header_alignment = Alignment(horizontal='center', vertical='center')
                
                for cell in worksheet[1]:
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = header_alignment
            
            print(f"✅ فایل {self.excel_path} با {len(DEFAULT_PRODUCT_TRANSLATION)} محصول ساخته شد")
            self.product_dict = DEFAULT_PRODUCT_TRANSLATION.copy()
            
        except Exception as e:
            print(f"❌ خطا در ساخت فایل Excel: {e}")
            self.product_dict = DEFAULT_PRODUCT_TRANSLATION.copy()
    
    def translate_product(self, persian_name):
        """
        ترجمه نام محصول فارسی به انگلیسی
        
        Args:
            persian_name: نام محصول فارسی
            
        Returns:
            نام محصول انگلیسی
        """
        if not persian_name or pd.isna(persian_name):
            return ''
        
        # نرمال‌سازی
        name = str(persian_name).strip()
        
        # حذف "کد XXXX" از نام
        name = re.sub(r'\s*کد\s*\d+', '', name).strip()
        
        # جستجوی در دیکشنری
        if name in self.product_dict:
            return self.product_dict[name]
        
        # اگر پیدا نشد، به missing اضافه کن
        if name not in self.missing_products:
            self.missing_products.append(name)
            
            # لاگ به کنسول
            print(f"⚠️ محصول '{name}' در فایل یافت نشد - استفاده از transliterate")
            
            # لاگ به فایل
            self._log_missing_product(name)
        
        # Fallback: تبدیل کامل فارسی به انگلیسی
        return transliterate_persian(name)
    
    def _log_missing_product(self, product):
        """ذخیره محصول ناشناخته در فایل لاگ"""
        try:
            log_file = _DEFAULT_LOG
            transliterated = transliterate_persian(product)
            
            with open(log_file, 'a', encoding='utf-8') as f:
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {product} → {transliterated}\n")
        except Exception as e:
            pass  # اگر لاگ نشد، مشکلی نیست
    
    def add_product(self, persian, english, notes=''):
        """افزودن محصول جدید"""
        try:
            if os.path.exists(self.excel_path):
                df = pd.read_excel(self.excel_path, sheet_name='Products')
            else:
                df = pd.DataFrame(columns=['Persian', 'English', 'Notes'])
            
            if persian in df['Persian'].values:
                print(f"⚠️ محصول '{persian}' قبلاً وجود دارد")
                return False
            
            new_row = pd.DataFrame([{
                'Persian': persian,
                'English': english,
                'Notes': notes
            }])
            df = pd.concat([df, new_row], ignore_index=True)
            
            df.to_excel(self.excel_path, sheet_name='Products', index=False)
            self.product_dict[persian] = english
            
            print(f"✅ محصول جدید اضافه شد: {persian} → {english}")
            return True
            
        except Exception as e:
            print(f"❌ خطا در افزودن محصول: {e}")
            return False
    
    def validate_products_in_dataframe(self, df, product_column='نام_محصول'):
        """بررسی محصولات موجود در DataFrame"""
        unknown_products = set()
        
        if product_column not in df.columns:
            print(f"⚠️ ستون '{product_column}' در DataFrame یافت نشد")
            return list(unknown_products)
        
        for _, row in df.iterrows():
            product_str = str(row.get(product_column, '')).strip()
            if pd.isna(product_str) or product_str == '' or product_str == 'nan':
                continue
            
            # حذف کد
            clean_name = re.sub(r'\s*کد\s*\d+', '', product_str).strip()
            
            if clean_name not in self.product_dict:
                unknown_products.add(clean_name)
        
        if unknown_products:
            print(f"\n⚠️ {len(unknown_products)} محصول ناشناخته یافت شد:")
            for product in sorted(unknown_products):
                suggested = transliterate_persian(product)
                print(f"   • {product} → {suggested}")
            print(f"\n💡 این محصولات را می‌توانید به فایل {self.excel_path} اضافه کنید")
        else:
            print(f"✅ همه محصولات شناخته شده‌اند")
        
        return list(unknown_products)
    
    def get_all_products(self):
        """دریافت تمام محصولات"""
        return self.product_dict.copy()
    
    def get_missing_products_from_log(self):
        """خواندن تمام محصولات ناشناخته از فایل لاگ"""
        try:
            log_file = _DEFAULT_LOG
            if not os.path.exists(log_file):
                return []
            
            products = []
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if '→' in line:
                        parts = line.split(']', 1)
                        if len(parts) > 1:
                            product_part = parts[1].split('→')[0].strip()
                            if product_part not in products:
                                products.append(product_part)
            return products
        except Exception as e:
            print(f"❌ خطا در خواندن لاگ: {e}")
            return []
    
    def print_missing_products_report(self):
        """نمایش گزارش محصولات ناشناخته"""
        print("\n" + "="*70)
        print("📊 گزارش محصولات ناشناخته")
        print("="*70)
        
        # از لاگ فایل
        log_products = self.get_missing_products_from_log()
        if log_products:
            print(f"\n📝 محصولات ثبت شده در لاگ ({len(log_products)} محصول):")
            for product in log_products:
                transliterated = transliterate_persian(product)
                print(f"   • {product:<30} → {transliterated}")
        
        # از حافظه
        if self.missing_products:
            print(f"\n⚡ محصولات این اجرا ({len(self.missing_products)} محصول):")
            for product in self.missing_products:
                transliterated = transliterate_persian(product)
                print(f"   • {product:<30} → {transliterated}")
        
        if not log_products and not self.missing_products:
            print("\n✅ هیچ محصول ناشناخته‌ای یافت نشد!")
        
        print("="*70)
    
    def reload(self):
        """بارگذاری مجدد"""
        self.missing_products = []
        self.load_products()

# ===========================
# تست
# ===========================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧪 تست Product Name Manager")
    print("="*70)
    
    pnm = ProductNameManager()
    
    print("\n🔍 تست ترجمه:")
    test_names = [
        'کیف زنانه کد 1234',
        'جاکارتی کد 9898',
        'کوله پشتی',
        'محصول ناشناخته'
    ]
    
    for name in test_names:
        result = pnm.translate_product(name)
        print(f"   {name:<30} → {result}")
    
    print("\n" + "="*70)
