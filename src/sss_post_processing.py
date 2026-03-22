#############################################################################
#
# Version 0.3.0 - ARGUS Project
# Original Author: Asaf Ravid <asaf.rvd@gmail.com>
# Updated: Fixed pandas 2.x fragmented DataFrame PerformanceWarning
#          Replaced repeated frame.insert() calls with single pd.concat()
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

import pandas as pd

import sss
import sss_config
import sss_filenames

SSS_VALUE_NORMALIZED_COLUMN_NAME = "sss_value_normalized"
SSS_VALUE_COLUMN_NAME            = "sss_value"


def process_engine_csv(path) -> object:
    filename_path = path + "/" + sss_filenames.ENGINE_FILENAME
    data          = pd.read_csv(filename_path + ".csv", skiprows=[0])  # 1st row is a description row, irrelevant for the data processing

    [numerator_parameters_list,              denominator_parameters_list             ] = sss.get_used_parameters_names_in_core_equation(False)
    [numerator_parameters_list_to_calculate, denominator_parameters_list_to_calculate] = sss.get_used_parameters_names_in_core_equation(sss_config.custom_sss_value_equation)

    max_numerator_values   = data[numerator_parameters_list].max()
    max_denominator_values = data[denominator_parameters_list].max()

    # pandas 2.x fix: build all normalized columns first, then concat once
    # Repeated frame.insert() inside loops causes PerformanceWarning: DataFrame is highly fragmented
    normalized_columns = {}
    sss_value_normalized = None

    # Process numerator parameters
    for parameter in numerator_parameters_list:
        normalized_col = data[parameter] / max_numerator_values[parameter]
        normalized_columns[parameter + "_normalized"] = normalized_col

        if sss_value_normalized is None:
            sss_value_normalized = normalized_col.copy()
        elif parameter in numerator_parameters_list_to_calculate:
            sss_value_normalized = sss_value_normalized + normalized_col

    # Process denominator parameters
    for parameter in denominator_parameters_list:
        normalized_col = data[parameter] / max_denominator_values[parameter]
        normalized_columns[parameter + "_normalized"] = normalized_col

        if parameter in denominator_parameters_list_to_calculate:
            if sss_value_normalized is not None:
                sss_value_normalized = sss_value_normalized - normalized_col

    # Build normalized columns DataFrame and insert sss_value_normalized
    normalized_df = pd.DataFrame(normalized_columns, index=data.index)
    if sss_value_normalized is not None:
        normalized_df.insert(0, SSS_VALUE_NORMALIZED_COLUMN_NAME, sss_value_normalized)

    # Insert sss_value_normalized next to sss_value column in original data
    sss_value_col_index = data.columns.get_loc(SSS_VALUE_COLUMN_NAME)

    # Rebuild data with normalized columns interleaved - concat all at once
    left  = data.iloc[:, :sss_value_col_index + 1]
    right = data.iloc[:, sss_value_col_index + 1:]
    data  = pd.concat([left, normalized_df, right], axis=1)

    sorted_data = data.sort_values(by=[SSS_VALUE_NORMALIZED_COLUMN_NAME])
    sorted_data.to_csv(filename_path + "_normalized.csv", index=False)
