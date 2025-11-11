from neurallib.clean import * 

'''
    Terminology:
        - Ad-Batch: A batch of adverts that are tested together in a single study. Approximately 20+ ads are usually tested together
            Ad viewing order in an Ad-Batch is randomised per participant, therefore absolute time at which each ad is viewed will 
            vary from participant to participant

    Data types:
        - Brain state metrics
        - Eye tracking metrics
    
    The current overall workflow is such:
        0. Currently, iMotions merges all data from the Ad-Batch into 1 file per respondent. So for an Ad-Batch where 20 ads are tested on 30 respondents, there will be 30 files (RespXX.csv),
            where each file data for every Ad in the Ad-Batch.

            SPLIT FILES:
                Data is split into per ad data. From 30 input files, 600 output files are generated
                    Ad_Name/RespXX.csv
                    
            DB Solve --> Just one file is uploaded, containing all ads and all respondents
        1. INPUT FILES: 
            1 file per respondent per Ad, stored in the following format:
                Ad_Name/RespXX.csv - Raw Data

            This file contains the following columns:
                Row, (data row index)
                Timestamp, (used for timing, data alignment and scene mapping)
                SlideEvent, (used to identify start time)
                Frontal Alpha Asymmetry, (containing alpha data at 0.5Hz)
                High Engagement, (containing Engagment data at 1Hz)
                Workload Average, (containing Workload data at 1Hz)
                Fixation Index, (fixation number for this particular stim)
                Fixation Duration, (how long the fixation was)
                SourceStimuliName, (used to identify Ad)
                AOIs gazed at (used to identify AOIs and which of them were gazed at)

            #### Cannot merge files for some experiments. Respondent data may be available 

            Ad_Name/Scenes.csv - Scene Information
            This file should contain the following columns:
                Ad,
                Scene, (will contain ( Scene1, Scene2...SeceneN ) as well as 'Stopping Power', 'Closing Power' and 'Brand Connection')
                Start Time,
                Stop Time

            Config/Core_Metric.csv - core metric algorithm variables
                This file should contain the key:value pairs:
                ra: [reliability constant for alpha ranging from 0 to 1], (default to 1)
                ka: [weighting constant for alpha ranging from 0 to 1], (default to 1/3)
                t0a: [start time for alpha calculation values] (defaulted to Scenes['Start Time']['Brand Connection'])
                tfa: [end time for alpha calculation values] (defaulted to Scenes['Stop Time']['Brand Connection'])

                re: [reliability constant for engagement ranging from 0 to 1], (default to 1)
                ke: [weighting constant for engagement ranging from 0 to 1], (default to 1/3)
                t0e: [start time for engagement calculation values] (defaulted to 0)
                tfe: [end time for engagement calculation values] (defaulted to end of ad)

                rw: [reliability constant for workload ranging from 0 to 1], (default to 1)
                kw: [weighting constant for workload ranging from 0 to 1], (default to 1/3)
                t0w: [start time for workload calculation values] (defaulted to 0)
                tfw: [end time for workload calculation values] (defaulted to end of ad)

                    

        2. CLEAN FILES:
            Replace -9999 with space
            Replace spaces with NA
            Drop NA 

            DB Solve --> Dont import eroneous data

            Add following columns per respondent:
                Scene Active,
                Stopping Power,
                Closing Power,
                Brand Connection,

            DB Solve--> Use Scene Table to filter data dynamically
            OUTPUT0 --> Time series of Alpha, Eng and WL proportions (per ad per respondent )

        3. MERGE ALL DATA PER AD FROM ALL RESPONDENTS
            Ad_Name/ALL_DATA.csv (per ad)
            DB Solve --> Filter based on StimuliID

        4. PROCESS DATA (using ALL_DATA)

            4.1. TIME SERIES

                4.1.1 BIN DATA
                    Because readings are not taken at the exact same timestamp, we have to bin data in order to approximate averages as a function of time
                    Per Bin (increment of time,t):
                        - Calculate proportions for Alpha (average value for Frontal Asymmetry Alpha)
                        ##### UPDATE TO AVERAGES
                        - Calculate proportions for High Engagement (average value of High Engagement)
                        - Calculate proportions for Optimal WL (Low, Optimal, Overworked) (proportion of total values that are between 0.4 and 0.6, (COUNTIF(>0.4 AND <0.6)/COUNT)
                    OUTPUT1 --> Proportion vs Time series of Alpha, Eng and WL proportions (per ad)

                4.1.2 PLOT TIME SERIES
                    Apply low pass filter to OUTPUT1
                    DB Solve:
                        
                    At t =0:
                           x_f = x*C 
                    At t>0:
                        x_f = x_fp + C*(x-x_fp)

                        where C is a constant = (2*pi*T*f)/(2*pi*T*f+1), and T is the sampling period and f is the filter frequency

                    Plot all data on one graph


            4.2 SCENE DATA (using ALL_DATA)
                
                4.2.1 For each scene ( Scene1, Scene2...SeceneN ) as well as 'Stopping Power', 'Closing Power' and 'Brand Connection':
                    - Calculate proportions for Alpha (proportion of total values that are positive, (COUNTIF+/COUNT))
                    - Calculate proportions for High Engagement (average value of High Engagement)
                    - Calculate proportions for Optimal WL (proportion of total values that are between 0.4 and 0.6, (COUNTIF(>0.4 AND <0.6)/COUNT)
                OUTPUT2 --> Proportions as a function Scene for Alpha, Eng and WL (per ad)

                ### ADD IN TOTAL SCORE (AVERAGE of a,e,wl)

            4.3 OVERALL SCORES (using ALL_DATA) (AD NEURO SCORE)
                
                For x in [a, e, w]:
                    - Calculate proportions from t0x to tfx

                CM = ra*ka*Frontal Asymmetry Alpha + re*ke*High Engagement + rw*kw*Workload Average


                OUTPUT3 --> Total Actual Score (a,e,w,CM) (per ad)

                

            4.4 PERCENTILES
                
                4.5.1 SCENE SCORES (using OUTPUT2 for all ads)
                    For ad in Ads
                        For ad_x in [Alpha, Engagement and Workload and CM]:
                            - Mean
                            - Std
                            - Percentile Score = 100*cumulative_normal_distribution(ad_x-Means/ad_x-Std)
                    OUTPUT4 --> Total Scores (a,e,w,CM as Percentiles) (for entire DB)

            4.5 BRAND SALIENCY (from eye metrics)
                0. Add constants (time brackets, 150, 900, useThreshold)
                1. Create an AOI table
                    - Populate with list of all AOIs (Names) and give ID
                2. Create Fixations Table
                    - Create a populateFixations Store Procedure
                        - Discard data where AOIGazedAt is empty
                        - For each participant, for each AOI, group fixation data (collection of values) by fixation index (this value is unique per PARTICIPANT)
                          sorted by Timestamp
                            - Store: 'RespondentID','StimulisID','AOIID','FixationIndex',
                            'FixationStartTime', this is first in group
                            'FixationDuration', this is last in group - first in group
                            'Classification', 
                                1: 0 - 150ms: Short, Express, absence of cognitive inhibition, high frequency search system
                                2: 150 - 900ms: Cognitive, pattern recognition, resonance or dissonance deteted
                                3: >900ms: Overtaxed, high inhibiton
                        - ROW ENTRY FOR EVERY FIXATION FOR EVERY RESPONDENT FOR EVERY AD
               3. Create AOIData Table
                    - Create a populateAOIData Store Procedure
                    - For each participant, for each AOI, group fixation data (collection of values) by fixation index (this value is unique per PARTICIPANT)
                      sorted by Timestamp
                      - Only where Classification = 2
                      - Store: 'RespondentID','StimulisID','AOIID',
                            'TFD', sum of all durations
                            'FFD', duaration of first entry
                      - ROW ENTRY FOR EVERY AOI FOR EVERY RESPONDENT FOR EVERY AD
               4. Create AOIAllMetrics Table
                    - Creat populateAOIAllMetrics Store Procedure
                    - For each AOI:
                        - 'StimulisID','AOIID',
                        'AverageTFD', sum of all durations
                        'CountTFD', number of respondents used
                        'UseValue', below or above useThreshold

               5. Create AOIUseMetrics Table
                    - Creat populateAOIUseMetrics Store Procedure
                    - For each AOI if UseValue is 1:
                        - 'StimulisID','AOIID',
                        'AverageTFD', sum of all durations
                        'ZScoreAverageTFD',  
                        'PercentileTFD',  

                6. Update Core Metrics AOIUseMetrics Table
                    - Creat populateBrandProminence Store Procedure
                    - For each AOI if UseValue is 1:
                        - 'StimulisID',
                        'SumAverageTFD', sum of all AverageTFD for each StimulusID
                        'ZScoreSumAverageTFD',  
                        'BrandProminence',  percentile of ZScoreSumAverageTFD
                          

                                
                    



            


            
                
'''


def alpha(in_folder, out_folder, results_folder, header_row = 0, freq = 0.1, freqn=None, mod = 0.750):
    '''
    This function extracts alpha data from a batch of adds. It expects add data to be stored in the following format:
    '''
    header("> Running: Extracting Batch Alpha")
    
    #Define variables
    calc_col = ['Ad','Alpha Proportions']
    calc = pd.DataFrame(columns = calc_col)
    data = "Frontal Asymmetry Alpha"
    keep = ['Row',data]

    #Get Ad names
    dirs = get_files(in_folder)
    
    DATA = pd.DataFrame()
    #For each Ad..
    for dir in dirs:
            print(f"> Now Working: {dir}")
            out_path = out_folder +dir+'/'+data #Set Ouput Directory
            os.makedirs(out_path, exist_ok=True)  
            
            ##Extract data from files
            files = get_files(in_folder + dir + '/Alpha') #Get list of all respondent files

            #For each respondent
            for file in files:
                try:
                    df = pd.read_csv(in_folder + dir + '/Alpha/' + file, header=header_row, low_memory = False)
                    clean = df[keep] #Keep only Relevent data
                    clean = clean.replace(to_replace=-99999,value=np.nan)
                    clean = clean.replace(to_replace=' ',value=np.nan)
                    clean = clean.dropna()
                    
                    if bool(freqn):
                        old = clean[data].to_numpy()                    
                        clean[data] = old + mod*filter(old,freqn,'lowpass')

                    clean.to_csv(out_path + '/clean' + file , index=False, header=True)
                    print(f">> Cleaned: {file}")
                except Exception as z:
                    get_key(z)        
            
            #Combine data per ad
            files = get_files(out_path)
            labels = ['Row',data]
            all_data = pd.DataFrame(columns = labels )
            res = 1
            for file in files:
                try:
                    _data = pd.read_csv(out_path + '/' + file, header=0, usecols=[0,1], names = labels)
                    _data.insert(0, 'Respondant',res)
                    _data.insert(0, 'Ad', dir)
                    all_data = pd.concat([all_data, _data])
                    res = res + 1
                    print(f">> Collected: {file}")
                except Exception as z:
                    get_key(z)
            pprint.pprint(len(all_data))
            all_data.to_csv(results_folder+dir+'_'+data+'.csv')
            
            
            prop_col = ['Time Alpha','Alpha Proportion','Alpha Mean']
            prop = pd.DataFrame(columns = prop_col)
            time = all_data['Row'].to_numpy()
            maxi = time.max()
            diff = 128
            bins = np.arange(0,maxi,diff)
            ind = np.digitize(all_data['Row'],bins)

            all_data['Corrected_Time']=ind
            DATA = pd.concat([DATA, all_data])

            gb = all_data.groupby(ind)
            for x in gb.groups:
                _data = gb.get_group(x)
                _time = _data['Row'].mean()/256
                _data = _data[data]
                _mean = _data.mean()
                _pos = sum(1 for item in _data if item>0)
                _prop = _pos/len(_data)*100 
                prop = prop.append({'Time Alpha':_time,'Alpha Proportion':_prop, 'Alpha Mean':_mean }, ignore_index = True)
            
            #Filter Data
            time = (prop['Time Alpha'].to_numpy())/256
            x = time
            y = prop['Alpha Proportion'].to_numpy()      
            b, a = signal.butter(8, freq,'lowpass')
            yf = signal.filtfilt(b, a, y, padlen=10)  
            prop[f"{data} Filtered"]=yf
            
            #Plot data
            line(x, f"{dir} {data}", results_folder , ys = {'Alpha Proportion':yf,})
            
            
            if os.path.isfile(f"{results_folder}time_series_{dir}.csv"):
                df = pd.read_csv(f"{results_folder}time_series_{dir}.csv")
                prop = pd.concat([df,prop],axis =1)
            prop.to_csv(f"{results_folder}time_series_{dir}.csv",index=False)
            #Calculate ad proportions
            _alphas = all_data[data]
            _score = np.abs(_alphas.mean())
            _pos = sum(1 for item in _alphas if item>0)
            _prop = _pos/len(_alphas)*100
            calc = calc.append({'Ad':dir,'Alpha Proportions':_score}, ignore_index = True)
            bin_data(results_folder+dir+'_'+data+'.csv','Row', data, 128).to_csv(f"{results_folder}time_{dir}_{data}.csv")

    pprint.pprint(len(calc))
    pp.pprint(calc)
    calc.to_csv(f"{results_folder}proportions_{data}.csv")
    DATA.to_csv(f"{results_folder}ALL_{data}.csv")
    print("> Completed: Extracting Batch Alpha")
 

def eeg_metrics(in_folder, out_folder, results_folder, header_row = 0, freq = 0.1, freqn=None, mod = 0.750):
    '''
    This function extracts alpha data from a batch of adds. It expects add data to be stored in the following format:
    '''
    header("> Running: Extracting Batch Alpha")
    
    #Define variables
    calc_col = ['Ad','Frontal Asymmetry Alpha Proportions','High Engagement Proportions','Workload Average Proportions']
    calc = pd.DataFrame(columns = calc_col)
    keep = ['Row','Frontal Asymmetry Alpha','High Engagement','Workload Average']

    #Get Ad names
    files = get_files(in_folder)
    
    DATA = pd.DataFrame()
    #For each Ad..
    for file in files:
            print(f"> Now Working: {file}")
            out_path = out_folder +file+'/' #Set Ouput Directory
            os.makedirs(out_path, exist_ok=True)  
            
            ###Extract data from files
            #files = get_files(in_folder + dir + '/Alpha') #Get list of all respondent files

            ##For each respondent
            #for file in files:
            try:
                df = pd.read_csv(in_folder + file, header=header_row, low_memory = False)
                clean = df[keep] #Keep only Relevent data
                clean = clean.replace(to_replace=-99999,value=np.nan)
                clean = clean.replace(to_replace=' ',value=np.nan)
                clean = clean.dropna()
                    
                if bool(freqn):
                    old = clean[data].to_numpy()                    
                    clean[data] = old + mod*filter(old,freqn,'lowpass')

                clean.to_csv(out_path + '/clean' + file , index=False, header=True)
                print(f">> Cleaned: {file}")
            except Exception as z:
                get_key(z)        
            
            #Combine data per ad
            files = get_files(out_path)
            labels = ['Row',data]
            all_data = pd.DataFrame(columns = labels )
            res = 1
            for file in files:
                try:
                    _data = pd.read_csv(out_path + '/' + file, header=0, usecols=[0,1], names = labels)
                    _data.insert(0, 'Respondant',res)
                    _data.insert(0, 'Ad', dir)
                    all_data = pd.concat([all_data, _data])
                    res = res + 1
                    print(f">> Collected: {file}")
                except Exception as z:
                    get_key(z)
            pprint.pprint(len(all_data))
            all_data.to_csv(results_folder+dir+'_'+data+'.csv')
            
            
            prop_col = ['Time Alpha','Alpha Proportion','Alpha Mean']
            prop = pd.DataFrame(columns = prop_col)
            time = all_data['Row'].to_numpy()
            maxi = time.max()
            diff = 128
            bins = np.arange(0,maxi,diff)
            ind = np.digitize(all_data['Row'],bins)

            all_data['Corrected_Time']=ind
            DATA = pd.concat([DATA, all_data])

            gb = all_data.groupby(ind)
            for x in gb.groups:
                _data = gb.get_group(x)
                _time = _data['Row'].mean()/256
                _data = _data[data]
                _mean = _data.mean()
                _pos = sum(1 for item in _data if item>0)
                _prop = _pos/len(_data)*100 
                prop = prop.append({'Time Alpha':_time,'Alpha Proportion':_prop, 'Alpha Mean':_mean }, ignore_index = True)
            
            #Filter Data
            time = (prop['Time Alpha'].to_numpy())/256
            x = time
            y = prop['Alpha Proportion'].to_numpy()      
            b, a = signal.butter(8, freq,'lowpass')
            yf = signal.filtfilt(b, a, y, padlen=10)  
            prop[f"{data} Filtered"]=yf
            
            #Plot data
            line(x, f"{dir} {data}", results_folder , ys = {'Alpha Proportion':yf,})
            
            
            if os.path.isfile(f"{results_folder}time_series_{dir}.csv"):
                df = pd.read_csv(f"{results_folder}time_series_{dir}.csv")
                prop = pd.concat([df,prop],axis =1)
            prop.to_csv(f"{results_folder}time_series_{dir}.csv",index=False)
            #Calculate ad proportions
            _alphas = all_data[data]
            _pos = sum(1 for item in _alphas if item>0)
            _prop = _pos/len(_alphas)*100
            calc = calc.append({'Ad':dir,'Alpha Proportions':_prop}, ignore_index = True)
            bin_data(results_folder+dir+'_'+data+'.csv','Row', data, 128).to_csv(f"{results_folder}time_{dir}_{data}.csv")

    pprint.pprint(len(calc))
    pp.pprint(calc)
    calc.to_csv(f"{results_folder}proportions_{data}.csv")
    DATA.to_csv(f"{results_folder}ALL_{data}.csv")
    print("> Completed: Extracting Batch Alpha")


def bin_mean(df, bin_col, data, freq):
            #Calculate time proportions
            _cols = [bin_col,data]                          # Set labels for columns
            result = pd.DataFrame(columns = _cols)          # Initialise return df 
            maxi = df[bin_col].max()                        # Get max time
            bins = np.arange(0,maxi,freq)                   # Create bin range
            ind = np.digitize(df[time_col],bins)            # Return bin membership per index
            gb = df.groupby(ind)                            # Group by bin
            
            for x in gb.groups:
                _data = gb.get_group(x)                                             # Get all values in bin
                result = result.append({bin_col: _data[bin_col].mean()/256,         # Add bin means to result
                                        data :prop_alpha(_data[data])},
                                       ignore_index = True)


def prop_alpha(data):
    _pos = sum(1 for item in data if item>0)
    return _pos/len(data)*100 


def engagement(in_folder, out_folder, results_folder, header_row= 0, freq = 0.2, freqn=None, mod=0.403):
    header("> Running: Extracting Batch Engagement")
    #Define variables
    calc_col = ['Ad','Eng Mean','Eng Disengaged Prop', 'Eng Low Prop', 'Eng High Prop','Eng Count']
    calc = pd.DataFrame(columns = calc_col)
    data = "High Engagement"
    keep = ['Row',data] 
    #Get Ad names
    dirs = get_files(in_folder)
    DATA = pd.DataFrame()
    #For each Ad..
    for dir in dirs:
            print(f"> Now Working: {dir}")
            out_path = out_folder +dir+'/'+data
            os.makedirs(out_path, exist_ok=True)
            #Extract data from files
            files = get_files(in_folder + dir + '/Eng and WL')
            for file in files:
                try:
                    df = pd.read_csv(in_folder + dir + '/Eng and WL/' + file, header=header_row, low_memory = False)
                    clean = df[keep] 
                    clean = clean.replace(to_replace=-99999,value=np.nan)
                    clean = clean.replace(to_replace=' ',value=np.nan)
                    clean = clean.dropna()

                    if bool(freqn):
                        old = clean[data].to_numpy()                    
                        clean[data] = old + mod*filter(old,freqn,'lowpass')

                    clean.to_csv(out_path + '/clean' + file , index=False, header=True)
                    print(f">> Cleaned: {file}")
                except Exception as z:
                    get_key(z)        
            #Combine data per ad
            files = get_files(out_path)
            labels = ['Row', data]
            all_data = pd.DataFrame(columns = labels )
            res = 1
            for file in files:
                try:
                    _data = pd.read_csv(out_path + '/' + file, header=0, usecols=[0,1], names = labels)
                    _data.insert(0, 'Respondant',res)
                    _data.insert(0, 'Ad', dir)
                    all_data = pd.concat([all_data, _data])
                    res = res + 1
                    print(f">> Collected: {file}")
                except Exception as z:
                    get_key(z) 
            pprint.pprint(len(all_data))
            all_data.to_csv(results_folder+dir+'_'+data+'.csv')

            #Calculate time proportions
            prop_col = ['Time Engagement','High Engagement Proportion','Low Engagement Proportion','Disengaged Proportion']
            prop = pd.DataFrame(columns = prop_col)
            time = all_data['Row'].to_numpy()
            maxi = time.max()
            diff = 256 # 256 or 1
            bins = np.arange(0,maxi,diff)
            ind = np.digitize(all_data['Row'],bins)

            all_data['Corrected_Time']=ind
            DATA = pd.concat([DATA, all_data])

            gb = all_data.groupby(ind)
            for x in gb.groups:
                _data = gb.get_group(x)
                _time = _data['Row'].mean()/256 # blank, or divided by 256
                _data = _data[data].mean()

                #Correct for decimal
                _data = _data*100

                #Not necessary because already proportion

                #_disengaged = sum(1 for item in _data if item < 0.4)
                #_low = sum(1 for item in _data if item > 0.4 and item < 0.7)
                #_high = sum(1 for item in _data if item > 0.7)
                #_count = len(_data)
                #if _count>0:
                #    _disengaged = _disengaged/_count*100
                #    _low = _low/_count*100
                #    _high = _high/_count*100
                #else: 
                #    _count = 0
                #    _disengaged = 0
                #    _low = 0
                #    _high = 0

                prop = prop.append({'Time Engagement':_time,'High Engagement Proportion':_data}, ignore_index = True)
            
            #Filter Data
            time = (prop['Time Engagement'].to_numpy())
            x = time
            y1 = prop['High Engagement Proportion'].to_numpy() 
            y2 = prop['Low Engagement Proportion'].to_numpy() 
            y3 = prop['Disengaged Proportion'].to_numpy() 
            b, a = signal.butter(8, freq,'lowpass')
            try:
                yf1 = signal.filtfilt(b, a, y1, padlen=10)  
                yf2 = signal.filtfilt(b, a, y2, padlen=10)  
                yf3 = signal.filtfilt(b, a, y3, padlen=10)
            

                #prob = []
                #yfs = np.sort(yf1)
                #for x in [0,1,2,-1,-2,-3]:
                #    index = np.where(yf1==yfs[x])
                #    if yf2[index] > yf3[index] :
                #        prob[x] = 'Low Engagement'
                #    else:
                #        prob[x] = 'Disengaged'

                prop[f"High Engagement Proportion Filtered"]=yf1
                #prop[f"Low Engagement Proportion Filtered"]=yf2
                #prop[f"Disengaged Proportion Filtered"]=yf3
            
                #Plot data
                #line(x, f"{dir} {data}" ,results_folder, ys = { 'Low Engagement Proportion':yf2, 'Disengaged Proportion':yf3, 'High Engagement Proportion':yf1}, legend = True)
                line(x, f"{dir} {data}" ,results_folder, ys = {'High Engagement Proportion':yf1}, legend = True)
            except Exception as z:
                    get_key(z) 

            if os.path.isfile(f"{results_folder}time_series_{dir}.csv"):
                df = pd.read_csv(f"{results_folder}time_series_{dir}.csv")
                prop = pd.concat([df,prop],axis =1)
            prop.to_csv(f"{results_folder}time_series_{dir}.csv",index=False)
            #Calculate ad proportions
            _data = all_data[data]
            _mean = _data.mean()
            _high = _mean*100
            _count = len(_data)
            #_disengaged = sum(1 for item in _data if item < 0.4)
            #_low = sum(1 for item in _data if item > 0.4 and item < 0.7)
            #_high = sum(1 for item in _data if item > 0.7)
            #_count = len(_data)
            #if _count>0:
            #    _disengaged = _disengaged/_count*100
            #    _low = _low/_count*100
            #    _high = _high/_count*100
            #else: 
            #    _count = 0
            #    _disengaged = 0
            #    _low = 0
            #    _high = 0
            calc = calc.append({'Ad':dir,'Eng Mean':_mean,'Eng High Prop' :_high , 'Eng Count':_count}, ignore_index = True)
            #Produce Time Series
            bin_data(results_folder+dir+'_'+data+'.csv','Row', data, 256).to_csv(f"{results_folder}time_{dir}_{data}.csv")
    
    pp.pprint(calc)
    calc.to_csv(f"{results_folder}proportions_{data}.csv")
    DATA.to_csv(f"{results_folder}ALL_{data}.csv")
    print("> Completed: Extracting Batch Engagement")


def workload(in_folder, out_folder, results_folder, header_row = 0, freq = 0.2, freqn= None, mod=0.076 ):
    header("> Running: Extracting Batch Workload")
    #Define variables
    calc_col = ['Ad','WL Mean','WL Low Prop', 'WL Optimal Prop', 'WL Overworked Prop','WL Count']
    calc = pd.DataFrame(columns = calc_col)
    data = "Workload Average"
    keep = ['Row',data]
    #Get Ad names
    dirs = get_files(in_folder)
    DATA = pd.DataFrame()
    #For each Ad..
    for dir in dirs:
            print(f"> Now Working: {dir}")
            out_path = out_folder +dir+'/'+data
            os.makedirs(out_path, exist_ok=True)
            #Extract data from files
            files = get_files(in_folder + dir + '/Eng and WL')
            for file in files:
                try:
                    df = pd.read_csv(in_folder + dir + '/Eng and WL/' + file, header=header_row, low_memory = False)
                    clean = df[keep] 
                    clean = clean.replace(to_replace=-99999,value=np.nan)
                    clean = clean.replace(to_replace=' ',value=np.nan)
                    clean = clean.dropna()

                    if bool(freqn):
                        old = clean[data].to_numpy()                    
                        clean[data] = old + mod*filter(old,freqn,'lowpass')

                    clean.to_csv(out_path + '/clean' + file , index=False, header=True)
                    print(f">> Cleaned: {file}")
                except Exception as z:
                    get_key(z)            
            #Combine data per ad
            files = get_files(out_path)
            labels = ['Row', data]
            all_data = pd.DataFrame(columns = labels )
            res = 1
            for file in files:
                try:
                    _data = pd.read_csv(out_path + '/' + file, header=0, usecols=[0,1], names = labels)
                    _data.insert(0, 'Respondant',res)
                    _data.insert(0, 'Ad', dir)
                    all_data = pd.concat([all_data, _data])
                    res = res + 1
                    print(f">> Collected: {file}")
                except Exception as z:
                    get_key(z) 
            pprint.pprint(len(all_data))
            all_data.to_csv(results_folder+dir+'_'+data+'.csv')
            DATA = pd.concat([DATA, all_data])
            #Calculate time proportions
            prop_col = ['Time Workload', 'Low Workload Proportion', 'Optimal Workload Proportion', 'Overworked Proportion']
            prop = pd.DataFrame(columns = prop_col) 
            time = all_data['Row'].to_numpy()
            maxi = time.max()
            diff = 256 # or 1
            bins = np.arange(0,maxi,diff)
            ind = np.digitize(all_data['Row'],bins)

            all_data['Corrected_Time']=ind
            DATA = pd.concat([DATA, all_data])

            gb = all_data.groupby(ind)
            for x in gb.groups:
                _data = gb.get_group(x)
                _time = _data['Row'].mean()/256# blank, or divided by 256
                _data = _data[data]
                _low = sum(1 for item in _data if item < 0.4)
                _optimal = sum(1 for item in _data if item > 0.4 and item < 0.6)
                _overworked = sum(1 for item in _data if item > 0.6)
                _count = len(_data)
                if _count>0:
                    _low = _low/_count*100
                    _optimal = _optimal/_count*100
                    _overworked = _overworked/_count*100
                else: 
                    _count = 0
                    _low = 0
                    _optimal = 0
                    _overworked = 0
                prop = prop.append({'Time Workload':_time,'Low Workload Proportion':_low, 'Optimal Workload Proportion':_optimal, 'Overworked Proportion':_overworked}, ignore_index = True)
            #Filter Data
            try:
                time = (prop['Time Workload'].to_numpy())
                x = time
                y1 = prop['Low Workload Proportion'].to_numpy() 
                y2 = prop['Optimal Workload Proportion'].to_numpy() 
                y3 = prop['Overworked Proportion'].to_numpy() 
                b, a = signal.butter(8, freq,'lowpass')
                yf1 = signal.filtfilt(b, a, y1, padlen=10)  
                yf2 = signal.filtfilt(b, a, y2, padlen=10)  
                yf3 = signal.filtfilt(b, a, y3, padlen=10)  
                #prop[f"Low Workload Proportion Filtered"]=yf1
                prop[f"Optimal Workload Proportion Filtered"]=yf2
                #prop[f"Overworked Proportion Filtered"]=yf3
            
                #Plot data
                #line(x, f"{dir} {data}" ,results_folder, ys = { 'Low Workload Proportion':yf1, 'Overworked Proportion':yf3, 'Optimal Workload Proportion':yf2}, legend = True)
                line(x, f"{dir} {data}" ,results_folder, ys = {'Optimal Workload Proportion':yf2}, legend = True)
            except Exception as z:
                    get_key(z) 

            if os.path.isfile(f"{results_folder}time_series_{dir}.csv"):
                df = pd.read_csv(f"{results_folder}time_series_{dir}.csv")
                prop = pd.concat([df,prop],axis =1)
            prop.to_csv(f"{results_folder}time_series_{dir}.csv",index=False)
            #Calculate ad proportions
            _data = all_data[data]
            _mean = _data.mean()
            _low = sum(1 for item in _data if item < 0.4)
            _optimal = sum(1 for item in _data if item > 0.4 and item < 0.6)
            _overworked = sum(1 for item in _data if item > 0.6)
            _count = len(_data)
            if _count>0:
                _low = _low/_count*100
                _optimal = _optimal/_count*100
                _overworked = _overworked/_count*100
            else: 
                _count = 0
                _low = 0
                _optimal = 0
                _overworked = 0
            calc = calc.append({'Ad':dir,'WL Mean':_mean, 'WL Low Prop': _low, 'WL Optimal Prop':_optimal, 'WL Overworked Prop':_overworked, 'WL Count':_count}, ignore_index = True)
            #Produce Time Series
            bin_data(results_folder+dir+'_'+data+'.csv','Row', data, 256).to_csv(f"{results_folder}time_{dir}_{data}.csv")

    pp.pprint(calc)
    calc.to_csv(f"{results_folder}proportions_{data}.csv")
    DATA.to_csv(f"{results_folder}ALL_{data}.csv")
    print("> Completed: Extracting Batch Workload")


def batch_GSR(in_folder, out_folder, results_folder):
    
    #Define variables

    row = "Row" 
    data = "GSR Raw (microSiemens)"
    
    keep = []
    keep.append(row)
    keep.append(data)
    
    #Get Ad names
    dirs = get_files(in_folder)
    #For each Ad..
    for dir in dirs:
            print(f"> Now Working: {dir}")
            out_path = out_folder +dir
            os.makedirs(out_path, exist_ok=True)

            #Extract data from files
            files = get_files(in_folder + dir + '/GSR')
            for file in files:
                try:
                    df = pd.read_csv(in_folder + dir + '/GSR/' + file, header=1, low_memory = False)
                    clean = df[keep] 
                    clean = clean.replace(to_replace=-99999,value=np.nan)
                    clean = clean.replace(to_replace=' ',value=np.nan)
                    clean = clean.dropna()
                    clean.to_csv(out_path + '/clean' + file , index=False, header=True)
                    print(f"> Cleaned: {file}")
                except OSError as error:
                    print(f">    Error cleaning outfile {file} : {error}")
                except:
                    print(f">    Error cleaning outfile {file} : Check")
                    pass
            
            #Combine data per ad
            files = get_files(out_path)
            labels = ['Row', data]
            all_data = pd.DataFrame(columns = labels )
            res = 1
            for file in files:
                try:
                    _data = pd.read_csv(out_path + '/' + file, header=0, usecols=[0,1], names = labels)
                    _data.insert(0, 'Respondant',res)
                    _data.insert(0, 'Ad', dir)
                    all_data = pd.concat([all_data, _data])
                    res = res + 1
                    print(f"> Collected: {file}")
                except OSError as error:
                    print(f"> ##### Error joining outfile file: {error} ##### ")
            pprint.pprint(len(all_data))
            all_data.to_csv(results_folder+dir+'_'+data+'.csv')
            
            #Produce Time Series
            
            df = df= pd.read_csv(results_folder+dir+'_'+data+'.csv', header=0)
            bins = np.arange(0,30000,1)
            ind = np.digitize(df['Row'],bins)
            df = df.groupby(ind).mean().reset_index()
            df[['Row',data]].to_csv(f"{results_folder}time_{dir}_{data}.csv")


    #Combine all data
    #files = get_files(results_folder)
    #all_data = pd.DataFrame()
    
    #for file in files:
    #    print(f"> Joined: {file}")
    #    _data = pd.read_csv(f"{results_folder}{file}", header=0)
    #    all_data = pd.concat([all_data, _data])

    #pprint.pprint(len(all_data))
    all_data.to_csv(f"{results_folder}combined_{data}.csv")  


def scenes_alpha(in_folder, out_folder, results_folder, scene_tags, header_row = 0, freqn= None, mod=0.750):
    header("> Running: Extracting Alpha ")
    
    #Define variables
    calc_col = ['Ad','Scene','Alpha Mean','Alpha Prop','Alpha Count']
    calc = pd.DataFrame(columns = calc_col)
    
    #For respondant specific data
    scalc = pd.DataFrame(columns = calc_col)
    
    data = "Frontal Asymmetry Alpha"
    keep = ['Row',data]
    
    #Get Ad names
    dirs = get_files(in_folder)
    
    #For each Ad..
    for dir in dirs:
            print(f"> Now Working: {dir}")
            out_path = out_folder +dir + '/Alpha'
            os.makedirs(out_path, exist_ok=True)
            
            #Extract data from files
            files = get_files(in_folder + dir + '/Alpha')
            for file in files:
                try:
                    df = pd.read_csv(in_folder + dir + '/Alpha/' + file, header=header_row, low_memory = False)
                    scenes = [s for s in df.columns if any(x in s for x in scene_tags)]
                    clean = df[keep+scenes] 
                    clean = clean.replace(to_replace=-99999,value=np.nan)
                    clean = clean.replace(to_replace=' ',value=np.nan)
                    clean = clean.dropna(subset=[data])

                    if bool(freqn):
                        old = clean[data].to_numpy()                    
                        clean[data] = old + mod*filter(old,freqn,'lowpass')

                    clean.to_csv(out_path + '/clean_' + file , index=False, header=True)
                    print(f">> Cleaned: {file}")
                except Exception as z:
                    get_key(z)            
            
            #Combine data per ad
            files = get_files(out_path)
            labels = ['Row',data]
            labels = labels + scenes
            all_data = pd.DataFrame(columns = labels)
            res = 1
            for file in files:
                try:
                    #_data = pd.read_csv(out_path + '/' + file, header=0, names = labels)
                    _data = pd.read_csv(out_path + '/' + file)
                    _data.insert(0, 'Respondant',res)
                    _data.insert(0, 'Ad', dir)
                    all_data = pd.concat([all_data, _data])
                    res = res + 1
                    print(f">> Collected: {file}")
 
                    for scn in scenes:
                        try:
                            _scenes = [data, scn]
                            _alphas = _data[_scenes]
                            _alphas = _alphas.dropna(subset=[scn])
                            _mean = _alphas[data].mean()
                            _pos = sum(1 for item in _alphas[data] if item>0)
                            _count = len(_alphas)
                            if _count>0:
                                _prop = _pos/_count*100
                            else: 
                                _count = 0
                                _prop = 0
                            scalc = scalc.append({'Ad':dir, 'Scene':scn, 'Alpha Mean':_mean, 'Alpha Prop':_prop, 'Alpha Count':_count}, ignore_index = True)
                        except Exception as z:
                            get_key(z)

                except Exception as z:
                    get_key(z)

            all_data.to_csv(results_folder+dir+'_'+data+'.csv')          
            
            #Calculate proportions
            for scn in scenes:
                try:
                    _scenes = [data, scn]
                    _alphas = all_data[_scenes]
                    _alphas = _alphas.dropna(subset=[scn])
                    _mean = _alphas[data].mean()
                    _pos = sum(1 for item in _alphas[data] if item>0)
                    _count = len(_alphas)
                    if _count>0:
                        _prop = _pos/_count*100
                    else: 
                        _count = 0
                        _prop = 0
                    calc = calc.append({'Ad':dir, 'Scene':scn, 'Alpha Mean':_mean, 'Alpha Prop':_prop, 'Alpha Count':_count}, ignore_index = True)
                except Exception as z:
                    get_key(z)
            print(f"> Got Scenes: {file}")
            
    calc.to_csv(f"{results_folder}scenes_{data}.csv")
    #scalc.to_csv(f"{results_folder}summary/scenes_{data}_all.csv")
    pp.pprint(len(calc))
    pp.pprint(calc)
    print("> Completed: Extracting Scene Alpha")


def scenes_workload(in_folder, out_folder, results_folder, scene_tags, header_row = 0, freqn= None, mod=0.403):
    header("> Running: Extracting Workload")
    
    #Define variables
    calc_col = ['Ad','Scene','WL Mean','WL Low Prop', 'WL Optimal Prop', 'WL Overworked Prop','WL Count']
    calc = pd.DataFrame(columns = calc_col)
    
    #For respondant specific data
    scalc = pd.DataFrame(columns = calc_col)
    
    data = "Workload Average"
    keep = ['Row',data]
    
    #Get Ad names
    dirs = get_files(in_folder)
    
    #For each Ad..
    for dir in dirs:
            print(f"> Now Working: {dir}")
            out_path = out_folder +dir + '/Workload'
            os.makedirs(out_path, exist_ok=True)
            
            #Extract data from files
            files = get_files(in_folder + dir + '/Eng and WL')
            for file in files:
                try:
                    df = pd.read_csv(in_folder + dir + '/Eng and WL/' + file, header=header_row, low_memory = False)
                    scenes = [s for s in df.columns if any(x in s for x in scene_tags)]
                    clean = df[keep+scenes] 
                    clean = clean.replace(to_replace=-99999,value=np.nan)
                    clean = clean.dropna(subset=[data])
                    
                    if bool(freqn):
                        old = clean[data].to_numpy()                    
                        clean[data] = old + mod*filter(old,freqn,'lowpass')

                    clean.to_csv(out_path + '/clean_' + file , index=False, header=True)
                    print(f"> Cleaned: {file}")
                except Exception as z:
                    get_key(z)        
            
            #Extract data per respondant
            files = get_files(out_path)
            labels = ['Row',data]
            labels = labels + scenes
            all_data = pd.DataFrame(columns = labels)
            res = 1

            for file in files:
                
                try:
                    _data = pd.read_csv(out_path + '/' + file)
                    _data.insert(0, 'Respondant',res)
                    _data.insert(0, 'Ad', dir)
                    all_data = pd.concat([all_data, _data])
                    res = res + 1
                    print(f">> Collected: {file}")

                    for scn in scenes:
                        try:
                            _scenes = [data, scn]
                            _sdata = _data[_scenes]
                            _sdata = _sdata.dropna(subset=[scn])
                            _sdata = _sdata[data]
                            _mean = _sdata.mean()

                            _low = sum(1 for item in _sdata if item < 0.4)
                            _optimal = sum(1 for item in _sdata if item > 0.4 and item < 0.6)
                            _overworked = sum(1 for item in _sdata if item > 0.6)

                            _count = len(_sdata)
                            if _count>0:
                                _low = _low/_count*100
                                _optimal = _optimal/_count*100
                                _overworked = _overworked/_count*100
                            else: 
                                _count = 0
                                _low = 0
                                _optimal = 0
                                _overworked = 0

                            scalc = scalc.append({'Ad':dir, 'WL Mean':_mean, 'WL Low Prop': _low, 'WL Optimal Prop':_optimal, 'WL Overworked Prop':_overworked, 'WL Count':_count}, ignore_index = True)
                        except Exception as z:
                            get_key(z)
                except Exception as z:
                    get_key(z)
            
            all_data.to_csv(results_folder+dir+'_'+data+'.csv')           
            #Calculate proportions
            for scn in scenes:
                try:
                    _scenes = [data, scn]
                    _data = all_data[_scenes]
                    _data = _data.dropna(subset=[scn])
                    _data = _data[data]
                    _mean = _data.mean()

                    _low = sum(1 for item in _data if item < 0.4)
                    _optimal = sum(1 for item in _data if item > 0.4 and item < 0.6)
                    _overworked = sum(1 for item in _data if item > 0.6)

                    _count = len(_data)
                    if _count>0:
                        _low = _low/_count*100
                        _optimal = _optimal/_count*100
                        _overworked = _overworked/_count*100
                    else: 
                        _count = 0
                        _low = 0
                        _optimal = 0
                        _overworked = 0

                    calc = calc.append({'Ad':dir, 'Scene':scn, 'WL Mean':_mean, 'WL Low Prop': _low, 'WL Optimal Prop':_optimal, 'WL Overworked Prop':_overworked, 'WL Count':_count}, ignore_index = True)
                except OSError or ValueError or ZeroDivisionError as error:
                    print(f">##### Error joining outfile file: {error} ##### ")
            print(f"> Got Scenes: {file}")
    
    calc.to_csv(f"{results_folder}scenes_{data}.csv")
    #scalc.to_csv(f"{results_folder}summary/scenes_{data}_all.csv")
    pp.pprint(len(calc))
    pp.pprint(calc)
    print("> Completed: Extracting Scene Workload")


def scenes_engagement(in_folder, out_folder, results_folder, scene_tags, header_row = 0, freqn= None, mod=0.076):
    header("> Running: Extracting Engagement")
    
    #Define variables
    calc_col = ['Ad','Scene','Eng Mean','Eng Disengaged Prop', 'Eng Low Prop', 'Eng High Prop','Eng Count']
    calc = pd.DataFrame(columns = calc_col)
    
    #For respondant specific data
    scalc = pd.DataFrame(columns = calc_col)
    
    data = "High Engagement"   
    keep = ['Row',data]
    
    #Get Ad names
    dirs = get_files(in_folder)
    
    #For each Ad..
    for dir in dirs:
            print(f"> Now Working: {dir}")
            out_path = out_folder +dir + '/Engagement'
            os.makedirs(out_path, exist_ok=True)
            
            #Extract data from files
            files = get_files(in_folder + dir + '/Eng and WL')
            for file in files:
                try:
                    df = pd.read_csv(in_folder + dir + '/Eng and WL/' + file, header=header_row, low_memory = False)
                    scenes = [s for s in df.columns if any(x in s for x in scene_tags)]
                    clean = df[keep+scenes] 
                    clean = clean.replace(to_replace=-99999,value=np.nan)
                    clean = clean.dropna(subset=[data])
                    
                    if bool(freqn):
                        old = clean[data].to_numpy()                    
                        clean[data] = old + mod*filter(old,freqn,'lowpass')
                    
                    clean.to_csv(out_path + '/clean_' + file , index=False, header=True)
                    print(f"> Cleaned: {file}")
                except Exception as z:
                            get_key(z)
            
            #Combine data per ad
            files = get_files(out_path)
            labels = ['Row',data]
            labels = labels + scenes
            all_data = pd.DataFrame(columns = labels)
            res = 1
            for file in files:
                try:
                    #_data = pd.read_csv(out_path + '/' + file, header=0, names = labels)
                    _data = pd.read_csv(out_path + '/' + file)
                    _data.insert(0, 'Respondant',res)
                    _data.insert(0, 'Ad', dir)
                    all_data = pd.concat([all_data, _data])
                    res = res + 1
                    print(f"> Collected: {file}")

                    for scn in scenes:
                        try:
                            _scenes = [data, scn]
                            _sdata = _data[_scenes]
                            _sdata = _sdata.dropna(subset=[scn])
                            _sdata = _sdata[data]
                            _mean = _sdata.mean()

                            _disengaged = sum(1 for item in _sdata if item < 0.4)
                            _low = sum(1 for item in _sdata if item > 0.4 and item < 0.7)
                            _high = sum(1 for item in _sdata if item > 0.7)

                            _count = len(_sdata)
                            if _count>0:
                                _disengaged = _disengaged/_count*100
                                _low = _low/_count*100
                                _high = _high/_count*100
                            else: 
                                _count = 0
                                _disengaged = 0
                                _low = 0
                                _high = 0

                            scalc = scalc.append({'Ad':dir, 'Scene':scn, 'Eng Mean':_mean, 'Eng Disengaged Prop': _disengaged, 'Eng Low Prop':_low, 'Eng High Prop' :_high , 'Eng Count':_count}, ignore_index = True)
                        except Exception as z:
                            get_key(z) 

                except Exception as z:
                    get_key(z) 

            all_data.to_csv(results_folder+dir+'_'+data+'.csv')
            
            #Calculate proportions
            for scn in scenes:
                try:
                    _scenes = [data, scn]
                    _data = all_data[_scenes]
                    _data = _data.dropna(subset=[scn])
                    _data = _data[data]
                    _mean = _data.mean()
                    _high = _mean*100
                    _count = len(_data)
                    
                    #_disengaged = sum(1 for item in _data if item < 0.4)
                    #_low = sum(1 for item in _data if item > 0.4 and item < 0.7)
                    #_high = sum(1 for item in _data if item > 0.7)

                    #_count = len(_data)
                    #if _count>0:
                    #    _disengaged = _disengaged/_count*100
                    #    _low = _low/_count*100
                    #    _high = _high/_count*100
                    #else: 
                    #    _count = 0
                    #    _disengaged = 0
                    #    _low = 0
                    #    _high = 0

                    calc = calc.append({'Ad':dir, 'Scene':scn, 'Eng Mean':_mean, 'Eng High Prop' :_high , 'Eng Count':_count}, ignore_index = True)
                except Exception as z:
                    get_key(z)                    
            print(f"> Got Scenes: {file}")
    
    calc.to_csv(f"{results_folder}scenes_{data}.csv")
    #scalc.to_csv(f"{results_folder}summary/scenes_{data}_all.csv")
    pp.pprint(len(calc))
    pp.pprint(calc)
    print("> Completed: Extracting Scene Engagement")

def eye_metrics_saliency(in_folder, out_folder, results_folder, header_row = 0):
    header("> Running: Extracting Eye Metrics")
    in_path = f"{in_folder}"
    out_path = f"{results_folder}"
    os.makedirs(out_path, exist_ok=True)  
         
    files = get_files(in_path)

    #Create the things we will need
    eye = pd.DataFrame()
    col  = ['Res','Slide','AOI','Timestamp','Index','Duration']
    calc = pd.DataFrame(columns = col)
    all_data = pd.DataFrame()

    #Extracting all raw data

    ### FOR EACH PARTICIPANT
    for f in files:
        try:
            df = pd.read_csv(f"{in_path}{f}", header=header_row, low_memory=False)
            stims = df['SourceStimuliName'].drop_duplicates()

            for stim in stims: #For each ad, skip this as data should already be split by ad
                _stim = df[df['SourceStimuliName']== stim]

                #Get list of AOIs viewed by participant - ALREADY DONE
                aois = _stim['AOIs gazed at'].dropna().drop_duplicates()

                #Get start time - ALREADY DONE
                _start_time = _stim.loc[_stim['SlideEvent']=='StartMedia']['Timestamp'].iloc[0]

                #Get data per AOI
                for aoi in aois:
                    
                    #Collect all data for the AOI, adjust the timestamp to start of ad
                    
                    _aoi = _stim.loc[_stim['AOIs gazed at']==aoi]
                    col = ['Row','Timestamp','FixIndex','FixDur','Stim','Respondent']
                    _pupil = pd.DataFrame(columns= col)
                    _pupil['Row'] = _aoi['Row']
                    _pupil['Timestamp']=_aoi['Timestamp']-_start_time
                    _pupil['FixIndex']=_aoi['Fixation Index']
                    _pupil['FixDur']=_aoi['Fixation Duration']
                    _pupil['Stim']=_aoi['SourceStimuliName']
                    _pupil['Respondent']= f[:11]

                    #Find all fixations for the ad
                    ### FIXATIONS IDENTIFIED BY INDEX
                    fixations = _pupil['FixIndex'].drop_duplicates().dropna()
                    
                    ### THIS IS COLLECTING ALL FIXATIONS FOR AN AOI, ROW ENTRY PER FIXATION
                    
                    #For each fixation
                    for fix in fixations:
                        _data = _pupil.loc[_pupil['FixIndex']==fix]

                        _calc = {'Res':_data['Respondent'].iloc[0],
                                'Stim':stim,
                                'AOI':aoi,
                                'Timestamp':_data['Timestamp'].iloc[0], #Identify start time of fixation from time of first appearance of fixation index
                                'Index':_data['FixIndex'].iloc[0],
                                'Duration':_data['Timestamp'].iloc[-1]-_data['Timestamp'].iloc[0]} #Set duration of fixation by time of last entry minus time of first entry
                        calc = calc.append(_calc, ignore_index=True)

                    #BY THE END OF THIS, WE HAVE A TABLE WITH A ROW ENTRY FOR EACH FIXATION OF EACH PARTICIPANT
            print(f">> Completed Collection: {f} ")
        except Exception as z:
                get_key(z)  
    
    #File containing eye data per ad per fixations
    calc.to_excel(f'{out_path}eye_metrics_raw.xlsx', index = False)

    print(len(calc))
    calc = calc.loc[(calc['Duration']>=150)]
    print(len(calc))
    calc = calc.loc[(calc['Duration']<=900)]
    print(len(calc))

    calcs = pd.DataFrame()

    resps = calc['Res'].drop_duplicates()
    
    #Calculating metrics from raw (FFD and TFD)
    for res in resps:                
        _res = calc.loc[calc['Res']==res]
        stims = _res['Stim'].drop_duplicates()

        for stim in stims:
            _stim = _res[_res['Stim']== stim].sort_values('Timestamp')
            aois = _stim['AOI'].dropna().drop_duplicates()

            for aoi in aois:
                _aoi = _stim.loc[_stim['AOI']==aoi].sort_values('Timestamp')
                _calcs = {'Res':res,
                        'Stim':stim,
                        'AOI':f"{stim}_{aoi}",
                        'Timestamp':_aoi['Timestamp'].iloc[0],
                        'Index':_aoi['Index'].iloc[0],
                        'TFD':_aoi['Duration'].sum(),
                        'FFD':_aoi['Duration'].iloc[0]}

                calcs = calcs.append(_calcs, ignore_index=True)

    calcs.to_excel(f'{out_path}eye_metrics_final.xlsx', index = False)
    
    #Calculates averages per AOI
    data = calcs
    data = data.groupby(['AOI']).mean()
    data['Stim'] = [list(calcs[calcs['AOI']==AOI]['Stim'])[0] for AOI in data.index]
    data['AOI'] = [AOI for AOI in data.index]
    data.to_excel(f'{out_path}RESULT_AOI_Performance.xlsx', index = True)

    data = pd.read_excel(f'{out_path}RESULT_AOI_Performance.xlsx')
    data2 = percentiles_df(data,'AOI',['TFD','FFD'])
    data2.to_excel(f'{out_path}RESULT_AOI_percentiles.xlsx', index = True)

  
    data2 = data.groupby(['Stim']).sum()
    print(data2)
    data2['Stim'] = data2.index
    data2 = percentiles_df(data2,'Stim',['TFD'])
    print(data2)
    data2.to_excel(f'{out_path}RESULT_Brand_Prominence.xlsx', index = True)


def eye_metrics_saliency_og(in_folder, out_folder, results_folder, header_row = 0):
    header("> Running: Extracting Eye Metrics")
    in_path = f"{in_folder}"
    out_path = f"{results_folder}"
    os.makedirs(out_path, exist_ok=True)  
         
    files = get_files(in_path)

    eye = pd.DataFrame()
    col  = ['Res','Slide','AOI','Timestamp','Index','Classification','Duration','Tonic','dPD','Peaks','ICA']
    calc = pd.DataFrame(columns = col)
    all_data = pd.DataFrame()

    #Extracting all raw data
    for f in files:
        try:
            res = f[:-3]
            df = pd.read_csv(f"{in_path}{f}", header=header_row, low_memory=False)
            stims = df['SourceStimuliName'].drop_duplicates()

            for stim in stims: #For each slide
                _stim = df[df['SourceStimuliName']== stim]
                aois = _stim['AOIs gazed at'].dropna().drop_duplicates()
                _start_time = _stim.loc[_stim['SlideEvent']=='StartMedia']['Timestamp'].iloc[0]

                for aoi in aois:          
                    _aoi = _stim.loc[_stim['AOIs gazed at']==aoi]
                    col = ['Row',
                           'Timestamp',
                           'PD',
                           'SacIndex',
                           'SacDur',
                           'FixIndex',
                           'FixDur',
                           'Slide',]
                    _pupil = pd.DataFrame(columns= col)
                    _pupil['Row'] = _aoi['Row']
                    _pupil['PD'] = (_aoi['ET_PupilLeft']+_aoi['ET_PupilRight'])/2
                    _pupil['Timestamp']=_aoi['Timestamp']-_start_time
                    _pupil['FixIndex']=_aoi['Fixation Index']
                    _pupil['FixDur']=_aoi['Fixation Duration']
                    _pupil['Stim']=_aoi['SourceStimuliName']

                    fixations = _pupil['FixIndex'].drop_duplicates().dropna()      

                    for fix in fixations:
                        _data = _pupil.loc[_pupil['FixIndex']==fix]

                        fc = 60
                        f = 2
                        freq = f/(0.5*fc)
                        y = _data['PD'].to_numpy()
                        if len(y)>2:
                            b, a = signal.butter(8, freq ,'lowpass')
                            yf = signal.filtfilt(b, a, y , padlen=2)
                        else:
                            yf = y
                        x = _data['Timestamp']

                        peaks = signal.find_peaks(y,height=0)
                        npeaks = len(peaks[1]['peak_heights'])

                        PPS = npeaks/_data['FixDur'].iloc[0]*1000

                        _calc = {'Res':res,
                                'Stim':stim,
                                'AOI':aoi,
                                'Timestamp':_data['Timestamp'].iloc[0],
                                'Index':_data['FixIndex'].iloc[0],
                                'Duration':_data['Timestamp'].iloc[-1]-_data['Timestamp'].iloc[0],
                                'Tonic':round(_data['PD'].mean(),3),
                                'dPD':round(yf[-1]-yf[0],3),
                                'Peaks':npeaks,
                                'ICA':round(PPS,2)}
                        calc = calc.append(_calc, ignore_index=True)
            print(f">> Completed Collection: {res} ")
        except Exception as z:
                get_key(z)  
    
    calc.to_excel(f'{out_path}eye_metrics_raw.xlsx', index = False)

    calc = calc.loc[(calc['Duration']>=150) & (calc['Duration']<=900)]
    
    calcs = pd.DataFrame()

    resps = calc['Res'].drop_duplicates()
    
    #Calculating metrics from raw (FFD and TFD)
    for res in resps:                
        _res = calc.loc[calc['Res']==res]
        stims = _res['Stim'].drop_duplicates()

        for stim in stims:
            _stim = _res[_res['Stim']== stim].sort_values('Timestamp')
            aois = _stim['AOI'].dropna().drop_duplicates()

            for aoi in aois:
                _aoi = _stim.loc[_stim['AOI']==aoi].sort_values('Timestamp')
                _calcs = {'Res':res,
                        'Stim':stim,
                        'AOI':f"{stim}_{aoi}",
                        'Timestamp':_aoi['Timestamp'].iloc[0],
                        'Index':_aoi['Index'].iloc[0],
                        'TFD':_aoi['Duration'].sum(),
                        'FFD':_aoi['Duration'].iloc[0],
                        'Tonic':_aoi['Tonic'].iloc[0],
                        'dPD':_aoi['dPD'].iloc[0],
                        'Peaks':_aoi['Peaks'].iloc[0],
                        'ICA':_aoi['ICA'].iloc[0]}

                calcs = calcs.append(_calcs, ignore_index=True)

    calcs.to_excel(f'{out_path}eye_metrics_final.xlsx', index = False)
    
    #Calculates averages per AOI
    data = calcs
    data = data.groupby(['AOI']).mean()
    data['Stim'] = [list(calcs[calcs['AOI']==AOI]['Stim'])[0] for AOI in data.index]
    data['AOI'] = [AOI for AOI in data.index]
    data.to_excel(f'{out_path}RESULT_eye_metrics_AOI_performance.xlsx', index = True)

    #Add code here to exclude certain AOIs from percentiles
    #exclude = ['Partner','CallToAction','Logo','Partner','KeyVisual']

    #Calculate percentiles acroos entire dataset (for AOIS)
    data = data.loc[~data['AOI'].str.contains('|'.join(exclude))]

    #Count how many particpants looked at each AOI
    #Exclu
    #de AOIs where less than 50% view count
    data2 = percentiles_df(data,'AOI',['TFD','ICA','FFD'])
    data2.to_excel(f'{out_path}RESULT_saliency_AOI_percentiles.xlsx', index = True)

    data2['Stim'] = [list(calcs[calcs['AOI']==AOI]['Stim'])[0] for AOI in data.index]
    data2 = data2.groupby(['Stim']).mean()

    data2.to_excel(f'{out_path}RESULT_saliency_stims_percentiles.xlsx', index = True)


def get_scene_times(in_folder, out_folder, results_folder): 
    
    #todo: 
    #   - move calcs to element->attribute
    #   - add stats calc

    task = 'SceneTimes'
    header(f"> Running: Getting Scene Times")
    in_path = f"{in_folder}"
    out_path = f"{results_folder}"
    os.makedirs(in_path, exist_ok=True) 
    os.makedirs(out_path, exist_ok=True)  
    
    #Define variables
    calc_col = ['Ad','Scene','Alpha Mean','Alpha Prop','Alpha Count']
    calc = pd.DataFrame(columns = calc_col)
    
    #For respondant specific data
    scalc = pd.DataFrame(columns = calc_col)
    
    keep = ['Row','Timestamp']

    #For each Ad..
    file = get_files(in_path)[0]
    scenes_df = pd.DataFrame(columns=['SourceStimuliName','Scene'])
    path = f"{in_path}{file}"
    df = read_imotions(path)
    ads = df['SourceStimuliName'].drop_duplicates().tolist()
    scene_timings = {ad:{} for ad in ads}

    for ad in ads:
            clean = df[df['SourceStimuliName']==ad]
            scenes = [s for s in df.columns if ad in s]
            scenes = [s for s in scenes if 'active' in s]
            scenes_keys = {s:{'start':0,'stop':0} for s in scenes}
            scene_timings[ad] = scenes_keys
            
            ad_start_time = float(clean[clean['SlideEvent']=='StartMedia']['Timestamp'].values[0])
            ad_duration = list(clean['Duration'])[0]
            clean['Time']= clean['Timestamp']-ad_start_time
            clean = clean[(clean['Time'] <= ad_duration) & (clean['Time'] >= 0)]
            clean = clean.replace(to_replace=' ',value=np.nan)

            print(scenes)
            for scene in scenes:
                _data = clean.dropna(subset=[scene])
                _time = list(_data['Time'])
                scene_timings[ad][scene]['start']=_time[0]
                scene_timings[ad][scene]['stop']=_time[-1]

                _clean = {'SourceStimuliName':ad,
                         'Scene':scene.split(' ')[0],
                         'SceneStart':int(_time[0]),
                         'SceneEnd':int(_time[-1])}
                scenes_df= scenes_df.append(_clean, ignore_index=True)

            


    df = pd.DataFrame.from_dict(scene_timings)
    scenes_df.to_csv(f"{out_path}scene_timings.csv",index = False)

    return scene_timings

def get_scene_times_TwoViewings(in_folder, out_folder, results_folder): 
    # todo: 
    #   - move calcs to element->attribute
    #   - add stats calc

    task = 'SceneTimes'
    print(f"> Running: Getting Scene Times")
    in_path = f"{in_folder}"
    out_path = f"{results_folder}"
    os.makedirs(in_path, exist_ok=True) 
    os.makedirs(out_path, exist_ok=True)  
    
    # Define variables
    calc_col = ['Ad','Scene','Alpha Mean','Alpha Prop','Alpha Count']
    calc = pd.DataFrame(columns = calc_col)
    
    # For respondent specific data
    scalc = pd.DataFrame(columns = calc_col)
    
    keep = ['Row','Timestamp']

    # For each Ad..
    file = get_files(in_path)[0]
    scenes_df = pd.DataFrame(columns=['SourceStimuliName','Scene', 'SceneStart', 'SceneEnd'])
    path = os.path.join(in_path, file)
    df = read_imotions(path)
    df['SourceStimuliName'] = df['SourceStimuliName'].apply(lambda x: '_'.join(x.split('_')[:-1]))

    ads = df['SourceStimuliName'].drop_duplicates().tolist()
    scene_timings = {ad: {} for ad in ads}

    for ad in ads:
        clean = df[df['SourceStimuliName'] == ad]
        scenes = [s for s in df.columns if ad in s]
        scenes = [s for s in scenes if 'active' in s]
        scenes_keys = {s: {'start': 0, 'stop': 0} for s in scenes}
        scene_timings[ad] = scenes_keys

        ad_start_time = float(clean[clean['SlideEvent'] == 'StartMedia']['Timestamp'].values[0])
        ad_duration = list(clean['Duration'])[0]
        clean['Time'] = clean['Timestamp'] - ad_start_time
        clean = clean[(clean['Time'] <= ad_duration) & (clean['Time'] >= 0)]
        clean = clean.replace(to_replace=' ', value=np.nan)

        for scene in scenes:
            _data = clean.dropna(subset=[scene])
            _time = list(_data['Time'])
            if _time:
                scene_timings[ad][scene]['start'] = _time[0]
                scene_timings[ad][scene]['stop'] = _time[-1]

                _clean = {
                    'SourceStimuliName': [ad],
                    'Scene': ['_'.join(scene.split(' ')[:2])],
                    'SceneStart': [int(_time[0])],
                    'SceneEnd': [int(_time[-1])]
                }
                scenes_df = pd.concat([scenes_df, pd.DataFrame(_clean)], ignore_index=True)

    scenes_df['Scene'] = scenes_df['Scene'].str.replace('_active', '')
    scenes_df.to_csv(f"{out_path}/scene_timings.csv", index=False)

    return scene_timings

def split_and_zip_ads(in_folder, out_folder, results_folder): 
    
    #todo: 
    #   - move calcs to element->attribute
    #   - add stats calc

    task = 'Task2'
    header(f"> Running: Splitting")
    in_path = f"{in_folder}{task}/"
    out_path = f"{results_folder}{task}/"
    os.makedirs(in_path, exist_ok=True) 
    os.makedirs(out_path, exist_ok=True)  
    
    
    ads = ['1. Castle 60 Online 15h00-1080',
            'Animatic_DEREK',
            'Animatics_SHAKE',
            'Castle Lite_Renewable',
            'Castle Lite_Summer Promo',
            'CBL 30',
            'CBL_30_1',
            'Flying Fish_Just Flow With It',
            'FlyingFish_Refreshing_30',
            'Heineken _ Cheers to all',
            'Savanna_Chakalaka Norris',
            'What The Flying Fish',]

    scene_timings = get_scene_times(f"{in_folder}/scenes/", out_folder, results_folder)
    files = get_files(in_path)
    
    [os.makedirs(f"{out_path}{ad}/Alpha", exist_ok=True) for ad in ads]
    [os.makedirs(f"{out_path}{ad}/Eng and WL", exist_ok=True) for ad in ads]
    
    keep = ['SourceStimuliName',
            'SlideEvent',
            'Timestamp',
            'Row',
            'Frontal Asymmetry Alpha',
            'Workload Average',
            'High Engagement']

    for file in files:
        df = pd.read_csv(f"{in_path}{file}", header=27, low_memory = False)
        print(f">> Cleaning : {file[:-4]}")
        for ad in ads:
            _ad = df[df['SourceStimuliName']==ad]
            ad_start_time = float(_ad[_ad['SlideEvent']=='StartMedia']['Timestamp'])
            ad_duration = list(_ad['Duration'])[0]
            _ad = _ad[keep]
            _ad['Time']= _ad['Timestamp']-ad_start_time
            _ad = _ad[(_ad['Time'] <= ad_duration) & (_ad['Time'] >= 0)]
            _ad = _ad.replace(to_replace=' ',value=np.nan)

            for s in scene_timings[ad]:
                _ad[s]=''
                _ad.loc[(_ad['Time'] <= scene_timings[ad][s]['stop']) & (_ad['Time'] >= scene_timings[ad][s]['start']),s] = 'Active'
        
            _ad.to_csv(f"{out_path}{ad}/Alpha/{file}",index = False)
            _ad.to_csv(f"{out_path}{ad}/Eng and WL/{file}",index = False)


def mergeAll(in_folder, results_folder, header_row = 0):
    '''
    This function merges data from a batch of adds. 
    It also appends metadata to the files
    '''
    header("> Running: Merging All Data")
    out_path = f"{results_folder}"
    os.makedirs(out_path, exist_ok=True)           
    #Combine data per ad
    files = get_files(in_folder)
    all_data = pd.DataFrame()

    i = 0
    j = 0
    for file in files:
        try:
            path = in_folder + '/' + file
            #with open(path) as fd:
            #    metadata = [next(fd)[1:].split(',') for i in range(header_row) ]
            #metadata = {x[0]:x[1] for x in metadata}

            _data = read_imotions(path)
            _data.insert(0, 'Age', '25')
            _data.insert(0, 'Gender', 'NA')
            _data.insert(0, 'Group', 'M')
            _data.insert(0, 'Respondent',file[:-4])
            #try
            _data = _data.drop(columns = ['F3','F4'])
            _data = _data.dropna(how='all', subset=['High Engagement','Frontal Asymmetry Alpha','Fixation Index','SlideEvent'])
            #except:
            #    pass
            all_data = pd.concat([all_data, _data])
            print(f">> Collected: {file}")
            i+=1
        except Exception as z:
            get_key(z)
        if i%10 == 0:
            all_data.to_csv(f"{results_folder}MergedData_{j}.csv",index = False)
            j+=1
            all_data = pd.DataFrame()
            print('Completed')
    
    all_data.to_csv(f"{results_folder}MergedData_{j}.csv",index = False)
    print('Completed')


def convertAnnotation(in_folder, results_folder):
    header("> Running: Converting All Data")
    out_path = f"{results_folder}"
    os.makedirs(out_path, exist_ok=True)           
    #Combine data per ad
    files = get_files(in_folder, tags=['Annotation',])

    for file in files:
        path = in_folder + '/' + file
        df = read_imotions(path)

        df = df.rename(columns={'Stimulus Name':'SourceStimuliName',
                                'Marker Name':'Scene',
                                'Start Time (ms)':'SceneStart',
                                'End Time (ms)':'SceneEnd'})
        df = df[['SourceStimuliName','Scene','SceneStart','SceneEnd']]
        df['SourceStimuliName'] = df['SourceStimuliName'].replace({'REESE_S_Yes!_30_01':'REESES_Yes_30_01',
                                              'BMW_Talkin Like Walken_60_01 (1)-1':'BMW_Talkin Like Walken_60_02',
                                              'OREO_OREO Makes Twistory_30_01-1':'OREO_OREO Makes Twistory_30_02',
                                              'Budweiser_Old School_60_01-1':'Budweiser_Old School_60_02',
                                              'REESE_S_Yes!_30_01-1':'REESES_Yes_30_02',
                                              'Booking.com_Tina Fey_30_01':'BookingCom_Tina Fey_30_01',
                                              'Homes.com_Mascot_30_01':'HomesCom_Mascot_30_01',
                                              "M&M’S_Almost Champions_30_01":'MandMS_Almost Champions_30_01',
                                              'Dunkin’_‘The DunKings_60_01':'Dunkin_The DunKings_60_01',
                                              'e.l.f Cosmetics_In e.l.f we Trust_30_01':'elf Cosmetics_In elf we Trust_30_01',
                                              'Pfizer_Here’s to Science_60_01':'Pfizer_Heres to Science_60_01',
                                              'Doritos_Dina & Mita_60_01':'Doritos_Dina and Mita_60_01',
                                              'Skechers_Mr. T in Skechers_30_01':'Skechers_Mr T in Skechers_30_01',
                                              'Verizon_Can’t B Broken_60_01':'Verizon_Cant B Broken_60_01',
                                              'Homes.com_Mascot_30_01':'HomesCom_Mascot_30_01',
                                              'T-Mobile_Home Internet Feeling_60_01':'TMobile_Home Internet Feeling_60_01',
                                              'Apartments.com_Extraterrentrials_30_01':'ApartmentsCom_Extraterrentrials_30_01',
                                              'Starry_It’s Time To_30_01':'Starry_Its Time To_30_01',
                                              'NERDS_Flashdance..._30_01':'NERDS_Flashdance_30_01',
                                              })
        df['Scene'] = df['Scene'].replace(' ','_')
        df.loc[df['Scene'].str.contains('Brand'), 'Scene']= 'Brand_Connection'
        df.loc[df['Scene'].str.contains('Stop'), 'Scene']= 'Stopping_Power'
        df.loc[df['Scene'].str.contains('Clos'), 'Scene']= 'Closing_Power'

        path = results_folder + '/' + file
        df.to_csv(path, index = False)

def mergeAllTwoViewings(in_folder, results_folder):
    '''
    This function merges data from a batch of adds. 
    It also appends metadata to the files
    '''
    header("> Running: Merging All Data")
    out_path = f"{results_folder}"
    os.makedirs(out_path, exist_ok=True)           
    #Combine data per ad
    files = get_files(in_folder)
    all_data = pd.DataFrame(columns = ['High Engagement','Frontal Asymmetry Alpha','Fixation Index','SlideEvent'])

    i = 0
    j = 0
    for file in files:
        try:
            path = in_folder + '/' + file
            _data = read_imotions(path)
            _data.insert(0, 'Age', '25')
            _data.insert(0, 'Gender', 'NA')
            _data.insert(0, 'Group', 'M')
            _data.insert(0, 'Respondent',file[:-4])
            #try
            _data = _data.drop(columns = ['F3','F4'])

            try:
                _data = _data.dropna(how='all', subset=['High Engagement','Frontal Asymmetry Alpha','Fixation Index','SlideEvent'])
            except:
                _data = _data.dropna(how='all', subset=['Frontal Asymmetry Alpha','Fixation Index','SlideEvent'])
                print(f">>>>> Failed: High Engagement for {file}")

            ### Change column to "AOIs gazed at"
            try:
                _data = _data.rename({"Respondent Annotations active":"AOIs gazed at"},axis=1)
                _data["AOIs gazed at"]=_data['AOIs gazed at'].replace(" dwelled on","")
            except:
               print(f">>>>> ET: No ET for {file}")
               pass
            #############
            for stim in  _data['SourceStimuliName'].drop_duplicates().tolist():
                start=_data.loc[(_data['SourceStimuliName']==stim)
                                &(_data['SlideEvent']=='StartMedia')]['Timestamp'].values[0]
                _data.loc[(_data['SourceStimuliName']==stim), 'Timestamp']=_data.loc[(_data['SourceStimuliName']==stim)]['Timestamp']-start

            # ### Rename stims
            _data['SourceStimuliName'] = _data['SourceStimuliName'].replace({'Royovac_Imagine Your Life_15_01-1':'Royovac_Imagine Your Life_15_02',
                                              })
            # Change remove first and second viewing
            _data['SourceStimuliName']= _data['SourceStimuliName'].apply(lambda x: '_'.join(x.split('_')[:-1]))

            
            ##########

            
            all_data = pd.concat([all_data, _data])
            print(f">> Collected: {file}")
            i+=1
        except Exception as z:
            get_key(z)
            print(f">> Failed: {file}")
        if i%10 == 0:

            desired_columns = ['Respondent', 'Group', 'Gender']

            # Include the rest of the columns in the order after the desired columns
            new_column_order = desired_columns + [col for col in all_data.columns if col not in desired_columns]

            # Reorder the DataFrame columns
            all_data = all_data[new_column_order]
            
            all_data.to_csv(f"{results_folder}MergedData_{j}.csv",index = False)
            j+=1
            all_data = pd.DataFrame()
            print('Completed')
    
    all_data['Timestamp'] = all_data['Timestamp'].astype(str).str.replace("'", "")
    all_data['Timestamp'] = all_data['Timestamp'].astype(float).round(0).astype(int)

    desired_columns = ['Respondent', 'Group', 'Gender']

    # Include the rest of the columns in the order after the desired columns
    new_column_order = desired_columns + [col for col in all_data.columns if col not in desired_columns]

    # Reorder the DataFrame columns
    all_data = all_data[new_column_order]   
       
    all_data.to_csv(f"{results_folder}MergedData_{j}.csv",index = False)
    print('Completed')


def read_imotions(path):
    file = open(path, 'r')
    count = 0
    while True:
        line = file.readline()
        if '#' in line.split(',')[0]:
            count += 1
        else:
            break
    file.close()
    return pd.read_csv(path, header=count, low_memory=False)


def parse_two_viewings(in_folder):
    files = get_files(f'{in_folder}',tags=['.csv',])
    for file in files:
        try:
            df = read_imotions(f'{in_folder}{file}')

            for stim in  df['SourceStimuliName'].drop_duplicates().tolist():
                start=df.loc[(df['SourceStimuliName']==stim)
                                &(df['SlideEvent']=='StartMedia')]['Timestamp'].values[0]
                df.loc[(df['SourceStimuliName']==stim), 'Timestamp']=df.loc[(df['SourceStimuliName']==stim)]['Timestamp']-start

            df['SourceStimuliName']= df['SourceStimuliName'].apply(lambda x: '_'.join(x.split('_')[:-1]))
            df.to_csv(f'{in_folder}{file}')
            print_status('Parsed',file)
        except:
            print_status('Failed Rename',file)
            pass



if __name__ == "__main__":
    main()