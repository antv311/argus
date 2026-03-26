# ARGUS - Project Context
> Read this file at the start of every Claude Code session to get up to speed.

---

## What Is ARGUS?

ARGUS is a thematic, supply-chain-aware stock and ETF screener built on Python 3.14.2. It extends the open source [asafravid/sss](https://github.com/asafravid/sss) fundamental scoring engine with geopolitical supply chain signals, institutional flow data (Quiver Quant, Unusual Whales), and congressional trading intelligence.

Named after the hundred-eyed giant of Greek mythology — it watches everything simultaneously.

**Owner:** Tony (antv311)  
**Repo:** https://github.com/antv311/argus  
**Stack:** Python 3.14.2, SQLite, yfinance, yahooquery, pandas, matplotlib, fpdf2

---

## Architecture (Current State)

```
Layer 1 — Data Sources
  yfinance / yahooquery     → price, fundamentals, financials
  Quiver Quant API          → congressional trades, lobbying, gov contracts  [PLANNED]
  Unusual Whales API        → dark pool, options flow, institutional flow     [PLANNED]
  worldmonitor-osint        → geopolitical/supply chain disruption signals    [PLANNED]

Layer 2 — Database (argus_db.py)
  SQLite via argus.db       → stocks, watchlists, indices, scan_results,
                              stock_financials, index_refresh_log

Layer 3 — Scoring Engine (sss.py)
  Core SSS equation         → EV/R, PE, EV/EBITDA, profit margin, PEG,
                              debt/equity, CFO ratio, Altman Z-score
  Multi-dimensional scan    → weighted scoring across time periods

Layer 4 — Output
  CSV + PDF reports         → Results/ directory per scan run
  Flask dashboard           → [PLANNED]
  Email alerts              → Mailer.py (existing)
```

---

## Project Structure

```
argus/
├── src/
│   ├── sss.py                  ← main scoring engine (3467 lines, actively refactoring)
│   ├── sss_run.py              ← scan runner / entry point
│   ├── sss_config.py           ← ALL config + scoring constants (recently moved here)
│   ├── sss_post_processing.py  ← normalized scoring output
│   ├── sss_diff.py             ← scan comparison / diff
│   ├── sss_filenames.py        ← output filename conventions
│   ├── sss_indices.py          ← TASE index updater
│   ├── sss_peg_ratios.py       ← PEG ratio scraper
│   ├── sss_results_performance.py ← historical performance analysis
│   ├── argus_db.py             ← SQLite database layer (NEW - just built)
│   ├── pdf_generator.py        ← PDF report generation (migrated to fpdf2)
│   ├── Mailer.py               ← email delivery
│   ├── Indices/                ← index CSV files (being replaced by DB)
│   └── Results/                ← scan output (gitignored)
├── requirements.txt
├── requirements-compiled.txt   ← C extension build notes for Python 3.14
├── README.md
└── CONTEXT.md                  ← this file
```

---

## Database Schema (argus_db.py)

All PKs follow `tablename_uid` convention. Key tables:

```sql
watchlists      -- named lists (default watchlist_uid=1)
stocks          -- master symbol table, has watchlist_uid + is_watched
indices         -- maps stocks to index membership (SP500, NASDAQ100, etc.)
stock_financials -- cached API data with staleness tracking
scans           -- scan run metadata
scan_results    -- per-ticker scored results per scan
index_refresh_log -- tracks when indices were last refreshed
```

Watchlist query pattern:
```sql
SELECT * FROM stocks WHERE watchlist_uid = 1 AND is_watched = 1
```

---

## What We've Fixed (Python 3.14 Migration)

| File | Fix |
|------|-----|
| `pdf_generator.py` | Migrated from `fpdf+HTMLMixin` to `fpdf2` API |
| `sss.py` | Removed `forex_python`, replaced with `CurrencyConverter` |
| `sss.py` | Fixed `fillna(method=)` → `.ffill()` / `.bfill()` for pandas 2.x |
| `sss.py` | Fixed `if_str_return_none()` for pandas 2.x |
| `sss.py` | Fixed yahooquery Timestamp keys → `str()` conversion |
| `sss.py` | Added `periodType == '12M'` filter for annual financials |
| `sss.py` | Moved json save block after yq assignments (financials now populate) |
| `sss.py` | Replaced `talib` with `pandas-ta` |
| `sss.py` | Fixed Wikipedia S&P500 scrape with `requests` + proper headers |
| `sss.py` | Bounds check on `EARNINGS_WEIGHTS` index |
| `sss.py` | Guard `shutil.move` for missing directories |
| `sss_post_processing.py` | Fixed pandas fragmented DataFrame warning with `pd.concat()` |

---

## What We've Refactored

| Change | Result |
|--------|--------|
| `round_and_avoid_none_values()` | 282 lines → 12 using `dataclasses.fields()` |
| `check_sector()` | Converted if-elif chain to `match-case` |
| `mode_str` block | Converted to `match-case` |
| `all_str` block | Converted to `match-case` |
| All scoring constants | Moved from `sss.py` to `sss_config.py` |
| `DEBUG_MODE` flag | Added to `sss_config.py`, all debug prints gated |

---

## Known Issues / In Progress

- `[perform_scan_close_values_days] Outer Exception 1` — non-critical, moving average calc issue
- TASE reference run paths in config still point to old results that don't exist locally
- `numba==0.61.2` blocked on Python 3.14 — pandas-ta installed with `--no-deps`

---

## Next Steps (Priority Order)

1. **Wire `argus_db.py` into scan flow** — replace CSV index reads with DB queries, hook `save_scan_result()` into `process_symbols()`
2. **Replace Wikipedia S&P500 scrape** — use `indices` table with weekly refresh instead of live scrape every run
3. **Replace all `Indices/` CSV files** — migrate to DB, populate on first run
4. **Replace `custom_portfolio` in config** — query `watchlists` table instead
5. **Integrate Quiver Quant** — congressional trades, lobbying data layer
6. **Integrate Unusual Whales** — dark pool, options flow layer
7. **Module split** — break `sss.py` into `data_fetcher.py`, `scoring.py`, `scanner.py`, `models.py`, `utils.py`
8. **Flask dashboard** — replace `driver.py` tkinter skeleton

---

## Environment

```
Python:   3.14.2
Platform: Windows (dev) → Ubuntu (deploy)
Venv:     venv_argus (always activate before running)
DB:       src/argus.db (SQLite, created by python argus_db.py)
Run:      cd src && python sss_run.py
```

## Compiled Dependencies (Windows x64, MSVC 19.38)
Built from source in `builds/` directory:
- numpy 2.5.0.dev0
- pandas 3.1.0.dev0
- matplotlib 3.11.0.dev
- psutil 8.0.0

---

## Quick Commands

```cmd
# Activate venv
venv_argus\Scripts\activate.bat

# Run a scan (custom 5-stock portfolio)
cd src && python sss_run.py

# Initialize/verify database
cd src && python argus_db.py

# Check git status
git status
```
