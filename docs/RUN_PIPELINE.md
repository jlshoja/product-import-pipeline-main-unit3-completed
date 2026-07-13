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

Notes & tips
------------
- For large catalogs increase PROCESS_TIMEOUT (3600–7200 seconds) so the image-processing subprocess has time to finish.
- Use IMG_MANIFEST to process only new products when possible — the tracker produces new_products_list.csv in runtime/reports dated folders.
- If you see console encoding errors on Windows, either enable UTF-8 (chcp 65001) or set PYTHONUTF8=1 in the environment.

If you want, I can add the GitHub Actions workflow file and a sample scheduled Task XML for Windows — tell me and I will commit them.
