# WooCommerce Generator v12

ابزار تولید خودکار محصولات WooCommerce از اکسل

---

## ساختار پروژه

```
woocommerce-generator/
│
├── web_panel_v12.py          ← اجرای اصلی (Flask web panel)
├── config_v9.py              ← تنظیمات (URL، مسیرها، ...)
├── requirements.txt          ← پکیج‌های مورد نیاز
├── install.bat               ← نصب اولیه (ویندوز)
├── start.bat                 ← اجرای برنامه (ویندوز)
│
├── src/                      ← کدهای ماژول‌ها
│   ├── paths.py              ← مدیریت مرکزی مسیرها
│   ├── color_manager.py      ← ترجمه رنگ فارسی ↔ انگلیسی
│   ├── color_similarity.py   ← رنگ‌های مشابه (fuzzy match)
│   ├── product_name_manager.py  ← ترجمه نام محصول
│   ├── image_naming_v11_fixed.py ← نام‌گذاری تصاویر
│   ├── image_processor_v9_1_fixed.py ← پردازش و آپلود تصاویر
│   ├── woocommerce_generator_v12.py  ← تولید CSV ووکامرس
│   └── ai_description_generator.py  ← تولید توضیحات با AI
│
├── data/                     ← فایل‌های داده (قابل ویرایش)
│   ├── color_mapping.xlsx    ← جدول رنگ‌ها (فارسی ↔ انگلیسی)
│   ├── product_names.xlsx    ← جدول نام محصولات
│   └── *.csv                 ← خروجی‌های پردازش شده
│
├── logs/                     ← لاگ‌ها
│   └── missing_products.log  ← محصولات ناشناخته
│
└── product-images/           ← عکس‌های محصولات (باید بسازید)
    ├── 1a.webp
    ├── 1b_black.webp
    └── ...
```

---

## اجرا

```bash
# نصب
pip install -r requirements.txt

# اجرا
python web_panel_v12.py

# سپس در مرورگر باز کنید:
# http://localhost:5000
```

---

## فایل‌های داده

### `data/mappings/color_mapping.xlsx`
جدول ترجمه رنگ‌ها. ستون‌ها: `Persian` | `English`

مثال:
| Persian | English |
|---------|---------|
| مشکی | black |
| سفید | white |
| سرمه‌ای | navy-blue |

### `data/mappings/product_names.xlsx`
جدول ترجمه نام محصولات. شیت: `Products`، ستون‌ها: `Persian` | `English`

مثال:
| Persian | English |
|---------|---------|
| کیف زنانه | women-bag |
| کوله پشتی | backpack |

---

## تنظیمات

فایل `config_v9.py` را ویرایش کنید:

```python
SOURCE_IMAGES_FOLDER = "product-images"   # پوشه عکس‌ها
BASE_IMAGES_URL = "https://yoursite.com/wp-content/uploads/..."
```
