#############################################################################
#
# Version 0.3.0 - ARGUS Project
# Original Author: Asaf Ravid <asaf.rvd@gmail.com>
# Updated: Moved all scoring constants from sss.py into config
#
#    Stock Screener and Scanner - based on yfinance
#    Copyright (C) 2021 Asaf Ravid
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################

# =============================================================================
# RUN MODES
# =============================================================================
PROFILE = False

ALL_COUNTRY_SYMBOLS_OFF = 0
ALL_COUNTRY_SYMBOLS_US  = 1  # Nasdaq
ALL_COUNTRY_SYMBOLS_SIX = 2  # Swiss Stock Exchange
ALL_COUNTRY_SYMBOLS_ST  = 3  # Swedish (Stockholm) Stock Exchange

run_custom_tase           = False  # Custom Portfolio
run_custom                = True
run_tase                  = True   # Tel Aviv Stock Exchange
run_nsr                   = False  # NASDAQ100+S&P500+RUSSEL1000
run_all                   = False  # All Nasdaq Stocks
run_six                   = False  # All Swiss Stocks
run_st                    = False  # All (Stockholm) Swedish Stocks
multi_dim_scan_mode       = False  # Multi-dimensional scan Mode
aggregate_only            = False
research_mode_max_ev      = False
use_reference_as_raw_data = False
custom_sss_value_equation = False

scan_close_values_interval      = '1d'
crash_and_continue_refresh_freq = 10 if run_custom or run_custom_tase else 100

# =============================================================================
# RESULTS FOLDER SELECTION
# =============================================================================
automatic_results_folder_selection = False

reference_run_custom = None
reference_run_tase   = 'Results/Tase/20230607-221131_Tase_Tchnlgy3.0_RlEstt1.0_nRes298'
reference_run_nsr    = None
reference_run_all    = 'Results/All/20221208-004305_Tchnlgy3.0_FnnclSrvcs1.0_A_nRes2543'
reference_run_six    = 'Results/Six/20220111-002719_S_nRes196'
reference_run_st     = 'Results/St/20210915-023602_St_Bdb_nRes130'

new_run_custom       = 'Results/Custom/20210917-201728_Bdb_nRes312_Custom'
new_run_tase         = 'Results/Tase/20240121-192140_Tase_Tchnlgy3.0_RlEstt1.0_nRes245'
new_run_nsr          = 'Results/Nsr/20230606-224929_Tchnlgy3.0_FnnclSrvcs1.0_nRes826'
new_run_all          = 'Results/All/20230620-045317_Tchnlgy3.0_FnnclSrvcs1.0_A_nRes2786'
new_run_six          = 'Results/Six/20220111-002719_S_nRes196'
new_run_st           = 'Results/St/20210915-023602_St_Bdb_nRes130'

crash_and_continue_path = None

custom_portfolio      = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'GOOG']
custom_portfolio_tase = ['AFRE', 'ITMR']

research_mode_probe_list = []

yq_mode    = True
DEBUG_MODE = False

# =============================================================================
# SCORING ENGINE CONSTANTS
# Moved from sss.py - tune these to adjust scoring behavior
# =============================================================================

VERBOSE_LOGS                  = 0   # Consolidated with DEBUG_MODE - use DEBUG_MODE for new debug prints
SKIP_5LETTER_Y_STOCK_LISTINGS = False  # Skip ADRs - American Depositary receipts (5 Letter Stocks)
NUM_ROUND_DECIMALS            = 7

# Unknown/fallback values - used when data is missing
NUM_EMPLOYEES_UNKNOWN         = 10000000   # Makes company appear inefficient
PROFIT_MARGIN_UNKNOWN         = 0.00001    # Makes company appear barely profitable
PRICE_TO_BOOK_UNKNOWN         = 1000.0
PERCENT_HELD_INSTITUTIONS_LOW = 0.01       # Low, to make less relevant
PERCENT_HELD_INSIDERS_UNKNOWN = 0.0000123
PEG_UNKNOWN                   = 10000     # Non-attractive value
QEG_MAX                       = 10000
REG_MAX                       = 10000
SHARES_OUTSTANDING_UNKNOWN    = 100000000  # 100 Million Shares
BAD_SSS                       = 10.0 ** 50.0

# Weighting arrays - index 0 = oldest, index -1 = newest
PROFIT_MARGIN_WEIGHTS         = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0, 256.0, 512.0]
PROFIT_MARGIN_YEARLY_WEIGHTS  = [1.0, 4.0, 16,  64,  256,  1024, 4096, 16384, 4*16384, 16*16384]
PROFIT_MARGIN_QUARTERLY_WEIGHTS = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0, 256.0, 512.0]
CASH_FLOW_WEIGHTS             = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0, 256.0, 512.0]
REVENUES_WEIGHTS              = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0, 256.0, 512.0]
NO_WEIGHTS                    = [1.0, 1.0, 1.0, 1.0,  1.0,  1.0,  1.0,   1.0,   1.0,   1.0]
EARNINGS_WEIGHTS              = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0, 256.0, 512.0]
BALANCE_SHEETS_WEIGHTS        = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0, 256.0, 512.0]

# Growth factors
EQG_UNKNOWN                   = -0.9   # -90%
RQG_UNKNOWN                   = -0.9   # -90%
EQG_POSITIVE_FACTOR           = 10.0
RQG_POSITIVE_FACTOR           = 10.0
EQG_WEIGHT_VS_YOY             = 0.75
RQG_WEIGHT_VS_YOY             = 0.75
EQG_DAMPER                    = 0.25
RQG_DAMPER                    = 0.25

# Dampers
TRAILING_EPS_PERCENTAGE_DAMP_FACTOR = 0.01
PROFIT_MARGIN_DAMPER                = 0.001
RATIO_DAMPER                        = 0.01
ROA_DAMPER                          = 0.1
ROA_NEG_FACTOR                      = 0.000001
ROE_DAMPER                          = 0.1
ROE_NEG_FACTOR                      = 0.000001

# Thresholds
REFERENCE_DB_MAX_VALUE_DIFF_FACTOR_THRESHOLD = 0.9
QUARTERLY_YEARLY_MISSING_FACTOR              = 0.25
NEGATIVE_ALTMAN_Z_FACTOR                     = 0.00001
MIN_REVENUE_FOR_0_REVENUE_DIV_BY_0_AVOIDANCE = 0.001
MAX_UNKNOWN_PE                               = 100000
MAX_UNKNOWN_EVR                              = 100000

# Profit margin boost factors
# These reference custom_sss_value_equation so they must be defined after it
PROFIT_MARGIN_BOOST_FOR_PRESENCE_OF_ANNUAL_NEGATIVE_EARNINGS      = 0.025 if custom_sss_value_equation else 0.1
PROFIT_MARGIN_BOOST_FOR_PRESENCE_OF_QUARTERLY_NEGATIVE_EARNINGS   = 0.025 if custom_sss_value_equation else 0.1
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_INCREASE                = 10.0  if custom_sss_value_equation else 3.75
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_INCREASE             = 10.0  if custom_sss_value_equation else 2.25
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_POSITIVE                = 10.0  if custom_sss_value_equation else 4.75
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_POSITIVE             = 10.0  if custom_sss_value_equation else 2.75
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_INCREASE_IN_EARNINGS    = 10.0  if custom_sss_value_equation else 4.25
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_INCREASE_IN_REVENUE     = 14.0  if custom_sss_value_equation else 7.77
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_INCREASE_IN_EARNINGS = 10.0  if custom_sss_value_equation else 3.25
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_INCREASE_IN_REVENUE  = 25.0  if custom_sss_value_equation else 9.99
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_DECREASE                = 0.05  if custom_sss_value_equation else 0.25
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_DECREASE             = 0.05  if custom_sss_value_equation else 0.25
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_DECREASE_IN_EARNINGS    = 0.05  if custom_sss_value_equation else 0.25
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_DECREASE_IN_REVENUE     = 0.05  if custom_sss_value_equation else 0.2
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_DECREASE_IN_EARNINGS = 0.05  if custom_sss_value_equation else 0.25
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_DECREASE_IN_REVENUE  = 0.05  if custom_sss_value_equation else 0.1
PROFIT_MARGIN_DUPLICATION_FACTOR                                  = 8.0

# Negative factor penalties
NEGATIVE_CFO_FACTOR            = 100000.0
NEGATIVE_PEG_RATIO_FACTOR      = 100000.0
NEGATIVE_DEBT_TO_EQUITY_FACTOR = 100.0
NEGATIVE_EARNINGS_FACTOR       = 100000.0
DEBT_TO_EQUITY_MIN_BASE        = 0.001

# PE weighting
FORWARD_PRICE_TO_EARNINGS_WEIGHT  = 0.125
TRAILING_PRICE_TO_EARNINGS_WEIGHT = 1 - FORWARD_PRICE_TO_EARNINGS_WEIGHT

# Distance from low
DIST_FROM_LOW_FACTOR_DAMPER                = 0.001
DIST_FROM_LOW_FACTOR_HIGHER_THAN_ONE_POWER = 6

EV_TO_EBITDA_MAX_UNKNOWN = 100000
