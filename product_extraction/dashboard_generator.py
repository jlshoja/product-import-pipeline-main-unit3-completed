# Fix Windows console encoding
import codecs
import sys

if sys.platform == "win32":
    try:
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "replace")
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "replace")
    except:
        pass

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Generator - تولید داشبورد HTML تعاملی
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

# اضافه کردن مسیر پروژه
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from common.file_registry import get_file
    from common.path_registry import (
        ASSET_TEMPLATES_DIR,
        REPORTS_DIR,
        RUNTIME_REPORTS_DIR,
        resolve_existing_path,
        get_dated_reports_dir,
    )
    from common.date_utils import get_persian_date as shared_get_persian_date
    from config import get_config
    from utils.logger import LoggerSetup

    logger = LoggerSetup.get_tracker_logger()

except ImportError:
    import logging

    from common.file_registry import get_file
    from common.path_registry import (
        ASSET_TEMPLATES_DIR,
        REPORTS_DIR,
        RUNTIME_REPORTS_DIR,
        resolve_existing_path,
    )
    from common.date_utils import get_persian_date as shared_get_persian_date

    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)


class DashboardGenerator:
    """کلاس تولید داشبورد تعاملی"""

    def __init__(self, template_path: Optional[Path] = None):
        """
        مقداردهی اولیه

        Args:
            template_path: مسیر template HTML
        """
        self.template_path = template_path or (
            ASSET_TEMPLATES_DIR / get_file("dashboard_template")
        )
        self.logger = logger

        # بررسی وجود template
        if not self.template_path.exists():
            self.logger.warning(f"Template not found: {self.template_path}")

    def generate(
        self,
        current_df: pd.DataFrame,
        new_products: List[Dict],
        price_changes: List[Dict],
        removed_products: List[Dict],
        previous_df: Optional[pd.DataFrame] = None,
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        تولید داشبورد HTML

        Args:
            current_df: DataFrame محصولات فعلی
            new_products: لیست محصولات جدید
            price_changes: لیست تغییرات قیمت
            removed_products: لیست محصولات حذف شده
            previous_df: DataFrame قبلی (برای روند قیمت)
            output_path: مسیر خروجی

        Returns:
            مسیر فایل تولید شده
        """
        self.logger.info("شروع تولید داشبورد...")

        # خواندن template
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template not found: {self.template_path}")

        with open(self.template_path, "r", encoding="utf-8") as f:
            template = f.read()

        # آماده‌سازی داده‌ها
        stats = self._calculate_statistics(
            current_df, new_products, price_changes, removed_products
        )

        chart_data = self._prepare_chart_data(current_df, price_changes, previous_df)

        # تولید جداول HTML
        all_products_rows = self._generate_all_products_rows(current_df)
        new_products_rows = self._generate_new_products_rows(new_products)
        changed_products_rows = self._generate_price_changes_rows(price_changes)
        removed_products_rows = self._generate_removed_products_rows(removed_products)

        # جایگزینی placeholder ها
        html = template
        html = html.replace("{{UPDATE_DATE}}", self._get_persian_date())
        html = html.replace("{{TOTAL_PRODUCTS}}", str(stats["total"]))
        html = html.replace("{{NEW_PRODUCTS}}", str(stats["new"]))
        html = html.replace("{{CHANGED_PRODUCTS}}", str(stats["changed"]))
        html = html.replace("{{REMOVED_PRODUCTS}}", str(stats["removed"]))

        html = html.replace("{{ALL_PRODUCTS_ROWS}}", all_products_rows)
        html = html.replace("{{NEW_PRODUCTS_ROWS}}", new_products_rows)
        html = html.replace("{{CHANGED_PRODUCTS_ROWS}}", changed_products_rows)
        html = html.replace("{{REMOVED_PRODUCTS_ROWS}}", removed_products_rows)

        html = html.replace(
            "{{CHART_DATA}}", json.dumps(chart_data, ensure_ascii=False)
        )

        # حذف handlebar conditionals (ساده‌سازی شده)
        html = self._remove_handlebar_conditionals(html, stats)

        # ذخیره فایل
        if output_path is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
            dated_dir = get_dated_reports_dir(date_str)
            output_path = dated_dir / f"dashboard_{date_str}.html"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        self.logger.info(f"✅ داشبورد تولید شد: {output_path}")

        return output_path

    def _calculate_statistics(
        self,
        current_df: pd.DataFrame,
        new_products: List[Dict],
        price_changes: List[Dict],
        removed_products: List[Dict],
    ) -> Dict:
        """محاسبه آمار کلی"""
        return {
            "total": len(current_df),
            "new": len(new_products),
            "changed": len(price_changes),
            "removed": len(removed_products),
            "unchanged": len(current_df) - len(new_products) - len(price_changes),
        }

    def _prepare_chart_data(
        self,
        current_df: pd.DataFrame,
        price_changes: List[Dict],
        previous_df: Optional[pd.DataFrame],
    ) -> Dict:
        """آماده‌سازی داده‌های نمودار"""

        # شمارش تغییرات قیمت
        price_increased = sum(
            1 for pc in price_changes if pc.get("تغییر (تومان)", 0) > 0
        )
        price_decreased = sum(
            1 for pc in price_changes if pc.get("تغییر (تومان)", 0) < 0
        )
        price_unchanged = (
            len(current_df)
            - len(price_changes)
            - len(
                [p for p in current_df.to_dict("records") if p.get("وضعیت") == "جدید"]
            )
        )

        # محاسبه روند قیمت (7 روز گذشته - mock data)
        dates = self._generate_last_7_days()
        avg_prices = self._calculate_price_trend(current_df, previous_df)

        return {
            "new": len(
                [p for p in current_df.to_dict("records") if p.get("وضعیت") == "جدید"]
            ),
            "changed": len(price_changes),
            "unchanged": price_unchanged,
            "removed": 0,  # این باید از لیست removed_products بیاید
            "priceIncreased": price_increased,
            "priceDecreased": price_decreased,
            "priceUnchanged": price_unchanged,
            "dates": dates,
            "avgPrices": avg_prices,
        }

    def _generate_last_7_days(self) -> List[str]:
        """تولید لیست 7 روز گذشته"""
        dates = []
        for i in range(6, -1, -1):
            date = datetime.now() - timedelta(days=i)
            dates.append(date.strftime("%Y/%m/%d"))
        return dates

    def _calculate_price_trend(
        self, current_df: pd.DataFrame, previous_df: Optional[pd.DataFrame]
    ) -> List[int]:
        """محاسبه روند میانگین قیمت"""
        # Mock data - در واقعیت باید از history استخراج شود
        if "قیمت فعلی" in current_df.columns:
            current_avg = current_df["قیمت فعلی"].mean()

            # تولید داده mock با تغییرات تصادفی
            import random

            base_price = current_avg
            prices = []
            for i in range(7):
                variation = random.uniform(-0.05, 0.05)  # +/- 5% تغییر
                prices.append(int(base_price * (1 + variation)))

            return prices

        return [0] * 7

    def _generate_all_products_rows(self, df: pd.DataFrame) -> str:
        """تولید ردیف‌های جدول همه محصولات"""
        rows = []

        for idx, row in df.iterrows():
            status = row.get("وضعیت", "نامشخص")
            badge_class = {
                "جدید": "new",
                "تغییر قیمت": "changed",
                "بدون تغییر": "unchanged",
            }.get(status, "unchanged")

            price = self._format_price(row.get("قیمت فعلی"))

            row_html = f"""
                <tr>
                    <td>{row.get("No", idx + 1)}</td>
                    <td>{row.get("نام محصول", "")}</td>
                    <td>{row.get("کد محصول", "")}</td>
                    <td class="price">{price}</td>
                    <td><span class="badge {badge_class}">{status}</span></td>
                    <td><a href="{row.get("لینک محصول", "#")}" target="_blank"><i class="fas fa-external-link-alt"></i></a></td>
                </tr>
            """
            rows.append(row_html)

        return "\n".join(rows)

    def _generate_new_products_rows(self, products: List[Dict]) -> str:
        """تولید ردیف‌های محصولات جدید"""
        if not products:
            return '<tr><td colspan="5" style="text-align:center;">محصول جدیدی یافت نشد</td></tr>'

        rows = []
        for i, product in enumerate(products, 1):
            price = self._format_price(product.get("قیمت فعلی"))

            row_html = f"""
                <tr>
                    <td>{i}</td>
                    <td>{product.get("نام محصول", "")}</td>
                    <td>{product.get("کد محصول", "")}</td>
                    <td class="price">{price}</td>
                    <td><a href="{product.get("لینک محصول", "#")}" target="_blank"><i class="fas fa-external-link-alt"></i></a></td>
                </tr>
            """
            rows.append(row_html)

        return "\n".join(rows)

    def _generate_price_changes_rows(self, changes: List[Dict]) -> str:
        """تولید ردیف‌های تغییرات قیمت"""
        if not changes:
            return '<tr><td colspan="7" style="text-align:center;">تغییر قیمتی یافت نشد</td></tr>'

        rows = []
        for i, change in enumerate(changes, 1):
            old_price = self._format_price(change.get("قیمت قبلی"))
            new_price = self._format_price(change.get("قیمت جدید"))
            price_diff = change.get("تغییر (تومان)", 0)
            percent = change.get("درصد تغییر", 0)

            # تعیین جهت تغییر
            if price_diff > 0:
                arrow = "↑"
                diff_class = "price-up"
            elif price_diff < 0:
                arrow = "↓"
                diff_class = "price-down"
            else:
                arrow = "="
                diff_class = ""

            row_html = f"""
                <tr>
                    <td>{i}</td>
                    <td>{change.get("نام محصول", "")}</td>
                    <td class="price">{old_price}</td>
                    <td class="price">{new_price}</td>
                    <td class="price-change {diff_class}">
                        <span>{arrow}</span>
                        <span>{self._format_price(abs(price_diff))}</span>
                    </td>
                    <td class="{diff_class}">{percent:+.2f}%</td>
                    <td><a href="{change.get("لینک محصول", "#")}" target="_blank"><i class="fas fa-external-link-alt"></i></a></td>
                </tr>
            """
            rows.append(row_html)

        return "\n".join(rows)

    def _generate_removed_products_rows(self, products: List[Dict]) -> str:
        """تولید ردیف‌های محصولات حذف شده"""
        if not products:
            return '<tr><td colspan="6" style="text-align:center;">محصول حذف شده‌ای یافت نشد</td></tr>'

        rows = []
        for i, product in enumerate(products, 1):
            price = self._format_price(product.get("قیمت آخرین"))

            row_html = f"""
                <tr style="background: rgba(220, 53, 69, 0.05);">
                    <td>{i}</td>
                    <td>{product.get("نام محصول", "")}</td>
                    <td>{product.get("کد محصول", "")}</td>
                    <td class="price">{price}</td>
                    <td>{product.get("تاریخ حذف", "")}</td>
                    <td><a href="{product.get("لینک محصول", "#")}" target="_blank"><i class="fas fa-external-link-alt"></i></a></td>
                </tr>
            """
            rows.append(row_html)

        return "\n".join(rows)

    def _format_price(self, price) -> str:
        """فرمت کردن قیمت"""
        if pd.isna(price) or price is None:
            return "N/A"

        try:
            price = float(str(price).replace(",", "").replace("٬", ""))
            return f"{int(price):,}".replace(",", "٬") + " تومان"
        except:
            return str(price)

    def _get_persian_date(self) -> str:
        """دریافت تاریخ شمسی"""
        try:
            return shared_get_persian_date()
        except:
            # Fallback به تاریخ میلادی
            return datetime.now().strftime("%Y/%m/%d")

    def _remove_handlebar_conditionals(self, html: str, stats: Dict) -> str:
        """حذف ساده conditional های handlebar"""
        # این یک implementation ساده است
        # برای استفاده حرفه‌ای‌تر می‌توان از Jinja2 استفاده کرد

        # جایگزینی {{#if}} blocks
        if stats["new"] > 0:
            html = html.replace("{{#if NEW_PRODUCTS_COUNT}}", "")
            html = html.replace("{{else}}", "<!--")
            html = html.replace("{{/if}}", "-->")
        else:
            html = html.replace("{{#if NEW_PRODUCTS_COUNT}}", "<!--")
            html = html.replace("{{else}}", "-->")
            html = html.replace("{{/if}}", "")

        # حذف باقیمانده tags
        import re

        html = re.sub(r"\{\{#if.*?\}\}", "", html)
        html = re.sub(r"\{\{else\}\}", "", html)
        html = re.sub(r"\{\{/if\}\}", "", html)

        return html


# ===========================
# Test Function
# ===========================


def test_dashboard_generator():
    """تست تولید داشبورد"""
    print("\n🧪 Testing Dashboard Generator...")
    print("=" * 70)

    # ساخت داده‌های تست
    current_df = pd.DataFrame(
        {
            "No": [1, 2, 3, 4, 5],
            "نام محصول": ["کیف 1", "کیف 2", "کیف 3", "کیف 4", "کیف 5"],
            "کد محصول": ["001", "002", "003", "004", "005"],
            "قیمت فعلی": [100000, 150000, 200000, 180000, 220000],
            "لینک محصول": ["#"] * 5,
            "وضعیت": ["جدید", "تغییر قیمت", "بدون تغییر", "جدید", "تغییر قیمت"],
        }
    )

    new_products = [
        {
            "نام محصول": "کیف 1",
            "کد محصول": "001",
            "قیمت فعلی": 100000,
            "لینک محصول": "#",
        },
        {
            "نام محصول": "کیف 4",
            "کد محصول": "004",
            "قیمت فعلی": 180000,
            "لینک محصول": "#",
        },
    ]

    price_changes = [
        {
            "نام محصول": "کیف 2",
            "قیمت قبلی": 140000,
            "قیمت جدید": 150000,
            "تغییر (تومان)": 10000,
            "درصد تغییر": 7.14,
            "لینک محصول": "#",
        },
        {
            "نام محصول": "کیف 5",
            "قیمت قبلی": 250000,
            "قیمت جدید": 220000,
            "تغییر (تومان)": -30000,
            "درصد تغییر": -12.0,
            "لینک محصول": "#",
        },
    ]

    removed_products = []

    # تولید داشبورد
    generator = DashboardGenerator()
    output_path = generator.generate(
        current_df=current_df,
        new_products=new_products,
        price_changes=price_changes,
        removed_products=removed_products,
    )

    print(f"\n✅ داشبورد تولید شد: {output_path}")
    print(f"📊 آمار:")
    print(f"  - کل محصولات: {len(current_df)}")
    print(f"  - محصولات جدید: {len(new_products)}")
    sys.stdout.flush()
    print(f"  - تغییرات قیمت: {len(price_changes)}")
    print(f"  - محصولات حذف شده: {len(removed_products)}")
    sys.stdout.flush()
    print("=" * 70 + "\n")

    return output_path


if __name__ == "__main__":
    test_dashboard_generator()

