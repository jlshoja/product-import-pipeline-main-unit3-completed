#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Manifest Generator - Creates machine-readable import manifest JSON
for the WooCommerce Import Project.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import from this module's directory
import sys
_this_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(_this_dir))

from paths import IMPORT_PROJECT_EXCEL_DIR, IMPORT_BUILDER_UPLOADS_DIR


def build_manifest(
    mode: str,
    generated_files: Dict[str, str],
    renamed_images_dir: Path,
    copy_results: Dict[str, List[Dict[str, Any]]],
    sku_counts: Optional[Dict[str, int]] = None,
    row_counts: Optional[Dict[str, int]] = None
) -> Dict[str, Any]:
    """
    Build the import manifest JSON structure.
    
    Args:
        mode: 'full' or 'incremental'
        generated_files: Dict with keys 'full', 'new', 'update' -> source paths
        renamed_images_dir: Path to the dated renamed_images folder
        copy_results: Output from import_copier.copy_all_to_import_project()
        sku_counts: Optional dict with SKU counts per file type
        row_counts: Optional dict with row counts per file type
    
    Returns:
        Manifest dict ready for JSON serialization.
    """
    files_list = []
    
    # Full catalog file (always present)
    if 'full' in generated_files:
        src = Path(generated_files['full'])
        files_list.append({
            'file_name': src.name,
            'file_type': 'xlsx',
            'purpose': 'full_catalog',
            'update_scope': 'all_fields',
            'import_priority': 1,
            'generated_date': datetime.now().strftime('%Y-%m-%d'),
            'sku_count': sku_counts.get('full', 0) if sku_counts else 0,
            'row_count': row_counts.get('full', 0) if row_counts else 0
        })
    
    # New products file (incremental only)
    if 'new' in generated_files:
        src = Path(generated_files['new'])
        files_list.append({
            'file_name': src.name,
            'file_type': 'xlsx',
            'purpose': 'new_products',
            'update_scope': 'create_only',
            'import_priority': 2,
            'generated_date': datetime.now().strftime('%Y-%m-%d'),
            'sku_count': sku_counts.get('new', 0) if sku_counts else 0,
            'row_count': row_counts.get('new', 0) if row_counts else 0
        })
    
    # Updated products file (incremental only)
    if 'update' in generated_files:
        src = Path(generated_files['update'])
        files_list.append({
            'file_name': src.name,
            'file_type': 'xlsx',
            'purpose': 'updated_products',
            'update_scope': 'price|color_variants|stock',
            'import_priority': 3,
            'generated_date': datetime.now().strftime('%Y-%m-%d'),
            'sku_count': sku_counts.get('update', 0) if sku_counts else 0,
            'row_count': row_counts.get('update', 0) if row_counts else 0
        })
    
    # Images info
    images_info = {
        'source_folder': str(renamed_images_dir),
        'destination_folder': str(IMPORT_PROJECT_EXCEL_DIR.parent / 'images'),
        'file_count': 0,
        'copied': False
    }
    
    # Calculate images copied from copy results
    for result in copy_results.get('image_copies', []):
        if result.get('summary'):
            images_info['file_count'] = result.get('images_copied', 0)
            images_info['copied'] = True
            break
    
    # Build copy log
    copy_log = []
    for result in copy_results.get('excel_copies', []):
        copy_log.append({
            'source': result['source'],
            'destination': result['destination'],
            'timestamp': result['timestamp'],
            'success': result['success'],
            'error': result.get('error')
        })
    for result in copy_results.get('image_copies', []):
        if result.get('summary'):
            continue
        copy_log.append({
            'source': result['source'],
            'destination': result['destination'],
            'timestamp': result['timestamp'],
            'success': result['success'],
            'error': result.get('error')
        })
    
    manifest = {
        'generated_at': datetime.now().isoformat(),
        'mode': mode,
        'files': files_list,
        'images': images_info,
        'copy_log': copy_log
    }
    
    return manifest


def save_manifest(manifest: Dict[str, Any], output_dir: Path) -> Path:
    """
    Save manifest to JSON file in the import project input folder.
    
    Args:
        manifest: Manifest dict from build_manifest()
        output_dir: Target directory (usually IMPORT_PROJECT_EXCEL_DIR)
    
    Returns:
        Path to saved manifest file.
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    manifest_path = output_dir / f"import_manifest_{timestamp}.json"
    
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    return manifest_path


def save_manifest_local(manifest: Dict[str, Any], project_uploads_dir: Path) -> Path:
    """
    Save a local copy of manifest in project's uploads folder for audit trail.
    
    Args:
        manifest: Manifest dict from build_manifest()
        project_uploads_dir: IMPORT_BUILDER_UPLOADS_DIR / YYYYMMDD
    
    Returns:
        Path to saved manifest file.
    """
    date_str = datetime.now().strftime('%Y%m%d')
    local_dir = project_uploads_dir / date_str
    local_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    manifest_path = local_dir / f"import_manifest_{timestamp}.json"
    
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    return manifest_path


def generate_import_manifest(
    generated_files: Dict[str, str],
    renamed_images_dir: Path,
    import_excel_dir: Path,
    import_images_dir: Path,
    copy_log: List[Dict[str, Any]],
    mode: str,
    df_output=None
) -> Path:
    """
    High-level function to generate and save import manifest.
    
    Args:
        generated_files: Dict from woocommerce_generator_v12 (full, new, update)
        renamed_images_dir: Path to dated renamed_images folder
        import_excel_dir: Target Excel directory
        import_images_dir: Target images directory
        copy_log: List of copy operation results
        mode: 'full' or 'incremental'
        df_output: Optional DataFrame to count SKUs/rows
    
    Returns:
        Path to saved manifest in import project input folder.
    """
    # Calculate SKU and row counts from df_output if provided
    sku_counts = {}
    row_counts = {}
    
    if df_output is not None and 'sku' in df_output.columns:
        # Count unique SKUs per file type
        for ftype, fpath in generated_files.items():
            if ftype == 'full':
                sku_counts[ftype] = df_output['sku'].nunique()
                row_counts[ftype] = len(df_output)
            elif ftype == 'new':
                # For new, we'd need the actual new SKUs - approximate with new count
                sku_counts[ftype] = df_output['sku'].nunique()
                row_counts[ftype] = len(df_output)
            elif ftype == 'update':
                sku_counts[ftype] = df_output['sku'].nunique()
                row_counts[ftype] = len(df_output)
    
    # Build copy_results structure expected by build_manifest
    copy_results = {
        'excel_copies': [r for r in copy_log if r.get('file_type') != 'image'],
        'image_copies': [r for r in copy_log if r.get('file_type') == 'image']
    }
    
    manifest = build_manifest(
        mode=mode,
        generated_files=generated_files,
        renamed_images_dir=renamed_images_dir,
        copy_results=copy_results,
        sku_counts=sku_counts,
        row_counts=row_counts
    )
    
    # Save to import project input folder
    manifest_path = save_manifest(manifest, import_excel_dir)
    
    # Also save local copy for audit
    save_manifest_local(manifest, IMPORT_BUILDER_UPLOADS_DIR)
    
    return manifest_path