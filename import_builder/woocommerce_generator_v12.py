#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WooCommerce Product Generator - Version 12.1
✅ Fixed: manage_stock = yes for parent products
✅ Fixed: variation image key matching (multi-step lookup)
✅ Fixed: Removed store name from meta:_yoast_wpseo_title
✅ Updated: 2024-12-25
"""

import pandas as pd
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path
import re

# Add src to path if running standalone
sys.path.insert(0, os.path.dirname(__file__))

try:
    from paths import COLOR_MAPPING_FILE, PRODUCT_NAMES_FILE, IMPORT_BUILDER_UPLOADS_DIR
except ImportError:
    COLOR_MAPPING_FILE = str(Path(__file__).resolve().parent.parent / 'data' / 'mappings' / 'color_mapping.xlsx')
    PRODUCT_NAMES_FILE = str(Path(__file__).resolve().parent.parent / 'data' / 'mappings' / 'product_names.xlsx')
    IMPORT_BUILDER_UPLOADS_DIR = Path(__file__).resolve().parent.parent / 'runtime' / 'cache' / 'import_builder' / 'uploads'

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
        print("[WARN] No image naming module found - using fallback")

HAS_FIXED_NAMING = HAS_V11_NAMING or HAS_V9_NAMING

# Import Color Manager
try:
    from color_manager import ColorManager
    HAS_COLOR_MANAGER = True
    color_manager = ColorManager(COLOR_MAPPING_FILE, auto_create=True)
except ImportError:
    HAS_COLOR_MANAGER = False
    color_manager = None

# Import Product Name Manager
try:
    from product_name_manager import ProductNameManager
    HAS_PRODUCT_MANAGER = True
    product_name_manager = ProductNameManager(PRODUCT_NAMES_FILE, auto_create=True)
except ImportError:
    HAS_PRODUCT_MANAGER = False
    product_name_manager = None

# Configuration
try:
    from config_v9 import BASE_IMAGES_URL, SOURCE_IMAGES_FOLDER, OUTPUT_IMAGE_EXTENSION
    HAS_CONFIG = True
except ImportError:
    HAS_CONFIG = False
    BASE_IMAGES_URL = "https://luxbaz.com/wp-content/uploads/products/"
    SOURCE_IMAGES_FOLDER = "product-images"
    OUTPUT_IMAGE_EXTENSION = '.webp'

# Attribute slugs mapping
ATTRIBUTE_SLUGS = {
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
ATTRIBUTE_NAMES = {v: k.replace('_', ' ') for k, v in ATTRIBUTE_SLUGS.items()}
ATTRIBUTE_NAMES['color'] = 'رنگ'
ATTRIBUTE_NAMES['dimention'] = 'ابعاد'

def normalize_persian_text(text):
    """نرمال‌سازی متن فارسی"""
    if pd.isna(text):
        return ''
    text = str(text).strip()
    replacements = {'ك': 'ک', 'ي': 'ی', 'ى': 'ی'}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return ' '.join(text.split()).strip()

def convert_to_persian_digits(text):
    """تبدیل اعداد انگلیسی به فارسی"""
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    english_digits = '0123456789'
    text = str(text)
    for en, fa in zip(english_digits, persian_digits):
        text = text.replace(en, fa)
    return text

def translate_product_name_to_english(persian_name):
    """ترجمه نام محصول"""
    if HAS_PRODUCT_MANAGER and product_name_manager:
        return product_name_manager.translate_product(persian_name)
    
    # Fallback
    persian_name = normalize_persian_text(persian_name)
    persian_name = re.sub(r'\s*کد\s*\d+', '', persian_name).strip()
    return persian_name.replace(' ', '-').lower()

def translate_color_to_english(persian_color):
    """ترجمه رنگ"""
    if HAS_COLOR_MANAGER and color_manager:
        return color_manager.translate_color(persian_color)
    return persian_color.replace(' ', '-').lower()

def expand_rows_by_colors(df):
    """تبدیل رنگ‌های جدا شده با | به ردیف‌های جداگانه"""
    expanded_rows = []
    for idx, row in df.iterrows():
        colors_str = str(row.get('رنگ', '')).strip()
        if pd.isna(colors_str) or colors_str == '' or colors_str == 'nan':
            expanded_rows.append(row.to_dict())
            continue
        colors = [c.strip() for c in re.split(r'\s*[-|,]\s*', colors_str) if c.strip()]
        if not colors:
            expanded_rows.append(row.to_dict())
            continue
        for color in colors:
            new_row = row.to_dict().copy()
            new_row['رنگ'] = normalize_persian_text(color)
            expanded_rows.append(new_row)
    return pd.DataFrame(expanded_rows)

def create_dimension_string(row):
    """ساخت رشته ابعاد"""
    def format_dim(value, label):
        if pd.isna(value) or str(value).strip().lower() in ('', 'nan', 'none', '-'):
            return ''
        value_str = str(value).strip()
        number_only = re.sub(r'[^0-9۰-۹.]', '', value_str)
        if not number_only:
            return ''
        persian_number = convert_to_persian_digits(number_only)
        return f"{label}: {persian_number}cm"
    
    dimensions = []
    length = format_dim(row.get('طول', ''), 'طول')
    if length:
        dimensions.append(length)
    width = format_dim(row.get('عرض', ''), 'عرض')
    if width:
        dimensions.append(width)
    depth = format_dim(row.get('کف', '') , 'کف')
    if depth:
        dimensions.append(depth)
    
    return '|'.join(dimensions) if dimensions else ''

def load_excluded_skus(sku_file='sku_list.txt'):
    """Load list of unavailable SKUs from text file"""
    excluded = set()
    if os.path.exists(sku_file):
        with open(sku_file, 'r', encoding='utf-8') as f:
            for line in f:
                sku = line.strip()
                if sku:
                    excluded.add(sku)
        print(f"[EXCLUDE] Loaded {len(excluded)} excluded SKUs from {sku_file}")
    else:
        print(f"[WARN]  {sku_file} not found - no SKUs will be excluded")
    return excluded


def process_products_v12(input_file, process_images=False, source_images_folder=None, dest_images_folder=None):
    """
    پردازش محصولات با استفاده از ستون 'شماره'
    """
    print("\n" + "="*70)
    print("[START] WooCommerce Product Processing - Version 12.0")
    print("[OK] Using 'Shomareh' column for image mapping")
    print("="*70)

    # Load excluded SKUs
    excluded_skus = load_excluded_skus('sku_list.txt')
    
    # خواندن فایل ورودی
    if input_file.endswith('.csv'):
        df_input = pd.read_csv(input_file, encoding='utf-8-sig')
        print("[FILE] File type: CSV")
    else:
        df_input = pd.read_excel(input_file, engine='openpyxl')
        print("[FILE] File type: Excel")
    
    print(f"[DATA] Total rows: {len(df_input)}")
    
    # ✅ بررسی وجود ستون 'شماره'
    if 'شماره' not in df_input.columns:
        print("\n[ERROR] ERROR: Column 'شماره' not found in file!")
        print("[LIST] Available columns:")
        for col in df_input.columns:
            print(f"   - {col}")
        print("\n[HINT] Please add 'شماره' column with row numbers (1, 2, 3, ...)")
        return None, None, None
    
    # Validation
    if HAS_PRODUCT_MANAGER and product_name_manager:
        product_name_manager.validate_products_in_dataframe(df_input, 'نام_محصول')
    
    if HAS_COLOR_MANAGER and color_manager:
        color_manager.validate_colors_in_dataframe(df_input, 'رنگ')
    
    # Expand by colors
    df_expanded = expand_rows_by_colors(df_input)
    print(f"[DATA] Expanded rows (by colors): {len(df_expanded)}")
    
    # تنظیم source folder
    if not source_images_folder:
        source_images_folder = SOURCE_IMAGES_FOLDER
    
    output_rows = []
    image_mappings = {}
    grouped = df_expanded.groupby('sku')
    
    print(f"\n[PAGE] Processing {len(grouped)} products...")
    if excluded_skus:
        print(f"[EXCLUDE] Will exclude variations with SKUs in sku_list.txt")
    print("="*70)
    
    for product_sku, group in grouped:
        first_row = group.iloc[0]
        
        # ✅ استفاده از SKU برای پیدا کردن عکس‌ها (به جای ستون شماره)
        row_number = product_sku  # SKU مستقیم به عنوان product_index
        if 'شماره' in first_row and pd.notna(first_row['شماره']):
            _ = int(first_row['شماره'])  # نگه‌داری برای سازگاری
        
        # ✅ FIX: حذف کد از نام محصول
        product_name = normalize_persian_text(first_row.get('نام_محصول', ''))
        product_name = re.sub(r'\s*کد\s*[\d۰-۹]+\s*', '', product_name).strip()
        
        model = str(first_row.get('مدل', '')).strip()
        model_display = convert_to_persian_digits(model)
        
        product_name_en = translate_product_name_to_english(product_name)
        model_en = model.replace(' ', '-').lower()
        
        # Use English version for console output to avoid encoding issues
        safe_product_name = product_name_en if product_name_en else product_name
        # Ensure safe_product_name only contains ASCII characters for console
        safe_product_name = safe_product_name.encode('ascii', 'replace').decode('ascii')
        print(f"\n[PRODUCT] Product {row_number}: {safe_product_name} (SKU: {product_sku})")
        
        # رنگ‌ها
        all_colors = []
        colors_en = []
        for _, row in group.iterrows():
            color_fa = normalize_persian_text(row['رنگ'])
            if color_fa and color_fa not in all_colors:
                all_colors.append(color_fa)
                color_en = translate_color_to_english(color_fa)
                colors_en.append(color_en)
        
        # ✅ استفاده از row_number به جای product_index
        if HAS_FIXED_NAMING:
            if HAS_V11_NAMING:
                image_info = generate_image_names_v11(
                    product_index=row_number,  # ✅ از row_number استفاده می‌کنیم
                    product_name_fa=product_name,
                    model=model,
                    colors=colors_en,
                    image_extension=OUTPUT_IMAGE_EXTENSION,
                    source_folder=source_images_folder,
                    enable_color_detection=False,
                    pnm=product_name_manager
                )
            else:
                # Fallback to v9
                image_info = generate_image_names_v9_fixed(
                    product_index=row_number,  # ✅ از row_number استفاده می‌کنیم
                    product_name_fa=product_name,
                    model=model,
                    colors=colors_en,
                    image_extension=OUTPUT_IMAGE_EXTENSION,
                    source_folder=source_images_folder,
                    pnm=product_name_manager
                )
        else:
            # Fallback ساده
            print(f"[WARN] Using fallback naming for product {row_number}")
            image_info = {
                'main_image': f"{product_name_en}-{model_en}-main{OUTPUT_IMAGE_EXTENSION}",
                'color_images': {},
                'general_images': [],
                'gallery_images': [],
                'all_images_with_alts': [],
                'mapping': {}
            }
        
        if process_images:
            image_mappings.update(image_info['mapping'])
        
        # Attributes
        attributes = {'color': '|'.join(all_colors)}
        for col in df_input.columns:
            if col in ATTRIBUTE_SLUGS:
                attr_value = first_row.get(col, '')
                if pd.notna(attr_value) and str(attr_value).strip():
                    attr_slug = ATTRIBUTE_SLUGS[col]
                    attributes[attr_slug] = normalize_persian_text(str(attr_value))
        
        dimension_str = create_dimension_string(first_row)
        if dimension_str:
            attributes['dimention'] = dimension_str
        
        category = normalize_persian_text(first_row.get('دسته_بندی', ''))
        
        # ✅ FIX: استفاده از all_images_with_alts برای gallery
        all_filenames = [img for img, alt in image_info['all_images_with_alts']]
        all_alts = [alt for img, alt in image_info['all_images_with_alts']]
        
        # عکس اصلی
        main_image = image_info['main_image']
        main_alt = all_alts[0] if all_alts else f"{product_name} کد {model_display}"
        
        # ✅ FIX: gallery_images شامل همه عکس‌ها
        gallery_filenames = all_filenames
        gallery_alts = all_alts
        
        # URLs
        main_image_url = f"{BASE_IMAGES_URL}{main_image}"
        gallery_urls = [f"{BASE_IMAGES_URL}{img}" for img in gallery_filenames]
        
        # Descriptions
        short_desc = normalize_persian_text(first_row.get('توضیحات_کوتاه', ''))
        full_desc = normalize_persian_text(first_row.get('توضیحات_کامل', ''))
        
        # SEO
        seo_title = f"{product_name} کد {model}"[:60]
        if short_desc:
            seo_description = short_desc[:155]
        else:
            colors_str = " و ".join(all_colors[:3])
            seo_description = f"خرید {product_name} کد {model} به رنگ {colors_str} با کیفیت عالی و قیمت مناسب از فروشگاه لوکس‌باز"[:155]
        focus_keyword = f"{product_name} کد {model}"
        
        # Parent product row
        parent_row = {
            'post_type': 'product',
            'post_title': f"{product_name} کد {model_display}",
            'post_status': 'publish',
            'sku': str(product_sku),
            'parent_sku': '',
            'regular_price': first_row.get('قیمت_اصلی', ''),
            'sale_price': first_row.get('قیمت_فروش', ''),
            'manage_stock': 'yes',
            'stock_quantity': '',
            'categories': category,
            'description': full_desc,
            'short_description': short_desc,
            'meta:_yoast_wpseo_title': seo_title,
            'meta:_yoast_wpseo_metadesc': seo_description,
            'meta:_yoast_wpseo_focuskw': focus_keyword,
            'meta:_yoast_wpseo_canonical': f"https://luxbaz.com/product/{product_name_en}-{model_en}/",
            'images': main_image_url,
            'gallery_images': '|'.join(gallery_urls),
            'gallery_image_alt': '|'.join(gallery_alts),
            'image_filename': '|'.join(all_filenames),
            'image_titles': '',
            'image_alt': main_alt,
            'sale_tag': normalize_persian_text(str(first_row.get('sale_tag', ''))) if str(first_row.get('sale_tag', '')).strip() not in ['', 'nan'] else '',
        }
        
        # اضافه کردن attributes
        for attr_slug, attr_value in attributes.items():
            parent_row[f'attribute:{attr_slug}'] = attr_value
            parent_row[f'attribute_name:{attr_slug}'] = ATTRIBUTE_NAMES.get(attr_slug, attr_slug)
        
        # Skip parent if ALL variations are excluded
        all_variation_skus = [
            f"{product_sku}-{(colors_en[i] if i < len(colors_en) else translate_color_to_english(normalize_persian_text(row['رنگ'])))}"
            for i, (_, row) in enumerate(group.iterrows())
        ]
        if all_variation_skus and all(sku in excluded_skus for sku in all_variation_skus):
            print(f"  [EXCLUDE] All variations excluded for product {product_sku} - skipping parent too")
            continue

        output_rows.append(parent_row)

        # Variations
        for idx, (_, row) in enumerate(group.iterrows()):
            color_fa = normalize_persian_text(row['رنگ'])
            color_en = colors_en[idx] if idx < len(colors_en) else translate_color_to_english(color_fa)
            variation_sku = f"{product_sku}-{color_en}"

            # Skip this variation if its SKU is in the excluded list
            if variation_sku in excluded_skus:
                print(f"  [EXCLUDE] Excluded: {variation_sku}")
                continue
            
            # ✅ FIX: normalize color_en همانند image_naming_v11 قبل از lookup
            import re as _re
            def _norm(c):
                c = str(c).strip().lower()
                c = c.replace(' ', '-').replace('_', '-')
                c = _re.sub(r'-+', '-', c)
                return c

            color_en_norm = _norm(color_en)
            color_images = image_info['color_images']
            general_images = image_info.get('general_images', [])
            
            # Try to find matching color image
            variation_image = (
                color_images.get(color_en_norm) or
                color_images.get(color_en) or
                next((v for k, v in color_images.items() if _norm(k) == color_en_norm), None) or
                next((v for k, v in color_images.items() if color_en_norm in _norm(k) or _norm(k) in color_en_norm), None)
            )
            
            # If no color match, use next available general image, then main_image
            if not variation_image:
                if general_images:
                    variation_image = general_images.pop(0)
                    safe_var = variation_image.encode('ascii', 'replace').decode('ascii')
                    print(f"   [FALLBACK] Color '{color_en}' -> general image: {safe_var}")
                else:
                    variation_image = main_image
                    print(f"   [FALLBACK] Color '{color_en}' -> main image (no general left)")
            variation_alt = f"{product_name} کد {model_display} - {color_fa}"
            
            variation_row = {
                'post_type': 'product_variation',
                'post_title': '',
                'post_status': 'publish',
                'sku': variation_sku,
                'parent_sku': str(product_sku),
                'regular_price': row.get('قیمت_اصلی', ''),
                'sale_price': row.get('قیمت_فروش', ''),
                'manage_stock': 'yes',
                'stock_quantity': row.get('موجودی', ''),
                'categories': '',
                'description': '',
                'short_description': '',
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
            
            # Clear parent fields
            for key in ['meta:_yoast_wpseo_title', 'meta:_yoast_wpseo_metadesc', 'meta:_yoast_wpseo_focuskw', 'meta:_yoast_wpseo_canonical']:
                variation_row[key] = ''
            
            output_rows.append(variation_row)
    
    # ساخت DataFrame خروجی
    df_output = pd.DataFrame(output_rows)

    # ── Copy images BEFORE writing the CSVs ──────────────────────────────
    # The WooCommerce CSVs reference image filenames. If we wrote the CSVs first
    # and the image copy then failed, we'd emit an import pointing at files that
    # never landed on disk. Copy first, track exactly which mapped images were
    # found vs missing, and let the caller gate on missing images before the
    # CSVs are treated as valid.
    copy_stats = {
        'expected': len(image_mappings),
        'copied': 0,
        'missing': 0,
        'missing_sources': [],
    }
    if process_images and source_images_folder and dest_images_folder:
        print(f"\n[IMAGE] Processing images (copying before CSV write)...")

        for source_name, target_name in image_mappings.items():
            extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.JPG', '.JPEG', '.PNG', '.WEBP']
            source_path = None

            # Try exact match first (e.g. 5718a.webp)
            for ext in extensions:
                test_path = Path(source_images_folder) / f"{source_name}{ext}"
                if test_path.exists():
                    source_path = test_path
                    break

            # Try prefix match (e.g. 5718a_black.webp)
            if not source_path:
                for f in Path(source_images_folder).iterdir():
                    if f.stem.startswith(source_name + '_') and f.suffix.lower() in [e.lower() for e in extensions]:
                        source_path = f
                        break

            if source_path:
                dest_path = Path(dest_images_folder) / target_name
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, dest_path)
                copy_stats['copied'] += 1
                safe_src = source_name.encode('ascii', 'replace').decode('ascii')
                safe_tgt = target_name.encode('ascii', 'replace').decode('ascii')
                print(f"  [OK] {safe_src} -> {safe_tgt}")
            else:
                copy_stats['missing'] += 1
                copy_stats['missing_sources'].append(source_name)
                safe_src = source_name.encode('ascii', 'replace').decode('ascii')
                print(f"  [WARN] Missing: {safe_src}")

        print(f"\n   [OK] Copied: {copy_stats['copied']} images")
        if copy_stats['missing'] > 0:
            print(f"   [WARN] Missing: {copy_stats['missing']} images")

        # Per-image gate: if any mapped image is missing, do NOT write the CSVs.
        # A partial import silently drops product images, which is worse than
        # failing loudly and re-running image processing.
        if copy_stats['missing'] > 0:
            print(
                f"\n[FAIL] {copy_stats['missing']} mapped image(s) were not found in "
                f"{source_images_folder}. Skipping CSV creation so a broken import "
                f"is not emitted. Missing sources: "
                f"{', '.join(copy_stats['missing_sources'][:20])}"
                + (" ..." if len(copy_stats['missing_sources']) > 20 else "")
            )
            return df_output, image_mappings, copy_stats

    # ذخیره CSV (only reached when every mapped image was copied)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    date_str = datetime.now().strftime('%Y%m%d')
    uploads_dir = str(IMPORT_BUILDER_UPLOADS_DIR)
    os.makedirs(uploads_dir, exist_ok=True)
    output_folder = os.path.join(uploads_dir, date_str)
    os.makedirs(output_folder, exist_ok=True)
    output_csv = os.path.join(output_folder, f"woocommerce_import_{timestamp}.csv")
    df_output.to_csv(output_csv, index=False, encoding='utf-8-sig')

# If manifests are provided, split into new vs updated CSVs using SKU
    new_manifest = os.environ.get('NEW_MANIFEST')
    updated_manifest = os.environ.get('UPDATED_MANIFEST')
    try:
        if new_manifest or updated_manifest:
            # Normalize sku column in df_output
            if 'sku' not in df_output.columns:
                if 'SKU' in df_output.columns:
                    df_output['sku'] = df_output['SKU']

            if new_manifest and os.path.exists(new_manifest):
                df_new_list = pd.read_csv(new_manifest, encoding='utf-8-sig')
                new_skus = set(map(str, df_new_list['sku'].astype(str))) if 'sku' in df_new_list.columns else set()
                if new_skus:
                    df_new_out = df_output[df_output['sku'].astype(str).isin(new_skus)]
                    new_csv = os.path.join(output_folder, f"woocommerce_new_{timestamp}.csv")
                    df_new_out.to_csv(new_csv, index=False, encoding='utf-8-sig')
                    print(f"[OK] New products CSV: {new_csv}  ({len(df_new_out)} rows)")

            if updated_manifest and os.path.exists(updated_manifest):
                df_updated_list = pd.read_csv(updated_manifest, encoding='utf-8-sig')
                updated_skus = set(map(str, df_updated_list['sku'].astype(str))) if 'sku' in df_updated_list.columns else set()
                if updated_skus:
                    df_update_out = df_output[df_output['sku'].astype(str).isin(updated_skus)]
                    update_csv = os.path.join(output_folder, f"woocommerce_update_{timestamp}.csv")
                    df_update_out.to_csv(update_csv, index=False, encoding='utf-8-sig')
                    print(f"[OK] Update products CSV: {update_csv}  ({len(df_update_out)} rows)")
    except Exception as e:
        print(f"[WARN] Could not split CSVs by manifests: {e}")

    print("\n" + "="*70)
    print(f"[OK] CSV created: {output_csv}")
    print(f"   [DATA] Total products: {len(grouped)}")
    print(f"   [DATA] Total rows: {len(df_output)}")
    print("="*70)

    # Export unknown colors to Excel
    if color_manager and hasattr(color_manager, 'export_unknown_colors'):
        color_manager.export_unknown_colors()
    
    # Export unknown product names to Excel
    if product_name_manager and hasattr(product_name_manager, 'export_unknown_products'):
        product_name_manager.export_unknown_products()

    return df_output, image_mappings, copy_stats


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("\nUsage: python woocommerce_generator_v12.py <input.xlsx|input.csv> [--process-images]")
        print("\nOptions:")
        print("   --process-images    Copy and rename images")
        print("\nExample:")
        print("   python woocommerce_generator_v12.py products.csv --process-images")
        sys.exit(1)
    
    input_file = sys.argv[1]
    process_images_flag = '--process-images' in sys.argv
    
    if not os.path.exists(input_file):
        print(f"[ERROR] Error: File not found: {input_file}")
        sys.exit(1)
    
    try:
        df_output, mappings, copy_stats = process_products_v12(
            input_file,
            process_images=process_images_flag,
            source_images_folder=SOURCE_IMAGES_FOLDER,  # ✅ همیشه پاس بده، fallback داخل تابع هندل میشه
            dest_images_folder=None
        )
        
        if df_output is not None:
            print("\n✅ Processing completed successfully!")
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
