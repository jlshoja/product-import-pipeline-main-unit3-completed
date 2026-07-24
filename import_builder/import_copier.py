#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Import Copier - Copies generated WooCommerce import files and images
to the target WooCommerce Import Project folders.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Import from this module's directory
import sys
_this_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(_this_dir))

from paths import IMPORT_PROJECT_EXCEL_DIR, IMPORT_PROJECT_IMAGES_DIR, IMPORT_BUILDER_UPLOADS_DIR


def copy_excel_files(generated_files: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Copy Excel files to the import project input folder.
    
    Args:
        generated_files: Dict mapping file type to source path.
                        Expected keys: 'full', 'new', 'update' (optional)
    
    Returns:
        List of copy operation results (for logging/manifest).
    """
    results = []
    target_dir = IMPORT_PROJECT_EXCEL_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    
    for ftype, src_path in generated_files.items():
        if ftype not in ('full', 'new', 'update'):
            continue
        src = Path(src_path)
        if not src.exists():
            results.append({
                'source': str(src),
                'destination': str(target_dir / src.name),
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': 'Source file not found'
            })
            continue
        
        dst = target_dir / src.name
        try:
            shutil.copy2(src, dst)
            results.append({
                'source': str(src),
                'destination': str(dst),
                'timestamp': datetime.now().isoformat(),
                'success': True,
                'file_type': ftype,
                'size_bytes': dst.stat().st_size
            })
        except Exception as e:
            results.append({
                'source': str(src),
                'destination': str(dst),
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results


def copy_images(source_images_dir: Path) -> List[Dict[str, Any]]:
    """
    Copy renamed images to the import project images folder (overwrite mode).
    
    Args:
        source_images_dir: Path to the dated renamed_images folder.
    
    Returns:
        List of copy operation results (for logging/manifest).
    """
    results = []
    target_dir = IMPORT_PROJECT_IMAGES_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    
    if not source_images_dir.exists():
        return [{
            'source': str(source_images_dir),
            'destination': str(target_dir),
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'error': 'Source images directory not found'
        }]
    
    image_extensions = {'.webp', '.jpg', '.jpeg', '.png', '.gif'}
    copied_count = 0
    
    for img_file in source_images_dir.iterdir():
        if not img_file.is_file():
            continue
        if img_file.suffix.lower() not in image_extensions:
            continue
        
        dst = target_dir / img_file.name
        try:
            shutil.copy2(img_file, dst)
            results.append({
                'source': str(img_file),
                'destination': str(dst),
                'timestamp': datetime.now().isoformat(),
                'success': True,
                'file_type': 'image',
                'size_bytes': dst.stat().st_size
            })
            copied_count += 1
        except Exception as e:
            results.append({
                'source': str(img_file),
                'destination': str(dst),
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    # Add summary
    results.append({
        'source': str(source_images_dir),
        'destination': str(target_dir),
        'timestamp': datetime.now().isoformat(),
        'success': True,
        'summary': True,
        'images_copied': copied_count
    })
    
    return results


def copy_all_to_import_project(
    generated_files: Dict[str, str],
    renamed_images_dir: Path
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Main orchestration function: copy both Excel files and images.
    
    Args:
        generated_files: Dict with keys 'full', 'new', 'update' mapping to source paths.
        renamed_images_dir: Path to the dated renamed_images folder.
    
    Returns:
        Dict with 'excel_copies' and 'image_copies' lists of operation results.
    """
    excel_results = copy_excel_files(generated_files)
    image_results = copy_images(renamed_images_dir)
    
    return {
        'excel_copies': excel_results,
        'image_copies': image_results
    }