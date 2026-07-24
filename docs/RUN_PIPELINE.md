Run Pipeline — wrappers & automation
=================================

Overview
--------
Two wrapper scripts are provided to run the automatic pipeline with sensible defaults:
- run_pipeline.ps1 — PowerShell wrapper (Windows)
- run_pipeline.sh — Bash wrapper (Linux, macOS, WSL)

Both set these environment variables before invoking the pipeline:
- AUTO_RESUME=1 — automatically resume a previous incomplete run (skip prompt)
- PROCESS_TIMEOUT — seconds to allow for long subprocesses (images), default 3600
- PROCESS_SUBPROCESS_RETRY — number of subprocess retry attempts, default 1

Which to use: Bash vs PowerShell
--------------------------------
- PowerShell (run_pipeline.ps1): native Windows shell. Use this on Windows machines or Windows Server.
- Bash (run_pipeline.sh): classic Unix shell. Use this on Linux, macOS, or WSL on Windows.

They do the same thing: set the environment variables and run python product_extraction/main.py auto.
Choose the script that matches the shell you normally use.

Quick examples
--------------
1) Default run (recommended for unattended runs)

PowerShell:

  .\run_pipeline.ps1

Bash:

  ./run_pipeline.sh

2) Custom timeout and retries

PowerShell (2 hours timeout, 2 retries):

  .\run_pipeline.ps1 -TimeoutSeconds 7200 -SubprocessRetries 2

Bash:

  ./run_pipeline.sh 7200 2

3) Prompt instead of auto-resume

PowerShell:

  .\run_pipeline.ps1 -NoResume

Bash:

  ./run_pipeline.sh 3600 1 --no-resume

Scheduled runs (examples)
-------------------------
1) Windows Task Scheduler (simple)
- Create a task that runs PowerShell with the action:
  Program/script: powershell
  Arguments: -NoProfile -ExecutionPolicy Bypass -File "C:\path\to\repo\run_pipeline.ps1"

2) GitHub Actions workflow (example)

Add a workflow file .github/workflows/run_pipeline.yml:

```yaml
name: Run Pipeline
on:
  workflow_dispatch:
  schedule:
    - cron: '0 2 * * *' # daily at 02:00 UTC

jobs:
  run:
    runs-on: ubuntu-latest
    env:
      AUTO_RESUME: '1'
      PROCESS_TIMEOUT: '3600'
      PROCESS_SUBPROCESS_RETRY: '1'
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install requirements
        run: pip install -r requirements.txt
      - name: Run pipeline
        run: ./run_pipeline.sh
```

Pipeline Modes (auto / full / incremental)
-----------------------------------------

The `auto` command accepts a `--mode` argument that controls how the pipeline behaves:

| Mode | Behavior | Use Case |
|------|----------|----------|
| `auto` (default) | **First run**: full (no previous catalog). **Subsequent runs**: incremental — compares new scan against last WooCommerce CSV, processes only new + changed products. | Daily/weekly automated runs. Recommended default. |
| `full` | Always scrapes ALL products, downloads ALL images, processes ALL, emits single full WooCommerce CSV. Ignores previous catalog. | Initial migration, major site redesign, or forced full refresh. |
| `incremental` | Forces change-detection even if it would otherwise fall back to full. Fails if no previous WooCommerce catalog exists. | When you explicitly want only delta changes (e.g., after fixing a scrape issue). |

### What happens in each mode

**Full mode** (`--mode full` or first run with `--mode auto`):
1. Link Scraper → all URLs from `archive_urls.xlsx`
2. Spec Scraper → all product details
3. Standardizer → full `product.csv`
4. **Change Detection skipped**
5. Image Processing → download + process ALL product images
6. Import Builder → single `woocommerce_import_<timestamp>.csv` (all products)

**Incremental mode** (`--mode incremental` or subsequent runs with `--mode auto`):
1. Link Scraper → all URLs (fresh scan)
2. Spec Scraper → all product details (fresh scan)
3. Standardizer → full `product.csv` (fresh)
4. **Change Detection runs** (`compare_scans.py`):
   - Compares new `product.csv` vs last `woocommerce_import_*.csv`
   - Produces manifests: `new_products_list.csv`, `updated_products_list.csv`, `image_subset_list.csv`
   - Partitions SKUs: `new_skus`, `price_changed_skus`, `color_added_skus`, `image_subset_skus = new ∪ color_added`
5. Image Processing:
   - If `image_subset_skus` empty → **skipped entirely**
   - If only price changes → download/process **skipped** (reuse existing images)
   - If new products or new colors → download/process **only `image_subset_skus`**
6. Import Builder:
   - Always emits full `woocommerce_import_<timestamp>.csv` (all products)
   - **Additionally emits split CSVs** when manifests exist:
     - `woocommerce_new_<timestamp>.csv` — only new products
     - `woocommerce_update_<timestamp>.csv` — only changed products (price + color)
   - Coverage gate scoped to `IMPORT_EXPECTED_SKUS` (the incremental subset), not full catalog

### Unchanged products in incremental mode
- **Re-scraped**: Yes (Link + Spec scrapers always run fresh)
- **Re-standardized**: Yes (Standardizer always runs fresh)
- **Images re-downloaded**: **No** — only new/color-changed products fetch images
- **Images re-processed**: **No** — processor restricted to `IMG_PROCESS_SKUS` subset
- **In WooCommerce import**: Present in **full CSV** but **NOT in new/update split CSVs**
  - Import the split CSVs for incremental WooCommerce updates
  - Import the full CSV only for full catalog replacement

### Running with specific mode

**PowerShell wrapper** (edit `run_pipeline.ps1` or call Python directly):
```powershell
# Auto (default)
python product_extraction/main.py auto --mode auto

# Full
python product_extraction/main.py auto --mode full

# Incremental (force)
python product_extraction/main.py auto --mode incremental
```

**Bash wrapper** (edit `run_pipeline.sh` or call Python directly):
```bash
# Auto (default)
python product_extraction/main.py auto --mode auto

# Full
python product_extraction/main.py auto --mode full

# Incremental (force)
python product_extraction/main.py auto --mode incremental
```

**Interactive menu** (`run_pipeline.bat`):
- Option 1: Run Automatic Pipeline (auto) — uses current global mode setting
- Option 2: Run Full Pipeline (full)
- Option 3: Run Incremental Pipeline (incremental)
- Press **S** in menu to change global mode setting

Notes & tips
------------
- For large catalogs increase PROCESS_TIMEOUT (3600–7200 seconds) so the image-processing subprocess has time to finish.
- Use IMG_MANIFEST to process only new products when possible — the tracker produces new_products_list.csv in runtime/reports dated folders.
- If you see console encoding errors on Windows, either enable UTF-8 (chcp 65001) or set PYTHONUTF8=1 in the environment.

If you want, I can add the GitHub Actions workflow file and a sample scheduled Task XML for Windows — tell me and I will commit them.
