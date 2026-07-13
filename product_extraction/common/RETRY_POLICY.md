Retry Policy and Configuration
==============================

Overview
--------
This module centralises retry/backoff behaviour for network operations used
across the pipeline (page loads, HTTP downloads, API calls).

Configuration (env)
--------------------
- RETRY_MAX_ATTEMPTS (int) — default 4
- RETRY_BASE_DELAY (float seconds) — default 2.0
- RETRY_CAP (float seconds) — default 60.0
- RETRY_JITTER (float fraction) — default 0.3

How to tune
-----------
- Image downloads: network operations are cheap; use higher attempts and
  shorter base_delay (e.g. RETRY_MAX_ATTEMPTS=6, RETRY_BASE_DELAY=1.0)
- Selenium page loads: more expensive; reduce attempts but increase backoff
  (e.g. RETRY_MAX_ATTEMPTS=3, RETRY_BASE_DELAY=3.0)
- CI / test environment: lower values so tests fail fast (e.g. RETRY_MAX_ATTEMPTS=2)

Notes
-----
- The implementation prefers class-based exception classification when
  common libraries (requests, urllib3, selenium) are available. It falls
  back to name-based matching otherwise.
- Callers may still explicitly raise PermanentError when an error is known
  to be unrecoverable.

Examples
--------
Run image downloader with aggressive retries:

  RETRY_MAX_ATTEMPTS=6 RETRY_BASE_DELAY=1.0 python image_processing/Image_Downloader.py
