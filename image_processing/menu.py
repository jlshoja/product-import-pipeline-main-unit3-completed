#!/usr/bin/env python3
"""
Image Processing Pipeline - Interactive Menu
"""

import os
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from product_extraction.common.progress_utils import load_json_state


ROOT_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# Default Settings — edit here
# ============================================================
EXCEL_FILE        = "extracted_products.xlsx"
DOWNLOADED_FOLDER = "./downloaded_images"
OUTPUT_FOLDER     = "./output"
USE_SELENIUM      = True
MAX_RETRIES       = 3
GALLERY_SIZE_KB   = 50
MAIN_SIZE_KB      = 100
REMOVE_BG         = False
BG_COLOR          = "white"   # white / black / transparent
DETECT_COLOR      = True
# ============================================================

DEFAULT_DOWNLOAD_STATE = {
    "completed_pages": [],
    "failed_images": {},
    "no_image_pages": [],
    "last_page": 0,
    "session_folder": None,
}


CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def print_header():
    print(f"{BOLD}{CYAN}")
    print("=" * 55)
    print("   Image Processing Pipeline")
    print("=" * 55)
    print(f"{RESET}")


def print_settings():
    print(f"{YELLOW}Current Settings:{RESET}")
    print(f"   Excel file        : {EXCEL_FILE}")
    print(f"   Download folder   : {DOWNLOADED_FOLDER}")
    print(f"   Output folder     : {OUTPUT_FOLDER}")
    print(f"   Selenium          : {'Yes' if USE_SELENIUM else 'No'}")
    print(f"   Max retries       : {MAX_RETRIES}")
    print(f"   Main image size   : {MAIN_SIZE_KB} KB")
    print(f"   Gallery image size: {GALLERY_SIZE_KB} KB")
    print(f"   Color detection   : {'Yes' if DETECT_COLOR else 'No'}")
    print(f"   Remove background : {'Yes -> ' + BG_COLOR if REMOVE_BG else 'No'}")
    print()


def print_menu():
    print(f"{BOLD}Select an option:{RESET}")
    print(f"  {GREEN}1{RESET}  --  Download images from websites")
    print(f"  {GREEN}2{RESET}  --  Process and compress images")
    print(f"  {GREEN}3{RESET}  --  Compare folder sizes")
    print(f"  {GREEN}4{RESET}  --  Run all 3 steps in order")
    print(f"  {YELLOW}5{RESET}  --  Change settings")
    print(f"  {RED}0{RESET}  --  Exit")
    print()


def run(cmd, label, env=None):
    print(f"\n{BOLD}{GREEN}{'='*55}{RESET}")
    print(f"{BOLD}>>  {label}{RESET}")
    print(f"{BOLD}{GREEN}{'='*55}{RESET}\n")
    result = subprocess.run(cmd, env=env)
    if result.returncode != 0:
        print(f"\n{RED}ERROR: {label} failed.{RESET}")
        return False
    print(f"\n{GREEN}DONE: {label}{RESET}")
    return True


def get_download_state():
    """Read previous session state from download_state.json"""
    canonical_state_file = ROOT_DIR / "runtime" / "state" / "download_state.json"
    if not canonical_state_file.exists():
        return None
    try:
        state = load_json_state(canonical_state_file, DEFAULT_DOWNLOAD_STATE)
        completed       = len(state.get("completed_pages", []))
        no_image        = len(state.get("no_image_pages", []))
        failed_products = len(state.get("failed_images", {}))
        failed_images   = sum(len(v) for v in state.get("failed_images", {}).values())
        if completed == 0 and no_image == 0 and failed_products == 0:
            return None
        return {
            "completed":       completed,
            "no_image":        no_image,
            "failed_products": failed_products,
            "failed_images":   failed_images,
            "state_file":      canonical_state_file,
        }
    except Exception:
        return None


def step1_download():
    if not os.path.exists(EXCEL_FILE):
        print(f"\n{RED}ERROR: Excel file not found: {EXCEL_FILE}{RESET}")
        print(f"   Place the file in this folder and try again.\n")
        return False

    prev = get_download_state()
    run_mode    = "full"
    resume_mode = "fresh"

    if prev:
        clear()
        print_header()
        print(f"{YELLOW}Previous download session found:{RESET}")
        print(f"   Completed products : {prev['completed']}")
        print(f"   No images found    : {prev['no_image']}")
        print(f"   Incomplete products: {prev['failed_products']}  ({prev['failed_images']} images failed)")
        print()
        print(f"{BOLD}Select an option:{RESET}")
        print(f"  {GREEN}1{RESET}  --  Resume from where it left off")

        has_incomplete = prev["failed_products"] > 0 or prev["no_image"] > 0
        if has_incomplete:
            print(f"  {GREEN}2{RESET}  --  Retry incomplete & no-image products only")
            print(f"  {GREEN}3{RESET}  --  Download incomplete & no-image products (re-fetch pages)")

        print(f"  {GREEN}4{RESET}  --  Start over (delete previous state)")
        print(f"  {RED}0{RESET}  --  Back to main menu")
        print()

        valid = ["0", "1", "4"] + (["2", "3"] if has_incomplete else [])
        while True:
            sub = input(f"{BOLD}Enter your choice: {RESET}").strip()
            if sub not in valid:
                print(f"{RED}Invalid choice.{RESET}")
                continue
            if sub == "0":
                return False
            elif sub == "1":
                run_mode    = "resume"
                resume_mode = "resume"
            elif sub == "2":
                run_mode    = "retry_only"
                resume_mode = "resume"
            elif sub == "3":
                run_mode    = "incomplete_only"
                resume_mode = "resume"
            elif sub == "4":
                run_mode    = "full"
                resume_mode = "fresh"
            break

    env = os.environ.copy()
    env["IMG_EXCEL"]    = EXCEL_FILE
    env["IMG_OUTPUT"]   = DOWNLOADED_FOLDER
    env["IMG_SELENIUM"] = "1" if USE_SELENIUM else "0"
    env["IMG_RETRIES"]  = str(MAX_RETRIES)
    env["IMG_RESUME"]   = resume_mode
    env["IMG_MODE"]     = run_mode

    labels = {
        "full":             "Step 1: Download Images (full)",
        "resume":           "Step 1: Download Images (resume)",
        "retry_only":       "Step 1: Retry Incomplete & No-Image Products",
        "incomplete_only":  "Step 1: Download Incomplete & No-Image Products",
    }
    label = labels.get(run_mode, "Step 1: Download Images")

    return run([sys.executable, "Image_Downloader.py"], label, env=env)


def step2_process():
    if not os.path.exists(DOWNLOADED_FOLDER):
        print(f"\n{RED}ERROR: Download folder not found: {DOWNLOADED_FOLDER}{RESET}")
        print(f"   Run Step 1 first.\n")
        return False

    cmd = [
        sys.executable, "unified_image_processor.py",
        "-i", DOWNLOADED_FOLDER,
        "-o", OUTPUT_FOLDER,
        "-s", str(GALLERY_SIZE_KB),
        "-m", str(MAIN_SIZE_KB),
    ]
    if REMOVE_BG:
        cmd += ["--remove-bg", "--bg-color", BG_COLOR]
    if not DETECT_COLOR:
        cmd.append("--no-color")

    return run(cmd, "Step 2: Process and Compress Images")


def step3_compare():
    missing = []
    if not os.path.exists(DOWNLOADED_FOLDER):
        missing.append(DOWNLOADED_FOLDER)
    if not os.path.exists(OUTPUT_FOLDER):
        missing.append(OUTPUT_FOLDER)

    if missing:
        print(f"\n{RED}ERROR: Folders not found:{RESET}")
        for m in missing:
            print(f"   - {m}")
        print()
        return False

    return run(
        [sys.executable, "compare_sizes.py", DOWNLOADED_FOLDER, OUTPUT_FOLDER],
        "Step 3: Compare File Sizes"
    )


def settings_menu():
    global EXCEL_FILE, DOWNLOADED_FOLDER, OUTPUT_FOLDER
    global USE_SELENIUM, MAX_RETRIES, GALLERY_SIZE_KB
    global MAIN_SIZE_KB, REMOVE_BG, BG_COLOR, DETECT_COLOR

    clear()
    print_header()
    print(f"{BOLD}Change Settings{RESET}\n")
    print("  (Press Enter to keep current value)\n")

    def ask(prompt, current, cast=str):
        val = input(f"  {prompt} [{current}]: ").strip()
        if val == "":
            return current
        try:
            return cast(val)
        except ValueError:
            print(f"  {RED}Invalid value -- keeping previous{RESET}")
            return current

    def ask_bool(prompt, current):
        val = input(f"  {prompt} [{'y' if current else 'n'}]: ").strip().lower()
        if val == "":
            return current
        return val in ("y", "yes", "1")

    EXCEL_FILE        = ask("Excel input file", EXCEL_FILE)
    DOWNLOADED_FOLDER = ask("Download folder", DOWNLOADED_FOLDER)
    OUTPUT_FOLDER     = ask("Output folder", OUTPUT_FOLDER)
    USE_SELENIUM      = ask_bool("Use Selenium? (y/n)", USE_SELENIUM)
    MAX_RETRIES       = ask("Max retries", MAX_RETRIES, int)
    MAIN_SIZE_KB      = ask("Main image max size (KB)", MAIN_SIZE_KB, int)
    GALLERY_SIZE_KB   = ask("Gallery image max size (KB)", GALLERY_SIZE_KB, int)
    DETECT_COLOR      = ask_bool("Color detection in filename? (y/n)", DETECT_COLOR)
    REMOVE_BG         = ask_bool("Remove background from main images? (y/n)", REMOVE_BG)
    if REMOVE_BG:
        BG_COLOR = ask("Background color (white/black/transparent)", BG_COLOR)

    print(f"\n{GREEN}Settings saved.{RESET}\n")
    input("  Press Enter to go back to menu... ")


def main():
    while True:
        clear()
        print_header()
        print_settings()
        print_menu()

        choice = input(f"{BOLD}Enter your choice: {RESET}").strip()

        if choice == "0":
            print(f"\n{CYAN}Goodbye!\n{RESET}")
            sys.exit(0)

        elif choice == "1":
            step1_download()
            input("\n  Press Enter to go back to menu... ")

        elif choice == "2":
            step2_process()
            input("\n  Press Enter to go back to menu... ")

        elif choice == "3":
            step3_compare()
            input("\n  Press Enter to go back to menu... ")

        elif choice == "4":
            ok = step1_download()
            if ok:
                ok = step2_process()
            if ok:
                step3_compare()
            input("\n  Press Enter to go back to menu... ")

        elif choice == "5":
            settings_menu()

        else:
            print(f"\n{RED}Invalid choice. Please enter 0 to 5.{RESET}")
            input("  Press Enter to continue... ")


if __name__ == "__main__":
    main()
