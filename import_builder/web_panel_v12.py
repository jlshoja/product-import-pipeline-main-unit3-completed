#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web Panel - Version 12.1
✅ Fixed: manage_stock = yes for parent products
✅ Fixed: stock_quantity input from user in web panel
✅ Fixed: variation image key matching (multi-step lookup)
✅ Fixed: Removed store name from meta:_yoast_wpseo_title
✅ Updated: 2024-12-25
"""

from flask import Flask, render_template, request, jsonify, send_file, session
import os
import pandas as pd
from werkzeug.utils import secure_filename
from datetime import datetime
import shutil
from pathlib import Path
import zipfile
import re

# Import Color Manager
try:
    from color_manager import ColorManager
    HAS_COLOR_MANAGER = True
except ImportError:
    HAS_COLOR_MANAGER = False

# Import Product Name Manager
try:
    from product_name_manager import ProductNameManager
    HAS_PRODUCT_MANAGER = True
except ImportError:
    HAS_PRODUCT_MANAGER = False

# Import Image Naming v11 (Color Matching from Filename)
try:
    from image_naming_v11_fixed import generate_image_names_v11, count_available_images
    HAS_V11_NAMING = True
except ImportError:
    # Fallback to v9
    try:
        from image_naming_v9_fixed import generate_image_names_v9_fixed, count_available_images
        HAS_V11_NAMING = False
        HAS_V9_NAMING = True
    except ImportError:
        HAS_V11_NAMING = False
        HAS_V9_NAMING = False

HAS_FIXED_NAMING = HAS_V11_NAMING or HAS_V9_NAMING

ASSET_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / 'assets' / 'templates' / 'import_builder'
LEGACY_TEMPLATE_DIR = Path(__file__).resolve().parent / 'templates'
TEMPLATE_DIR = ASSET_TEMPLATE_DIR if ASSET_TEMPLATE_DIR.exists() else LEGACY_TEMPLATE_DIR

app = Flask(__name__, template_folder=str(TEMPLATE_DIR))
app.secret_key = os.environ.get('SECRET_KEY', 'woocommerce-generator-secret-key-2024')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Settings
try:
    from config_v9 import SOURCE_IMAGES_FOLDER, SOURCE_IMAGES_BASE, get_latest_images_folder, BASE_IMAGES_URL, OUTPUT_IMAGE_EXTENSION
    HAS_CONFIG = True
except ImportError:
    HAS_CONFIG = False
    SOURCE_IMAGES_FOLDER = "product-images"
    SOURCE_IMAGES_BASE = "product-images"
    def get_latest_images_folder():
        return "product-images"
    BASE_IMAGES_URL = "https://luxbaz.com/wp-content/uploads/products/"
    OUTPUT_IMAGE_EXTENSION = '.webp'

try:
    from paths import COLOR_MAPPING_FILE, PRODUCT_NAMES_FILE
except ImportError:
    COLOR_MAPPING_FILE = str(Path(__file__).resolve().parent.parent / 'data' / 'mappings' / 'color_mapping.xlsx')
    PRODUCT_NAMES_FILE = str(Path(__file__).resolve().parent.parent / 'data' / 'mappings' / 'product_names.xlsx')

print("\n" + "="*70)
print("🌐 WooCommerce Web Panel - Version 12.1")
print("="*70)

# Initialize managers
if HAS_COLOR_MANAGER:
    color_manager = ColorManager(COLOR_MAPPING_FILE, auto_create=True)
    print(f"🎨 Color Manager: ✅ Loaded")
else:
    color_manager = None
    print(f"🎨 Color Manager: ⚠️ Not available")

if HAS_PRODUCT_MANAGER:
    product_name_manager = ProductNameManager(PRODUCT_NAMES_FILE, auto_create=True)
    print(f"📦 Product Name Manager: ✅ Loaded")
else:
    product_name_manager = None
    print(f"📦 Product Name Manager: ⚠️ Not available")

if HAS_FIXED_NAMING:
    print(f"🖼️ Image Naming: ✅ v9.3 Complete version loaded")
else:
    print(f"🖼️ Image Naming: ⚠️ Using fallback")

print("="*70)

# Attribute mapping
ATTRIBUTE_MAPPING = {
    'کاربرد': 'application',
    'محفظه_های_کیف': 'bag-compartments',
    'نوع_کیف': 'bag-type',
    'نحوه_بسته_شدن_کیف': 'closure-style',
    'جنس_آستر': 'lining-material',
    'بند_بلند': 'long-strap',
    'تعداد_جیب_داخلی': 'number-of-inside-pockets',
    'تعداد_جیب_بیرونی': 'number-of-outside-pockets',
    'تعداد_بند': 'number-of-straps',
    'جنس_رویه': 'outer-material',
    'مناسب_برای': 'suitable-for',
}

# نگاشت معکوس: slug → نام فارسی
ATTRIBUTE_NAMES = {v: k.replace('_', ' ') for k, v in ATTRIBUTE_MAPPING.items()}
ATTRIBUTE_NAMES['color'] = 'رنگ'

def normalize_text(text):
    if pd.isna(text) or text == '':
        return ''
    text = str(text)
    replacements = {'ك': 'ک', 'ي': 'ی', 'ى': 'ی', '\u200c': ' ', '‌': ' '}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return ' '.join(text.split()).strip()

def translate_product_name_to_english(persian_name):
    if HAS_PRODUCT_MANAGER and product_name_manager:
        return product_name_manager.translate_product(persian_name)
    persian_name = normalize_text(persian_name)
    persian_name = re.sub(r'\s*کد\s*\d+', '', persian_name).strip()
    return persian_name.replace(' ', '-').lower()

def translate_color_to_english(persian_color):
    if HAS_COLOR_MANAGER and color_manager:
        return color_manager.translate_color(persian_color)
    else:
        return normalize_text(persian_color).replace(' ', '-').lower()

def convert_to_persian_digits(number):
    persian_digits = {'0':'۰','1':'۱','2':'۲','3':'۳','4':'۴','5':'۵','6':'۶','7':'۷','8':'۸','9':'۹'}
    number_str = str(number)
    for eng, per in persian_digits.items():
        number_str = number_str.replace(eng, per)
    return number_str

def create_dimension_string(row):
    try:
        length = str(row.get('طول', '')).strip()
        width = str(row.get('عرض', '')).strip()
        depth = str(row.get('کف', '')).strip()
        
        dimensions = []
        
        if length:
            length_clean = length.replace('cm','').replace('CM','').replace('Cm','').replace('cM','').strip()
            if length_clean:
                length_persian = convert_to_persian_digits(length_clean)
                dimensions.append(f"طول: {length_persian}cm")
        
        if width:
            width_clean = width.replace('cm','').replace('CM','').replace('Cm','').replace('cM','').strip()
            if width_clean:
                width_persian = convert_to_persian_digits(width_clean)
                dimensions.append(f"عرض: {width_persian}cm")
        
        if depth:
            depth_clean = depth.replace('cm','').replace('CM','').replace('Cm','').replace('cM','').strip()
            if depth_clean:
                depth_persian = convert_to_persian_digits(depth_clean)
                dimensions.append(f"کف: {depth_persian}cm")
        
        return '|'.join(dimensions) if dimensions else ''
    except Exception as e:
        return ''

def find_source_image(source_folder, source_name):
    """
    Find source image file with pattern matching
    Supports both:
    - Exact match: 1a.webp
    - With color suffix: 1a_black.webp, 1a_red.webp
    """
    extensions = ['.webp','.jpg','.jpeg','.png','.gif','.WEBP','.JPG','.JPEG','.PNG']
    
    # Try exact match first
    for ext in extensions:
        file_path = Path(source_folder) / f"{source_name}{ext}"
        if file_path.exists():
            return file_path
    
    # Try pattern matching (e.g., 1a_*.webp)
    folder_path = Path(source_folder)
    for file_path in folder_path.iterdir():
        if not file_path.is_file():
            continue
        
        # Check if filename starts with source_name (e.g., "1a")
        if file_path.stem.startswith(source_name):
            # Check if extension matches
            if file_path.suffix.lower() in [e.lower() for e in extensions]:
                return file_path
    
    return None

def process_images(image_mapping, source_folder, output_folder):
    stats = {'found': 0, 'copied': 0, 'missing': 0, 'errors': 0}
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*70}")
    print(f"🖼️ Processing {len(image_mapping)} images")
    print(f"{'='*70}\n")
    
    for source_name, target_name in image_mapping.items():
        source_path = find_source_image(source_folder, source_name)
        if not source_path:
            print(f"  ⚠️ Missing: {source_name}")
            stats['missing'] += 1
            continue
        try:
            target_path = output_folder / target_name
            shutil.copy2(source_path, target_path)
            print(f"  ✅ {source_name:<15} → {target_name:<40}")
            stats['found'] += 1
            stats['copied'] += 1
        except Exception as e:
            print(f"  ❌ Error copying {source_name}: {e}")
            stats['errors'] += 1
    
    print(f"\n{'='*70}")
    print(f"📊 Image Processing Stats:")
    print(f"   ✅ Found & Copied: {stats['copied']}")
    print(f"   ⚠️ Missing: {stats['missing']}")
    print(f"   ❌ Errors: {stats['errors']}")
    print(f"{'='*70}\n")
    
    return stats

def create_images_zip(folder_path):
    folder_path = Path(folder_path)
    zip_filename = f"{folder_path.name}.zip"
    zip_path = folder_path.parent / zip_filename
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in folder_path.glob('*'):
            if file.is_file():
                zipf.write(file, file.name)
    
    return zip_path

def process_excel_to_csv(excel_file, rename_images=False, default_stock=''):
    print("\n" + "="*70)
    print("🚀 WooCommerce Product Processing - Version 12.0")
    print("✅ Using 'شماره' column for image mapping")
    print("="*70)

    # ── نمایش مسیر عکس‌ها ──────────────────────────────────────────────
    active_folder = get_latest_images_folder()
    folder_exists = os.path.exists(active_folder)
    if folder_exists:
        from config_v9 import ALLOWED_IMAGE_EXTENSIONS
        exts = [e.lower() for e in ALLOWED_IMAGE_EXTENSIONS]
        img_count = sum(
            1 for f in os.listdir(active_folder)
            if os.path.splitext(f)[1].lower() in exts
        )
        folder_name = os.path.basename(active_folder)
        print(f"\n📂 Reading images from : {active_folder}")
        print(f"   📁 Folder           : {folder_name}")
        print(f"   🖼️  Images found     : {img_count} files")
    else:
        print(f"\n⚠️  Images folder NOT found: {active_folder}")
        print(f"   Image processing will be skipped.")
    print("="*70 + "\n")
    # ────────────────────────────────────────────────────────────────────

    # متغیر یکپارچه برای مسیر عکس‌ها در کل این اجرا
    active_source_folder = get_latest_images_folder()
    
    # Read file based on extension
    if excel_file.endswith('.csv'):
        df = pd.read_csv(excel_file, encoding='utf-8-sig')
        print("📄 File type: CSV")
    else:
        df = pd.read_excel(excel_file, engine='openpyxl')
        print("📄 File type: Excel")
    
    # ✅ بررسی وجود ستون 'شماره'
    if 'شماره' not in df.columns:
        raise ValueError("❌ ERROR: Column 'شماره' not found in file!\n" +
                        "   Please add 'شماره' column with row numbers (1, 2, 3, ...)")
    
    print(f"✅ Column 'شماره' found in file")
    
    if HAS_PRODUCT_MANAGER and product_name_manager:
        product_name_manager.validate_products_in_dataframe(df, 'نام_محصول')
    
    if HAS_COLOR_MANAGER and color_manager:
        color_manager.validate_colors_in_dataframe(df, 'رنگ')
    
    expanded_rows = []
    for idx, row in df.iterrows():
        colors_str = str(row.get('رنگ', '')).strip()
        if pd.isna(colors_str) or not colors_str or colors_str == 'nan':
            expanded_rows.append(row.to_dict())
            continue
        
        colors = [c.strip() for c in re.split(r'\s*[-|,]\s*', colors_str) if c.strip()]
        if not colors:
            expanded_rows.append(row.to_dict())
            continue
        
        for color in colors:
            new_row = row.to_dict().copy()
            new_row['رنگ'] = normalize_text(color)
            expanded_rows.append(new_row)
    
    df_expanded = pd.DataFrame(expanded_rows)
    
    output_rows = []
    image_mappings = {}
    grouped = df_expanded.groupby('sku')
    
    for sku, group in grouped:
        first_row = group.iloc[0]
        
        # ✅ استفاده از ستون 'شماره' به جای product_index
        if 'شماره' in first_row and pd.notna(first_row['شماره']):
            row_number = int(first_row['شماره'])
        else:
            print(f"⚠️ Warning: No 'شماره' for SKU {sku}, skipping...")
            continue
        
        print(f"\n🔹 Product {row_number}: SKU {sku}")
        
        # ✅ FIX: حذف کد از نام محصول (اگر از قبل در اکسل وارد شده)
        product_name = normalize_text(first_row.get('نام_محصول', ''))
        product_name = re.sub(r'\s*کد\s*[\d۰-۹]+\s*', '', product_name).strip()
        
        model = str(first_row.get('مدل', '')).strip()
        model_display = convert_to_persian_digits(model)
        
        product_name_en = translate_product_name_to_english(product_name)
        model_en = model.replace(' ', '-').lower()
        
        all_colors = [normalize_text(row['رنگ']) for _, row in group.iterrows() if pd.notna(row.get('رنگ'))]
        colors_en = [translate_color_to_english(c) for c in all_colors]
        
        # ✅ FIX: Auto-detect actual image count
        num_gallery_from_excel = int(first_row.get('تعداد_عکس_گالری', 0)) if pd.notna(first_row.get('تعداد_عکس_گالری')) else 0
        expected_total = 1 + len(colors_en) + num_gallery_from_excel
        
        # ✅ تولید نام عکس‌ها با v11 (Color Matching از نام فایل)
        # ✅ استفاده از SKU به عنوان product_index (فایل‌ها با SKU نام‌گذاری شده‌اند)
        if HAS_V11_NAMING:
            # منطق v11: برای هر رنگ، اولین عکسی که اون رنگ در نامش باشه رو پیدا می‌کنه
            # مثال: 4721b_blue.jpg با رنگ 'blue' match می‌شه
            image_info = generate_image_names_v11(
                product_index=sku,
                product_name_fa=product_name,
                model=model_en,
                colors=colors_en,
                image_extension=OUTPUT_IMAGE_EXTENSION,
                source_folder=active_source_folder,
                enable_color_detection=False,
                pnm=product_name_manager if HAS_PRODUCT_MANAGER else None
            )
        elif HAS_V9_NAMING:
            # Fallback to v9
            if HAS_FIXED_NAMING:
                actual_count, _ = count_available_images(sku, active_source_folder)
                num_total_images = max(actual_count, expected_total)
            else:
                num_total_images = expected_total
            
            image_info = generate_image_names_v9_fixed(
                product_index=sku,
                product_name_fa=product_name,
                model=model_en,
                colors=colors_en,
                num_total_images=num_total_images,
                image_extension=OUTPUT_IMAGE_EXTENSION,
                source_folder=active_source_folder
            )
        else:
            # Fallback
            image_info = {
                'main_image': f"{product_name_en}-{model_en}-main{OUTPUT_IMAGE_EXTENSION}",
                'color_images': {},
                'general_images': [],
                'all_images_with_alts': [(f"{product_name_en}-{model_en}-main{OUTPUT_IMAGE_EXTENSION}", f"{product_name} کد {model_display}")],
                'mapping': {}
            }
        
        if rename_images:
            image_mappings.update(image_info['mapping'])
        
        attributes = {'color': '|'.join(all_colors)}
        for col, slug in ATTRIBUTE_MAPPING.items():
            val = first_row.get(col, '')
            if pd.notna(val) and str(val).strip():
                attributes[slug] = normalize_text(str(val))
        
        dimension_str = create_dimension_string(first_row)
        if dimension_str:
            attributes['dimention'] = dimension_str
        
        category = normalize_text(first_row.get('دسته_بندی', ''))
        
        # ✅ FIX: استخراج همه تصاویر و alt ها
        all_filenames = [img for img, alt in image_info['all_images_with_alts']]
        all_alts = [alt for img, alt in image_info['all_images_with_alts']]
        
        main_image = image_info['main_image']
        main_alt = all_alts[0] if all_alts else f"{product_name} کد {model_display}"
        
        # ✅ FIX: gallery شامل همه تصاویر (از جمله main)
        gallery_filenames = all_filenames
        gallery_alts = all_alts
        gallery_urls = [f"{BASE_IMAGES_URL}{img}" for img in gallery_filenames]
        
        short_desc = normalize_text(first_row.get('توضیحات_کوتاه', ''))
        
        seo_title = f"{product_name} کد {model}"[:60]
        
        if short_desc:
            seo_description = short_desc[:155]
        else:
            colors_str = " و ".join(all_colors[:3])
            seo_description = f"خرید {product_name} کد {model} به رنگ {colors_str} با کیفیت عالی و قیمت مناسب از فروشگاه لوکس‌باز"[:155]
        
        focus_keyword = f"{product_name} کد {model}"
        canonical_url = f"https://luxbaz.com/product/{product_name_en}-{model_en}/"
        og_title = f"{product_name} کد {model} | خرید آنلاین"[:95]
        og_description = seo_description[:200]
        twitter_title = f"{product_name} کد {model}"[:70]
        twitter_description = seo_description[:200]
        
        parent_row = {
            'post_type': 'product',
            'post_title': f"{product_name} کد {model_display}",  # ✅ فقط یک بار کد (فارسی)
            'post_status': 'publish',
            'sku': str(sku),
            'parent_sku': '',
            'regular_price': first_row.get('قیمت_اصلی', ''),
            'sale_price': first_row.get('قیمت_فروش', ''),
            'manage_stock': 'yes',
            'stock_quantity': default_stock,
            'categories': category,
            'description': normalize_text(first_row.get('توضیحات_کامل', '')),
            'short_description': short_desc,
            'meta:_yoast_wpseo_title': seo_title,
            'meta:_yoast_wpseo_metadesc': seo_description,
            'meta:_yoast_wpseo_focuskw': focus_keyword,
            'meta:_yoast_wpseo_canonical': canonical_url,
            'meta:_yoast_wpseo_opengraph-title': og_title,
            'meta:_yoast_wpseo_opengraph-description': og_description,
            'meta:_yoast_wpseo_twitter-title': twitter_title,
            'meta:_yoast_wpseo_twitter-description': twitter_description,
            'images': f"{BASE_IMAGES_URL}{main_image}",
            'gallery_images': '|'.join(gallery_urls),
            'gallery_image_alt': '|'.join(gallery_alts),
            'image_filename': '|'.join(all_filenames),
            'image_titles': '',
            'image_alt': main_alt,
            'sale_tag': normalize_text(str(first_row.get('sale_tag', ''))) if str(first_row.get('sale_tag', '')).strip() not in ['', 'nan'] else '',
        }
        
        for attr_slug, attr_val in attributes.items():
            parent_row[f'attribute:{attr_slug}'] = attr_val
            parent_row[f'attribute_name:{attr_slug}'] = ATTRIBUTE_NAMES.get(attr_slug, attr_slug)
        
        output_rows.append(parent_row)
        
        for idx, (_, row) in enumerate(group.iterrows()):
            color_fa = normalize_text(row['رنگ'])
            color_en = colors_en[idx] if idx < len(colors_en) else translate_color_to_english(color_fa)
            variation_sku = f"{sku}-{color_en}"
            
            # ✅ FIX: normalize color_en همانند image_naming_v11 قبل از lookup
            import re as _re
            def _norm(c):
                c = str(c).strip().lower()
                c = c.replace(' ', '-').replace('_', '-')
                c = _re.sub(r'-+', '-', c)
                return c

            color_en_norm = _norm(color_en)
            color_images = image_info['color_images']
            variation_image = (
                color_images.get(color_en_norm) or
                color_images.get(color_en) or
                next((v for k, v in color_images.items() if _norm(k) == color_en_norm), None) or
                next((v for k, v in color_images.items() if color_en_norm in _norm(k) or _norm(k) in color_en_norm), None) or
                main_image
            )
            variation_alt = f"{product_name} کد {model_display} - {color_fa}"
            
            variation_row = {
                'post_type': 'product_variation',
                'post_title': '',
                'post_status': 'publish',
                'sku': variation_sku,
                'parent_sku': str(sku),
                'regular_price': row.get('قیمت_اصلی', ''),
                'sale_price': row.get('قیمت_فروش', ''),
                'manage_stock': 'yes',
                'stock_quantity': (lambda v: v if v and v != 'nan' else default_stock)(str(row.get('موجودی', '')).strip()),
                'categories': '',
                'description': '',
                'short_description': '',
                'meta:_yoast_wpseo_title': '',
                'meta:_yoast_wpseo_metadesc': '',
                'meta:_yoast_wpseo_focuskw': '',
                'meta:_yoast_wpseo_canonical': '',
                'meta:_yoast_wpseo_opengraph-title': '',
                'meta:_yoast_wpseo_opengraph-description': '',
                'meta:_yoast_wpseo_twitter-title': '',
                'meta:_yoast_wpseo_twitter-description': '',
                'attribute:color': color_fa,
                'attribute_name:color': 'رنگ',
                'images': f"{BASE_IMAGES_URL}{variation_image}",
                'gallery_images': '',
                'gallery_image_alt': '',
                'image_filename': variation_image,
                'image_titles': variation_alt,
                'image_alt': variation_alt,
                'sale_tag': '',
            }
            output_rows.append(variation_row)
    
    df_output = pd.DataFrame(output_rows)
    
    print("\n" + "="*70)
    print("📊 گزارش نهایی")
    print("="*70)
    
    unknown_colors_list = []
    unknown_products_list = []
    
    if HAS_COLOR_MANAGER and color_manager:
        unknown_colors_list = color_manager.get_missing_colors()
        if unknown_colors_list:
            print(f"\n⚠️ تعداد رنگ‌های ناشناخته: {len(unknown_colors_list)}")
        else:
            print("\n✅ همه رنگ‌ها شناخته شده‌اند")
    
    if HAS_PRODUCT_MANAGER and product_name_manager:
        unknown_products_list = product_name_manager.missing_products
        if unknown_products_list:
            print(f"\n⚠️ تعداد محصولات ناشناخته: {len(unknown_products_list)}")
        else:
            print("\n✅ همه محصولات شناخته شده‌اند")
    
    print("\n" + "="*70)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    date_str = datetime.now().strftime('%Y%m%d')
    output_folder = os.path.join(app.config['UPLOAD_FOLDER'], date_str)
    os.makedirs(output_folder, exist_ok=True)

    csv_filename = f"woocommerce_import_{timestamp}.csv"
    csv_path = os.path.join(output_folder, csv_filename)
    df_output.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    # Export unknown items
    unknown_colors = []
    unknown_colors_csv = None
    if HAS_COLOR_MANAGER and color_manager:
        unknown_colors = color_manager.get_missing_colors()
        
        if unknown_colors:
            unknown_colors_filename = f"unknown_colors_{timestamp}.csv"
            unknown_colors_path = os.path.join(output_folder, unknown_colors_filename)
            
            unknown_data = []
            for color in unknown_colors:
                unknown_data.append({
                    'Persian': color,
                    'Term Slug': '',
                    'product_pa_انتخاب-رنگ': '',
                    'product_pa_color-selector': ''
                })
            
            df_unknown = pd.DataFrame(unknown_data)
            df_unknown.to_csv(unknown_colors_path, index=False, encoding='utf-8-sig')
            unknown_colors_csv = os.path.join(date_str, unknown_colors_filename)
    
    unknown_products = []
    unknown_products_csv = None
    if HAS_PRODUCT_MANAGER and product_name_manager:
        unknown_products = product_name_manager.missing_products
        
        if unknown_products:
            unknown_products_filename = f"unknown_products_{timestamp}.csv"
            unknown_products_path = os.path.join(output_folder, unknown_products_filename)
            
            from product_name_manager import transliterate_persian
            unknown_data = []
            for product in unknown_products:
                transliterated = transliterate_persian(product)
                unknown_data.append({
                    'Persian': product,
                    'English (Suggested)': transliterated,
                    'Notes': 'محصول ناشناخته - لطفاً ترجمه صحیح را وارد کنید'
                })
            
            df_unknown = pd.DataFrame(unknown_data)
            df_unknown.to_csv(unknown_products_path, index=False, encoding='utf-8-sig')
            unknown_products_csv = os.path.join(date_str, unknown_products_filename)
    
    result = {
        'csv_file': os.path.join(date_str, csv_filename),
        'csv_path': csv_path,
        'total_products': len(grouped),
        'total_rows': len(df_output),
        'image_mappings': image_mappings if rename_images else None,
        'zip_file': None,
        'unknown_colors': unknown_colors,
        'unknown_colors_count': len(unknown_colors),
        'unknown_colors_csv': unknown_colors_csv,
        'unknown_products': unknown_products,
        'unknown_products_count': len(unknown_products),
        'unknown_products_csv': unknown_products_csv
    }
    
    if rename_images and image_mappings:
        images_folder = Path(output_folder) / f"renamed_images_{timestamp}"
        active_source = get_latest_images_folder()
        stats = process_images(image_mappings, active_source, images_folder)
        zip_path = create_images_zip(images_folder)
        result['zip_file'] = zip_path.name
        result['image_stats'] = stats
    
    return result

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        return jsonify({'error': 'Only Excel (.xlsx, .xls) or CSV files allowed'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    rename_images = request.form.get('rename_images') == 'true'
    default_stock = request.form.get('stock_quantity', '').strip()
    
    try:
        result = process_excel_to_csv(filepath, rename_images, default_stock)
        session['last_result'] = result
        return jsonify({
            'success': True,
            'csv_file': result['csv_file'],
            'zip_file': result.get('zip_file'),
            'total_products': result['total_products'],
            'total_rows': result['total_rows'],
            'image_stats': result.get('image_stats'),
            'unknown_colors_count': result.get('unknown_colors_count', 0),
            'unknown_colors_csv': result.get('unknown_colors_csv'),
            'unknown_products_count': result.get('unknown_products_count', 0),
            'unknown_products_csv': result.get('unknown_products_csv')
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/download/<path:filename>')
def download_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(filepath, as_attachment=True)

@app.route('/api/update-path', methods=['POST'])
def update_path():
    """
    مسیر پایه عکس‌ها را در config_v9.py به صورت دائمی ذخیره می‌کند
    """
    data = request.get_json()
    if not data or 'path' not in data:
        return jsonify({'error': 'No path provided'}), 400

    new_path = data['path'].strip().rstrip('/\\')  # حذف / و \ انتهایی

    # پیدا کردن فایل config_v9.py کنار همین اسکریپت
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config_v9.py')
    if not os.path.exists(config_path):
        return jsonify({'error': f'config_v9.py not found at: {config_path}'}), 404

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # جایگزینی مقدار SOURCE_IMAGES_BASE
        import re as _re
        new_content = _re.sub(
            r'^(SOURCE_IMAGES_BASE\s*=\s*)r?"[^"]*"',
            lambda m: f'SOURCE_IMAGES_BASE = r"{new_path}"',
            content,
            flags=_re.MULTILINE
        )

        if new_content == content:
            return jsonify({'error': 'Could not find SOURCE_IMAGES_BASE in config file'}), 500

        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        # بارگذاری مجدد config در همین پروسه
        import importlib
        import config_v9
        config_v9.SOURCE_IMAGES_BASE = new_path
        new_folder = config_v9.get_latest_images_folder()
        config_v9.SOURCE_IMAGES_FOLDER = new_folder

        # به‌روزرسانی متغیرهای global این ماژول
        global SOURCE_IMAGES_FOLDER, SOURCE_IMAGES_BASE
        SOURCE_IMAGES_BASE = new_path
        SOURCE_IMAGES_FOLDER = new_folder

        folder_exists = os.path.exists(new_folder)
        img_count = 0
        if folder_exists:
            from config_v9 import ALLOWED_IMAGE_EXTENSIONS
            exts = [e.lower() for e in ALLOWED_IMAGE_EXTENSIONS]
            img_count = sum(
                1 for f in os.listdir(new_folder)
                if os.path.splitext(f)[1].lower() in exts
            )

        return jsonify({
            'success': True,
            'new_base': new_path,
            'active_folder': new_folder,
            'folder_exists': folder_exists,
            'image_count': img_count,
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    import os
    from pathlib import Path

    source_folder = get_latest_images_folder()
    folder_exists = os.path.exists(source_folder)
    folder_files = []
    if folder_exists:
        folder_files = [f.name for f in Path(source_folder).iterdir() if f.is_file()][:10]
    
    return jsonify({
        'status': 'ok',
        'version': '12.1',
        'color_manager': HAS_COLOR_MANAGER,
        'product_manager': HAS_PRODUCT_MANAGER,
        'fixed_naming': HAS_FIXED_NAMING,
        'has_v11_naming': HAS_V11_NAMING,
        'source_images_folder': source_folder,
        'source_folder_exists': folder_exists,
        'source_folder_sample_files': folder_files,
        'working_directory': os.getcwd(),
    })


if __name__ == '__main__':
    print("\n🌐 Starting Web Panel on http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
