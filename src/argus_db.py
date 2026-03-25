#############################################################################
#
# ARGUS Project - Database Layer
# argus_db.py
#
# SQLite database schema and connection management
#
#############################################################################

import sqlite3
import os
import json
from datetime import datetime, timedelta
from contextlib import contextmanager

DB_PATH = 'argus.db'

# =============================================================================
# CONNECTION MANAGEMENT
# =============================================================================

@contextmanager
def get_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # allows dict-style access to rows
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")  # better concurrent read performance
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# =============================================================================
# SCHEMA
# =============================================================================

SCHEMA = """

-- =============================================================================
-- WATCHLISTS
-- A named list of stocks to track (e.g. 'default', 'tase_custom', 'speculative')
-- =============================================================================
CREATE TABLE IF NOT EXISTS watchlists (
    watchlist_uid   INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL UNIQUE,
    description     TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed a default watchlist
INSERT OR IGNORE INTO watchlists (watchlist_uid, name, description)
VALUES (1, 'default', 'Default watchlist');


-- =============================================================================
-- STOCKS
-- Master table for all known symbols across all indices and watchlists.
-- is_watched and watchlist_uid allow simple watchlist membership queries:
--   SELECT * FROM stocks WHERE watchlist_uid = 1 AND is_watched = 1
-- =============================================================================
CREATE TABLE IF NOT EXISTS stocks (
    stock_uid       INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol          TEXT    NOT NULL UNIQUE,
    company_name    TEXT,
    sector          TEXT,
    industry        TEXT,
    country         TEXT,
    exchange        TEXT,
    currency        TEXT,
    quote_type      TEXT,                       -- EQUITY, ETF, etc.
    is_etf          INTEGER DEFAULT 0,          -- 0 or 1
    is_watched      INTEGER DEFAULT NULL,       -- NULL = not set, 0 = excluded, 1 = watched
    watchlist_uid   INTEGER DEFAULT NULL        -- FK to watchlists, NULL = not on any watchlist
        REFERENCES watchlists(watchlist_uid),
    last_updated    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =============================================================================
-- INDICES
-- Maps stocks to index membership (SP500, NASDAQ100, RUSSELL1000, TASE, etc.)
-- A stock can belong to multiple indices
-- =============================================================================
CREATE TABLE IF NOT EXISTS indices (
    index_uid       INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_uid       INTEGER NOT NULL
        REFERENCES stocks(stock_uid) ON DELETE CASCADE,
    index_name      TEXT    NOT NULL,           -- 'SP500', 'NASDAQ100', 'RUSSELL1000', 'TASE', 'NASDAQ', 'SIX', 'ST'
    last_updated    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_uid, index_name)
);


-- =============================================================================
-- STOCK_FINANCIALS
-- Cached financial data per stock - avoids hitting API on every scan run
-- Stale threshold configurable - check last_updated before deciding to re-fetch
-- =============================================================================
CREATE TABLE IF NOT EXISTS stock_financials (
    financials_uid  INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_uid       INTEGER NOT NULL UNIQUE
        REFERENCES stocks(stock_uid) ON DELETE CASCADE,
    -- Summary data (changes daily)
    previous_close              REAL,
    market_cap                  INTEGER,
    enterprise_value            INTEGER,
    fifty_two_week_low          REAL,
    fifty_two_week_high         REAL,
    two_hundred_day_average     REAL,
    trailing_pe                 REAL,
    forward_pe                  REAL,
    price_to_book               REAL,
    price_to_sales_ttm          REAL,
    enterprise_to_revenue       REAL,
    enterprise_to_ebitda        REAL,
    profit_margins              REAL,
    revenue_growth              REAL,
    earnings_quarterly_growth   REAL,
    held_percent_insiders       REAL,
    held_percent_institutions   REAL,
    shares_outstanding          INTEGER,
    trailing_eps                REAL,
    forward_eps                 REAL,
    peg_ratio                   REAL,
    -- Raw API response cache (full JSON for deep financial data)
    raw_info_json               TEXT,
    raw_financials_json         TEXT,
    -- Staleness tracking
    prices_updated_at           TIMESTAMP,      -- refresh daily
    financials_updated_at       TIMESTAMP,      -- refresh weekly
    last_updated                TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =============================================================================
-- SCANS
-- Metadata for each scan run
-- =============================================================================
CREATE TABLE IF NOT EXISTS scans (
    scan_uid        INTEGER PRIMARY KEY AUTOINCREMENT,
    mode            TEXT    NOT NULL,           -- 'custom', 'nsr', 'tase', 'all', 'six', 'st'
    watchlist_uid   INTEGER DEFAULT NULL
        REFERENCES watchlists(watchlist_uid),
    num_results     INTEGER,
    config_snapshot TEXT,                       -- JSON snapshot of sss_config at time of scan
    started_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at    TIMESTAMP
);


-- =============================================================================
-- SCAN_RESULTS
-- Per-ticker scored results for each scan run
-- =============================================================================
CREATE TABLE IF NOT EXISTS scan_results (
    result_uid                    INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_uid                      INTEGER NOT NULL
        REFERENCES scans(scan_uid) ON DELETE CASCADE,
    stock_uid                     INTEGER NOT NULL
        REFERENCES stocks(stock_uid),
    -- Core scoring fields
    sss_value                     REAL,
    evr_effective                 REAL,
    pe_effective                  REAL,
    effective_ev_to_ebitda        REAL,
    effective_profit_margin       REAL,
    held_percent_insiders         REAL,
    price_to_book                 REAL,
    enterprise_value              INTEGER,
    market_cap                    INTEGER,
    eqg_factor_effective          REAL,
    rqg_factor_effective          REAL,
    effective_peg_ratio           REAL,
    ev_to_cfo_ratio_effective     REAL,
    debt_to_equity_effective_used REAL,
    ma                            TEXT,
    skip_reason                   TEXT,
    -- Full scored data as JSON for fields not in columns
    full_result_json              TEXT,
    scored_at                     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =============================================================================
-- INDEX_REFRESH_LOG
-- Tracks when each index was last refreshed from its source
-- =============================================================================
CREATE TABLE IF NOT EXISTS index_refresh_log (
    refresh_uid     INTEGER PRIMARY KEY AUTOINCREMENT,
    index_name      TEXT    NOT NULL,
    source          TEXT,                       -- 'wikipedia', 'nasdaq_ftp', 'tase_api', 'six_api', 'manual'
    num_symbols     INTEGER,
    refreshed_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =============================================================================
-- INDEXES for common query patterns
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_stocks_symbol       ON stocks(symbol);
CREATE INDEX IF NOT EXISTS idx_stocks_watchlist    ON stocks(watchlist_uid, is_watched);
CREATE INDEX IF NOT EXISTS idx_indices_index_name  ON indices(index_name);
CREATE INDEX IF NOT EXISTS idx_scan_results_scan   ON scan_results(scan_uid);
CREATE INDEX IF NOT EXISTS idx_scan_results_stock  ON scan_results(stock_uid);
"""


# =============================================================================
# INITIALIZATION
# =============================================================================

def init_db():
    """Initialize the database, creating tables if they don't exist."""
    with get_connection() as conn:
        conn.executescript(SCHEMA)
    print(f"[DB] Database initialized at {os.path.abspath(DB_PATH)}")


# =============================================================================
# WATCHLIST OPERATIONS
# =============================================================================

def get_watchlist(watchlist_uid: int = 1) -> list:
    """Return all watched symbols for a given watchlist."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT s.symbol, s.company_name, s.sector, s.country
            FROM stocks s
            WHERE s.watchlist_uid = ? AND s.is_watched = 1
            ORDER BY s.symbol
        """, (watchlist_uid,)).fetchall()
    return [dict(row) for row in rows]


def add_to_watchlist(symbols: list, watchlist_uid: int = 1):
    """Add symbols to a watchlist. Inserts stock record if it doesn't exist."""
    with get_connection() as conn:
        for symbol in symbols:
            conn.execute("""
                INSERT INTO stocks (symbol, is_watched, watchlist_uid)
                VALUES (?, 1, ?)
                ON CONFLICT(symbol) DO UPDATE SET
                    is_watched    = 1,
                    watchlist_uid = ?,
                    last_updated  = CURRENT_TIMESTAMP
            """, (symbol, watchlist_uid, watchlist_uid))
    print(f"[DB] Added {len(symbols)} symbols to watchlist {watchlist_uid}")


def remove_from_watchlist(symbols: list, watchlist_uid: int = 1):
    """Remove symbols from a watchlist (sets is_watched = 0, keeps the stock record)."""
    with get_connection() as conn:
        for symbol in symbols:
            conn.execute("""
                UPDATE stocks SET is_watched = 0
                WHERE symbol = ? AND watchlist_uid = ?
            """, (symbol, watchlist_uid))


# =============================================================================
# STOCK OPERATIONS
# =============================================================================

def upsert_stock(symbol: str, **kwargs) -> int:
    """Insert or update a stock record. Returns stock_uid."""
    fields = ', '.join(kwargs.keys())
    placeholders = ', '.join(['?'] * len(kwargs))
    updates = ', '.join([f"{k} = excluded.{k}" for k in kwargs.keys()])
    with get_connection() as conn:
        conn.execute(f"""
            INSERT INTO stocks (symbol, {fields})
            VALUES (?, {placeholders})
            ON CONFLICT(symbol) DO UPDATE SET
                {updates},
                last_updated = CURRENT_TIMESTAMP
        """, (symbol, *kwargs.values()))
        row = conn.execute("SELECT stock_uid FROM stocks WHERE symbol = ?", (symbol,)).fetchone()
    return row['stock_uid']


def get_stock(symbol: str) -> dict | None:
    """Get a stock record by symbol."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM stocks WHERE symbol = ?", (symbol,)).fetchone()
    return dict(row) if row else None


# =============================================================================
# INDEX OPERATIONS
# =============================================================================

def get_index_symbols(index_name: str) -> list:
    """Get all symbols for a given index."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT s.symbol, s.company_name, s.sector
            FROM stocks s
            JOIN indices i ON s.stock_uid = i.stock_uid
            WHERE i.index_name = ?
            ORDER BY s.symbol
        """, (index_name,)).fetchall()
    return [dict(row) for row in rows]


def upsert_index_symbols(index_name: str, symbols: list[dict]):
    """
    Bulk upsert symbols for an index.
    symbols: list of dicts with keys: symbol, company_name (optional), sector (optional)
    """
    with get_connection() as conn:
        for item in symbols:
            symbol = item['symbol']
            # Upsert the stock
            conn.execute("""
                INSERT INTO stocks (symbol, company_name, sector, country, exchange)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(symbol) DO UPDATE SET
                    company_name = COALESCE(excluded.company_name, company_name),
                    sector       = COALESCE(excluded.sector, sector),
                    last_updated = CURRENT_TIMESTAMP
            """, (
                symbol,
                item.get('company_name'),
                item.get('sector'),
                item.get('country'),
                item.get('exchange'),
            ))
            # Get the stock_uid
            stock_uid = conn.execute(
                "SELECT stock_uid FROM stocks WHERE symbol = ?", (symbol,)
            ).fetchone()['stock_uid']
            # Upsert index membership
            conn.execute("""
                INSERT INTO indices (stock_uid, index_name)
                VALUES (?, ?)
                ON CONFLICT(stock_uid, index_name) DO UPDATE SET
                    last_updated = CURRENT_TIMESTAMP
            """, (stock_uid, index_name))

        # Log the refresh
        conn.execute("""
            INSERT INTO index_refresh_log (index_name, num_symbols, source)
            VALUES (?, ?, 'bulk_upsert')
        """, (index_name, len(symbols)))

    print(f"[DB] Upserted {len(symbols)} symbols for index '{index_name}'")


def index_needs_refresh(index_name: str, max_age_days: int = 7) -> bool:
    """Returns True if the index hasn't been refreshed within max_age_days."""
    with get_connection() as conn:
        row = conn.execute("""
            SELECT refreshed_at FROM index_refresh_log
            WHERE index_name = ?
            ORDER BY refreshed_at DESC
            LIMIT 1
        """, (index_name,)).fetchone()
    if not row:
        return True
    last_refresh = datetime.fromisoformat(row['refreshed_at'])
    return datetime.now() - last_refresh > timedelta(days=max_age_days)


# =============================================================================
# FINANCIALS CACHE
# =============================================================================

def get_cached_financials(symbol: str, max_age_hours: int = 24) -> dict | None:
    """
    Return cached financials if fresh enough, else None.
    Prices stale after max_age_hours, full financials stale after 7 days.
    """
    with get_connection() as conn:
        row = conn.execute("""
            SELECT f.* FROM stock_financials f
            JOIN stocks s ON f.stock_uid = s.stock_uid
            WHERE s.symbol = ?
        """, (symbol,)).fetchone()

    if not row:
        return None

    if row['prices_updated_at']:
        age = datetime.now() - datetime.fromisoformat(row['prices_updated_at'])
        if age > timedelta(hours=max_age_hours):
            return None

    return dict(row)


def upsert_financials(symbol: str, data: dict):
    """Cache financial data for a symbol."""
    with get_connection() as conn:
        stock = conn.execute(
            "SELECT stock_uid FROM stocks WHERE symbol = ?", (symbol,)
        ).fetchone()
        if not stock:
            conn.execute("INSERT INTO stocks (symbol) VALUES (?)", (symbol,))
            stock = conn.execute(
                "SELECT stock_uid FROM stocks WHERE symbol = ?", (symbol,)
            ).fetchone()

        stock_uid = stock['stock_uid']
        conn.execute("""
            INSERT INTO stock_financials (
                stock_uid, previous_close, market_cap, enterprise_value,
                fifty_two_week_low, fifty_two_week_high, two_hundred_day_average,
                trailing_pe, forward_pe, price_to_book, price_to_sales_ttm,
                enterprise_to_revenue, enterprise_to_ebitda, profit_margins,
                revenue_growth, earnings_quarterly_growth,
                held_percent_insiders, held_percent_institutions,
                shares_outstanding, trailing_eps, forward_eps, peg_ratio,
                raw_info_json, prices_updated_at, financials_updated_at
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            ON CONFLICT(stock_uid) DO UPDATE SET
                previous_close             = excluded.previous_close,
                market_cap                 = excluded.market_cap,
                enterprise_value           = excluded.enterprise_value,
                fifty_two_week_low         = excluded.fifty_two_week_low,
                fifty_two_week_high        = excluded.fifty_two_week_high,
                two_hundred_day_average    = excluded.two_hundred_day_average,
                trailing_pe                = excluded.trailing_pe,
                forward_pe                 = excluded.forward_pe,
                price_to_book              = excluded.price_to_book,
                price_to_sales_ttm         = excluded.price_to_sales_ttm,
                enterprise_to_revenue      = excluded.enterprise_to_revenue,
                enterprise_to_ebitda       = excluded.enterprise_to_ebitda,
                profit_margins             = excluded.profit_margins,
                revenue_growth             = excluded.revenue_growth,
                earnings_quarterly_growth  = excluded.earnings_quarterly_growth,
                held_percent_insiders      = excluded.held_percent_insiders,
                held_percent_institutions  = excluded.held_percent_institutions,
                shares_outstanding         = excluded.shares_outstanding,
                trailing_eps               = excluded.trailing_eps,
                forward_eps                = excluded.forward_eps,
                peg_ratio                  = excluded.peg_ratio,
                raw_info_json              = excluded.raw_info_json,
                prices_updated_at          = CURRENT_TIMESTAMP,
                last_updated               = CURRENT_TIMESTAMP
        """, (
            stock_uid,
            data.get('previousClose'),
            data.get('marketCap'),
            data.get('enterpriseValue'),
            data.get('fiftyTwoWeekLow'),
            data.get('fiftyTwoWeekHigh'),
            data.get('twoHundredDayAverage'),
            data.get('trailingPE'),
            data.get('forwardPE'),
            data.get('priceToBook'),
            data.get('priceToSalesTrailing12Months'),
            data.get('enterpriseToRevenue'),
            data.get('enterpriseToEbitda'),
            data.get('profitMargins'),
            data.get('revenueGrowth'),
            data.get('earningsQuarterlyGrowth'),
            data.get('heldPercentInsiders'),
            data.get('heldPercentInstitutions'),
            data.get('sharesOutstanding'),
            data.get('trailingEps'),
            data.get('forwardEps'),
            data.get('pegRatio'),
            json.dumps(data),
        ))


# =============================================================================
# SCAN OPERATIONS
# =============================================================================

def create_scan(mode: str, watchlist_uid: int = None, config_snapshot: dict = None) -> int:
    """Create a new scan record and return its scan_uid."""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO scans (mode, watchlist_uid, config_snapshot)
            VALUES (?, ?, ?)
        """, (mode, watchlist_uid, json.dumps(config_snapshot) if config_snapshot else None))
        scan_uid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    return scan_uid


def complete_scan(scan_uid: int, num_results: int):
    """Mark a scan as complete."""
    with get_connection() as conn:
        conn.execute("""
            UPDATE scans SET completed_at = CURRENT_TIMESTAMP, num_results = ?
            WHERE scan_uid = ?
        """, (num_results, scan_uid))


def save_scan_result(scan_uid: int, stock_uid: int, result: dict):
    """Save a single ticker's scored result."""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO scan_results (
                scan_uid, stock_uid, sss_value, evr_effective, pe_effective,
                effective_ev_to_ebitda, effective_profit_margin, held_percent_insiders,
                price_to_book, enterprise_value, market_cap, eqg_factor_effective,
                rqg_factor_effective, effective_peg_ratio, ev_to_cfo_ratio_effective,
                debt_to_equity_effective_used, ma, skip_reason, full_result_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            scan_uid,
            stock_uid,
            result.get('sss_value'),
            result.get('evr_effective'),
            result.get('pe_effective'),
            result.get('effective_ev_to_ebitda'),
            result.get('effective_profit_margin'),
            result.get('held_percent_insiders'),
            result.get('price_to_book'),
            result.get('enterprise_value'),
            result.get('market_cap'),
            result.get('eqg_factor_effective'),
            result.get('rqg_factor_effective'),
            result.get('effective_peg_ratio'),
            result.get('ev_to_cfo_ratio_effective'),
            result.get('debt_to_equity_effective_used'),
            result.get('ma'),
            result.get('skip_reason'),
            json.dumps(result),
        ))


def get_scan_results(scan_uid: int) -> list:
    """Get all results for a scan, joined with stock info."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT r.*, s.symbol, s.company_name, s.sector, s.country
            FROM scan_results r
            JOIN stocks s ON r.stock_uid = s.stock_uid
            WHERE r.scan_uid = ?
            ORDER BY r.sss_value ASC
        """, (scan_uid,)).fetchall()
    return [dict(row) for row in rows]


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == '__main__':
    init_db()
