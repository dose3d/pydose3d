import logging
import numpy as np
import pandas as pd
from pandas.core.frame import DataFrame
from numpy import median
from collections import defaultdict
from scipy.signal import savgol_filter

def bunch_mean(data, sel_criteria={}, no_rows=1, log_level=logging.INFO):
    log = logging.getLogger("Batch mean")
    log.setLevel(log_level)

    log.debug(f"Mean computation for {no_rows} no. of rows and keys={sel_criteria}")

    df = DataFrame()      # prepare empty data frame

    irow = 0
    col_sum = dict()
    col_sum = defaultdict(list)
    for col in data.columns:
        col_sum[col] = list()

    total_count = 0
    do_selection = False
    selected = False

    if(sel_criteria):
        do_selection = True

    for index, row in data.iterrows():            
        for col in data.columns:
            if(do_selection):
                if(col in sel_criteria):
                    if(row[col]==sel_criteria[col]):
                        selected = True
                    else:
                        selected = False
            if(do_selection and selected):
                col_sum[col].append(row[col])
            else:
                col_sum[col].append(row[col])
        irow = irow + 1
        total_count = total_count + 1
        if(irow % no_rows == 0):
            df = df.append({k: median(v) for k, v in col_sum.items()}, ignore_index = True)
            col_sum = {k: [] for k, v in col_sum.items()}
            irow = 0
        if(total_count % 10000 == 0):
            log.debug(f" No. of {total_count} rows processed..")
        
        if(total_count == 100000):
            break
    return df

# ----------------------------------------------------------------------------------------------

def bunch_count(data, sel_criteria={}, no_rows=1, log_level=logging.INFO):
    log = logging.getLogger("Batch count")
    log.setLevel(log_level)

    log.debug(f"Sum computation for {no_rows} no. of rows and keys={sel_criteria}")
    df = DataFrame()      # prepare empty data frame

    irow = 0
    col_sum = {}
    for col in data.columns:
        col_sum[col] = 0
    total_count = 0
    for index, row in data.iterrows():
        for col in data.columns:
            if(row[col]==sel_criteria[col]):
                col_sum[col] = col_sum[col] + 1
        irow = irow + 1
        total_count = total_count + 1
        if(irow % no_rows == 0):
            # TODO: Refactor frame.append
            # FutureWarning: The frame.append method is deprecated 
            # and will be removed from pandas in a future version. Use pandas.concat instead.
            df = df.append(col_sum, ignore_index = True)
            col_sum = {k: 0 for k, v in col_sum.items()}
            irow = 0
        if(total_count % 10000 == 0):
            log.debug(f" No. of {total_count} rows processed..")
        
        if(total_count == 100000):
            break
    return df

# ----------------------------------------------------------------------------------------------

def print_full(x):
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', 20)
    pd.set_option('display.width', 2000)
    pd.set_option('display.float_format', '{:20,.8f}'.format)
    pd.set_option('display.max_colwidth', None)
    print(x.head(25))
    print(x.tail(25))
    pd.reset_option('display.max_rows')
    pd.reset_option('display.max_columns')
    pd.reset_option('display.width')
    pd.reset_option('display.float_format')
    pd.reset_option('display.max_colwidth')

# ----------------------------------------------------------------------------------------------

def density_check(single_df):
    if 45 < (abs(single_df.iloc[1, 0] * 100 - single_df.iloc[2, 0] * 100)) < 110:
        return single_df
    else:
        denser_data = np.empty([1, 2])
        while True:
            if (abs(single_df.iloc[1, 0] * 100 - single_df.iloc[2, 0] * 100)) < 45:
                single_df = single_df.iloc[::2]

            elif 110 < abs(single_df.iloc[1, 0] * 100 - single_df.iloc[2, 0] * 100):
                i = 0
                scaler = (1/len(single_df.columns))
                for x in range(0, int(scaler * np.size(single_df)), 1):
                    if x == 0:
                        denser_data = single_df.iloc[x, 0]
                        denser_data = np.append(denser_data, single_df.iloc[x, 1])
                        i += 2

                    else:
                        temp_data = np.empty([0, 2])
                        temp_data = np.append(temp_data, ((denser_data[i - 2] + single_df.iloc[(int(x)), 0]) / 2))
                        temp_data = np.append(temp_data,
                                            ((denser_data[i - 1] + single_df.iloc[(int(x)), 1]) / 2))
                        temp_data = np.append(temp_data, (single_df.iloc[(int(x)), 0]))
                        temp_data = np.append(temp_data, (single_df.iloc[(int(x)), 1]))
                        denser_data = np.append(denser_data, temp_data)
                        i += 4
                denser_data = np.reshape(denser_data, (int(0.5 * np.size(denser_data)), 2))

                dataframe = pd.DataFrame(denser_data)
                if ('origin' in single_df):
                    dataframe['origin'] = single_df.iloc[10, 2]
                if ('flsz' in single_df):
                    dataframe['flsz'] = single_df.iloc[10, 3]
                dataframe.columns = single_df.columns
                single_df = dataframe

            else:
                single_df[single_df.columns[0]] = single_df[single_df.columns[0]].round(decimals=2)
                flag = list(single_df.columns.values)
                single_df = single_df.drop_duplicates(flag[0])
                single_df = single_df.reset_index(drop=True)
                return single_df   

# ----------------------------------------------------------------------------------------------

def smoother_svagol(original_data):

    denser_data = original_data
    data = denser_data.to_numpy()
    smooth_data = np.empty([0, 1])

    np.set_printoptions(precision=10)

    x = data[::,1]

    smooth_data = savgol_filter(x, 10, 2)

    smooth_frame = pd.DataFrame(smooth_data)
    order_frame = denser_data.iloc[:, 0]
    final_frame = pd.concat([order_frame, smooth_frame], axis=1)
    final_frame.columns = original_data.columns
    return final_frame