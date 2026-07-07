#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Color Manager - Complete Version with transliterate support
- Persian to English translation
- Automatic color detection from images (optional)
- FIXED: Added _simple_transliterate method
"""

import pandas as pd
import os
import re

try:
    from paths import COLOR_MAPPING_FILE as DEFAULT_COLOR_MAPPING_PATH
except ImportError:
    DEFAULT_COLOR_MAPPING_PATH = 'color_mapping.xlsx'

class ColorManager:
    """مدیر رنگ‌ها با قابلیت ترجمه فارسی به انگلیسی"""
    
    # نقشه transliterate فارسی به انگلیسی
    PERSIAN_TO_ENGLISH = {
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
    
    def __init__(self, excel_path=DEFAULT_COLOR_MAPPING_PATH, auto_create=False):
        """
        Initialize Color Manager
        
        Args:
            excel_path: Path to color mapping Excel file
            auto_create: Create default file if not exists (not implemented)
        """
        self.excel_path = excel_path
        self.color_dict = {}
        self.reverse_color_dict = {}  # English -> Persian mapping
        self.missing_colors = []
        self.load_colors()
    
    def load_colors(self):
        """Load color mappings from Excel"""
        if not os.path.exists(self.excel_path):
            print(f"⚠️ {self.excel_path} not found")
            print(f"   Color translation will not work!")
            return
        
        try:
            df = pd.read_excel(self.excel_path)
            
            # Check if has Persian and English columns
            if 'Persian' not in df.columns or 'English' not in df.columns:
                print(f"⚠️ Excel must have 'Persian' and 'English' columns")
                return
            
            # Load mappings
            for _, row in df.iterrows():
                persian = str(row['Persian']).strip()
                english = str(row['English']).strip()
                
                if persian and english and persian != 'nan' and english != 'nan':
                    # Normalize  
                    persian_normalized = persian.lower()
                    english_normalized = english.lower().strip()
                    
                    self.color_dict[persian_normalized] = english_normalized
                    # ساخت reverse mapping (English -> Persian)
                    self.reverse_color_dict[english_normalized] = persian
            
            print(f"✅ ColorManager: Loaded {len(self.color_dict)} color mappings")
            
        except Exception as e:
            print(f"❌ Error loading {self.excel_path}: {e}")
    
    def _simple_transliterate(self, text):
        """
        تبدیل ساده متن فارسی به انگلیسی
        
        Args:
            text: متن فارسی
            
        Returns:
            متن transliterate شده
        """
        if not text or pd.isna(text):
            return ''
        
        text = str(text).strip()
        result = ''
        
        for char in text:
            if char in self.PERSIAN_TO_ENGLISH:
                result += self.PERSIAN_TO_ENGLISH[char]
            elif char.isascii() and (char.isalnum() or char in '-_'):
                result += char.lower()
            elif char in ' \u200c':  # فاصله و نیم‌فاصله
                result += '-'
        
        # پاکسازی نهایی
        result = re.sub(r'-+', '-', result)  # حذف خط تیره‌های متوالی
        result = result.strip('-')  # حذف خط تیره از ابتدا و انتها
        
        return result
    
    def translate_color(self, persian_color):
        """
        Translate Persian color to English
        
        Args:
            persian_color: Persian color name
            
        Returns:
            English color name
        """
        if not persian_color or pd.isna(persian_color):
            return ''
        
        # Normalize
        persian_normalized = str(persian_color).strip().lower()
        
        # Try exact match
        if persian_normalized in self.color_dict:
            return self.color_dict[persian_normalized]
        
        # Try partial match (remove spaces, dashes, zero-width spaces)
        persian_clean = persian_normalized.replace(' ', '').replace('-', '').replace('‌', '')
        
        for key, value in self.color_dict.items():
            key_clean = key.replace(' ', '').replace('-', '').replace('‌', '')
            if persian_clean == key_clean:
                return value
        
        # Not found - add to missing list
        if persian_color not in self.missing_colors:
            self.missing_colors.append(persian_color)
            print(f"⚠️ Color not found in mapping: '{persian_color}'")
        
        # Fallback: use transliterate
        transliterated = self._simple_transliterate(persian_color)
        return transliterated if transliterated else persian_color
    
    def get_persian_color(self, english_color):
        """
        برگرداندن نام فارسی رنگ از روی نام انگلیسی
        
        Args:
            english_color: نام رنگ به انگلیسی (مثلاً 'black', 'navy-blue')
            
        Returns:
            نام رنگ به فارسی (مثلاً 'مشکی', 'سرمه‌ای')
        """
        if not english_color or pd.isna(english_color):
            return ''
        
        # نرمال‌سازی
        english_normalized = str(english_color).strip().lower()
        
        # جستجوی دقیق
        if english_normalized in self.reverse_color_dict:
            return self.reverse_color_dict[english_normalized]
        
        # جستجوی با حذف فاصله‌ها و خط تیره‌ها
        english_clean = english_normalized.replace(' ', '').replace('-', '').replace('_', '')
        
        for key, value in self.reverse_color_dict.items():
            key_clean = key.replace(' ', '').replace('-', '').replace('_', '')
            if english_clean == key_clean:
                return value
        
        # اگر پیدا نشد، همان نام انگلیسی را برگردان
        return english_color
    
    def add_color(self, persian, english, notes=''):
        """Add new color mapping to Excel file"""
        try:
            if os.path.exists(self.excel_path):
                df = pd.read_excel(self.excel_path)
            else:
                df = pd.DataFrame(columns=['Persian', 'English', 'Notes'])
            
            # Check if exists
            existing = df[df['Persian'].str.lower() == persian.lower()]
            if not existing.empty:
                print(f"⚠️ Color '{persian}' already exists")
                return False
            
            # Add new row
            new_row = pd.DataFrame([{
                'Persian': persian,
                'English': english,
                'Notes': notes
            }])
            df = pd.concat([df, new_row], ignore_index=True)
            
            # Save
            df.to_excel(self.excel_path, index=False)
            
            # Update dict
            self.color_dict[persian.lower()] = english.lower()
            
            print(f"✅ Added: {persian} → {english}")
            return True
            
        except Exception as e:
            print(f"❌ Error adding color: {e}")
            return False
    
    def get_missing_colors(self):
        """Get list of colors that were requested but not found"""
        return self.missing_colors.copy()
    
    def save_missing_colors(self, notes='*** نیاز به ترجمه ***'):
        """
        ذخیره رنگ‌های ناشناخته در انتهای فایل color_mapping.xlsx
        ستون English خالی می‌ماند تا دستی پر شود
        رنگ‌هایی که قبلاً در فایل هستند نادیده گرفته می‌شوند
        
        Returns:
            تعداد رنگ‌های جدید اضافه شده
        """
        if not self.missing_colors:
            return 0
        
        try:
            if os.path.exists(self.excel_path):
                df = pd.read_excel(self.excel_path)
            else:
                df = pd.DataFrame(columns=['Persian', 'English', 'Notes'])
            
            # رنگ‌های موجود در فایل
            existing = set(df['Persian'].str.strip().str.lower().tolist())
            
            added = 0
            new_rows = []
            for color in self.missing_colors:
                if color.strip().lower() not in existing:
                    new_rows.append({
                        'Persian': color,
                        'English': '',  # خالی - باید دستی پر شود
                        'Notes': notes
                    })
                    existing.add(color.strip().lower())
                    added += 1
            
            if new_rows:
                df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
                df.to_excel(self.excel_path, index=False)
                print(f"✅ {added} رنگ ناشناخته به {self.excel_path} اضافه شد")
                for row in new_rows:
                    print(f"   ➕ '{row['Persian']}' (انگلیسی خالی - نیاز به تکمیل)")
            else:
                print("ℹ️ همه رنگ‌های ناشناخته قبلاً در فایل موجودند")
            
            return added
        
        except Exception as e:
            print(f"❌ Error saving missing colors: {e}")
            return 0
    
    def validate_colors_in_dataframe(self, df, color_column='رنگ'):
        """Validate all colors in a DataFrame and return unknown ones"""
        if color_column not in df.columns:
            return []
        
        unknown = set()
        
        for _, row in df.iterrows():
            color_str = str(row.get(color_column, '')).strip()
            
            if not color_str or color_str == 'nan':
                continue
            
            # Split by common separators (including pipe |)
            colors = re.split(r'[,،\-/|]', color_str)
            colors = [c.strip() for c in colors if c.strip()]
            
            for color in colors:
                translated = self.translate_color(color)
                # If translation is same as input, it wasn't found
                if translated.lower() == color.lower():
                    unknown.add(color)
        
        if unknown:
            print(f"\n⚠️ {len(unknown)} unknown colors found in DataFrame:")
            for color in sorted(unknown):
                print(f"   - {color}")
        
        return list(unknown)


# Test
if __name__ == "__main__":
    print("="*70)
    print("🎨 Color Manager Test")
    print("="*70)
    
    cm = ColorManager('color_mapping.xlsx')
    
    if cm.color_dict:
        print("\n🧪 Testing translations:")
        test_colors = ['مشکی', 'سفید', 'قرمز', 'آبی', 'خاکستری تیره', 'نسکافه‌ای', 'سرمه‌ای روشن']
        
        for color in test_colors:
            translated = cm.translate_color(color)
            status = "✅" if translated.lower() != color.lower() else "❌"
            print(f"   {status} {color:25s} → {translated}")
        
        print(f"\n📊 Total mappings loaded: {len(cm.color_dict)}")
    else:
        print("\n❌ No mappings loaded - check color_mapping.xlsx")
    
    # Test transliterate
    print("\n🧪 Testing transliterate:")
    test_texts = ['مشکی', 'قرمز', 'آبی کاربنی', 'سبز یشمی']
    for text in test_texts:
        result = cm._simple_transliterate(text)
        print(f"   {text:20s} → {result}")
    
    print("\n" + "="*70)
