# ARGUS
### Thematic Supply-Chain-Aware Stock & ETF Screener

ARGUS is a multi-source stock and ETF screening platform built on top of the [asafravid/sss](https://github.com/asafravid/sss) engine, extended with geopolitical supply chain signals, institutional flow data, and congressional trading intelligence.

The name comes from the hundred-eyed giant of Greek mythology — it watches everything simultaneously: fundamentals, dark pools, options flow, supply chain disruptions, and congressional activity.

---

## What It Does

- Screens stocks and ETFs using a core fundamental scoring equation (EV, PEG, profit margins, ROA, debt ratios)
- Multi-dimensional scan ranking across multiple time periods
- Thematic signal layering — supply chain disruptions, geopolitical chokepoints, institutional flow
- Outputs ranked results to CSV and PDF reports
- Email delivery of scan results via Mailer

---

## Architecture (In Progress)

| Layer | Components | Status |
|-------|-----------|--------|
| Data Sources | yfinance, yahooquery, Quiver Quant, Unusual Whales | 🔧 In Progress |
| Processing Engine | sss core equation, pandas-ta, supply chain scoring | 🔧 In Progress |
| Database | MySQL backend for historical scan results | 📋 Planned |
| Interface | Flask web dashboard | 📋 Planned |
| Alerts | Email (Mailer.py), SMS | 📋 Planned |

---

## Setup

### Requirements
- Python 3.14.2
- Windows: Visual Studio Build Tools 2022 (x64)
- Windows: Chocolatey (for pkgconfiglite)

### Step 1 — Install Windows Build Prerequisites
```cmd
choco install pkgconfiglite -y
pip install meson-python meson ninja cython pybind11 versioneer setuptools setuptools_scm
```

### Step 2 — Create and Activate Virtual Environment
```cmd
python -m venv venv_argus

# Windows (must use x64 Native Tools Command Prompt for VS 2022)
venv_argus\Scripts\activate.bat

# Linux/Mac
source venv_argus/bin/activate
```

### Step 3 — Compile C Extensions from Source
See `requirements-compiled.txt` for full instructions. Compile in this order:
```cmd
# Must be run from x64 Native Tools Command Prompt for VS 2022 on Windows
pip install numpy --no-build-isolation    # from builds/numpy
pip install pandas --no-build-isolation   # from builds/pandas
pip install matplotlib --no-build-isolation # from builds/matplotlib
pip install psutil --no-build-isolation   # from builds/psutil
```

### Step 4 — Install Pure Python Dependencies
```cmd
pip install -r requirements.txt
```

---

## Known 3.14 Compatibility Issues

| Package | Issue | Workaround |
|---------|-------|------------|
| numba 0.61.2 | Hard caps at <3.14 | pandas-ta installed with --no-deps |
| forex-python | Unmaintained, broken | Removed, replaced with currency_converter |
| fpdf/HTMLMixin | HTMLMixin removed in fpdf2 | Migrated to fpdf2 API |
| pyPdf | Dead since 2010 | Replaced with pypdf |

---

## Supported Markets
- US (NASDAQ, S&P500, Russell 1000)
- Tel Aviv Stock Exchange (TASE)
- Swiss Stock Exchange (SIX)
- Stockholm Stock Exchange (ST)
- Custom portfolios

---

## Configuration
Edit `src/sss_config.py` to set:
- Scan mode (`run_nsr`, `run_tase`, `run_all`, `run_custom`, etc.)
- Reference run paths for diff comparison
- Custom portfolio tickers

---

## Running a Scan
```cmd
cd src
python sss_run.py
```

Results are saved to `Results/<scan_mode>/<date_and_time>/`

---

## Credits
- Core scanning engine: [Asaf Ravid](https://github.com/asafravid/sss)
- Extended and modernized for Python 3.14 as part of the ARGUS project

---

## Disclaimer
Scan results are **not investment recommendations**. They provide a basis for research and analysis only.

---

## License
GNU General Public License v3.0 — see LICENSE for details.
