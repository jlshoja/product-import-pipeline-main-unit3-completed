#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Image Naming Logic - Version 11.3 with Persian Color Translation
✅ Partial matching (e.g., 'black' matches 'black-shrink')
✅ Fuzzy matching with color similarity (e.g., 'dark-gray' ~ 'black')
✅ First image (1a, 2a) = always main
✅ Match images to colors based on filename
✅ Remaining images = general
✅ FIX v11.3: ترجمه رنگ فارسی به انگلیسی قبل از match با نام فایل
✅ Updated: 2025-01-01
"""

import re
import os
import sys
from pathlib import Path

# Add src to path if running standalone
sys.path.insert(0, os.path.dirname(__file__))

try:
    from paths import COLOR_MAPPING_FILE
except ImportError:
    COLOR_MAPPING_FILE = str(Path(__file__).resolve().parent.parent / 'data' / 'mappings' / 'color_mapping.xlsx')

# Try to import color similarity
try:
    from color_similarity import is_color_similar, get_similar_colors
    HAS_COLOR_SIMILARITY = True
except ImportError:
    HAS_COLOR_SIMILARITY = False

# Try to import color detection (optional)
try:
    from color_manager import get_average_color, find_closest_color_name
    HAS_COLOR_DETECTION = True
except ImportError:
    HAS_COLOR_DETECTION = False

# Try to import ColorManager for translation
try:
    from color_manager import ColorManager
    HAS_COLOR_MANAGER = True
except ImportError:
    HAS_COLOR_MANAGER = False

def normalize_color_name(color):
    """نرمالسازی نام رنگ"""
    if not color or color == 'nan':
        return ''
    color_str = str(color).strip().lower()
    color_str = color_str.replace(' ', '-').replace('_', '-')
    color_str = re.sub(r'-+', '-', color_str)
    return color_str

def extract_colors_from_filename(filename):
    """
    استخراج رنگ از نام فایل
    فرمت: {SKU}{letter}_{color}.ext
    مثال: 4721e_sky-blue.jpg → ['sky-blue']
    مثال: 4721a_black.jpg → ['black']
    ✅ underscore = جداکننده بین letter و رنگ
    ✅ dash = بخشی از نام رنگ (مثل sky-blue, light-navy)
    """
    stem = Path(filename).stem
    # جدا کردن با underscore: 4721e_sky-blue → color_part = 'sky-blue'
    match = re.match(r'^\d+[a-z]_(.*)', stem, re.IGNORECASE)
    if match:
        color_part = match.group(1).strip().lower()
        if color_part:
            return [color_part]
    
    # fallback: اگه underscore نبود، با dash جدا کن (فرمت قدیمی)
    match2 = re.match(r'^\d+[a-z]-(.*)', stem, re.IGNORECASE)
    if match2:
        color_part = match2.group(1).strip().lower()
        if color_part:
            return [color_part]
    
    return []

def detect_color_from_image(filepath):
    """تشخیص رنگ از تصویر (اختیاری)"""
    if not HAS_COLOR_DETECTION:
        return None
    
    try:
        avg_color = get_average_color(str(filepath))
        if avg_color:
            return find_closest_color_name(avg_color)
    except:
        pass
    
    return None

def count_available_images(product_index, source_folder):
    """
    شمارش تعداد عکس‌های موجود برای یک محصول
    product_index می‌تواند SKU باشد (مثلاً 4729) یا شماره ردیف (مثلاً 1)
    فایل‌ها با نام 4729a.jpg, 4729b.jpg یا 1a.jpg, 1b.jpg جستجو می‌شوند
    """
    if not source_folder or not os.path.exists(source_folder):
        return 0, []
    
    letters = 'abcdefghijklmnopqrstuvwxyz'
    found_images = []
    extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.JPG', '.JPEG', '.PNG', '.WEBP']
    
    product_index_str = str(product_index)
    
    folder_path = Path(source_folder)
    all_files = [f for f in folder_path.iterdir() if f.is_file()]
    
    for letter in letters:
        pattern = f"{product_index_str}{letter}"
        for file_path in all_files:
            suffix = file_path.suffix.lower()
            allowed = suffix in [e.lower() for e in extensions] or suffix == ''
            if file_path.stem.startswith(pattern) and allowed:
                found_images.append((letter, file_path))
                break
    
    found_images.sort(key=lambda x: x[0])
    return len(found_images), found_images

def is_persian(text):
    """بررسی اینکه متن فارسی است یا نه"""
    return any('\u0600' <= c <= '\u06ff' for c in str(text))

def smart_translate_color(color, color_manager):
    """
    ترجمه هوشمند رنگ:
    - اگه فارسی بود → ترجمه به انگلیسی
    - اگه انگلیسی بود → همون را برگردان (بدون ترجمه)
    """
    if not color_manager or not is_persian(color):
        return color
    return smart_translate_color(color, color_manager)

def find_image_for_color(color, available_images, used_indices, enable_detection=False):
    """
    پیدا کردن اولین عکس مناسب برای یک رنگ
    ✅ v11.3: اگه هر کلمه‌ای از رنگ در نام فایل بود → match
    ✅ انتظار می‌رود color از قبل به انگلیسی ترجمه شده باشد
    """
    normalized_color = normalize_color_name(color)
    
    if not normalized_color:
        return None
    
    # کلمات رنگ را جدا کن (مثلاً 'dark-gray' → ['dark', 'gray'])
    color_words = re.split(r'[-_ ]+', normalized_color)
    color_words = [w for w in color_words if w]
    
    # نام فایل را normalize کن برای جستجو (حذف SKU و حرف از ابتدا)
    def get_filename_text(filepath):
        stem = filepath.stem.lower()
        # حذف پیشوند SKU+letter (مثلاً '6332b_' یا '6332b-')
        stem = re.sub(r'^\d+[a-z][_\-]?', '', stem, flags=re.IGNORECASE)
        return stem
    
    # Pass 1: Exact match — رنگ کامل در نام فایل
    for idx, (letter, filepath) in enumerate(available_images):
        if idx == 0 or idx in used_indices:
            continue
        filename_text = get_filename_text(filepath)
        if normalized_color in filename_text or filename_text in normalized_color:
            return idx, letter, filepath, 'exact'
    
    # Pass 2: Word match — هر کلمه از رنگ در نام فایل باشد
    for idx, (letter, filepath) in enumerate(available_images):
        if idx == 0 or idx in used_indices:
            continue
        filename_text = get_filename_text(filepath)
        if any(word in filename_text for word in color_words):
            return idx, letter, filepath, 'word_match'
    
    # Pass 3: Fuzzy match — رنگ‌های مشابه
    if HAS_COLOR_SIMILARITY:
        for idx, (letter, filepath) in enumerate(available_images):
            if idx == 0 or idx in used_indices:
                continue
            filename_text = get_filename_text(filepath)
            if is_color_similar(normalized_color, filename_text):
                return idx, letter, filepath, 'fuzzy'
    
    # Pass 4: تشخیص رنگ از تصویر (اختیاری)
    if enable_detection and HAS_COLOR_DETECTION:
        for idx, (letter, filepath) in enumerate(available_images):
            if idx == 0 or idx in used_indices:
                continue
            detected_color = detect_color_from_image(filepath)
            if detected_color and detected_color == normalized_color:
                return idx, letter, filepath, 'detected'
    
    return None

def generate_image_names_v11(product_index, product_name_fa, model, colors, 
                             image_extension='.jpg', source_folder=None, 
                             enable_color_detection=False, pnm=None):
    """
    تولید نام‌های استاندارد برای عکس‌های محصول
    با قابلیت partial و fuzzy matching
    ✅ v11.3: رنگ‌های فارسی اکسل قبل از match به انگلیسی ترجمه می‌شوند
    """
    
    # ساخت ColorManager برای ترجمه رنگ فارسی↔انگلیسی
    color_manager = None
    if HAS_COLOR_MANAGER:
        try:
            color_manager = ColorManager(COLOR_MAPPING_FILE)
        except:
            pass
    
    # ترجمه نام محصول
    if pnm and hasattr(pnm, 'translate_product'):
        product_name_en = pnm.translate_product(product_name_fa)
    else:
        product_name_en = product_name_fa.lower().replace(' ', '-')
    
    # نرمالسازی مدل
    model_normalized = str(model).replace(' ', '-').lower()
    
    product_index_str = str(product_index)
    
    # دریافت عکس‌های موجود
    count, available_images = count_available_images(product_index_str, source_folder)
    
    if count == 0:
        print(f"[WARN] No images found for product {product_index_str} in folder — generating names from colors")
        
        # FALLBACK: ساخت نام‌ها از روی رنگ‌های اکسل بدون نیاز به فایل فیزیکی
        result = {
            'mapping': {},
            'main_image': '',
            'color_images': {},
            'general_images': [],
            'gallery_images': [],
            'all_images_with_alts': [],
            'match_report': {}
        }
        
        # عکس main
        main_filename = f"{product_name_en}-{model_normalized}-main{image_extension}"
        result['main_image'] = main_filename
        result['all_images_with_alts'].append((main_filename, f"{product_name_fa} کد {model}"))
        
        # عکس هر رنگ
        for color in colors:
            # ✅ FIX v11.3: ترجمه رنگ فارسی به انگلیسی
            color_en = smart_translate_color(color, color_manager) if color_manager else color
            color_normalized = normalize_color_name(color_en)
            if not color_normalized:
                continue
            
            color_filename = f"{product_name_en}-{model_normalized}-{color_normalized}{image_extension}"
            result['color_images'][color_normalized] = color_filename
            
            # alt به فارسی (رنگ اصلی فارسی را نگه می‌داریم)
            color_fa = color  # رنگ در اکسل فارسیه، همان را برای alt استفاده می‌کنیم
            result['all_images_with_alts'].append((color_filename, f"{product_name_fa} کد {model} رنگ {color_fa}"))
        
        result['gallery_images'] = [img for img, _ in result['all_images_with_alts']]
        
        print(f"   [OK] Generated {len(result['all_images_with_alts'])} image names from colors (no physical files needed)")
        return result
    
    print(f"[IMG] Product {product_index_str}: {product_name_en}")
    
    result = {
        'mapping': {},
        'main_image': '',
        'color_images': {},
        'general_images': [],
        'gallery_images': [],
        'all_images_with_alts': [],
        'match_report': {}
    }
    
    used_indices = set()
    
    # عکس اول = main
    if available_images:
        letter, filepath = available_images[0]
        main_filename = f"{product_name_en}-{model_normalized}-main{image_extension}"
        result['main_image'] = main_filename
        result['mapping'][f"{product_index_str}{letter}"] = main_filename
        used_indices.add(0)
        print(f"   Main: {product_index_str}{letter} -> {main_filename}")
    
    # Match کردن رنگ‌ها
    if colors:
        print(f"   Colors to match: {colors}")
        
        for color in colors:
            # ✅ FIX v11.3: ترجمه رنگ فارسی به انگلیسی قبل از match
            color_en = smart_translate_color(color, color_manager) if color_manager else color
            color_normalized = normalize_color_name(color_en)
            
            match_result = find_image_for_color(color_en, available_images, used_indices, enable_color_detection)
            
            if match_result:
                idx, letter, filepath, match_type = match_result
                color_filename = f"{product_name_en}-{model_normalized}-{color_normalized}{image_extension}"
                
                result['color_images'][color_normalized] = color_filename
                result['mapping'][f"{product_index_str}{letter}"] = color_filename
                result['match_report'][color] = (f"{product_index_str}{letter}", match_type)
                used_indices.add(idx)
                
                print(f"   [MATCH] Color '{color}' -> '{color_en}': {product_index_str}{letter} -> {color_filename} ({match_type})")
            else:
                print(f"   [WARN] Color '{color}' -> '{color_en}': No matching image found!")
    
    # عکس‌های باقیمانده = general
    general_count = 1
    for idx, (letter, filepath) in enumerate(available_images):
        if idx not in used_indices:
            general_filename = f"{product_name_en}-{model_normalized}-{general_count:02d}{image_extension}"
            result['general_images'].append(general_filename)
            result['mapping'][f"{product_index_str}{letter}"] = general_filename
            used_indices.add(idx)
            print(f"   [IMG] General: {product_index_str}{letter} -> {general_filename}")
            general_count += 1
    
    # ساخت gallery و alts
    all_images = [result['main_image']]
    all_images.extend(result['color_images'].values())
    all_images.extend(result['general_images'])
    
    result['gallery_images'] = all_images
    
    # ساخت alt text
    # نگاشت color_normalized → color_fa برای استفاده در alt
    color_fa_map = {}
    for color in colors:
        color_en = smart_translate_color(color, color_manager) if color_manager else color
        color_normalized = normalize_color_name(color_en)
        color_fa_map[color_normalized] = color  # رنگ فارسی اصلی از اکسل

    for img in all_images:
        if '-main' in img:
            alt = f"{product_name_fa} کد {model}"
        else:
            # پیدا کردن رنگ از نام فایل
            matched_color_fa = None
            for color_normalized, color_fa in color_fa_map.items():
                if img.endswith(f"-{color_normalized}{image_extension}"):
                    matched_color_fa = color_fa
                    break
            
            if matched_color_fa:
                alt = f"{product_name_fa} کد {model} رنگ {matched_color_fa}"
            else:
                num = re.search(r'-(\d+)' + re.escape(image_extension) + '$', img)
                if num:
                    alt = f"{product_name_fa} کد {model} - نمای {num.group(1)}"
                else:
                    alt = f"{product_name_fa} کد {model}"
        
        result['all_images_with_alts'].append((img, alt))
    
    print(f"   [OK] Total: {len(result['mapping'])} images mapped")
    
    return result
