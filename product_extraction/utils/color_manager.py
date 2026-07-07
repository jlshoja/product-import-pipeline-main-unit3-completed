#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Color Manager Module - Version 9.0
مدیریت رنگ‌ها از فایل Excel خارجی با Fallback به رنگ‌های پیش‌فرض
"""

import pandas as pd
import os
from pathlib import Path
from datetime import datetime

try:
    from common.file_registry import get_file
    from common.path_registry import ARCHIVES_DIR, ROOT_DIR, resolve_existing_path
except ImportError:
    from product_extraction.common.file_registry import get_file
    from product_extraction.common.path_registry import ARCHIVES_DIR, ROOT_DIR, resolve_existing_path

try:
    from common.color_utils import (
        normalize_persian_color_text,
        simple_color_slug,
        split_color_values,
    )
except ImportError:
    from product_extraction.common.color_utils import (
        normalize_persian_color_text,
        simple_color_slug,
        split_color_values,
    )

# ===========================
# رنگ‌های پیش‌فرض (Fallback)
# ===========================

DEFAULT_COLOR_TRANSLATION = {
    'آبی': 'blue',
    'آبی آسمانی': 'sky-blue',
    'برنزی': 'bronze',
    'بژ': 'beige',
    'بنفش': 'purple',
    'خردلی': 'mustard',
    'زرد': 'yellow',
    'سبز': 'green',
    'سبز تیره': 'dark-green',
    'سرمه‌ای': 'navy-blue',
    'سفید': 'white',
    'سفید شیری': 'off-white',
    'شرابی': 'burgundy',
    'شکلاتی': 'chocolate',
    'صورتی': 'pink',
    'طلایی': 'gold',
    'طوسی': 'gray',
    'فیروزه‌ای': 'turquoise',
    'قرمز': 'red',
    'قهوه‌ای': 'brown',
    'قهوه‌ای تیره': 'dark-brown',
    'کرم': 'cream',
    'مشکی': 'black',
    'نارنجی': 'orange',
    'نارنجی سوخته': 'burnt-orange',
    'نقره‌ای': 'silver',
}

# ===========================
# Color Manager Class
# ===========================

class ColorManager:
    """مدیر رنگ‌ها با قابلیت خواندن از Excel"""
    
    def __init__(self, excel_path=None, auto_create=True):
        """
        مقداردهی اولیه
        
        Args:
            excel_path: مسیر فایل Excel رنگ‌ها
            auto_create: ساخت خودکار فایل در صورت عدم وجود
        """
        self.excel_path = excel_path or str(resolve_existing_path(
            ROOT_DIR / 'data' / 'mappings' / get_file('color_mapping'),
            ARCHIVES_DIR / get_file('color_mapping'),
        ))
        self.auto_create = auto_create
        self.color_dict = {}
        self.missing_colors = []
        self.load_colors()
    
    def load_colors(self):
        """بارگذاری رنگ‌ها از Excel یا استفاده از پیش‌فرض"""
        
        # بررسی وجود فایل
        if not os.path.exists(self.excel_path):
            if self.auto_create:
                print(f" فایل {self.excel_path} وجود ندارد. در حال ساخت...")
                self.create_default_excel()
            else:
                print(f" فایل {self.excel_path} یافت نشد. استفاده از رنگ‌های پیش‌فرض...")
                self.color_dict = DEFAULT_COLOR_TRANSLATION.copy()
                return
        
        try:
            # خواندن از Excel
            df = pd.read_excel(self.excel_path, sheet_name='Colors')
            
            # تبدیل به دیکشنری
            self.color_dict = {}
            for _, row in df.iterrows():
                persian = str(row['Persian']).strip()
                english = str(row['English']).strip()
                if persian and english and persian != 'nan' and english != 'nan':
                    self.color_dict[persian] = english
            
            print(f" {len(self.color_dict)} رنگ از {self.excel_path} بارگذاری شد")
            
        except Exception as e:
            print(f" خطا در خواندن فایل Excel: {e}")
            print(f"   استفاده از رنگ‌های پیش‌فرض...")
            self.color_dict = DEFAULT_COLOR_TRANSLATION.copy()
    
    def create_default_excel(self):
        """ساخت فایل Excel با رنگ‌های پیش‌فرض"""
        try:
            df = pd.DataFrame([
                {'Persian': persian, 'English': english, 'Notes': ''}
                for persian, english in DEFAULT_COLOR_TRANSLATION.items()
            ])
            
            with pd.ExcelWriter(self.excel_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Colors', index=False)
                
                # تنظیم عرض ستون‌ها
                worksheet = writer.sheets['Colors']
                worksheet.column_dimensions['A'].width = 20
                worksheet.column_dimensions['B'].width = 20
                worksheet.column_dimensions['C'].width = 30
                
                # فرمت‌بندی هدر
                from openpyxl.styles import Font, PatternFill, Alignment
                
                header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
                header_font = Font(color='FFFFFF', bold=True, size=12)
                header_alignment = Alignment(horizontal='center', vertical='center')
                
                for cell in worksheet[1]:
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = header_alignment
            
            print(f" فایل {self.excel_path} با {len(DEFAULT_COLOR_TRANSLATION)} رنگ ساخته شد")
            self.color_dict = DEFAULT_COLOR_TRANSLATION.copy()
            
        except Exception as e:
            print(f" خطا در ساخت فایل Excel: {e}")
            self.color_dict = DEFAULT_COLOR_TRANSLATION.copy()
    
    def translate_color(self, persian_color):
        """
        ترجمه رنگ فارسی به انگلیسی
        
        Args:
            persian_color: رنگ فارسی
            
        Returns:
            رنگ انگلیسی یا همان متن نرمال‌سازی شده
        """
        if not persian_color or pd.isna(persian_color):
            return ''
        
        # نرمال‌سازی متن
        color = str(persian_color).strip()
        color = normalize_persian_color_text(color)
        
        # جستجوی در دیکشنری
        if color in self.color_dict:
            return self.color_dict[color]
        
        # اگر پیدا نشد، به لیست missing اضافه کن
        if color not in self.missing_colors:
            self.missing_colors.append(color)
            print(f" رنگ '{color}' در فایل رنگ‌ها یافت نشد")
        
        # Fallback: تبدیل ساده
        return self._simple_transliterate(color)
    
    def _normalize_persian(self, text):
        """نرمال‌سازی متن فارسی"""
        replacements = {
            'ك': 'ک', 'ي': 'ی', 'ى': 'ی',
            '‌': ' ', '\u200c': ' '
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return ' '.join(text.split()).strip()
    
    def _simple_transliterate(self, text):
        """تبدیل ساده برای رنگ‌های ناشناخته"""
        # حذف کاراکترهای خاص و جایگزینی فاصله با خط تیره
        return simple_color_slug(text)
    
    def add_color(self, persian, english, notes=''):
        """
        افزودن رنگ جدید به فایل Excel
        
        Args:
            persian: رنگ فارسی
            english: رنگ انگلیسی
            notes: یادداشت (اختیاری)
        """
        try:
            # خواندن فایل موجود
            if os.path.exists(self.excel_path):
                df = pd.read_excel(self.excel_path, sheet_name='Colors')
            else:
                df = pd.DataFrame(columns=['Persian', 'English', 'Notes'])
            
            # بررسی وجود رنگ
            if persian in df['Persian'].values:
                print(f" رنگ '{persian}' قبلاً وجود دارد")
                return False
            
            # افزودن سطر جدید
            new_row = pd.DataFrame([{
                'Persian': persian,
                'English': english,
                'Notes': notes
            }])
            df = pd.concat([df, new_row], ignore_index=True)
            
            # ذخیره
            df.to_excel(self.excel_path, sheet_name='Colors', index=False)
            
            # به‌روزرسانی دیکشنری
            self.color_dict[persian] = english
            
            print(f" رنگ جدید اضافه شد: {persian} -> {english}")
            return True
            
        except Exception as e:
            print(f" خطا در افزودن رنگ: {e}")
            return False
    
    def validate_colors_in_dataframe(self, df, color_column='رنگ'):
        """
        بررسی رنگ‌های موجود در DataFrame
        
        Args:
            df: DataFrame ورودی
            color_column: نام ستون رنگ
            
        Returns:
            لیست رنگ‌های ناشناخته
        """
        unknown_colors = set()
        
        if color_column not in df.columns:
            print(f" ستون '{color_column}' در DataFrame یافت نشد")
            return list(unknown_colors)
        
        for _, row in df.iterrows():
            colors_str = str(row.get(color_column, '')).strip()
            if pd.isna(colors_str) or colors_str == '' or colors_str == 'nan':
                continue
            
            # جدا کردن رنگ‌ها (با - یا | یا ,)
            colors = split_color_values(colors_str)
            
            for color in colors:
                color_normalized = normalize_persian_color_text(color)
                if color_normalized not in self.color_dict:
                    unknown_colors.add(color_normalized)
        
        if unknown_colors:
            print(f"\n {len(unknown_colors)} رنگ ناشناخته یافت شد:")
            for color in sorted(unknown_colors):
                print(f"   • {color}")
            print(f"\n این رنگ‌ها را می‌توانید به فایل {self.excel_path} اضافه کنید")
        else:
            print(f" همه رنگ‌ها شناخته شده‌اند")
        
        return list(unknown_colors)
    
    def get_all_colors(self):
        """دریافت تمام رنگ‌ها"""
        return self.color_dict.copy()
    
    def get_missing_colors(self):
        """دریافت رنگ‌های پیدا نشده در طول اجرا"""
        return self.missing_colors.copy()
    
    def reload(self):
        """بارگذاری مجدد رنگ‌ها از فایل"""
        self.missing_colors = []
        self.load_colors()
    
    def export_summary(self, output_path='color_summary.txt'):
        """خروجی گزارش رنگ‌ها"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("="*70 + "\n")
                f.write(" گزارش رنگ‌ها\n")
                f.write("="*70 + "\n\n")
                
                f.write(f"تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"تعداد کل رنگ‌ها: {len(self.color_dict)}\n")
                f.write(f"رنگ‌های ناشناخته: {len(self.missing_colors)}\n\n")
                
                f.write("="*70 + "\n")
                f.write("لیست رنگ‌ها:\n")
                f.write("="*70 + "\n\n")
                
                for persian, english in sorted(self.color_dict.items()):
                    f.write(f"{persian:<20} -> {english}\n")
                
                if self.missing_colors:
                    f.write("\n" + "="*70 + "\n")
                    f.write("رنگ‌های ناشناخته:\n")
                    f.write("="*70 + "\n\n")
                    for color in self.missing_colors:
                        f.write(f"• {color}\n")
            
            print(f" گزارش در {output_path} ذخیره شد")
            return True
            
        except Exception as e:
            print(f" خطا در ذخیره گزارش: {e}")
            return False

# ===========================
# توابع کمکی
# ===========================

def get_color_manager(excel_path=None):
    """
    دریافت instance از ColorManager (Singleton pattern)
    """
    if not hasattr(get_color_manager, 'instance'):
        get_color_manager.instance = ColorManager(excel_path)
    return get_color_manager.instance

# ===========================
# تست
# ===========================

if __name__ == "__main__":
    print("\n" + "="*70)
    print(" تست Color Manager")
    print("="*70)
    
    # ساخت ColorManager
    cm = ColorManager()
    
    # تست ترجمه
    print("\n تست ترجمه:")
    test_colors = ['قرمز', 'آبی', 'سرمه‌ای', 'رنگ ناشناخته']
    for color in test_colors:
        result = cm.translate_color(color)
        print(f"   {color} -> {result}")
    
    # نمایش رنگ‌های ناشناخته
    if cm.get_missing_colors():
        print(f"\n رنگ‌های ناشناخته: {cm.get_missing_colors()}")
    
    # تست افزودن رنگ جدید
    print("\n تست افزودن رنگ جدید:")
    cm.add_color('یشمی', 'jade', 'رنگ سبز یشمی')
    
    # خروجی گزارش
    print("\n ذخیره گزارش:")
    cm.export_summary()
    
    print("\n" + "="*70)
    print(" تست کامل شد!")
    print("="*70)
# در انتهای فایل color_manager.py اضافه کنید:

def __del__(self):
    """Destructor - وقتی برنامه تمام می‌شود"""
    if self.missing_colors:
        try:
            # ذخیره در فایل لاگ
            log_file = Path('missing_colors_auto.log')
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"Session: {timestamp}\n")
                f.write(f"Missing colors: {len(self.missing_colors)}\n")
                f.write(f"{'='*50}\n")
                for color in self.missing_colors:
                    f.write(f"• {color}\n")
            
            print(f"\n✅ Missing colors logged to {log_file}")
        except:
            pass  # در صورت خطا، بی‌خیال
