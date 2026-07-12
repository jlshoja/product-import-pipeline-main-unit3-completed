import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def round_price(price):
    """Round to nearest 1000 (matches JS Math.round behavior)."""
    return int(price / 1000 + 0.5) * 1000


def parse_pricing_ranges(pricing_data):
    """Parse pricing ranges from list-of-lists (header + data rows).

    Expected columns: مقدار_از, مقدار_تا, درصد_افزایش, درصد_تخفیف
    """
    if not pricing_data or len(pricing_data) < 2:
        return []

    headers = [str(h or '') for h in pricing_data[0]]
    from_idx = next((i for i, h in enumerate(headers) if 'مقدار_از' in h), None)
    to_idx = next((i for i, h in enumerate(headers) if 'مقدار_تا' in h), None)
    increase_idx = next((i for i, h in enumerate(headers) if 'درصد_افزایش' in h), None)
    discount_idx = next((i for i, h in enumerate(headers) if 'درصد_تخفیف' in h), None)

    if from_idx is None or to_idx is None:
        return []

    ranges = []
    for row in pricing_data[1:]:
        if not row:
            continue
        ranges.append({
            'from': float(row[from_idx] or 0),
            'to': float(row[to_idx] or 0),
            'increase_percent': float(row[increase_idx] or 0) if increase_idx is not None else 0,
            'discount_percent': float(row[discount_idx] or 0) if discount_idx is not None else 0,
        })
    return ranges


def find_price_range(price, ranges):
    """Find the first range bracket matching the given price."""
    for r in ranges:
        if r['from'] <= price <= r['to']:
            return r
    return None


def process(df, pricing_data, extra_discount_percent=0):
    """Step 4: Apply pricing rules.

    Args:
        df: DataFrame with product data
        pricing_data: list of lists from pricing_sample.xlsx
        extra_discount_percent: additional discount from config

    Returns:
        (df, prices_updated, discounts_applied)
    """
    base_price_col = next((c for c in df.columns if 'قیمت_اصلی' in c and 'قبل' not in c and 'بعد' not in c), None)
    sale_price_col = next((c for c in df.columns if 'قیمت_فروش' in c and 'قبل' not in c and 'بعد' not in c), None)

    if base_price_col is None:
        return df, 0, 0

    ranges = parse_pricing_ranges(pricing_data)
    if not ranges:
        return df, 0, 0

    if sale_price_col is None:
        sale_price_col = 'قیمت_فروش'
        df[sale_price_col] = ''

    df['قیمت_اصلی_قبل'] = df[base_price_col].copy()
    df['قیمت_فروش_قبل'] = df[sale_price_col].copy()

    prices_updated = 0
    discounts_applied = 0

    for idx in df.index:
        raw_price = str(df.at[idx, base_price_col] or '').replace(',', '')
        try:
            current_price = float(raw_price)
        except (ValueError, TypeError):
            current_price = 0

        if current_price <= 0:
            continue

        price_range = find_price_range(current_price, ranges)
        if price_range is None:
            continue

        new_price = current_price
        if price_range['increase_percent'] > 0:
            new_price = current_price * (1 + price_range['increase_percent'] / 100)

        new_price = round_price(new_price)

        total_discount = price_range['discount_percent'] + extra_discount_percent

        if total_discount > 0:
            final_sale_price = new_price
            display_price = final_sale_price / (1 - total_discount / 100)
            df.at[idx, base_price_col] = round_price(display_price)
            df.at[idx, sale_price_col] = final_sale_price
            discounts_applied += 1
        else:
            df.at[idx, base_price_col] = new_price

        prices_updated += 1

    df['قیمت_اصلی_بعد'] = df[base_price_col].copy()
    df['قیمت_فروش_بعد'] = df[sale_price_col].copy()

    return df, prices_updated, discounts_applied
