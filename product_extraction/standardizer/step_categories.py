import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DEFAULT_TREE = {
    'اکسسوری': ['کیف پول', 'کیف آرایشی', 'کیف پاسپورتی', 'جاکارتی', 'کیف کمری'],
    'سفر و ورزش': ['ساک', 'چمدان', 'کیف باشگاه', 'کیف کوهنوردی'],
    'کوله‌پشتی': ['کوله‌پشتی روزمره', 'کوله‌پشتی زنانه', 'کوله‌پشتی لپ‌تاپ', 'کوله‌پشتی مردانه'],
    'کیف زنانه': ['کیف اداری زنانه', 'کیف دستی زنانه', 'کیف دوشی زنانه', 'کیف روزمره زنانه', 'کیف کراس‌بادی زنانه', 'کیف مجلسی زنانه'],
    'کیف مردانه': ['کیف اداری مردانه', 'کیف دستی مردانه', 'کیف دوشی مردانه', 'کیف روزمره مردانه', 'کیف کراس‌بادی مردانه'],
}

DEFAULT_KEYWORDS = {
    'کیف پول': ['کیف پول'],
    'کیف آرایشی': ['آرایشی'],
    'کیف پاسپورتی': ['پاسپورتی'],
    'جاکارتی': ['جاکارتی'],
    'کیف کمری': ['کمری'],
    'ساک': ['ساک'],
    'چمدان': ['چمدان'],
    'کیف باشگاه': ['کیف باشگاه', 'باشگاه'],
    'کیف کوهنوردی': ['کیف کوهنوردی', 'کوهنوردی'],
    'کوله‌پشتی روزمره': ['روزمره', 'روزانه', 'مدرسه', 'دانشگاه', 'اسپرت', 'daily', 'school'],
    'کوله‌پشتی لپ‌تاپ': ['لپ‌تاپ', 'لپتاپ', 'لپ تاپ', 'laptop'],
    'کوله‌پشتی زنانه': ['زنانه', 'دخترانه'],
    'کوله‌پشتی مردانه': ['مردانه', 'پسرانه'],
    'کیف روزمره زنانه': ['روزمره', 'روزانه', 'اسپرت', 'daily', 'sport', 'athletic'],
    'کیف اداری زنانه': ['اداری', 'رسمی', 'formal', 'office'],
    'کیف دستی زنانه': ['دستی'],
    'کیف دوشی زنانه': ['دوشی'],
    'کیف کراس‌بادی زنانه': ['کراس بادی', 'کراس‌بادی', 'کراسبادی'],
    'کیف مجلسی زنانه': ['مجلسی', 'مهمانی', 'ceremonial'],
    'کیف روزمره مردانه': ['روزمره', 'روزانه', 'اسپرت', 'daily', 'sport', 'athletic', 'school'],
    'کیف اداری مردانه': ['اداری', 'رسمی', 'formal', 'office'],
    'کیف دستی مردانه': ['دستی'],
    'کیف دوشی مردانه': ['دوشی'],
    'کیف کراس‌بادی مردانه': ['کراس بادی', 'کراس‌بادی', 'کراسبادی'],
}


def _build_category_maps(categories_data):
    """Build category tree and alias map from standard_categories file."""
    standard_tree = {}
    alias_map = {}

    if categories_data and len(categories_data) > 1:
        for row in categories_data[1:]:
            if not row:
                continue
            main_cat = str(row[0]).strip() if len(row) > 0 and row[0] else None
            sub_cat = str(row[1]).strip() if len(row) > 1 and row[1] else None
            expr = str(row[2]).strip() if len(row) > 2 and row[2] else None
            equiv = str(row[3]).strip() if len(row) > 3 and row[3] else None

            if main_cat and sub_cat:
                if main_cat not in standard_tree:
                    standard_tree[main_cat] = []
                if sub_cat not in standard_tree[main_cat]:
                    standard_tree[main_cat].append(sub_cat)
            if expr and equiv:
                alias_map[expr] = equiv

    if not standard_tree:
        standard_tree = DEFAULT_TREE.copy()

    return standard_tree, alias_map


def _build_sub_map(main_cat_name, standard_tree, alias_map):
    """Build keyword-to-subcategory map for a main category."""
    subs = standard_tree.get(main_cat_name, [])
    result = []
    for sub_full in subs:
        base_kws = DEFAULT_KEYWORDS.get(sub_full, [])
        alias_kws = [expr for expr, equiv in alias_map.items() if equiv == sub_full]
        result.append({'sub': sub_full, 'kws': base_kws + alias_kws})
    result.sort(key=lambda x: 0 if 'روزمره' in x['sub'] else 1)
    return result


def _find_sub_from_map(text, sub_map):
    """Find subcategory by keyword match in text."""
    t = str(text or '')
    for entry in sub_map:
        if any(kw in t for kw in entry['kws']):
            return entry['sub']
    return None


def _resolve_sub_cat(name_text, usage_text, suitable_text, sub_map):
    """Resolve subcategory from name, then usage, then suitable columns."""
    return (
        _find_sub_from_map(name_text, sub_map)
        or _find_sub_from_map(usage_text, sub_map)
        or _find_sub_from_map(suitable_text, sub_map)
    )


def process(df, categories_data):
    """Step 5: Generate categories and sale_tag.

    Args:
        df: DataFrame with product data
        categories_data: list of lists from standard_categories.xlsx

    Returns:
        (df, count, tagged_count)
    """
    standard_tree, alias_map = _build_category_maps(categories_data)

    backpack_key = next((k for k in standard_tree if 'کوله' in k), 'کوله‌پشتی')
    backpack_sub_map = _build_sub_map(backpack_key, standard_tree, alias_map)
    women_sub_map = _build_sub_map('کیف زنانه', standard_tree, alias_map)
    men_sub_map = _build_sub_map('کیف مردانه', standard_tree, alias_map)

    accessory_keywords = []
    for sub in standard_tree.get('اکسسوری', []):
        kws = DEFAULT_KEYWORDS.get(sub, [sub])
        accessory_keywords.append({'kw': kws[0], 'sub': sub})

    travel_keywords = []
    for sub in standard_tree.get('سفر و ورزش', []):
        if sub == 'ساک':
            continue
        kws = DEFAULT_KEYWORDS.get(sub, [sub])
        travel_keywords.append({'kw': kws[0], 'sub': sub})

    name_col = next((c for c in df.columns if 'نام' in c), None)
    category_col = next((c for c in df.columns if 'دسته_بندی' in c), None)
    usage_col = next((c for c in df.columns if 'کاربرد' in c), None)
    suitable_col = next((c for c in df.columns if 'مناسب' in c), None)
    sale_price_col = next((c for c in df.columns if c.strip() == 'قیمت_فروش'), None)
    sale_after_col = next((c for c in df.columns if 'قیمت_فروش_بعد' in c), None)

    if 'sale_tag' not in df.columns:
        df['sale_tag'] = ''

    if name_col is None or category_col is None:
        return df, 0, 0

    count = 0
    tagged_count = 0

    for idx in df.index:
        name_val = df.at[idx, name_col]
        product_name = '' if pd.isna(name_val) else str(name_val)
        usage_val = df.at[idx, usage_col] if usage_col else None
        usage = '' if usage_val is None or pd.isna(usage_val) else str(usage_val)
        suitable_val = df.at[idx, suitable_col] if suitable_col else None
        suitable = '' if suitable_val is None or pd.isna(suitable_val) else str(suitable_val)

        sale_val = 0
        if sale_price_col:
            try:
                sale_val = float(str(df.at[idx, sale_price_col] or '0').replace(',', ''))
            except (ValueError, TypeError):
                pass
        sale_after_val = 0
        if sale_after_col:
            try:
                sale_after_val = float(str(df.at[idx, sale_after_col] or '0').replace(',', ''))
            except (ValueError, TypeError):
                pass
        has_discount = sale_val > 0 or sale_after_val > 0

        if 'کیف ساک' in product_name:
            product_name = product_name.replace('کیف ساک', 'ساک')
            df.at[idx, name_col] = product_name

        main_cat = None
        sub_cat = None

        # Phase 1: Detect main category from product name
        if not main_cat:
            for acc in accessory_keywords:
                if acc['kw'] in product_name:
                    main_cat = 'اکسسوری'
                    sub_cat = acc['sub']
                    break

        if not main_cat:
            for ts in travel_keywords:
                if ts['kw'] in product_name:
                    main_cat = 'سفر و ورزش'
                    sub_cat = ts['sub']
                    break

        if not main_cat and 'ساک' in product_name:
            main_cat = 'سفر و ورزش'
            subs = standard_tree.get('سفر و ورزش', [])
            sub_cat = 'ساک' if 'ساک' in subs else (subs[0] if subs else 'ساک')

        if not main_cat and ('کوله' in product_name or 'کوله‌پشتی' in product_name):
            main_cat = backpack_key

        if not main_cat and 'کیف زنانه' in product_name:
            main_cat = 'کیف زنانه'

        if not main_cat and 'کیف مردانه' in product_name:
            main_cat = 'کیف مردانه'

        # Phase 2: Try usage column
        if not main_cat:
            for acc in accessory_keywords:
                if acc['kw'] in usage:
                    main_cat = 'اکسسوری'
                    sub_cat = acc['sub']
                    break

        if not main_cat:
            for ts in travel_keywords:
                if ts['kw'] in usage:
                    main_cat = 'سفر و ورزش'
                    sub_cat = ts['sub']
                    break

        # Phase 3: Resolve subcategory from sub_map
        if main_cat and not sub_cat:
            if main_cat == backpack_key:
                sub_cat = _resolve_sub_cat(product_name, usage, suitable, backpack_sub_map)
            elif main_cat == 'کیف زنانه':
                sub_cat = _resolve_sub_cat(product_name, usage, suitable, women_sub_map)
            elif main_cat == 'کیف مردانه':
                sub_cat = _resolve_sub_cat(product_name, usage, suitable, men_sub_map)

        # Build final category value
        if main_cat:
            category_value = f'{main_cat}>{sub_cat}' if sub_cat else main_cat
        else:
            category_value = ''

        df.at[idx, category_col] = category_value

        if has_discount:
            df.at[idx, 'sale_tag'] = 'تخفیف خورده‌ها'
            tagged_count += 1

        count += 1

    return df, count, tagged_count
