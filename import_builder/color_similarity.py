#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Color Similarity Mapping
رنگ‌های مشابه برای fuzzy matching
"""

# رنگ‌های مشابه: هر رنگ می‌تونه با کدوم رنگ‌ها match بشه
COLOR_SIMILARITY = {
    # سیاه و خاکستری‌ها
    'black': ['dark-gray', 'charcoal', 'ebony', 'jet-black', 'stone-black', 'plain-black'],
    'dark-gray': ['black', 'charcoal', 'gray', 'stone-black'],
    'gray': ['dark-gray', 'light-gray', 'silver', 'charcoal'],
    'light-gray': ['gray', 'silver', 'off-white', 'white'],
    
    # سفید و کرم‌ها
    'white': ['off-white', 'cream', 'ivory', 'light-cream', 'silver', 'light-gray'],
    'off-white': ['white', 'cream', 'ivory', 'silver', 'light-gray'],
    'cream': ['beige', 'off-white', 'light-cream', 'ivory', 'light-gray', 'tan'],
    'light-cream': ['cream', 'beige', 'off-white', 'light-gray'],
    'beige': ['cream', 'tan', 'sand', 'light-gray'],
    'sand': ['beige', 'tan', 'light-gray'],
    
    # قهوه‌ای‌ها
    'brown': ['dark-brown', 'chocolate', 'coffee', 'tan'],
    'dark-brown': ['brown', 'chocolate', 'coffee', 'espresso'],
    'chocolate': ['brown', 'dark-brown', 'coffee'],
    'coffee': ['brown', 'dark-brown', 'chocolate', 'espresso'],
    'tan': ['beige', 'brown', 'sand', 'light-gray'],
    
    # عسلی و کاراملی
    'honey': ['gold', 'caramel', 'amber', 'mustard', 'tan', 'beige'],
    'caramel': ['honey', 'tan', 'brown', 'beige'],
    'gold': ['honey', 'yellow', 'mustard', 'amber'],
    
    # آبی‌ها
    'blue': ['light-blue', 'sky-blue', 'navy-blue', 'navy'],
    'light-blue': ['blue', 'sky-blue', 'cyan', 'aqua'],
    'sky-blue': ['light-blue', 'blue', 'cyan'],
    'navy-blue': ['navy', 'dark-blue', 'blue'],
    'navy': ['navy-blue', 'dark-blue', 'blue'],
    'light-navy': ['navy', 'navy-blue', 'blue'],
    'dark-blue': ['navy', 'navy-blue', 'blue'],
    
    # سرمه‌ای (special case for Persian)
    'سرمه-ای': ['navy', 'navy-blue', 'dark-blue'],
    'سرمه-ای-روشن': ['light-navy', 'navy', 'blue'],
    
    # قرمز و صورتی‌ها
    'red': ['dark-red', 'burgundy', 'maroon', 'crimson'],
    'dark-red': ['red', 'burgundy', 'maroon'],
    'burgundy': ['red', 'dark-red', 'maroon', 'wine'],
    'pink': ['light-pink', 'dusty-pink', 'rose'],
    'dusty-pink': ['pink', 'rose', 'mauve'],
    'fuchsia': ['magenta', 'pink', 'hot-pink'],
    
    # سبز‌ها
    'green': ['dark-green', 'forest-green', 'olive'],
    'dark-green': ['green', 'forest-green', 'olive'],
    'light-green': ['green', 'lime', 'mint'],
    'olive': ['green', 'dark-green', 'khaki'],
    'sage-green': ['green', 'olive', 'mint'],
    'teal': ['turquoise', 'cyan', 'green-blue'],
    'turquoise': ['teal', 'cyan', 'aqua'],
    
    # بنفش‌ها
    'purple': ['violet', 'lilac', 'lavender'],
    'lilac': ['purple', 'lavender', 'violet'],
    'violet': ['purple', 'lilac'],
    
    # نقره‌ای و طلایی
    'silver': ['gray', 'light-gray', 'metallic-gray', 'white'],
    'gold': ['golden', 'bronze', 'brass'],
    'bronze': ['gold', 'copper', 'brown'],
    'copper': ['bronze', 'gold', 'metallic-orange'],
    
    # نارنجی و زرد
    'orange': ['burnt-orange', 'tangerine', 'coral'],
    'yellow': ['mustard', 'gold', 'lemon'],
    'mustard': ['yellow', 'gold', 'honey'],
}

def get_similar_colors(color):
    """
    دریافت لیست رنگ‌های مشابه
    
    Args:
        color: نام رنگ (انگلیسی، normalize شده)
        
    Returns:
        لیست رنگ‌های مشابه
    """
    color_normalized = color.lower().strip()
    
    # اگر در جدول هست، رنگ‌های مشابه رو برگردون
    if color_normalized in COLOR_SIMILARITY:
        return COLOR_SIMILARITY[color_normalized].copy()
    
    # اگر نبود، خودش رو برگردون
    return []

def is_color_similar(color1, color2):
    """
    بررسی شباهت دو رنگ
    
    Args:
        color1: رنگ اول
        color2: رنگ دوم
        
    Returns:
        True اگر مشابه باشند
    """
    c1 = color1.lower().strip()
    c2 = color2.lower().strip()
    
    # دقیقاً یکسان
    if c1 == c2:
        return True
    
    # یکی زیرمجموعه دیگری است
    if c1 in c2 or c2 in c1:
        return True
    
    # در لیست مشابه‌ها هست
    similar = get_similar_colors(c1)
    if c2 in similar:
        return True
    
    similar = get_similar_colors(c2)
    if c1 in similar:
        return True
    
    return False

# Test
if __name__ == "__main__":
    print("="*70)
    print("Color Similarity Test")
    print("="*70)
    
    test_pairs = [
        ('black', 'dark-gray'),
        ('navy', 'navy-blue'),
        ('cream', 'beige'),
        ('coffee', 'brown'),
        ('red', 'burgundy'),
        ('black', 'white'),  # Not similar
    ]
    
    for c1, c2 in test_pairs:
        result = is_color_similar(c1, c2)
        status = "[OK] Similar" if result else "[FAIL] Not similar"
        print(f"{status}: '{c1}' ↔ '{c2}'")
    
    print("\n" + "="*70)
    print("Similar colors to 'black':")
    for c in get_similar_colors('black'):
        print(f"   - {c}")
    
    print("="*70)
