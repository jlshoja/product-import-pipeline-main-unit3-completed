#!/usr/bin/env python3
"""
اسکریپت مقایسه اندازه فایل‌ها
این اسکریپت اندازه عکس‌های اصلی را با عکس‌های پردازش شده مقایسه می‌کند
"""

import os
from pathlib import Path


def get_folder_size(folder_path):
    """محاسبه مجموع اندازه فایل‌های یک پوشه"""
    total_size = 0
    for file in Path(folder_path).rglob('*'):
        if file.is_file():
            total_size += file.stat().st_size
    return total_size


def format_size(size_bytes):
    """فرمت کردن اندازه به واحد مناسب"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def compare_folders(input_folder, output_folder):
    """مقایسه دو پوشه"""
    
    if not os.path.exists(input_folder):
        print(f"Folder {input_folder} does not exist!")
        return
    
    if not os.path.exists(output_folder):
        print(f"Folder {output_folder} does not exist!")
        return
    
    # محاسبه اندازه پوشه‌ها
    input_size = get_folder_size(input_folder)
    output_size = get_folder_size(output_folder)
    
    # محاسبه درصد کاهش
    reduction = ((input_size - output_size) / input_size * 100) if input_size > 0 else 0
    
    # شمارش فایل‌ها
    input_files = list(Path(input_folder).rglob('*.*'))
    output_files = list(Path(output_folder).rglob('*.*'))
    
    print("=" * 70)
    print("File Size Comparison Report")
    print("=" * 70)
    print()
    
    print("Input folder:")
    print(f"   Path: {input_folder}")
    print(f"   File count: {len(input_files)}")
    print(f"   Total size: {format_size(input_size)}")
    print()
    
    print("Output folder:")
    print(f"   Path: {output_folder}")
    print(f"   File count: {len(output_files)}")
    print(f"   Total size: {format_size(output_size)}")
    print()
    
    print("=" * 70)
    print("Result:")
    print("=" * 70)
    
    if output_size < input_size:
        saved = input_size - output_size
        print(f"Size decreased: {format_size(saved)} ({reduction:.1f}%)")
        print(f"Space saved: {format_size(saved)}")
    elif output_size > input_size:
        increase = output_size - input_size
        print(f"Size increased: {format_size(increase)}")
    else:
        print("No size change")
    
    print("=" * 70)
    print()
    
    # مقایسه فایل به فایل
    print("File-by-file comparison:")
    print("=" * 70)
    print(f"{'Original File':<30} {'Original Size':<12} {'New File':<30} {'New Size':<12}")
    print("-" * 70)
    
    input_file_dict = {f.stem: f for f in input_files if f.is_file()}
    
    for output_file in sorted(output_files):
        if not output_file.is_file():
            continue
            
        output_name = output_file.stem
        output_size_kb = output_file.stat().st_size / 1024
        
        # پیدا کردن فایل اصلی مشابه (ممکن است پسوند متفاوت باشد)
        matching_input = None
        for input_stem, input_file in input_file_dict.items():
            # بررسی شروع شدن نام فایل
            if input_stem.startswith(output_name[:2]):  # مثلاً 1a
                matching_input = input_file
                break
        
        if matching_input:
            input_size_kb = matching_input.stat().st_size / 1024
            reduction_percent = ((input_size_kb - output_size_kb) / input_size_kb * 100) if input_size_kb > 0 else 0
            
            status = "DOWN" if output_size_kb < input_size_kb else "UP" if output_size_kb > input_size_kb else "SAME"
            
            print(f"{matching_input.name:<30} {input_size_kb:>8.1f} KB   {output_file.name:<30} {output_size_kb:>8.1f} KB {status} {reduction_percent:>+6.1f}%")
        else:
            print(f"{'--':<30} {'--':>12}   {output_file.name:<30} {output_size_kb:>8.1f} KB")
    
    print("=" * 70)
    print()
    print("Legend:")
    print("  DOWN = size decreased")
    print("  UP   = size increased")
    print("  SAME = no change")
    print()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 2:
        input_folder = sys.argv[1]
        output_folder = sys.argv[2]
    else:
        input_folder = "./images"
        output_folder = "./output"
    
    compare_folders(input_folder, output_folder)
