#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive Web Panel - Fixed Version 2.1
"""

from flask import Flask, jsonify, send_file, request, render_template
import subprocess
import threading
import os
import sys
from pathlib import Path
from datetime import datetime
import time
import re
import queue

ASSET_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "assets" / "templates" / "product_extraction"
LEGACY_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
TEMPLATE_DIR = ASSET_TEMPLATE_DIR if ASSET_TEMPLATE_DIR.exists() else LEGACY_TEMPLATE_DIR

app = Flask(__name__, template_folder=str(TEMPLATE_DIR))

# Thread-safe state
state_lock = threading.Lock()

scraper_state = {
    'running': False,
    'log': [],
    'start_time': None,
    'current_task': None,
    'current_task_display': None,
    'progress': {
        'current': 0,
        'total': 0,
        'percentage': 0,
        'current_item': '',
        'eta': ''
    },
    'waiting_for_input': False,
    'last_question': '',
    'process': None,
    'input_queue': queue.Queue()
}


def extract_progress(line):
    """Extract progress information from output line"""
    progress_info = {}
    
    match = re.search(r'Processing.*?(\d+)/(\d+)', line, re.IGNORECASE)
    if match:
        progress_info['current'] = int(match.group(1))
        progress_info['total'] = int(match.group(2))
        progress_info['percentage'] = int((progress_info['current'] / progress_info['total']) * 100)
    
    match = re.search(r'Processed\s+(\d+)\s+products', line, re.IGNORECASE)
    if match:
        progress_info['current'] = int(match.group(1))
        progress_info['current_item'] = f"Processed {match.group(1)} products"
    
    match = re.search(r'Page\s+(\d+)\s+(?:of|/)\s+(\d+)', line, re.IGNORECASE)
    if match:
        progress_info['current'] = int(match.group(1))
        progress_info['total'] = int(match.group(2))
        progress_info['percentage'] = int((progress_info['current'] / progress_info['total']) * 100)
        progress_info['current_item'] = f"Page {match.group(1)}/{match.group(2)}"
    
    match = re.search(r'Found\s+(\d+)\s+products', line, re.IGNORECASE)
    if match:
        progress_info['current_item'] = f"Found {match.group(1)} products"
    
    match = re.search(r'Extracted\s+(\d+)\s+(?:unique\s+)?products', line, re.IGNORECASE)
    if match:
        progress_info['current_item'] = f"Extracted {match.group(1)} products"
    
    match = re.search(r'Product[:\s]+(.+)', line, re.IGNORECASE)
    if match:
        progress_info['current_item'] = match.group(1).strip()
    
    match = re.search(r'(\d+)%', line)
    if match:
        progress_info['percentage'] = int(match.group(1))
    
    match = re.search(r'https?://[^\s]+', line)
    if match:
        url = match.group(0)
        if '/product/' in url or '/item/' in url:
            progress_info['current_item'] = f"Processing: {url.split('/')[-1][:50]}"
    
    return progress_info


def is_question(line):
    """Check if line is asking for user input - Version 2.1"""
    line_clean = line.strip()
    line_lower = line_clean.lower()
    
    # Definite question patterns
    patterns = [
        r'resume\s+from.*\(y/n\)',
        r'continue\s+from.*\(y/n\)',
        r'\(y/n\)\s*:',
        r'\(y/n\)\s*$',
        r'yes/no\s*:',
        r'\?\s*\(y/n\)',
        r'enter\s+your\s+choice',
        r'please\s+enter',
        r'type\s+y\s+or\s+n',
        r'y\s*/\s*n',
    ]
    
    for pattern in patterns:
        if re.search(pattern, line_lower):
            return True
    
    # Check if has both ? and (y/n)
    if '?' in line_clean:
        if '(y/n)' in line_lower or 'yes/no' in line_lower or 'y/n' in line_lower:
            return True
    
    # Check emoji questions
    if line_clean.startswith('?') or '?' in line_clean[:10]:
        if '(y/n)' in line_lower or 'yes/no' in line_lower:
            return True
    
    # False positives
    false_words = [
        'waiting', 'processing', 'loading', 'extracted',
        'saved', 'found', 'error', 'warning', 'opening',
        'closing', 'installing', 'updating', 'completed',
        'scrolling', 'comparing', 'reading', 'writing',
        'browser', 'driver', 'chrome', 'selenium',
        'page', 'element', 'click', 'scroll', 'timeout',
        'success', 'failed', 'done', 'finished', 'ready',
        'products...', 'file', 'sample', 'report'
    ]
    
    for word in false_words:
        if word in line_lower:
            return False
    
    return False


def run_command(command):
    """Run command and capture output"""
    with state_lock:
        scraper_state['running'] = True
        scraper_state['log'] = []
        scraper_state['start_time'] = datetime.now()
        scraper_state['waiting_for_input'] = False
        scraper_state['progress'] = {
            'current': 0,
            'total': 0,
            'percentage': 0,
            'current_item': '',
            'eta': ''
        }
    
    try:
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONLEGACYWINDOWSSTDIO'] = 'utf-8'
        
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            bufsize=0,
            universal_newlines=False,
            env=env
        )
        
        with state_lock:
            scraper_state['process'] = process
        
        # Buffer to accumulate incomplete lines
        line_buffer = ""
        
        while True:
            # Read with small timeout to catch partial lines
            try:
                chunk = process.stdout.read(1)
                if not chunk:
                    break
                
                char = chunk.decode('utf-8', errors='replace')
                line_buffer += char
                
                # Check if we have a complete line OR if it looks like a question prompt
                if char == '\n' or (': ' in line_buffer and len(line_buffer) > 20):
                    line = line_buffer.rstrip()
                    line_buffer = ""
                    
                    if line:
                        # DEBUG: Log all lines
                        with state_lock:
                            timestamp = datetime.now().strftime('%H:%M:%S')
                            scraper_state['log'].append(f"{timestamp} | {line}")
                        
                        if is_question(line):
                            # DEBUG: Log detection
                            with state_lock:
                                scraper_state['log'].append(f">>> QUESTION DETECTED: {line}")
                                scraper_state['waiting_for_input'] = True
                                scraper_state['last_question'] = line
                            
                            try:
                                user_input = scraper_state['input_queue'].get(timeout=300)
                                process.stdin.write(f"{user_input}\n".encode('utf-8'))
                                process.stdin.flush()
                                
                                with state_lock:
                                    scraper_state['waiting_for_input'] = False
                                    scraper_state['log'].append(f"> User input: {user_input}")
                            except queue.Empty:
                                process.stdin.write(b"n\n")
                                process.stdin.flush()
                                with state_lock:
                                    scraper_state['waiting_for_input'] = False
                                    scraper_state['log'].append("> Timeout: defaulted to 'n'")
                        
                        progress_info = extract_progress(line)
                        
                        with state_lock:
                            if progress_info:
                                scraper_state['progress'].update(progress_info)
                            
                            if len(scraper_state['log']) > 500:
                                scraper_state['log'] = scraper_state['log'][-500:]
            
            except:
                break
        
        process.wait()
        
    except Exception as e:
        with state_lock:
            scraper_state['log'].append(f"Error: {str(e)}")
    
    finally:
        with state_lock:
            scraper_state['running'] = False
            scraper_state['current_task'] = None
            scraper_state['waiting_for_input'] = False
            scraper_state['process'] = None


@app.route('/')
def index():
    return render_template('index_interactive.html')


@app.route('/api/status')
def get_status():
    """Get current status"""
    with state_lock:
        return jsonify({
            'running': scraper_state['running'],
            'waiting_for_input': scraper_state['waiting_for_input'],
            'last_question': scraper_state['last_question'],
            'task': scraper_state['current_task'],
            'task_display': scraper_state['current_task_display'],
            'start_time': scraper_state['start_time'].isoformat() if scraper_state['start_time'] else None,
            'log': scraper_state['log'][-100:],
            'progress': scraper_state['progress']
        })


@app.route('/api/input', methods=['POST'])
def send_input():
    """Send user input to process"""
    data = request.json
    user_input = data.get('input', '')
    
    with state_lock:
        if not scraper_state['waiting_for_input']:
            return jsonify({'success': False, 'error': 'Not waiting for input'})
        
        scraper_state['input_queue'].put(user_input)
    
    return jsonify({'success': True})


@app.route('/api/run/<task>')
def run_task(task):
    """Run a specific task"""
    with state_lock:
        if scraper_state['running']:
            return jsonify({'success': False, 'error': 'Another task is running'})
    
    base_commands = {
        'scrape-links': (['python', 'main.py', 'scrape-links'], 'Scrape Links'),
        'scrape-specs': (['python', 'main.py', 'scrape-specs'], 'Scrape Specs'),
        'track': (['python', 'main.py', 'track'], 'Track Prices'),
        'dashboard': (['python', 'main.py', 'dashboard'], 'Generate Dashboard'),
        'full': (['python', 'main.py', 'full'], 'Full Pipeline'),
        'test': (['python', 'main.py', 'test'], 'Run Tests')
    }
    
    if task not in base_commands:
        return jsonify({'success': False, 'error': 'Invalid task'})
    
    command, display_name = base_commands[task]
    
    with state_lock:
        scraper_state['current_task'] = task
        scraper_state['current_task_display'] = display_name
    
    thread = threading.Thread(target=run_command, args=(command,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'task': task, 'display': display_name})


@app.route('/api/files')
def get_files():
    """Get list of output files"""
    files = []
    
    file_patterns = {
        'extracted_products.xlsx': 'Product Links',
        'product_details_complete.xlsx': 'Product Details',
    }
    
    for filename, description in file_patterns.items():
        filepath = Path(filename)
        if filepath.exists():
            stat = filepath.stat()
            files.append({
                'name': filename,
                'path': str(filepath),  # Convert to string
                'description': description,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })
    
    reports_dir = Path('reports')
    if reports_dir.exists():
        report_files = [
            ('product_tracking_LATEST.xlsx', 'Latest Tracking'),
            ('price_changes.xlsx', 'Price Changes')
        ]
        
        for filename, description in report_files:
            filepath = reports_dir / filename
            if filepath.exists():
                stat = filepath.stat()
                files.append({
                    'name': filename,
                    'path': str(filepath).replace('\\', '/'),  # Use forward slashes
                    'description': description,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
        
        for html_file in reports_dir.glob('product_tracking_report_*.html'):
            stat = html_file.stat()
            files.append({
                'name': html_file.name,
                'path': str(html_file).replace('\\', '/'),  # Use forward slashes
                'description': 'HTML Report',
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })
    
    files.sort(key=lambda x: x['modified'], reverse=True)
    
    return jsonify(files)


@app.route('/api/download/<path:filepath>')
def download_file(filepath):
    """Download a file"""
    try:
        # Ensure the path exists
        file_path = Path(filepath)
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(str(file_path.absolute()), as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/view/<path:filepath>')
def view_file(filepath):
    """View a file in browser"""
    try:
        # Ensure the path exists
        file_path = Path(filepath)
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        # For HTML files, send as inline
        if file_path.suffix.lower() == '.html':
            return send_file(str(file_path.absolute()), mimetype='text/html')
        
        # For other files, redirect to download
        return send_file(str(file_path.absolute()), as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*70)
    print("  Product Scraper - Interactive Web Panel v2.1")
    print("  http://localhost:5000")
    print("  ")
    print("  Changes v2.1:")
    print("  - Fixed question detection")
    print("  - Support for spec_scraper questions")
    print("  - No false positives")
    print("  ")
    print("  Interactive Mode:")
    print("  - Answer questions in browser")
    print("  - Quick buttons: Yes/No")
    print("  - Timeout: 5 minutes (default: No)")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
