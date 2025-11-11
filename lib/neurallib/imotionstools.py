
from .clean import * 
from subprocess import call
import re
from scipy.stats import f_oneway
from matplotlib import font_manager
from wordcloud import WordCloud, ImageColorGenerator
from PIL import Image
from nltk.stem import WordNetLemmatizer
import pingouin as pg
import scikit_posthocs as sp
from itertools import permutations
from .stats import get_significance, get_significance_footnote
import warnings

BAR_COLORS = ['lightgrey',
              'lightskyblue',
              'steelblue',
              'slategrey',
              'deepskyblue']


category_keys={'A':'ValueAdd',
                'B':'Premium',
                'C':'Fruit',
                'D':'Everyday'}


def combine_key_file(df: pd.DataFrame, key_path: str, on: str) -> pd.DataFrame:
    """
    Combines data in a key file with a DataFrame.

    Parameters:
    - df: Input DataFrame
    - key_path: Path to the key file
    - on: Column that will be found in both df and key, on which data will be joined

    Returns:
    - pd.DataFrame: Combined DataFrame

    Raises:
    - KeyError: If the 'on' column cannot be found in either the key file or the df
    - Key
    """
    try:
        if on not in df.columns:
            raise KeyError(f"'{on}' column missing from main DataFrame")
        
        key_df = pd.read_csv(key_path).drop_duplicates(subset=on)

        if on not in key_df.columns:
            raise KeyError(f"'{on}' column missing from key file")

        key_cols = [x for x in key_df.columns if x != on]
        df_cols = [x for x in df.columns if x != on]

        if any(item in key_cols for item in df_cols):
            if all(item in key_cols for item in df_cols):
                raise ValueError(f'Key File already merged')
            else:
                duplicates = [item for item in df_cols if item in key_cols]
                warnings.warn(f'Found duplicate {duplicates} columns when merging key file', UserWarning)
                key_cols = [x for x in key_cols if x not in df_cols]

        key_df = key_df[[on,]+key_cols]
        
        return pd.merge(df, key_df, on=on, how='inner')
    except ValueError:
        return df



def get_tool_slides(key_path: str,*, slide_column: str = 'Slide') -> list:
    """
    Combines data in a key file with a DataFrame.

    Parameters:
    - key_path: Path to the key file
    - slide_column: Column that will be found in the key file with the Slide ID

    Returns:
    - list: a list of slides

    Raises:
    - KeyError: If the 'slide_column' column cannot be found in the key file
    """ 
    key_df = pd.read_csv(key_path)
    if slide_column not in key_df.columns:
        raise KeyError(f"'{slide_column}' column missing from key file")  
    return key_df[slide_column].unique().tolist()


class FlashExposure:
    def __init__(self, task: str, in_path: str, out_path: str,*, attribute: str = 'Preference', exposure_time: int = 70, task_key_path: str = None, sample_key_path: str = None): # type: ignore
        self._task = task
        self._in_path = os.path.join(in_path, 'Sensor Data')
        self._out_path = os.path.join(out_path, self._task)
        self._task_key_path = task_key_path
        self._sample_key_path = sample_key_path

        # Data Initialization
        os.makedirs(self._out_path, exist_ok=True)
        print_status('Created Output Directory', self._out_path)
        self._data = pd.DataFrame()
        self._response_slides = get_tool_slides(self._task_key_path)
        self._significance = pd.DataFrame()
        self._results = pd.DataFrame()

        # Flags
        self._data_processed = False

    @property
    def sample_key_path(self):
        return self._sample_key_path
    
    @sample_key_path.setter
    def sample_key_path(self, value):
        self._sample_key_path = value
        self._data_processed = False

    @property
    def task_key_path(self):
        return self._sample_key_path
    
    @task_key_path.setter
    def task_key_path(self, value):
        self._sample_key_path = value
        self._data_processed = False

    @property
    def data(self) -> pd.DataFrame:
        return self._data

    def process_data(self):
        header(f"> Running: {self._task}") 
        
        if self._task_key_path is None:
            raise ValueError("Please define a task_key_path to complete data processing.")
        
        # Get input files
        files = get_files(self._in_path, tags=['.csv'])

        # Initialize working DataFrame
        keep_columns = ['SourceStimuliName', 'Data']
        keyboards = ['Left', 'Right']

        data_list = []

        for file in files:
            path = os.path.join(self._in_path, file)
            respondent = 'Resp' + '_'.join(file.split('Resp')[1:]).split('.')[0]

            df = read_imotions(path)
            df = df[df['SourceStimuliName'].isin(self._response_slides)]
            df = df[keep_columns].dropna()

            df.rename(columns={'SourceStimuliName': 'Slide', 'Data': 'Press'}, inplace=True)

            for key in keyboards:
                key_df = df[df['Press'].str.contains(key, na=False)].copy()
                if not key_df.empty:
                    key_df['Data'] = key
                    key_df['Respondent'] = respondent
                    data_list.append(key_df)
                else:
                    print(f'>> No {key} for {file}')

            print_status('Extracted', path)

        combined_data = pd.concat(data_list, ignore_index=True)

        # Combine with task key attributes
        combined_data = combine_key_file(combined_data, self._task_key_path, 'Slide')

        # Optionally combine with sample key attributes
        if self._sample_key_path is not None:
            combined_data = combine_key_file(combined_data, self._sample_key_path, 'Respondent')

        expanded_data = []

        for _, row in combined_data.iterrows():
            try:
                for direction in ['Right', 'Left']:
                    new_row = row.copy()
                    new_row['Route'] = row[direction]
                    new_row['Chosen'] = int(row['Data'] == row[direction])
                    expanded_data.append(new_row)
            except KeyError:
                pass

        self._data = pd.DataFrame(expanded_data).dropna()
        self._data_processed = True

    def apply_task_attributes(self):
        self._data = combine_key_file(self._data, self._task_key_path, 'Slide')

    def apply_sample_attributes(self):
        if self._sample_key_path:
            self._data = combine_key_file(self._data, self._sample_key_path, 'Respondent')

    def save_processed_data(self):
        self._data.to_excel(f'{self._out_path}{self._task}_Raw.xlsx', index = False)

    def get_results(self):
        '''
        Per C1, R
        Per C1, Per S1, R
        Per C1, Per S2, R
        Per C1, Per S1, Per S2, R
        Per C1, Per S1S2, R
        Per C1, Per C2, R
        Per C1, Per C2, Per S1, R
        Per C1, Per C2, Per S2, R
        Per C1, Per C2, Per S1, Per S2, R
        Per C1, Per C2, Per S1S2, R
        Per R, S1
        Per R, S2
        Per R, S1S2

        '''
        

        


    results = []
    significance = pd.DataFrame()
    
    for r in routes:
        stats_routes = {}
        preference = {}
        for g in groups:
            route = data.loc[data['Shown'].str.contains(r)
                            & (data['Category']==g)]

            route.loc[route['Salient']==r, ['Preferred']] = 1
            route.loc[route['Salient']!=r, ['Preferred']] = 0
            stats_routes[g] = np.array(route['Preferred'])

            ####
            chosen = route['Preferred'].sum() 

            result = dict()
            result['Route'] = r
            result['Proportion'] = chosen/len(route)*100
            result['Type'] = g
            result['Cluster'] = g
            results.append(result)
 
        significance = pd.concat([significance, get_significance(stats_routes, r, groups)])

    results = pd.DataFrame(results)
    results.to_excel(f'{out_path}{task}_PerRoute_Results.xlsx', index = False)
    significance.to_excel(f'{out_path}{task}_PerRoute_Significance.xlsx', index = False)
    significance = significance.drop_duplicates(subset=['Cluster','Groups'])

    x_data = results['Route'].sort_values().drop_duplicates().tolist()
    y_data = dict()
    i = 0

    for cluster in groups:
        _data = results.loc[results['Cluster']==cluster].set_index('Route')
        y_data[cluster] = dict()
        y_data[cluster]['values'] = _data.loc[x_data]['Proportion'].values
        y_data[cluster]['label'] = cluster
        y_data[cluster]['color'] = [route_colors[x] for x in x_data]
        i += 1

    ### Add footnote for significance
    sig = significance.loc[(significance['pValue']<=0.055)]
    footnote,footnoteLines = get_significance_footnote( sig, clusters=True)
    plot.multi_bar(out_path,
                x_data,
                y_data,
                xlabel = '',
                ylabel = 'Percentage Chosen (%)',
                title = f'Implicit Preference and Visual Salience Split By Pack Type',
                ylim = 100,
                footnote = footnote,
                footnoteLines = footnoteLines
                )

    # Split Group
    results = []
    significance = pd.DataFrame()
    
    for g in groups:
        stats_routes = {}
        for r in routes:
            route = data.loc[data['Shown'].str.contains(r)
                            & (data['Category']==g)]

            route.loc[route['Salient']==r, ['Preferred']] = 1
            route.loc[route['Salient']!=r, ['Preferred']] = 0
            stats_routes[r] = np.array(route['Preferred'])
            chosen = route['Preferred'].sum() 

            result = dict()
            result['Route'] = r
            result['Proportion'] = chosen/len(route)*100
            result['Type'] = r
            result['Cluster'] = g
            results.append(result)
                
        significance = pd.concat([significance, get_significance(stats_routes, g, routes)])

    results = pd.DataFrame(results)
    results.to_excel(f'{out_path}{task}_PerGroup_Results.xlsx', index = False)
    significance.to_excel(f'{out_path}{task}_PerGroup_Significance.xlsx', index = False)
    significance = significance.drop_duplicates(subset=['Cluster','Groups'])

    # Overall
    overall_results = []
    significance = pd.DataFrame()
    stats_routes = {}
    for r in routes:
        route = data.loc[data['Shown'].str.contains(r)]
        route.loc[route['Salient']==r, ['Preferred']] = 1
        route.loc[route['Salient']!=r, ['Preferred']] = 0
        stats_routes[r] = np.array(route['Preferred'])

        chosen = route['Preferred'].sum()

        result = dict()
        result['Route'] = r
        result['Proportion'] = chosen/len(route)*100
        result['Type'] = 'Overall'
        result['Cluster'] = 'Overall'
        overall_results.append(result)     
    significance = pd.concat([significance, get_significance(stats_routes,'Overall', routes)])  

    overall_results = pd.DataFrame(overall_results)
    overall_results.to_excel(f'{out_path}{task}_Results.xlsx', index = False)
    significance.to_excel(f'{out_path}{task}_Significance.xlsx', index = False)
    significance = significance.drop_duplicates(subset=['Cluster','pValue'])

    #Plot results
    results = pd.concat([results,overall_results])
    clusters = results['Cluster'].drop_duplicates().tolist()
    for cluster in clusters:
        _data = results.loc[results['Cluster']==cluster]
        _data = _data.sort_values(by='Proportion', ascending = False)
        _x_data = _data['Route']
        _prop_data = _data['Proportion'].values

        ### Add footnote for significance
        sig = significance.loc[(significance['Cluster']==cluster) & (significance['pValue']<=0.055)]
        footnote,footnoteLines = get_significance_footnote(sig)

        plot.bar(out_path,
                    _x_data,
                    _prop_data,
                    bar1_color =[route_colors[x] for x in _x_data],
                    xlabel = '',
                    y1label = 'Implicit Preference and Visual Salience (%)',
                    title = cluster,
                    y1lim = 100,
                    tag = "",
                    footnote = footnote,
                    footnoteLines = footnoteLines
                    )
        
    return None


def get_packNavigation_data(in_folder, results_folder, key_path):
    task = 'Pack Navigation'
    in_path = f"{in_folder}/"
    out_path = f"{results_folder}{task}/"
    os.makedirs(out_path, exist_ok=True)
    
    ###################
    ####################
    #$#################
    ## PLEASE REMOVE FIRST 200ms of EXPOSURE !!!!!!!

    
    files = get_files(in_path)
    
    # Create the necessary data structures
    calc = []
    all_data = pd.DataFrame()
    key_df = pd.read_csv(key_path).drop_duplicates(subset=['Slide'])
    key_dict = key_df.set_index('Slide').to_dict(orient='index')
    slides = key_df['Slide'].drop_duplicates().tolist()
    
    # Extracting all raw data for each participant
    for f in files:
        try:
            path = f"{in_path}{f}"
            df = read_imotions(path)
            df = df[df['SourceStimuliName'].isin(slides)]
            stims = df['SourceStimuliName'].drop_duplicates()

            res = '_'.join(f.split('.csv')[0].split('_')[1:])
            
            for stim in stims:
                _stim = df[df['SourceStimuliName'] == stim]
                aois = _stim['AOIs gazed at'].dropna().unique()
                aois = [a for a in aois if ';' not in a]
                _start_time = _stim.loc[_stim['SlideEvent'] == 'StartMedia', 'Timestamp'].iloc[0]

                for aoi in aois:
                    _aoi = _stim[_stim['AOIs gazed at'] == aoi]
                    _aoi['Timestamp'] -= _start_time
                    _pupil = _aoi[['Row', 'Timestamp', 'Fixation Index', 'Fixation Duration']]
                    _pupil['Stim'] = stim
                    _pupil['Respondent'] = f[:11]

                    fixations = _pupil['Fixation Index'].drop_duplicates().dropna()

                    for fix in fixations:
                        _data = _pupil[_pupil['Fixation Index'] == fix]

                        variant = key_dict[stim]['Variant']
                        brand = key_dict[stim]['Brand']
                        pack = f"{brand}_{variant}"

                        try:
                            aoi_fields = aoi.split('_')
                            aoi_type = aoi_fields[0]
                            aoi_variant = ' '.join(aoi_fields[1:])
                            if aoi_variant.isdigit() and int(aoi_variant) == 0:
                                aoi_variant = 'Main'

                            _calc = {
                                'Res': _data['Respondent'].iloc[0],
                                'Stim': stim,
                                'Variant': variant,
                                'Pack': pack,
                                'Brand': brand,
                                'AOI_Type': aoi_type,
                                'AOI_Variant': aoi_variant,
                                'AOI': aoi,
                                'Timestamp': _data['Timestamp'].iloc[0],
                                'Index': _data['Fixation Index'].iloc[0],
                                'Duration': _data['Timestamp'].iloc[-1] - _data['Timestamp'].iloc[0]
                            }
                            calc.append(_calc)

                        except Exception as e:
                            print(f'>>> Invalid AOI info on {aoi}: {e}')

                print(f">> Completed Collection: {f} ")

        except Exception as e:
            print(f'Error processing file {f}: {e}')
    
    calc_df = pd.DataFrame(calc)
    calc_df.to_excel(f'{out_path}eye_metrics_raw.xlsx', index=False)
    calcs = []

    resps = calc_df['Res'].drop_duplicates()

    # Calculating metrics from raw (FFD and TFD)
    for res in resps:
        _res = calc_df[calc_df['Res'] == res]
        stims = _res['Stim'].drop_duplicates()

        for stim in stims:
            _stim = _res[_res['Stim'] == stim].sort_values('Timestamp')
            aois = _stim['AOI'].dropna().drop_duplicates()

            for aoi in aois:
                _aoi = _stim[_stim['AOI'] == aoi].sort_values('Timestamp')

                variant = key_dict[stim]['Variant']
                brand = key_dict[stim]['Brand']
                pack = f"{variant}_{brand}"

                try:
                    aoi_fields = aoi.split('_')
                    aoi_type = aoi_fields[0]
                    aoi_variant = ' '.join(aoi_fields[1:])
                    if aoi_variant.isdigit() and int(aoi_variant) == 0:
                        aoi_variant = 'Main'

                    _calcs = {
                        'Res': res,
                        'Stim': stim,
                        'Variant': variant,
                        'Pack': pack,
                        'Size': brand,
                        'AOI_Type': aoi_type,
                        'AOI_Variant': aoi_variant,
                        'AOI': aoi,
                        'Timestamp': _aoi['Timestamp'].iloc[0],
                        'Index': _aoi['Index'].iloc[0],
                        'TFD': _aoi['Duration'].sum(),
                        'FFD': _aoi['Duration'].iloc[0]
                    }

                    calcs.append(_calcs)

                except Exception as e:
                    print(f'>>> Invalid AOI info on {aoi}: {e}')

    calcs_df = pd.DataFrame(calcs)
    calcs_df.to_csv(f'{out_path}eye_metrics_final.csv', index=False)

    data = calcs_df

    # Separate numeric columns and non-numeric columns
    numeric_columns = data.select_dtypes(include='number').columns
    non_numeric_columns = data.select_dtypes(exclude='number').columns

    # Perform groupby operation on numeric columns only for AOI
    data_numeric = data.groupby(['AOI'])[numeric_columns].mean()

    # Handle non-numeric columns for AOI
    for col in non_numeric_columns:
        data_numeric[col] = data.groupby('AOI')[col].first()

    data_numeric.reset_index(inplace=True)

    # Save the result to an Excel file for AOI
    data_numeric.to_excel(f'{out_path}RESULT_AOI_Performance.xlsx', index=False)

    # Read the saved AOI performance data
    data = pd.read_excel(f'{out_path}RESULT_AOI_Performance.xlsx')

    # Apply percentiles_df function to AOI data
    data2 = percentiles_df(data, 'AOI', ['TFD', 'FFD'])

    # Save the result to an Excel file for AOI percentiles
    data2.to_excel(f'{out_path}RESULT_AOI_percentiles.xlsx', index=True)

    # Perform groupby operation on numeric columns only for Stim
    data2_numeric = data.groupby(['Stim'])[numeric_columns].sum()

    data2_numeric.reset_index(inplace=True)

    # Apply percentiles_df function to Stim data
    data2_numeric = percentiles_df(data2_numeric, 'Stim', ['TFD'])

    # Save the result to an Excel file for Brand Prominence
    data2_numeric.to_excel(f'{out_path}RESULT_Brand_Prominence.xlsx', index=True)


def get_packNavigation_results(results_folder):
    task = 'Pack Navigation'
    data = pd.read_csv(f"{results_folder}{task}/eye_metrics_final.csv")


    ### For every pack
    metrics = ['TFD','Timestamp']
    out_path = f"{results_folder}{task}/PerPack/"
    os.makedirs(out_path, exist_ok=True) 

    for metric in metrics:
        packs = data['Pack'].drop_duplicates().tolist()

        results = pd.DataFrame()
        significance = pd.DataFrame()
        for pack in packs:
            pack_data = data.loc[(data['Pack']==pack)]
            aois = pack_data['AOI'].drop_duplicates().tolist()
            stats_routes = {}
            plot_data = pd.DataFrame()
            
            for aoi in aois:
                aoi_data = pack_data.loc[(pack_data['AOI']==aoi)].dropna(subset=[metric])
                n_fill = 30-len(aoi_data)

                ###### AGP'
                if metric == 'Timestamp':                   
                    values =  np.concatenate((aoi_data['Timestamp'].values,np.array(n_fill*[3000]))) 
                ###### Salience
                else:
                    values = np.concatenate((aoi_data['TFD'].values,np.array(n_fill*[0])))

                stats_routes[aoi] = values

                result = pd.DataFrame()
                result['Pack']=[pack]
                result['AOI']=[aoi]
                result['Metric']=[metric]
                result['Value']=[values.mean()]

                results = pd.concat([results,result])
                plot_data = pd.concat([plot_data,result])
                                
            significance = pd.concat([significance, get_significance(stats_routes, f'{pack}_{metric}', aois)])
            ### Plot TFD Results
            sig = significance.loc[(significance['Cluster']==f'{pack}_{metric}') & (significance['pValue']<=0.055)]
            footnote,footnoteLines = get_significance_footnote(sig)

            if metric == 'Timestamp':
                x_data = plot_data.sort_values(by='Value',ascending=True)['AOI']
                y1_data= plot_data.set_index('AOI').loc[x_data]['Value'].values

                plot.bar(out_path,
                            x_data,
                            y1_data,
                            bar1_color ='deepskyblue',
                            xlabel = '',
                            y1label = f'Time to First Fixation (ms)',
                            title = f'Attention Grabbing Power of {pack}',
                            tag = "",
                            footnote = footnote,
                            footnoteLines = footnoteLines
                            )
            elif metric == 'TFD':
                x_data = plot_data.sort_values(by='Value',ascending=False)['AOI']
                y1_data= plot_data.set_index('AOI').loc[x_data]['Value'].values

                plot.bar(out_path,
                            x_data,
                            y1_data,
                            bar1_color ='deepskyblue',
                            xlabel = '',
                            y1label = f'Total Fixation Duration (ms)',
                            title = f'Attention Holding Power of {pack}',
                            tag = "",
                            footnote = footnote,
                            footnoteLines = footnoteLines
                            )

        results = results.sort_values(by=['Pack','Value'])   

    ##########

    ### For every pack
    metrics = ['TFD','Timestamp']
    out_path = f"{results_folder}{task}/PerAOIType/"
    os.makedirs(out_path, exist_ok=True) 

    variants = data['Variant'].drop_duplicates().tolist()
    for variant in variants:
        for metric in metrics:
            aoi_types = data['AOI'].drop_duplicates().tolist()

            results = pd.DataFrame()
            significance = pd.DataFrame()
            for aoi_type in aoi_types:
                aoi_type_data = data.loc[(data['AOI']==aoi_type) & 
                                         (data['Variant']==variant)]
                brands = aoi_type_data['Brand'].drop_duplicates().tolist()
                stats_routes = {}
                plot_data = pd.DataFrame()
                
                if len(aoi_type_data)>1:
                    for brand in brands:
                        brand_data = aoi_type_data.loc[(aoi_type_data['Brand']==brand)].dropna(subset=[metric])
                        n_fill = 30-len(brand_data)

                        ###### AGP'
                        if metric == 'Timestamp':                   
                            values =  np.concatenate((brand_data['Timestamp'].values,np.array(n_fill*[3000]))) 
                        ###### Salience
                        else:
                            values = np.concatenate((brand_data['TFD'].values,np.array(n_fill*[0])))

                        stats_routes[brand] = values

                        result = pd.DataFrame()
                        result['Brand']=[brand]
                        result['Variant']= [variant]
                        result['AOI']=[aoi_type]
                        result['Metric']=[metric]
                        result['Value']=[values.mean()]

                        results = pd.concat([results,result])
                        plot_data = pd.concat([plot_data,result])
                                        
                    significance = pd.concat([significance, get_significance(stats_routes, f'{variant}_{metric}_{aoi_type}', brands)])
                    ### Plot TFD Results
                    sig = significance.loc[(significance['Cluster']==f'{variant}_{metric}_{aoi_type}') & (significance['pValue']<=0.055)]
                    footnote,footnoteLines = get_significance_footnote(sig)

                    if metric == 'Timestamp':
                        x_data = plot_data.sort_values(by='Value',ascending=True)['Brand']
                        y1_data= plot_data.set_index('Brand').loc[x_data]['Value'].values

                        plot.bar(out_path,
                                    x_data,
                                    y1_data,
                                    bar1_color ='deepskyblue',
                                    xlabel = '',
                                    y1label = f'Time to First Fixation (ms)',
                                    title = f'Attention Grabbing Power of {aoi_type} for {variant}',
                                    tag = "",
                                    )
                    elif metric == 'TFD':
                        x_data = plot_data.sort_values(by='Value',ascending=False)['Brand']
                        y1_data= plot_data.set_index('Brand').loc[x_data]['Value'].values

                        plot.bar(out_path,
                                    x_data,
                                    y1_data,
                                    bar1_color ='deepskyblue',
                                    xlabel = '',
                                    y1label = f'Total Fixation Duration (ms)',
                                    title = f'Attention Holding Power of {aoi_type} for {variant}',
                                    tag = "",
                                    )
                        
                    
                
            results.to_excel(f'{out_path}ET_{variant}_{metric}_Results.xlsx', index = False)
            significance = significance.drop_duplicates(subset=['Cluster','Groups'])
            significance.to_excel(f'{out_path}ET_{variant}_{metric}_Significance.xlsx', index = False)
 


def shelf_navigation(in_folder,results_folder,task_tag=None,pack_graphs=False): 

    task = 'ShelfNavigation'
    header(f"> Running: {task}")
    
    #Create directories and paths for filesave
    in_path = f"{in_folder}"
    out_path = f"{results_folder}{task}_{task_tag}/"
    os.makedirs(out_path, exist_ok=True)  
    
    #Get input files
    files = get_files(in_path,tags=['.csv',])

    #Intialise working dataframes
    data = pd.DataFrame()
    #keep = ['SourceStimuliName','Computer timestamp']
    AOI_data = pd.DataFrame()
    raw_AOI_data = pd.DataFrame()

    eye = pd.DataFrame()
    col  = ['Res','Slide','AOI','Timestamp','Index','Duration']
    calc = pd.DataFrame(columns = col)
    all_data = pd.DataFrame()

    for f in files:
        path = f"{in_path}{f}"
        df = pd.read_csv(path, header = 1)

        df['SourceStimuliName'] = df['SourceStimuliName'].str.replace('Every Valu','Every+Valu')
        df['SourceStimuliName'] = df['SourceStimuliName'].str.replace('Prem','Premium')

        stims = df['SourceStimuliName'].drop_duplicates()

        for stim in stims: 
            _stim = df[df['SourceStimuliName']== stim]
            #Get list of AOIs viewed by participant 
            aois = _stim['AOIs gazed at'].dropna().drop_duplicates()
            #Get start time
            _stim.to_csv('temp.csv')
            _start_time = _stim.loc[_stim['SlideEvent']=='StartMedia']['Timestamp'].values[0]
            _stim.insert(0, 't', _stim['Timestamp']-_start_time, True)
            _stim = _stim.loc[_stim['t']>=150]
            #Get data per AOI
            for aoi in aois:                    
                #Collect all data for the AOI, adjust the timestamp to start of ad                 
                _aoi = _stim.loc[_stim['AOIs gazed at']==aoi]
                col = ['t','FixIndex']
                _pupil = pd.DataFrame(columns= col)
                _pupil['t']=_aoi['t']
                _pupil['FixIndex']=_aoi['Fixation Index']

                ### FIXATIONS IDENTIFIED BY INDEX
                fixations_list = _pupil['FixIndex'].drop_duplicates().dropna()
                fixations = pd.DataFrame() 
                if len(fixations_list):
                    #For each fixation
                    for fix in fixations_list:                       
                        _data = _pupil.loc[_pupil['FixIndex']==fix]
                        duration = _data['t'].iloc[-1]-_data['t'].iloc[0]
                        if (duration > 150) and (duration <900):
                            result = {}
                            result['Start'] = _data['t'].values[0]
                            result['Duration'] = duration
                            fixations = fixations.append(result, ignore_index=True)
                if len(fixations):
                    result = {}
                    fields = aoi.split('_')
                    fields[5] = fields[5][:2]
                    result['ID']=aoi
                    result['Respondent']=f
                    result['Route']=fields[1]
                    result['Category']=fields[2]
                    result['Variant']=fields[3]
                    result['AOI']= fields[4]
                    result['Instance']=fields[5]
                    result['Pack']=fields[5]
                    result['TTFF']=fixations['Start'].values[0]
                    result['TFD']=fixations['Duration'].sum()
                    result['FFD']=fixations['Duration'].values[0]
                    AOI_data = AOI_data.append(result, ignore_index=True)
                    raw_AOI_data = raw_AOI_data.append(result, ignore_index=True)       

                #BY THE END OF THIS, WE HAVE A TABLE WITH A ROW ENTRY FOR EACH FIXATION OF EACH PARTICIPANT
        print_status('Extracted',path)
    
    data = pd.DataFrame()
    for i, ID in raw_AOI_data.groupby(['ID']):
        result = ID.iloc[0].to_dict()
        result['TTFF']=ID['TTFF'].mean()
        result['TFD']=ID['TFD'].mean()
        result['FFD']=ID['FFD'].mean()
        result['Count']=len(ID)
        data = data.append(result, ignore_index=True)

    ## We need raw_AOI_data
    ## We need AOI_data
    raw_AOI_data.to_excel(f'{out_path}{task}_Raw.xlsx', index = False)
    data.to_excel(f'{out_path}{task}_Results.xlsx', index = False)
    
    #Initialise results dataframes
    results = pd.DataFrame()
    significance = pd.DataFrame()

    #Do calcs per route
    significance = pd.DataFrame()
    routes = data['Route'].drop_duplicates().tolist()

    AOIs = raw_AOI_data['AOI'].drop_duplicates().tolist()
    AOI_Results = pd.DataFrame()
    variants = raw_AOI_data['Variant'].drop_duplicates().tolist()

    for v in variants:
        plot_data = pd.DataFrame()
        stats_routes_TFD = {}
        stats_routes_FFD = {}
        stats_routes_TTFF = {}
        for r in routes:
            route = raw_AOI_data.loc[(raw_AOI_data['Route']==r) & (raw_AOI_data['Variant']==v)]
            stats_routes_TFD[r] = route['TFD']
            stats_routes_FFD[r] = route['FFD']
            stats_routes_TTFF[r] = route['TTFF']
            result = {}
            result['Route'] = r
            result['TFD'] = route['TFD'].mean()
            result['FFD'] = route['FFD'].mean()
            result['TTFF'] = route['TTFF'].mean()
            result['Variant'] = v
            plot_data = plot_data.append(result,ignore_index=True)
            AOI_Results = AOI_Results.append(result,ignore_index=True)
        significance = pd.concat([significance, get_significance(stats_routes_TFD, routes,f'{v}_TFD')])
        significance = pd.concat([significance, get_significance(stats_routes_FFD, routes,f'{v}_FFD')])
        significance = pd.concat([significance, get_significance(stats_routes_TTFF, routes,f'{v}_TTFF')])
        significance = significance.drop_duplicates(subset=['Cluster','pValue'])

        ### Add footnote for significance
        sig = significance.loc[(significance['Cluster']==f'{v}_TFD') & (significance['pValue']<=0.055)]
        footnote,footnoteLines = get_significance_footnote(sig)
        _x_data = plot_data['Route']
        _prop_data = plot_data['TFD'].values
        plot.bar(out_path,
                    _x_data,
                    _prop_data,
                    bar1_color ='deepskyblue',
                    xlabel = '',
                    y1label = 'Average Total Fixation Duration (ms)',
                    title = f'Visual Hierarchy of {v}',
                    tag = "",
                    footnote = footnote,
                    footnoteLines = footnoteLines
                    )

        sig = significance.loc[(significance['Cluster']==f'{v}_FFD') & (significance['pValue']<=0.055)]
        footnote,footnoteLines = get_significance_footnote(sig)
        _prop_data = plot_data['FFD'].values
        plot.bar(out_path,
                    _x_data,
                    _prop_data,
                    bar1_color ='deepskyblue',
                    xlabel = '',
                    y1label = 'Average First Fixation Duration (ms)',
                    title = f'Attention Holding Power of {v}',
                    tag = "",
                    footnote = footnote,
                    footnoteLines = footnoteLines
                    )

        sig = significance.loc[(significance['Cluster']==f'{v}_TTFF') & (significance['pValue']<=0.055)]
        footnote,footnoteLines = get_significance_footnote(sig)
        _prop_data = plot_data['TTFF'].values
        plot.bar(out_path,
                    _x_data,
                    _prop_data,
                    bar1_color ='deepskyblue',
                    xlabel = '',
                    y1label = 'Average Time to First Fixation (ms)',
                    title = f'Attention Grabbing Power of {v}',
                    tag = "",
                    footnote = footnote,
                    footnoteLines = footnoteLines
                    )

        categories = raw_AOI_data['Category'].drop_duplicates().tolist()

        for c in categories:
            plot_data = pd.DataFrame()
            stats_routes_TFD = {}
            stats_routes_FFD = {}
            stats_routes_TTFF = {}
            for r in routes:
                route = raw_AOI_data.loc[(raw_AOI_data['Route']==r) & (raw_AOI_data['Variant']==v) & (raw_AOI_data['Category']==c)]
                stats_routes_TFD[r] = route['TFD']
                stats_routes_FFD[r] = route['FFD']
                stats_routes_TTFF[r] = route['TTFF']
                result = {}
                result['Route'] = r
                result['TFD'] = route['TFD'].mean()
                result['FFD'] = route['FFD'].mean()
                result['TTFF'] = route['TTFF'].mean()
                result['Variant'] = v
                result['Category'] = c
                plot_data = plot_data.append(result,ignore_index=True)
                AOI_Results = AOI_Results.append(result,ignore_index=True)
            significance = pd.concat([significance, get_significance(stats_routes_TFD, routes,f'{v}_{c}_TFD')])
            significance = pd.concat([significance, get_significance(stats_routes_FFD, routes,f'{v}_{c}_FFD')])
            significance = pd.concat([significance, get_significance(stats_routes_TTFF, routes,f'{v}_{c}_TTFF')])
            significance = significance.drop_duplicates(subset=['Cluster','pValue'])

            ### Add footnote for significance
            sig = significance.loc[(significance['Cluster']==f'{v}_{c}_TFD') & (significance['pValue']<=0.055)]
            footnote,footnoteLines = get_significance_footnote(sig)
            _x_data = plot_data['Route']
            _prop_data = plot_data['TFD'].values
            plot.bar(out_path,
                        _x_data,
                        _prop_data,
                        bar1_color ='deepskyblue',
                        xlabel = '',
                        y1label = 'Average Total Fixation Duration (ms)',
                        title = f'Visual Hierarchy of {v}-{c}',
                        tag = "",
                        footnote = footnote,
                        footnoteLines = footnoteLines
                        )

            sig = significance.loc[(significance['Cluster']==f'{v}_{c}_FFD') & (significance['pValue']<=0.055)]
            footnote,footnoteLines = get_significance_footnote(sig)
            _prop_data = plot_data['FFD'].values
            plot.bar(out_path,
                        _x_data,
                        _prop_data,
                        bar1_color ='deepskyblue',
                        xlabel = '',
                        y1label = 'Average First Fixation Duration (ms)',
                        title = f'Attention Holding Power of {v}-{c}',
                        tag = "",
                        footnote = footnote,
                        footnoteLines = footnoteLines
                        )

            sig = significance.loc[(significance['Cluster']==f'{v}_{c}_TTFF') & (significance['pValue']<=0.055)]
            footnote,footnoteLines = get_significance_footnote(sig)
            _prop_data = plot_data['TTFF'].values
            plot.bar(out_path,
                        _x_data,
                        _prop_data,
                        bar1_color ='deepskyblue',
                        xlabel = '',
                        y1label = 'Average Time to First Fixation (ms)',
                        title = f'Attention Grabbing Power of {v}-{c}',
                        tag = "",
                        footnote = footnote,
                        footnoteLines = footnoteLines
                        )
    
    AOI_Results.to_excel(f'{out_path}{task}_AOI_Results.xlsx', index = False)
    
    if pack_graphs:
        for r in routes:
            route = data.loc[data['Route']==r]
            categories = route['Category'].drop_duplicates().tolist()
            for c in categories:
                category = route.loc[route['Category']==c]
                variants = category['Variant'].drop_duplicates().tolist()   
                for v in variants:
                    variant = category.loc[category['Variant']==v]
                    AOIs = variant['AOI'].drop_duplicates().tolist()
                    #stats_AOIs= {}
                    plot_data = pd.DataFrame()
                    for a in AOIs:
                        #AOI = raw_AOI_data.loc[(raw_AOI_data['Route']==r) & (raw_AOI_data['Category']==c) & (raw_AOI_data['Variant']==v) & (raw_AOI_data['AOI']==a)]
                        #stats_AOIs[a] = AOI['TTFF']
                        AOI = variant.loc[variant['AOI']==a]
                        result = {}
                        result['AOI'] = a
                        result['FFD'] = AOI['FFD'].values[0]
                        result['TTFF']= AOI['TTFF'].values[0]
                        result['Count']= AOI['Count'].values[0]
                        plot_data = plot_data.append(result,ignore_index=True) 
                    #significance = pd.concat([significance, get_significance(stats_AOIs, AOIs, f'TTFF for {r} {c} {v}')])
                
                    plot_data = plot_data.sort_values(by=['TTFF'])
                    x_data = plot_data['AOI'].tolist()
                    TTFF = plot_data['TTFF'].values
                    FFD = plot_data['FFD'].values
                    Count = plot_data['Count'].values

                    plot.double_bar(out_path,
                            x_data,
                            TTFF,
                            FFD,
                            bar1_color ='lightgrey',
                            bar2_color ='deepskyblue',
                            xlabel = '',
                            ylabel = 'Time (ms)',
                            y1label = 'Time to First Fixation',
                            y2label = 'First Fixation Duration',
                            title = f"Pack navigation for {c} {v} in {r}",
                            )

                    plot.bar_bar_line(out_path,
                            x_data,
                            TTFF,
                            FFD,
                            Count,
                            bar1_color ='lightgrey',
                            bar2_color ='steelblue',
                            line_color='deepskyblue',
                            xlabel = '',
                            yax1label = 'Duration (s)',
                            yax2label = '',
                            y1label= 'Time to First Fixation',
                            y2label= 'First Fixation Duration',
                            y3label= 'Seen By',
                            title = f"Pack navigation for {c} {v} in {r}",
                            tag = 'line'
                            )

        categories = data['Category'].drop_duplicates().tolist()
        for c in categories:
            category = data.loc[data['Category']==c]
            variants = category['Variant'].drop_duplicates().tolist()   
            for v in variants:
                variant = category.loc[category['Variant']==v]
                AOIs = variant['AOI'].drop_duplicates().tolist()
                for a in AOIs:
                    aoi = variant.loc[variant['AOI']==a]
                    routes = aoi['Route'].drop_duplicates().tolist()
                    stats_routes= {}
                    plot_data = pd.DataFrame()
                    for r in routes:
                        route = raw_AOI_data.loc[(raw_AOI_data['Route']==r) & (raw_AOI_data['Category']==c) & (raw_AOI_data['Variant']==v) & (raw_AOI_data['AOI']==a)]
                        stats_routes[r] = route['TFD']
                        route = aoi.loc[aoi['Route']==r]
                        result = {}
                        result['Route'] = r
                        result['FFD'] = route['FFD'].values[0]
                        result['TTFF']= route['TTFF'].values[0]
                        result['Count']= route['Count'].values[0]
                        plot_data = plot_data.append(result,ignore_index=True) 
                    significance = pd.concat([significance, get_significance(stats_routes, routes, f'TTFF for {a} {c} {v}')])
                
                    x_data = plot_data['Route'].tolist()
                    TTFF = plot_data['TTFF'].values
                    FFD = plot_data['FFD'].values
                    Count = plot_data['Count'].values

                    plot.double_bar(out_path,
                            x_data,
                            TTFF,
                            FFD,
                            bar1_color ='lightgrey',
                            bar2_color ='deepskyblue',
                            xlabel = '',
                            ylabel = 'Time (ms)',
                            y1label = 'Time to First Fixation',
                            y2label = 'First Fixation Duration',
                            title = f"Pack navigation for {a} on {c} {v}",
                            )

                    plot.bar_bar_line(out_path,
                            x_data,
                            TTFF,
                            FFD,
                            Count,
                            bar1_color ='lightgrey',
                            bar2_color ='steelblue',
                            line_color='deepskyblue',
                            xlabel = '',
                            yax1label = 'Duration (s)',
                            yax2label = '',
                            y1label= 'Time to First Fixation',
                            y2label= 'First Fixation Duration',
                            y3label= 'Seen By',
                            title = f"Pack navigation for {a} on {c} {v}",
                            tag = 'line'
                            )

    significance.to_excel(f'{out_path}{task}_Significance.xlsx', index = False)
    significance = significance.drop_duplicates(subset=['Cluster','pValue'])
    return None


def top_down_preferance(in_folder,results_folder,task_tag=None,keyboards = None, key_path=None): 

    task = 'TopDownPreference'
    header(f"> Running: {task}")
    
    #Create directories and paths for filesave
    in_path = f"{in_folder}Raw/"
    key_path = f"{in_folder}Keys/{key_path}"
    out_path = f"{results_folder}{task}{task_tag}/"
    os.makedirs(out_path, exist_ok=True)  
    
    #Get input files
    files = get_files(in_path,tags=['.csv',])

    #Intialise working dataframes
    keyboard_data = pd.DataFrame()
    keyboard_keep = ['Presented Stimulus name', 'Event', 'Event value']
    keep = ['Presented Stimulus name', 'Event', 'Event value','Computer timestamp']
    AOI_data = pd.DataFrame()
    raw_AOI_data = pd.DataFrame()
    

    for f in files:
        path = f"{in_path}{f}"
        df = pd.read_csv(path)
        df.rename(columns=lambda s: s.replace("bioDegradable", "biodegradable"), inplace=True)
        df.rename(columns=lambda s: s.replace("T4_T5_recyclable_00", "T4_R5_recyclable_00"), inplace=True)
        df.rename(columns=lambda s: s.replace("T4_T4_natural_00", "T4_R4_natural_00"), inplace=True)
        df = df.replace(to_replace='Slide229_2',value='Slide229')
        df = df.replace(to_replace='Slide240_2',value='Slide240')
        df_choice = df[keyboard_keep]
        
        #Get shifted stimulus column
        df_choice.insert(0, 'Slide', df_choice['Presented Stimulus name'].shift(1), True)
        df_choice = df_choice[['Event value','Slide']].dropna()

        #Get rows for this task only
        for k in keyboards:
            result = df_choice.loc[(df_choice['Event value']==k)]
            result = result.loc[df_choice['Slide'].str.contains('Slide')]
            result['Respondent']=f
            keyboard_data = pd.concat([keyboard_data, result])
        
        ##For each aoi, get FFD and TTFF
        #AOI_cols = [c for c in df.columns if 'AOI' in c]
        #AOI_cols = [c for c in AOI_cols if task_tag in c]

        #for c in AOI_cols:
        #    data = df[keep+[c,]].dropna(subset=[c,])
        #    try:
        #        start_time = data['Computer timestamp'].values[0]
        #        data.insert(0, 't', data['Computer timestamp']-start_time, True)
        #        data = data.loc[data['t']>=150]
        #        fixation_count = 0
        #        fixations = pd.DataFrame()
        #        for i, event in data.groupby([(data[c] != data[c].shift()).cumsum()]):
        #            if event[c].sum():
        #                duration = event.t.values[-1]-event.t.values[0]
        #                if (duration > 150) and (duration <900):
        #                    result = {}
        #                    result['Start'] = event.t.values[0]
        #                    result['Duration'] = duration
        #                    fixations = fixations.append(result, ignore_index=True)
        #        if len(fixations):
        #            result = {}
        #            fields = c.split(task_tag)[1][:-1]
        #            fields = fields.split('_')
        #            result['ID']=c
        #            result['Slide'] = int(c.split('Slide')[1].split(' ')[0])
        #            result['Respondent']=f
        #            result['Goal']=fields[2]
        #            result['AOI']= fields[1]
        #            result['Instance']=fields[3]
        #            result['TTFF']=fixations['Start'].values[0]
        #            result['TFD']=fixations['Duration'].sum()
        #            result['FFD']=fixations['Duration'].values[0]
        #            AOI_data = AOI_data.append(result, ignore_index=True)
        #            raw_AOI_data = raw_AOI_data.append(result, ignore_index=True)
        #    except Exception as z:
        #        print_status(f'No Fixation Data',f"{c} - {z!r}")

        print_status('Extracted',path)
    
    keyboard_data.to_excel(f'{out_path}{task}_Keyboard_Raw.xlsx', index = False)
    #Aggeragate AOI Data
    isAOIData = True if len(AOI_data) else False
    
    if isAOIData:
        AOI_mean_data = pd.DataFrame()
        for i, ID in AOI_data.groupby(['ID']):
            result = ID.iloc[0].to_dict()
            result['TTFF']=ID['TTFF'].mean()
            result['TFD']=ID['TFD'].mean()
            result['FFD']=ID['FFD'].mean()
            result['Count']=len(ID)
            AOI_mean_data = AOI_mean_data.append(result, ignore_index=True)

    #Get key file
    keys = pd.read_csv(key_path)
    slides = keys['Slide Number'].tolist()

    for index, row in keyboard_data.iterrows():
        #Get slide number
        slide = int(row['Slide'][5:].split(' ')[0])
        if slide in slides:
            choice = row['Event value']
            #Get preference
            info = keys.loc[keys['Slide Number']==slide]
            keyboard_data.loc[index, 'Choice'] = info[choice].values[0]
            keyboard_data.loc[index, 'Goal'] = info['Goal'].values[0]
            keyboard_data.loc[index, 'Category'] = info['Category'].values[0]
            
            res = row['Respondent']
            if isAOIData:
                AOI = AOI_mean_data.loc[(AOI_mean_data['Respondent']==res) & (AOI_mean_data['Slide']==slide)]
                keyboard_data.loc[index, 'Highest_TFD'] = AOI.loc[AOI['TFD'].idxmax()]['AOI'] if len(AOI) else np.nan
                keyboard_data.loc[index, 'Lowest_TFD'] = AOI.loc[AOI['TFD'].idxmin()]['AOI'] if len(AOI) else np.nan
                keyboard_data.loc[index, 'Highest_FFD'] = AOI.loc[AOI['FFD'].idxmax()]['AOI'] if len(AOI) else np.nan
                keyboard_data.loc[index, 'Lowest_TTFF'] = AOI.loc[AOI['TTFF'].idxmin()]['AOI'] if len(AOI) else np.nan

            shown = str()
            for k in keyboards:
                _shown = info[k].values[0] 
                shown = shown + _shown if _shown is not np.nan else shown
            keyboard_data.loc[index, 'Shown'] = shown

    keyboard_data = keyboard_data.dropna(subset=['Goal'])   

    keyboard_data.to_excel(f'{out_path}{task}_Keyboard_Results.xlsx', index = False)
    
    if isAOIData:
        raw_AOI_data.to_excel(f'{out_path}{task}_Fixation_Raw.xlsx', index = False)
        AOI_mean_data.to_excel(f'{out_path}{task}_Fixation_Results.xlsx', index = False)
        keyboard_data[['Choice','Highest_TFD','Lowest_TFD','Highest_FFD','Lowest_TTFF']].apply(lambda x: x.factorize()[0]).corr().to_excel(f'{out_path}{task}_Fixation_Choice_Correlation.xlsx', index = False)
    
    #Initialise results dataframes
    results = pd.DataFrame()
    significance = pd.DataFrame()
    
    routes = []
    for k in keyboards:
        _k = keys[k].drop_duplicates().dropna().tolist()
        routes = routes + _k
    routes = get_unique(routes)

    #Do calcs per route
    significance = pd.DataFrame()
    stats_routes = {}

    goals = keyboard_data['Goal'].drop_duplicates().tolist()

    for g in goals:
        if isAOIData:
            goal_AOI = AOI_mean_data.loc[AOI_mean_data['Goal']==g]
        goal = keyboard_data.loc[keyboard_data['Goal']==g]
        
        stats_routes = {}
        for r in routes:
            route = goal.loc[goal['Shown'].str.contains(r)]
            route.loc[route['Choice']==r, ['Preferred']] = 1
            route.loc[route['Choice']!=r, ['Preferred']] = 0
            stats_routes[r] = route['Preferred']
            chosen = sum(route['Preferred'])

            result = dict()
            result['Route'] = r
            result['Chosen'] = chosen/len(route)*100
            result['Goal'] = g

            if isAOIData:
                AOI = AOI_mean_data.loc[(AOI_mean_data['Goal']==g) & (AOI_mean_data['AOI']==r)]
                AOI = AOI_mean_data.loc[(AOI_mean_data['Goal']==g) & (AOI_mean_data['AOI']==r)]['TFD'].values[0] if len(AOI) else 0
                result['TFD'] = AOI
            results = results.append(result,ignore_index = True)     
        significance = pd.concat([significance, get_significance(stats_routes, routes, g)])  

    results.to_excel(f'{out_path}{task}_Results.xlsx', index = False)
    significance.to_excel(f'{out_path}{task}_Significance.xlsx', index = False)
    significance = significance.drop_duplicates(subset=['Cluster','pValue'])

    #Plot results
    clusters = results['Goal'].drop_duplicates().tolist()
    for cluster in clusters:
        _data = results.loc[results['Goal']==cluster].sort_values(by='Route')
        _x_data = _data['Route']
        _prop_data = _data['Chosen'].values

        ### Add footnote for significance
        sig = significance.loc[(significance['Cluster']==cluster) & (significance['pValue']<=0.055)]
        footnote,footnoteLines = get_significance_footnote(sig)
        plot.bar(out_path,
                    _x_data,
                    _prop_data,
                    bar1_color ='deepskyblue',
                    xlabel = '',
                    y1label = 'Percentage Chosen (%)',
                    title = cluster,
                    y1lim = 100,
                    tag = "",
                    footnote = footnote,
                    footnoteLines = footnoteLines
                    )
    
    results = results.sort_values(by='Route')
    x_data = results['Route'].drop_duplicates()
    y_data = dict()
    i = 0

    for cluster in clusters:
        _data = results.loc[results['Goal']==cluster].sort_values(by='Route')
        y_data[cluster] = dict()
        y_data[cluster]['values'] = _data['Chosen'].values
        y_data[cluster]['label'] = cluster
        y_data[cluster]['bar_color'] = BAR_COLORS[i]
        i += 1

    ### Add footnote for significance
    sig = significance.loc[(significance['pValue']<=0.055)]
    footnote,footnoteLines = get_significance_footnote( sig, clusters=True)
    plot.multi_bar(out_path,
                x_data,
                y_data,
                xlabel = '',
                ylabel = 'Percentage Chosen (%)',
                title = 'Combined Choice Results',
                ylim = 100,
                footnote = footnote,
                footnoteLines = footnoteLines
                )
        
    return None


def wordcloud(in_folder,results_folder):
    ######### Define some parameters #####
    font = 'Century Gothic'
    background_color = 'white'
    colormap='Blues'
    width=800
    height=400
    #####################################
    font_manager.findSystemFonts(fontpaths=None, fontext="ttf")
    font_path=font_manager.findfont(font) # Test with "Special Elite" too
   
    task = 'WordCloud'
    header(f"> Running: {task}")
    
    #Create directories and paths for filesave
    in_path = f"{in_folder}SelfReport/"
    out_path = f"{results_folder}{task}/"
    os.makedirs(out_path, exist_ok=True)  
    
    #Get input files
    files = get_files(in_path,tags=['.csv',])
    
    for f in files:
        #Header row 0
        path = f"{in_path}{f}"
        data = pd.read_csv(path, delimiter=',')

        #tasks = data['Task'].drop_duplicates().tolist()
        #for t in tasks:
        #    task = data.loc[data['Task']==t]
        #    goals = task['Goal'].drop_duplicates().tolist()
        #    for g in goals:
        #        goal = task.loc[task['Goal']==g]
        #        routes = goal['Route'].drop_duplicates().tolist()
        #        for r in routes:
        #            route = goal.loc[goal['Route']==r]
        #            #Exclude first column
        #            words = flatten([r.split(' ') for r in route['SelfReport'].tolist()])       
        #            words = ' '.join(words)
   
        #            wc = WordCloud(font_path=font_path, colormap=colormap, background_color=background_color,width=width,height=height).generate_from_text(words)
        
        #            plt.figure(figsize=(20,10))
        #            plt.imshow(wc)
        #            plt.axis('off')
        #            plt.savefig(f'{out_path}T{int(t)}_{g}_{r}.png', dpi=300, transparent=True)
        #            plt.close()
        #            print_status('Completed',f'T{int(t)}_{g}_{r}')
        
        routes = data['Route'].drop_duplicates().dropna().tolist()
        route_words = dict()
        for r in routes:
            route = data.loc[data['Route']==r]
            #Exclude first column
            
            words = flatten([r.split(' ') for r in route['SelfReport'].tolist()])       
            words = ' '.join(words)
            route_words[r]=words.split(' ')
            #wc = WordCloud(font_path=font_path, colormap=colormap, background_color=background_color,width=width,height=height).generate_from_text(words)
        
            #plt.figure(figsize=(20,10))
            #plt.imshow(wc)
            #plt.axis('off')
            #plt.savefig(f'{out_path}{r}.png', dpi=300, transparent=True)
            #plt.close()
            #print_status('Completed',f'{r}')
        
        unique_words=dict()
        for r in routes:
            other = [o for o in routes if o!=r]
            unique_words[r]=route_words[r]
            for o in other:
                print(len(unique_words[r]))
                unique_words[r] = [w for w in unique_words[r] if w not in route_words[o]]
                print(len(unique_words[r]))
            words = ' '.join(unique_words[r])
            wc = WordCloud(font_path=font_path, colormap=colormap, background_color=background_color,width=width,height=height).generate_from_text(words)
        
            plt.figure(figsize=(20,10))
            plt.imshow(wc)
            plt.axis('off')
            plt.savefig(f'{out_path}Only_in_{r}.png', dpi=300, transparent=True)
            plt.close()
            print_status('Completed',f'{r}')


def memoryEncoding(in_folder,results_folder,task_tag=None):
    pass

def main():
    pass

if __name__ == "__main__":
    main()