#!/usr/bin/env python3
"""
🎨 Unified Product Image Processing System - Optimized Version

In a single pass, this program:
1. Groups images by category
2. Prioritizes square images (1a square, then non-square)
3. Detects the dominant color
4. Converts and compresses to WebP
5. Final naming: 1a_black.webp, 1b_navy.webp, 2a_red.webp, ...

Author: Claude
Date: 2026
"""

import os
import re
from pathlib import Path
from PIL import Image
from collections import defaultdict
import string
import numpy as np
from sklearn.cluster import MiniBatchKMeans

# =============================================================================
# COLOR DETECTION - from color_detector.py
# =============================================================================

COLOR_NAMES = {
    'red': (255, 0, 0),
    'dark-red': (139, 0, 0),
    'burgundy': (128, 0, 32),
    'maroon': (128, 0, 0),
    'burnt-orange': (204, 85, 0),
    'orange': (255, 165, 0),
    'copper': (184, 115, 51),
    'bronze': (205, 127, 50),
    'brown': (165, 42, 42),
    'dark-brown': (101, 67, 33),
    'chocolate': (123, 63, 0),
    'coffee': (111, 78, 55),
    'honey': (235, 180, 70),
    'caramel': (175, 111, 9),
    'gold': (255, 215, 0),
    'yellow': (255, 255, 0),
    'mustard': (255, 219, 88),
    'mustard-yellow': (228, 193, 55),
    'cream': (255, 253, 208),
    'light-cream': (255, 250, 230),
    'beige': (245, 245, 220),
    'tan': (210, 180, 140),
    'green': (0, 255, 0),
    'lime': (0, 255, 0),
    'dark-green': (0, 100, 0),
    'sage-green': (188, 184, 138),
    'pistachio-green': (147, 197, 114),
    'olive': (128, 128, 0),
    'jade': (0, 168, 107),
    'teal': (0, 128, 128),
    'turquoise': (64, 224, 208),
    'cyan': (0, 255, 255),
    'aqua': (0, 255, 255),
    'blue': (0, 0, 255),
    'light-blue': (173, 216, 230),
    'sky-blue': (135, 206, 235),
    'powder-blue': (176, 224, 230),
    'navy-blue': (0, 0, 128),
    'navy': (0, 0, 128),
    'light-navy': (70, 70, 140),
    'purple': (128, 0, 128),
    'lilac': (200, 162, 200),
    'magenta': (255, 0, 255),
    'fuchsia': (255, 0, 255),
    'pink': (255, 192, 203),
    'dusty-pink': (220, 177, 177),
    'white': (255, 255, 255),
    'off-white': (250, 250, 245),
    'ivory': (255, 255, 240),
    'silver': (192, 192, 192),
    'gray': (128, 128, 128),
    'light-gray': (211, 211, 211),
    'dark-gray': (105, 105, 105),
    'black': (0, 0, 0),
}

def is_background_color(rgb):
    """Check whether a color is the background"""
    r, g, b = rgb
    
    if r > 235 and g > 235 and b > 235:
        return True
    
    color_range = max(r, g, b) - min(r, g, b)
    avg_brightness = (r + g + b) / 3
    if color_range < 25 and avg_brightness > 200:
        return True
    
    return False

def rgb_to_hsv(rgb):
    """Convert RGB to HSV"""
    r, g, b = [x / 255.0 for x in rgb]
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    diff = max_c - min_c
    
    if max_c == min_c:
        h = 0
    elif max_c == r:
        h = (60 * ((g - b) / diff) + 360) % 360
    elif max_c == g:
        h = (60 * ((b - r) / diff) + 120) % 360
    elif max_c == b:
        h = (60 * ((r - g) / diff) + 240) % 360
    
    s = 0 if max_c == 0 else (diff / max_c)
    v = max_c
    
    return h, s, v

def find_closest_color_name(rgb):
    """Find the closest color name"""
    if rgb is None:
        return None
    
    r, g, b = rgb
    h, s, v = rgb_to_hsv(rgb)
    
    # Check for gray colors
    color_range = max(r, g, b) - min(r, g, b)
    avg = (r + g + b) / 3
    
    if color_range < 20:
        if avg < 40:
            return 'black'
        elif avg < 80:
            return 'dark-gray'
        elif avg < 130:
            return 'gray'
        elif avg < 180:
            return 'light-gray'
        elif avg < 235:
            return 'silver'
        else:
            return 'white'
    
    if v < 0.30 and s < 0.35:
        return 'black'
    
    if v < 0.25:
        return 'black'
    
    # Low saturation colors (neutral warm)
    if s < 0.25:
        if v > 0.80:
            if r > g > b:
                r_g_diff = r - g
                g_b_diff = g - b
                if r_g_diff > 5 and g_b_diff > 5:
                    if avg > 230:
                        return 'cream'
                    elif avg > 200:
                        return 'beige'
                    elif avg > 170:
                        return 'tan'
            if avg > 240:
                return 'off-white'
            else:
                return 'light-gray'
        elif v < 0.35:
            return 'black'
        else:
            if r > g > b and (r - b) > 15:
                return 'tan' if avg > 140 else 'brown'
            return 'gray'
    
    # Reds
    if (h < 15 or h > 345) and s > 0.4:
        if v < 0.5:
            return 'dark-red'
        elif s > 0.7 and v > 0.7:
            return 'red'
        else:
            return 'burgundy'
    
    # Pinks
    if 300 <= h < 345 and s > 0.3:
        if s > 0.7:
            return 'magenta'
        elif v > 0.7:
            return 'pink'
        else:
            return 'dusty-pink'
    
    # Find the closest color
    best_match = None
    best_score = float('inf')
    
    for color_name, color_rgb in COLOR_NAMES.items():
        c_h, c_s, c_v = rgb_to_hsv(color_rgb)
        
        h_diff = min(abs(h - c_h), 360 - abs(h - c_h))
        s_diff = abs(s - c_s)
        v_diff = abs(v - c_v)
        
        score = (h_diff * 2.0) + (s_diff * 100) + (v_diff * 80)
        
        if score < best_score:
            best_score = score
            best_match = color_name
    
    return best_match if best_match else 'unknown'

def get_dominant_color(image_path):
    """Extract dominant color - optimized version"""
    try:
        img = Image.open(image_path)
        img = img.convert('RGB')
        
        img.thumbnail((400, 400))
        pixels = np.array(img)
        
        height, width = pixels.shape[:2]
        
        # Corners for background
        corner_size = max(int(height * 0.12), int(width * 0.12), 20)
        corners = np.vstack([
            pixels[:corner_size, :corner_size].reshape(-1, 3),
            pixels[:corner_size, -corner_size:].reshape(-1, 3),
            pixels[-corner_size:, :corner_size].reshape(-1, 3),
            pixels[-corner_size:, -corner_size:].reshape(-1, 3)
        ])
        
        bg_median = np.median(corners, axis=0)
        
        # Remove background pixels
        all_pixels = pixels.reshape(-1, 3)
        bg_distance = np.sqrt(np.sum((all_pixels - bg_median) ** 2, axis=1))
        
        threshold = 45
        mask = bg_distance > threshold
        product_pixels = all_pixels[mask]
        
        if len(product_pixels) < 1000:
            cy_start = int(height * 0.2)
            cy_end = int(height * 0.8)
            cx_start = int(width * 0.2)
            cx_end = int(width * 0.8)
            center_pixels = pixels[cy_start:cy_end, cx_start:cx_end].reshape(-1, 3)
            
            center_bg_dist = np.sqrt(np.sum((center_pixels - bg_median) ** 2, axis=1))
            center_mask = center_bg_dist > (threshold * 0.7)
            product_pixels = center_pixels[center_mask]
        
        if len(product_pixels) < 500:
            cy_start = int(height * 0.3)
            cy_end = int(height * 0.7)
            cx_start = int(width * 0.3)
            cx_end = int(width * 0.7)
            product_pixels = pixels[cy_start:cy_end, cx_start:cx_end].reshape(-1, 3)
        
        # Remove strong highlights
        brightness = np.mean(product_pixels, axis=1)
        valid_mask = brightness < 250
        product_pixels = product_pixels[valid_mask]
        
        if len(product_pixels) < 100:
            return None
        
        # Sampling
        if len(product_pixels) > 5000:
            indices = np.random.choice(len(product_pixels), 5000, replace=False)
            product_pixels = product_pixels[indices]
        
        # K-means
        n_clusters = min(3, len(product_pixels) // 100)
        if n_clusters < 2:
            n_clusters = 2
        
        kmeans = MiniBatchKMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
        kmeans.fit(product_pixels)
        
        centers = kmeans.cluster_centers_
        labels = kmeans.labels_
        
        unique, counts = np.unique(labels, return_counts=True)
        sorted_indices = np.argsort(-counts)
        
        overall_brightness = np.mean(brightness)
        is_dark_product = overall_brightness < 80
        
        best_color = None
        best_score = -1
        
        for idx in sorted_indices:
            color = tuple(centers[idx].astype(int))
            percentage = counts[idx] / len(product_pixels)
            
            if is_background_color(color):
                continue
            
            h, s, v = rgb_to_hsv(color)
            color_brightness = (color[0] + color[1] + color[2]) / 3
            
            saturation_score = s * 2.0
            percentage_score = percentage * 4.0
            
            if is_dark_product:
                if color_brightness < 60:
                    darkness_bonus = 5.0
                elif color_brightness < 100:
                    darkness_bonus = 3.0
                else:
                    darkness_bonus = -2.0
            else:
                if s > 0.3:
                    darkness_bonus = 2.0
                elif color_brightness > 200:
                    darkness_bonus = -3.0
                else:
                    darkness_bonus = 0
            
            score = saturation_score + percentage_score + darkness_bonus
            
            if score > best_score and percentage > 0.05:
                best_score = score
                best_color = color
        
        return best_color
    
    except Exception as e:
        print(f"Warning: Error processing {image_path}: {e}")
        return None

# =============================================================================
# COMPRESSION & RENAMING
# =============================================================================

def get_file_size_kb(file_path):
    """Return file size in kilobytes"""
    return os.path.getsize(file_path) / 1024

def is_square_image(image_path):
    """Check whether the image is square"""
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            return width == height
    except Exception as e:
        print(f"Error reading {image_path}: {e}")
        return False

def compress_image_webp(image_path, output_path, max_size_kb=100):
    """Convert to WebP and compress"""
    try:
        with Image.open(image_path) as img:
            if img.mode not in ('RGB', 'RGBA'):
                if img.mode == 'P':
                    img = img.convert('RGBA')
                else:
                    img = img.convert('RGB')
            
            quality = 90
            img.save(output_path, 'WEBP', quality=quality, method=0)
            
            while get_file_size_kb(output_path) > max_size_kb and quality > 20:
                quality -= 5
                img.save(output_path, 'WEBP', quality=quality, method=0)
            
            if get_file_size_kb(output_path) > max_size_kb:
                current_img = img
                scale = 0.95
                while get_file_size_kb(output_path) > max_size_kb and scale > 0.2:
                    new_width = int(current_img.width * scale)
                    new_height = int(current_img.height * scale)
                    new_size = (new_width, new_height)
                    resized_img = current_img.resize(new_size, Image.Resampling.LANCZOS)
                    
                    for q in [85, 75, 65, 55, 45, 35]:
                        resized_img.save(output_path, 'WEBP', quality=q, method=0)
                        if get_file_size_kb(output_path) <= max_size_kb:
                            break
                    
                    if get_file_size_kb(output_path) <= max_size_kb:
                        break
                        
                    scale -= 0.05
            
            final_size = get_file_size_kb(output_path)
            return final_size
            
    except Exception as e:
        print(f"Error converting to WebP {image_path}: {e}")
        return None

def extract_category_number(filename):
    """Extract the category number from the filename"""
    match = re.match(r'^(\d+)', filename)
    if match:
        return int(match.group(1))
    return None

def get_next_letter(index):
    """Return the next letter (a, b, c, ...)"""
    letters = string.ascii_lowercase
    if index < 26:
        return letters[index]
    else:
        first = letters[index // 26 - 1]
        second = letters[index % 26]
        return first + second

# =============================================================================
# MAIN UNIFIED PROCESSOR
# =============================================================================

def process_images_unified(input_folder, output_folder, max_size_kb=50,
                          main_image_size_kb=100,
                          remove_bg_for_a_images=False, detect_color=True, bg_color='white'):
    """
    Unified image processing

    Args:
        input_folder: input folder containing images
        output_folder: output folder
        max_size_kb: maximum allowed size for gallery images (KB) - default: 50
        main_image_size_kb: maximum allowed size for the main 'a' image (KB) - default: 100
        remove_bg_for_a_images: remove background from 'a' images
        detect_color: detect color and add it to the filename
        bg_color: background color after removal ('white', 'black', 'transparent')
    """
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find images recursively in all subfolders
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    image_files = []
    for root, _, files in os.walk(input_path):
        for file in files:
            if Path(file).suffix.lower() in image_extensions:
                image_files.append(Path(root) / file)
    
    if not image_files:
        print("No images found!")
        return
    
    print(f"Found {len(image_files)} images\n")
    
    # Group by category
    categories = defaultdict(list)
    
    for img_file in image_files:
        category_num = extract_category_number(img_file.stem)
        if category_num is not None:
            categories[category_num].append(img_file)
        else:
            print(f"File {img_file.name} without category number - skipped")
    
    if not categories:
        print("No files with category number found!")
        return
    
    print(f"Found {len(categories)} categories: {sorted(categories.keys())}\n")
    
    # Process each category
    total_processed = 0
    total_compressed = 0
    a_images = []
    total_categories = len(categories)
    
    for cat_idx, category_num in enumerate(sorted(categories.keys()), start=1):
        images = categories[category_num]
        print(f"{'='*60}")
        print(f"Processing category {category_num} ({len(images)} images)")
        print(f"{'='*60}")
        
        # Separate square and non-square — image opened only once
        square_images = []
        non_square_images = []
        
        for img_file in images:
            try:
                with Image.open(img_file) as img:
                    w, h = img.size
                if w == h:
                    square_images.append(img_file)
                else:
                    non_square_images.append(img_file)
        
            except Exception as e:
                print(f"Error reading {img_file.name}: {e}")
                non_square_images.append(img_file)
        
        print(f"   Square images: {len(square_images)}")
        print(f"   Non-square images: {len(non_square_images)}\n")
        
        # Combine: square images first, then non-square
        sorted_images = square_images + non_square_images
        
        # Process and rename
        for idx, img_file in enumerate(sorted_images):
            letter = get_next_letter(idx)
            
            # Color detection
            color_name = None
            if detect_color:
                print(f"   Detecting color for {img_file.name}...")
                dominant_color = get_dominant_color(img_file)
                if dominant_color:
                    color_name = find_closest_color_name(dominant_color)
                    if not color_name:
                        color_name = 'unknown'
                else:
                    color_name = 'unknown'
            
            # Final name
            if color_name:
                new_name = f"{category_num}{letter}_{color_name}.webp"
            else:
                new_name = f"{category_num}{letter}.webp"
            
            output_file = output_path / new_name
            
            original_size = get_file_size_kb(img_file)
            is_square = "🟦" if img_file in square_images else "🟨"
            
            # Convert and compress (main image 100KB, rest 50KB)
            size_limit = main_image_size_kb if letter == 'a' else max_size_kb
            final_size = compress_image_webp(img_file, output_file, size_limit)
            
            if final_size:
                color_info = f" [{color_name}]" if color_name else ""
                if original_size > size_limit:
                    print(f"   {img_file.name} -> {new_name}{color_info}")
                    print(f"       ({original_size:.1f}KB -> {final_size:.1f}KB) Compressed\n")
                    total_compressed += 1
                else:
                    print(f"   {img_file.name} -> {new_name}{color_info}")
                    print(f"       ({final_size:.1f}KB) Converted\n")
                
                # If this is the 'a' image
                if letter == 'a':
                    a_images.append(output_file)
                    
                total_processed += 1
            else:
                print(f"   Error processing {img_file.name}\n")
                continue
        
        # Overall progress after finishing this category's images
        progress_pct = (cat_idx / total_categories) * 100
        print(f"   Progress: {cat_idx}/{total_categories} categories completed ({progress_pct:.1f}%)")
        
        print()
    
    # Final report
    print(f"{'='*60}")
    print(f"Processing complete!")
    print(f"{'='*60}")
    print(f"Total images processed: {total_processed}")
    print(f"Images compressed: {total_compressed}")
    print(f"Output format: WebP")
    if detect_color:
        print(f"Color in filename: Yes")
    print(f"Output folder: {output_path.absolute()}")
    print(f"{'='*60}\n")
    
    # Remove background from 'a' images
    if remove_bg_for_a_images and a_images:
        try:
            from rembg import remove
            
            print(f"{'='*60}")
            print(f"[BG REMOVAL] Removing background from 'a' images")
            print(f"{'='*60}")
            print(f"Number of 'a' images: {len(a_images)}")
            print(f"Background color: {bg_color.capitalize()}\n")
            
            # Determine background color
            if bg_color == 'white':
                bg_rgb = (255, 255, 255)
            elif bg_color == 'black':
                bg_rgb = (0, 0, 0)
            else:  # transparent
                bg_rgb = None
            
            success_count = 0
            for a_image in a_images:
                print(f"[PROCESSING] {a_image.name}...")
                
                temp_file = a_image.parent / f"temp_{a_image.name}"
                
                try:
                    # Step 1: Remove background (makes it transparent)
                    with open(a_image, 'rb') as input_file:
                        input_data = input_file.read()
                        output_data = remove(input_data)
                    
                    # Step 2: Open the image with transparent background
                    from io import BytesIO
                    img_transparent = Image.open(BytesIO(output_data))
                    
                    # Step 3: Add background color (if not transparent)
                    if bg_rgb is not None and img_transparent.mode in ('RGBA', 'LA'):
                        # Create colored background
                        colored_bg = Image.new('RGB', img_transparent.size, bg_rgb)
                        
                        # Paste the image on colored background
                        if img_transparent.mode == 'RGBA':
                            colored_bg.paste(img_transparent, mask=img_transparent.split()[3])  # Use alpha channel as mask
                        else:  # LA
                            colored_bg.paste(img_transparent, mask=img_transparent.split()[1])
                        
                        # Save with colored background
                        colored_bg.save(temp_file, 'WebP', quality=95)
                        status_msg = f"Background removed + {bg_color} background added"
                    else:
                        # Save with transparent background or no transparency
                        img_transparent.save(temp_file, 'WebP', quality=95)
                        status_msg = "Background removed (transparent)"
                    
                    temp_file.replace(a_image)
                    print(f"   [OK] {status_msg}\n")
                    success_count += 1
                    
                except Exception as e:
                    print(f"   [ERROR] {e}\n")
                    if temp_file.exists():
                        temp_file.unlink()
            
            print(f"{'='*60}")
            print(f"[COMPLETE] Background removal complete!")
            print(f"[SUCCESS] {success_count} of {len(a_images)} images processed")
            if bg_rgb is not None:
                print(f"[NOTE] {bg_color.capitalize()} background added to all images")
            else:
                print(f"[NOTE] Transparent background kept")
            print(f"{'='*60}\n")
            
        except ImportError:
            print(f"\n[WARNING] rembg library not installed!")
            print(f"To install: pip install \"rembg[cpu]\"\n")

# =============================================================================
# MAIN
# =============================================================================

def find_all_dated_subfolders(base_folder):
    """
    Looks inside base_folder for all dated subfolders and returns them sorted by date.
    Main format: YYYY-MM-DD_HH-MM-SS  (example: 2026-06-10_23-19-37)
    Alternative formats: YYYY-MM-DD, YYYYMMDD
    """
    import re
    from datetime import datetime

    base_path = Path(base_folder)

    formats = [
        (re.compile(r'^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$'), '%Y-%m-%d_%H-%M-%S'),
        (re.compile(r'^\d{4}-\d{2}-\d{2}$'),                    '%Y-%m-%d'),
        (re.compile(r'^\d{8}$'),                                  '%Y%m%d'),
    ]

    dated_folders = []
    for entry in base_path.iterdir():
        if not entry.is_dir():
            continue
        for pattern, fmt in formats:
            if pattern.match(entry.name):
                try:
                    dt = datetime.strptime(entry.name, fmt)
                    dated_folders.append((dt, entry))
                    break
                except ValueError:
                    pass

    dated_folders.sort(key=lambda x: x[0])
    return [folder for (dt, folder) in dated_folders]

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Unified Image Processing System')
    parser.add_argument('-i', '--input', 
                        default='./downloaded_images',
                        help='Input folder containing images (default: ./downloaded_images)')
    parser.add_argument('-o', '--output',
                        default='./output',
                        help='Output folder (default: ./output)')
    parser.add_argument('-s', '--size',
                        type=int,
                        default=50,
                        help='Maximum file size for gallery images in KB (default: 50)')
    parser.add_argument('-m', '--main-size',
                        type=int,
                        default=100,
                        help="Maximum file size for main 'a' image in KB (default: 100)")
    parser.add_argument('--remove-bg',
                        action='store_true',
                        help="Remove background from 'a' images (1a, 2a, 3a, ...)")
    parser.add_argument('--bg-color',
                        default='white',
                        choices=['white', 'black', 'transparent'],
                        help="Background color after removal (default: white)")
    parser.add_argument('--no-color',
                        action='store_true',
                        help="Without color detection (simple naming only)")
    
    args = parser.parse_args()

    # ── Input: all dated subfolders ──────────────────────────────────────
    if not os.path.exists(args.input):
        print(f"Error: Folder '{args.input}' does not exist!")
        print(f"Please create the folder and place images in it.")
        return

    all_subfolders = find_all_dated_subfolders(args.input)
    if all_subfolders:
        print(f"Found {len(all_subfolders)} dated subfolders:")
        for folder in all_subfolders:
            print(f"   - {folder.name}")
        
        # Use all subfolders for processing
        effective_input = args.input
        print(f"Processing images from all dated subfolders in '{args.input}'")
    else:
        # If no dated subfolder is found, use the base folder directly
        effective_input = args.input
        print(f"No dated subfolder found in '{args.input}' — reading directly from it.")

    # ── Output: subfolder dated with today's date ───────────────────────────
    from datetime import datetime
    today_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    effective_output = str(Path(args.output) / today_str)

    print("Unified Image Processing System")
    print(f"{'='*60}")
    print(f"Input base folder: {args.input}")
    print(f"Input folder used: {effective_input}")
    print(f"Output folder: {effective_output}")
    print(f"Main image (a) max size: {args.main_size} KB")
    print(f"Gallery images max size: {args.size} KB")
    print(f"Output format: WebP")
    print(f"Color detection: {'No' if args.no_color else 'Yes'}")
    print(f"Square priority: Yes")
    if args.remove_bg:
        print(f"Remove background: Yes (only 'a' images)")
        print(f"Background color: {args.bg_color.capitalize()}")
    print(f"{'='*60}\n")
    
    # Process images
    process_images_unified(
        effective_input,
        effective_output,
        args.size,
        args.main_size,
        args.remove_bg,
        not args.no_color,
        args.bg_color
    )
    
    print("\nDone!")


if __name__ == "__main__":
    main()
