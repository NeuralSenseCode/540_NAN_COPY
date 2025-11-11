"""
Assembly script for Nandos analysis project.
This script processes sensor data, extracts features, and merges results.

Functions:
- get_specific_data: Extracts specific task responses from sensor data
- get_slides: Extracts slide/stimuli information
- get_times: Extracts and aligns timing information from iMotions and survey data
- merge_data: Combines all data sources into final output files
"""

import os
import sys

# Configure path to find vendorized neurallib package
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "lib"))

from neurallib.clean import *
from scipy.ndimage import gaussian_filter1d
import seaborn as sns
from functools import reduce

client = '540_nan_copy'
project = '540_nan_copy'

# Define folder paths relative to project root
results_folder = f"../results/{project}/"
in_folder = f"../data/infiles/{project}/"


def get_specific_data(in_folder, results_folder):
    """
    Extract task-specific data from sensor files.
    
    This function processes iMotions sensor data to extract:
    - Response times (RT) from stimulus onset to user response
    - Selected AOI (Area of Interest) at time of response
    - Fixation counts during stimulus viewing
    - Accuracy metrics for data quality
    
    Args:
        in_folder: Path to input data directory
        results_folder: Path to output results directory
    
    Returns:
        None (writes results to CSV file)
    """
    task = 'specific'
    in_path = f"{in_folder}Sensors/"
    out_path = f"{results_folder}{task}/"
    os.makedirs(out_path, exist_ok=True)
    
    # Get list of all sensor data files
    files = get_files(in_path)
    # Optional: Process specific files only
    # files = ['002_Resp_064.csv',]
    
    # Store results for all participants
    results = []
    
    # Process each participant file
    for f in files:
        path = f"{in_path}{f}"
        # Read iMotions file and extract metadata
        df, metadata = read_imotions(path, metadata=['Respondent Name', 'Study name'])
        
        # Initialize result dictionary for this participant
        result = {}
        result['file'] = f
        
        # Extract participant ID from metadata
        try:
            result['resp_id_old'] = int(metadata['Respondent Name'].split('_')[1])
        except:
            result['resp_id_old'] = np.nan
        
        # Extract study subset identifier
        try:
            result['subset_old'] = metadata['Study name']
        except:
            result['subset_old'] = np.nan
        
        # Process each stimulus shown to this participant
        for stim, dfs in df.groupby('SourceStimuliName'):
            # Initialize accuracy counter for quality control
            accuracy = 0
            
            # Step 1: Find end of stimulus viewing (Space key press or Shift+Z)
            mask = dfs['Data'].str.contains('Space', na=False)
            if mask.any():
                # Trim data to before Space key press
                dfs = dfs.loc[:mask.idxmax()-1]
                accuracy += 1
            else:
                # Alternative end marker: Shift+Z
                mask = dfs['Data'].str.contains('Shift Z', na=False)
                if mask.any():
                    dfs = dfs.loc[:mask.idxmax()-1]
                    accuracy += 1
                else:
                    print(f"### Could not find Space for {stim} for {result['resp_id_old']}")
            
            # Step 2: Find last mouse click (response selection)
            if accuracy == 1:
                mask = dfs['Data'].str.contains('LBUTTONDOWN', na=False)
                
                if mask.any():
                    # Get index of last click
                    last_idx = mask[::-1].idxmax()
                    # Trim data up to and including last click
                    dfs = dfs.loc[:last_idx]
                    accuracy += 1
                else:
                    print(f"### Could not find Click for {stim} for {result['resp_id_old']}")
                
                # Step 3: Extract metrics if valid response found
                if accuracy == 2:
                        start_time = dfs['Timestamp'].values[0]
                        end_time = dfs['Timestamp'].values[-1]

                        try:
                            if not pd.isna(dfs['Respondent Annotations active'].iloc[-1]):
                                aoi_selected = dfs['Respondent Annotations active'].values[-1].strip(' dwelled on')
                                accuracy += 1
                            else:
                                aoi_selected = dfs['Respondent Annotations active'].dropna().values[-1].strip(' dwelled on')
                        except:
                            aoi_selected = np.nan

                        try:
                            fixation_counts = dfs['Fixation Index by Stimulus'].dropna().values[-1]
                            accuracy += 1
                        except:
                            fixation_counts = np.nan

                        result[f'{stim}_RT']=end_time-start_time
                        result[f'{stim}_AOISelected']=aoi_selected
                        result[f'{stim}_AOIAccuracy']=accuracy
                        result[f'{stim}_FixationCount']=fixation_counts

            results.append(result)

    results = pd.DataFrame(results)
    results.to_csv(f'{out_path}prepared_data.csv')

def get_slides(in_folder,results_folder):
    from itertools import chain
    in_path = f"{in_folder}Sensors/"
    out_path = f"{results_folder}/"
    os.makedirs(out_path, exist_ok=True)   
         
    files = get_files(in_path)
    results = []

    for file in files:
        df,_ = read_imotions(f'{in_path}{file}')
        result= {'Slide':(df['SourceStimuliName'].drop_duplicates().tolist())}
        results.append(pd.DataFrame(result))

    df = pd.concat(results)
    df.to_csv(f'{out_path}stimuli.csv')


def get_times(in_folder,results_folder):
    from itertools import chain
    in_path = f"{in_folder}Sensors/"
    out_path = f"{results_folder}/"
    os.makedirs(out_path, exist_ok=True)   
         
    files = get_files(in_path)
    results = []
    resp_id_key = pd.read_csv(f'{in_folder}Keys/nandos_resp_id_new.csv')

    for file in files:
        df,metadata = read_imotions(f'{in_path}{file}', metadata=['Respondent Name','Study name','Recording time'])
        result={}
        result['sns_filename']=file
        try:
            result['resp_id_old'] = int(metadata['Respondent Name'].split(',')[0].split('_')[1])
        except:
            result['resp_id_old'] = np.nan
        try:
            result['subset_old'] = metadata['Study name'].split(',')[0]
        except:
            result['subset_old'] = np.nan
        try:
            result['imotions_date'] = metadata['Recording time'].split(',')[0].split(': ')[1]
        except:
            result['imotions_date'] = np.nan
        try:
            result['imotions_time'] = metadata['Recording time'].split(',')[1].split(': ')[1].split(' ')[0]
        except:
            result['imotions_time'] = np.nan

        results.append(result)

    df = pd.DataFrame(results)
    df = pd.merge(resp_id_key,df,on=['resp_id_old','subset_old'])


    # ── 1. Build a single timestamp string for iMotions ───────────────────────────
    full_stamp = (
        df["imotions_date"].str.strip() + " " +
        df["imotions_time"].str.strip()
        .str.replace(r"\s+\+\d{2}:\d{2}$", "", regex=True)   # drop “ +02:00” if present
    )

    # ── 2. Pass 1: Try with milliseconds (“%f”) ───────────────────────────────────
    ts_1 = pd.to_datetime(
        full_stamp,
        format="%d/%m/%Y %H:%M:%S.%f",
        errors="coerce",          # rows that lack .### will turn into NaT here
        dayfirst=True
    )

    # ── 3. Pass 2: Fill in the NaT rows with a seconds-only format ────────────────
    need_second_try = ts_1.isna()
    ts_2 = pd.to_datetime(
        full_stamp[need_second_try],
        format="%d/%m/%Y %H:%M:%S",
        errors="coerce",
        dayfirst=True
    )

    df["imotions_ts"] = ts_1.fillna(ts_2)

    # --- 1.  Parse the survey timestamp (US-style, 12-hour clock) ---
    df["survey_ts"] = pd.to_datetime(
        df["survey_immediate_start"],
        format="%m/%d/%Y %I:%M:%S %p",   # 05/19/2025 1:13:53 PM
        errors="coerce"                  # avoids crashing on bad rows
    )

    # --- 2.  Parse the iMotions timestamp ---
    #   a)  Glue the date + time together
    #full_stamp = df["imotions_date"].str.strip() + " " + df["imotions_time"].str.strip()

    # #   b)  Ignore the time-zone offset when converting (keeps it simple)
    # df["imotions_ts"] = pd.to_datetime(
    #     full_stamp.str.replace(r"\s+\+\d{2}:\d{2}$", "", regex=True),
    #     format="%d/%m/%Y %H:%M:%S.%f",   # 19/05/2025 13:06:09.132
    #     errors="coerce",
    #     dayfirst=True
    # )

    one_hour  = pd.Timedelta(hours=1)

    same_date      = df["survey_ts"].dt.date == df["imotions_ts"].dt.date
    within_1_hour  = (df["survey_ts"] - df["imotions_ts"]).abs() <= one_hour

    df["aligned_date"] = same_date
    df["aligned_time"] = within_1_hour


    df=df.drop(['survey_ts','imotions_ts'], axis=1)
    df.to_csv(f'{out_path}imotions_times.csv')


def merge_data(in_folder,results_folder):

    resp_id_key = pd.read_csv(f'{in_folder}Keys/nandos_resp_id_new.csv')
    df = pd.read_csv(f'{results_folder}specific/prepared_data.csv')

    all_cols = [col for col in df.columns if 'Slide' in col]
    cols = [col for col in all_cols if 'Item' not in col]
    item_cols = [col for col in all_cols if 'Item' in col]

    item_rename = {x: f"sns_findSpecific_{x.split(' ')[1]}" for x in item_cols}

    df = df.drop(cols,axis = 1)
    df = df.rename(item_rename, axis =1)
    item_cols = [col for col in df.columns if 'AOISelected' in col]

    # one-liner version -----------------------------------------------------------
    mask = (
        df[item_cols]                                           # just those columns
        .astype("string")                                # force string dtype
        .apply(lambda s:
                ~(~s.str.contains('dwell', case=False)  # has 'dwell'
                & s.str.contains('Item',  case=False)) # but not 'Item'
        )
    )

    # overwrite the offending cells with NA
    df.loc[:, item_cols] = df[item_cols].mask(mask, other=pd.NA)

    df = pd.merge(resp_id_key,df,on=['resp_id_old','subset_old'])

    ###################################

    # fam1 = pd.read_csv(f'{in_folder}FAM/ms_FAM_01.csv')
    # fam2 = pd.read_csv(f'{in_folder}FAM/ms_FAM_02.csv')
    # fam3 = pd.read_csv(f'{in_folder}FAM/Subset1.csv')
    # fam4 = pd.read_csv(f'{in_folder}FAM/Subset2.csv')

    # df_fam = pd.concat([fam1, fam2, fam3, fam4])

    df_fam = pd.read_csv(f'{results_folder}df_fam.csv')

    item_dict = {'Item1':'FAM_10',
                 'Item2':'FAM_18',
                 'Item3':'FAM_61',
                 'Item4':'FAM_11',
                 'Item5':'FAM_31',}
    
    for item, fam in item_dict.items():
        src_col = f"VALUE_{fam}_Question (2)"          # what we’re looking up
        dst_col = f"sns_findSpecific_{item}_subjUndiscovered"

        # Build a Series keyed by resp_id_old just once (O(N)), not per row (O(N²))
        lookup = (
            df_fam.set_index("respondent")[src_col]   # Series: index = id, value = answer
            # .groupby(level=0).first()                # <-- if df_fam has duplicate IDs
        )

        # Vectorised map: unmatched IDs become NaN instead of crashing
        df[dst_col] = df["respondent"].map(lookup)

    #just need to figure out now the last bit of the puzzle
    drop_col = [c for c in df.columns if 'Unnamed' in c]
    df = df.drop(drop_col, axis = 1)

    df1 = df.rename({'file':'sns_filename'}, axis = 1)

    df = pd.read_csv(f'{results_folder}specific/prepared_data.csv')

    #Replace 
    df.columns = (
        df.columns
        .str.replace(r'Slide8 (?:Current1|NewF1|NewU1)',  'sns_findAnything_FrontPage', regex=True)
        .str.replace(r'Slide13 (?:Current2|NewF2|NewU2)', 'sns_findAnything_BackPage',  regex=True)
    )

    collapse_rule = 'sum'          # or a function, e.g. lambda s: s.max(skipna=True)

    # 2️⃣  Fuse columns that share the same header
    df = (
        df                       # your DataFrame with duplicate column names
        .groupby(df.columns, axis=1, sort=False)   # keep original order
        .aggregate(collapse_rule)                  # apply rule
    )

    ##################################

    #just need to figure out now the last bit of the puzzle
    drop_col = [c for c in df.columns if 'Unnamed' in c]
    df = df.drop(drop_col, axis = 1)

    drop_col = [c for c in df.columns if 'file' in c]
    df = df.drop(drop_col, axis = 1)

    drop_col = [c for c in df.columns if 'Slide' in c]
    df = df.drop(drop_col, axis = 1)

    df = df.rename({'file':'sns_filename'}, axis = 1)

    df = pd.merge(df1,df,on=['resp_id_old','subset_old'])
    df.to_csv(f'{results_folder}sensor_uv.csv')


def get_specific_data(in_folder,results_folder):

    # Get files
    # Read info from metadata

    # For each stim:
    # in Data, find space
    # find LBUTTONDOWN before space
    # find current or most recent fixation
    # get fixation count leading up to
    # append per stim

    task = 'anything'
    in_path = f"{in_folder}Sensors/"
    out_path = f"{results_folder}{task}/"
    os.makedirs(out_path, exist_ok=True)   
         
    files = get_files(in_path)
    #files = ['002_Resp_064.csv',]

    
    #Extracting all raw data
    results = []
    ### FOR EACH PARTICIPANT
    for f in files:
        # try: 
            path = f"{in_path}{f}"
            df, metadata = read_imotions(path, metadata=['Respondent Name','Study name'])

            result = {}
            result['file']=f
            try:
                result['resp_id_old'] = int(metadata['Respondent Name'].split('_')[1])
            except:
                result['resp_id_old'] = np.nan
            try:
                result['subset_old'] = metadata['Study name']
            except:
                result['subset_old'] = np.nan

            for stim,dfs in df.groupby('SourceStimuliName'): #For each ad, skip this as data should already be split by ad
                # in Data, find space

                accuracy = 0
                mask = dfs['Data'].str.contains('Space', na=False)
                if mask.any():
                    dfs = dfs.loc[:mask.idxmax()-1]
                    accuracy += 1
                else:
                    mask = dfs['Data'].str.contains('Shift Z', na=False)
                    if mask.any():
                        dfs = dfs.loc[:mask.idxmax()-1]
                        accuracy += 1
                    else:
                        print(f"### Could not find Space for {stim} for {result['resp_id_old']}")
                
                if accuracy == 1:
                    mask = dfs['Data'].str.contains('LBUTTONDOWN', na=False)

                    if mask.any():                                # at least one match exists
                        last_idx = mask[::-1].idxmax()            # index of the last True
                        # ▸ rows up to *and including* the last 'space' row
                        dfs  = dfs.loc[:last_idx]
                        accuracy += 1
                    else:
                        print(f"### Could not find Click for {stim} for {result['resp_id_old']}")

                    if accuracy == 2:
                        start_time = dfs['Timestamp'].values[0]
                        end_time = dfs['Timestamp'].values[-1]

                        try:
                            if not pd.isna(dfs['Respondent Annotations active'].iloc[-1]):
                                aoi_selected = dfs['Respondent Annotations active'].values[-1].strip(' dwelled on')
                                accuracy += 1
                            else:
                                aoi_selected = dfs['Respondent Annotations active'].dropna().values[-1].strip(' dwelled on')
                        except:
                            aoi_selected = np.nan

                        try:
                            fixation_counts = dfs['Fixation Index by Stimulus'].dropna().values[-1]
                            accuracy += 1
                        except:
                            fixation_counts = np.nan

                        result[f'{stim}_RT']=end_time-start_time
                        result[f'{stim}_AOISelected']=aoi_selected
                        result[f'{stim}_AOIAccuracy']=accuracy
                        result[f'{stim}_FixationCount']=fixation_counts

            results.append(result)

    results = pd.DataFrame(results)
    results.to_csv(f'{out_path}prepared_data.csv')


def main():
    #Specific Task
    #get_specific_data(in_folder,results_folder)
    #get_times(in_folder,results_folder)
    merge_data(in_folder,results_folder)

if __name__ == "__main__":
    main()