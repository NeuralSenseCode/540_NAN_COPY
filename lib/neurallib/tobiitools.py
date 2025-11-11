
from .clean import * 
from subprocess import call
import re
from scipy.stats import f_oneway
from matplotlib import font_manager
from wordcloud import WordCloud, ImageColorGenerator
from PIL import Image
from nltk.stem import WordNetLemmatizer

#'deepskyblue'
BAR_COLORS = ['lightgrey',
              'lightskyblue',
              'steelblue',
              'slategrey',
              'lightgrey',
              'lightskyblue',
              'steelblue',
              'slategrey',
              'lightgrey',
              'lightskyblue',
              'steelblue',
              'slategrey',
              'lightgrey',
              'lightskyblue',
              'steelblue',
              'slategrey',
              'lightgrey',
              'lightskyblue',
              'steelblue',
              'slategrey',
              'lightgrey',
              'lightskyblue',
              'steelblue',
              'slategrey',
              ]

def get_significance(data, list, cluster):
    significance = pd.DataFrame()
    for e in list:
        try:
            treatment = data[e]
            other_elements = [i for i in list if i != e]
            for o in other_elements:
                    control = data[o]
                    _,pValue = f_oneway(treatment, control)
                    cohenD, hedgesG = get_effect(treatment,control)

                    label = f"{control}_to_{treatment}"
                    result = {'Test':label,
                            'Control':e,
                            'Treatment':o,
                            'pValue':pValue,
                            'Confidence':100-pValue*100,
                            'EffectSize':cohenD,
                            'CorrectedEffectSize':hedgesG,
                            'nC':len(control),
                            'nT':len(treatment),
                            'Cluster':cluster}
                    significance = significance.append(result, ignore_index= True)
        except:
            pass
    return significance


def get_significance_footnote(sig,clusters = False):
    footnote = str()
    footnoteLines = 0
    if len(sig):
        footnote = 'Result are statistically significant, with a value of\n'
        for index, row in sig.iterrows():
            if (row['pValue'] < 0.001):
                if clusters:
                    text = f"p<0.001 between {row['Control']} and {row['Treatment']} (n={row['nT']:.0f}) in {row['Cluster']}"
                else:
                    text = f"p<0.001 between {row['Control']} and {row['Treatment']} (n={row['nT']:.0f})"
            else:
                if clusters:
                    text = f"p<0.05 between {row['Control']} and {row['Treatment']} (n={row['nT']:.0f}) in {row['Cluster']}"
                else:
                    text = f"p<0.05 between {row['Control']} and {row['Treatment']} (n={row['nT']:.0f})"
            if footnoteLines:
                footnote = footnote + ' and\n'
            footnote = footnote + text
            footnoteLines += 1
    else:
        footnote = 'Results did not show any statistical significance'
    footnoteLines +=1

    return footnote,footnoteLines


def flash_exposure(in_folder,results_folder,key_path = None): 

    task = 'FlashExposure'
    header(f"> Running: {task}")
    
    #Create directories and paths for filesave
    in_path = f"{in_folder}Raw/"
    key_path = f"{in_folder}Keys/{key_path}"
    out_path = f"{results_folder}{task}/"
    os.makedirs(out_path, exist_ok=True)  
    
    #Get input files
    files = get_files(in_path,tags=['.tsv',])

    #Intialise working dataframes
    data = pd.DataFrame()
    keep = ['Presented Stimulus name', 'Event', 'Event value']
    keyboards = ['Left','Right']

    for f in files:
        path = f"{in_path}{f}"
        df = pd.read_csv(path, delimiter='\t',low_memory=False)
        df = df[keep]

        #Get shifted stimulus column
        df['Slide'] = df['Presented Stimulus name'].shift(1)
        df = df[['Event value','Slide']].dropna()


        #Get rows for this task only
        for k in keyboards:
            _df = df.loc[(df['Event value']==k)]
            _df = _df.loc[df['Slide'].str.contains('Slide')]
            data = pd.concat([data, _df])

        print_status('Extracted',path)

    #Get key file
    keys = pd.read_csv(key_path)
    slides = keys['Slide Number'].tolist()

    data = data.reset_index()
    data.to_excel(f'{out_path}{task}_Raw0.xlsx', index = False)

    for index, row in data.iterrows():
        #Get slide number
        slide = int(row['Slide'][5:].split(" ")[0])
        if slide in slides:
            choice = row['Event value']
            #Get preference
            info = keys.loc[keys['Slide Number']==slide]
            data.loc[index, 'Salient'] = info[choice].values[0]
            data.loc[index, 'Category'] = info['Stim'].values[0]
            data.loc[index, 'Variant'] = info['Variant'].values[0]
            data.loc[index, 'Shown'] = info['Left'].values[0]+info['Right'].values[0]
    data = data.dropna()

    data.to_excel(f'{out_path}{task}_Raw.xlsx', index = False)
    
    #Initialise results dataframes
    results = pd.DataFrame()
    significance = pd.DataFrame()
    
    routes = pd.concat([keys['Left'], keys['Right']]).drop_duplicates().tolist()

    #Do calcs per route
    significance = pd.DataFrame()
    stats_routes = {}

    for r in routes:
        route = data.loc[data['Shown'].str.contains(r)]
        route.loc[route['Salient']==r, ['Preferred']] = 1
        route.loc[route['Salient']!=r, ['Preferred']] = 0
        stats_routes[r] = route['Preferred']
        chosen = route['Preferred'].sum()

        result = dict()
        result['Route'] = r
        result['Proportion'] = chosen/len(route)*100
        result['Type'] = 'Overall'
        result['Cluster'] = 'Overall'
        results = results.append(result,ignore_index = True)     
    significance = pd.concat([significance, get_significance(stats_routes, routes, 'Overall')])  

    categories = data['Category'].drop_duplicates().tolist()
    for c in categories:
        category = data.loc[data['Category']==c]
        stats_routes= {}
        for r in routes:
            route = category.loc[category['Shown'].str.contains(r)]
            route.loc[route['Salient']==r, ['Preferred']] = 1
            route.loc[route['Salient']!=r, ['Preferred']] = 0
            stats_routes[r] = route['Preferred']
            chosen = route['Preferred'].sum()

            result = dict()
            result['Route'] = r
            result['Proportion'] = chosen/len(route)*100
            result['Type'] = 'Category'
            result['Cluster'] = f'{c}'
            results = results.append(result,ignore_index = True)        
        significance = pd.concat([significance, get_significance(stats_routes, routes, c)])

        variants = category['Variant'].drop_duplicates().tolist()   
        for v in variants:
            variant = category.loc[category['Variant']==v]
            stats_routes= {}
            for r in routes:
                route = variant.loc[variant['Shown'].str.contains(r)]
                route.loc[route['Salient']==r, ['Preferred']] = 1
                route.loc[route['Salient']!=r, ['Preferred']] = 0
                stats_routes[r] = route['Preferred']
                chosen = route['Preferred'].sum()

                result = dict()
                result['Route'] = r
                result['Proportion'] = chosen/len(route)*100
                result['Type'] = 'Variant'
                result['Cluster'] = f'{c}- {v}'
                results = results.append(result,ignore_index = True) 
        
            significance = pd.concat([significance, get_significance(stats_routes, routes, f'{c}- {v}')])

    results.to_excel(f'{out_path}{task}_Results.xlsx', index = False)
    significance.to_excel(f'{out_path}{task}_Significance.xlsx', index = False)
    significance = significance.drop_duplicates(subset=['Cluster','pValue'])

    #Plot results
    clusters = results['Cluster'].drop_duplicates().tolist()
    for cluster in clusters:
        _data = results.loc[results['Cluster']==cluster]
        _x_data = _data['Route']
        _prop_data = _data['Proportion'].values

        ### Add footnote for significance
        sig = significance.loc[(significance['Cluster']==cluster) & (significance['pValue']<=0.055)]
        footnote,footnoteLines = get_significance_footnote(sig)

        plot.bar(out_path,
                    _x_data,
                    _prop_data,
                    bar1_color ='deepskyblue',
                    xlabel = '',
                    y1label = 'Percentage Preferance (%)',
                    title = cluster,
                    y1lim = 100,
                    tag = "",
                    footnote = footnote,
                    footnoteLines = footnoteLines
                    )
    
    return None


def pack_navigation(in_folder,results_folder,task_tag=None): 

    task = 'PackNavigation'
    header(f"> Running: {task}")
    
    #Create directories and paths for filesave
    in_path = f"{in_folder}Raw/"
    out_path = f"{results_folder}{task}/"
    os.makedirs(out_path, exist_ok=True)  
    
    #Get input files
    files = get_files(in_path,tags=['.tsv',])

    #Intialise working dataframes
    data = pd.DataFrame()
    keep = ['Presented Stimulus name','Computer timestamp']
    AOI_data = pd.DataFrame()
    raw_AOI_data = pd.DataFrame()

    for f in files:
        path = f"{in_path}{f}"
        df = pd.read_csv(path, delimiter='\t',low_memory=False)

        ##Special correction for Project Green
        #df.rename(columns=lambda s: s.replace("powderproductName", "powder_productName"), inplace=True)
        #df.rename(columns=lambda s: s.replace("multi-purpose", "multiPurpose"), inplace=True)
        df.rename(columns=lambda s: s.replace('AOI hit [Slide55 - T2_R1Super_Regular_keyVisual_00]', 'AOI hit [Slide55 - T2_R1_Super_Regular_keyVisual_00]'), inplace=True)

        #For each aoi, get FFD and TTFF
        AOI_cols = [c for c in df.columns if 'AOI' in c]
        AOI_cols = [c for c in AOI_cols if task_tag in c]
        #print(AOI_cols)
        for c in AOI_cols:
            data = df[keep+[c,]].dropna()
            if len(data):
                start_time = data['Computer timestamp'].values[0]
                data.insert(0, 't', data['Computer timestamp']-start_time, True)
                data = data.loc[data['t']>=150]
                fixation_count = 0
                fixations = pd.DataFrame()
                for i, event in data.groupby([(data[c] != data[c].shift()).cumsum()]):
                    if event[c].sum():
                        duration = event.t.values[-1]-event.t.values[0]
                        if (duration > 150) and (duration <900):
                            result = {}
                            result['Start'] = event.t.values[0]
                            result['Duration'] = duration
                            fixations = fixations.append(result, ignore_index=True)
                if len(fixations):
                    result = {}
                    fields = c.split(task_tag)[1][:-1]
                    fields = fields.split('_')
                    result['ID']=c
                    result['Respondent']=f
                    result['Route']=fields[1]
                    result['Category']=fields[2]
                    result['Variant']=fields[3]
                    result['AOI']= fields[4]
                    result['Instance']=fields[5]
                    result['TTFF']=fixations['Start'].values[0]
                    result['TFD']=fixations['Duration'].sum()
                    result['FFD']=fixations['Duration'].values[0]
                    AOI_data = AOI_data.append(result, ignore_index=True)
                    raw_AOI_data = raw_AOI_data.append(result, ignore_index=True)
        print_status('Extracted',path)
    
    data = pd.DataFrame()
    for i, ID in AOI_data.groupby(['ID']):
        result = ID.iloc[0].to_dict()
        result['TTFF']=ID['TTFF'].mean()
        result['TFD']=ID['TFD'].mean()
        result['FFD']=ID['FFD'].mean()
        result['Count']=len(ID)
        data = data.append(result, ignore_index=True)

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
    for k in AOIs:
        plot_data = pd.DataFrame()
        stats_routes_TFD = {}
        stats_routes_FFD = {}
        stats_routes_TTFF = {}
        for r in routes:
            route = raw_AOI_data.loc[(raw_AOI_data['Route']==r) & (raw_AOI_data['AOI']==k)]
            stats_routes_TFD[r] = route['TFD']
            stats_routes_FFD[r] = route['FFD']
            stats_routes_TTFF[r] = route['TTFF']
            result = {}
            result['Route'] = r
            result['TFD'] = route['TFD'].mean()
            result['FFD'] = route['FFD'].mean()
            result['TTFF'] = route['TTFF'].mean()
            result['AOI'] = k
            plot_data = plot_data.append(result,ignore_index=True)
            AOI_Results = AOI_Results.append(result,ignore_index=True)
        significance = pd.concat([significance, get_significance(stats_routes_TFD, routes,f'{k}_TFD')])
        significance = pd.concat([significance, get_significance(stats_routes_FFD, routes,f'{k}_FFD')])
        significance = pd.concat([significance, get_significance(stats_routes_TTFF, routes,f'{k}_TTFF')])
        significance = significance.drop_duplicates(subset=['Cluster','pValue'])

        ### Add footnote for significance
        sig = significance.loc[(significance['Cluster']==f'{k}_TFD') & (significance['pValue']<=0.055)]
        footnote,footnoteLines = get_significance_footnote(sig)
        _x_data = plot_data['Route']
        _prop_data = plot_data['TFD'].values
        plot.bar(out_path,
                    _x_data,
                    _prop_data,
                    bar1_color ='deepskyblue',
                    xlabel = '',
                    y1label = 'Average Total Fixation Duration (ms)',
                    title = f'Visual Hierarchy of {k}',
                    tag = "",
                    footnote = footnote,
                    footnoteLines = footnoteLines
                    )

        sig = significance.loc[(significance['Cluster']==f'{k}_FFD') & (significance['pValue']<=0.055)]
        footnote,footnoteLines = get_significance_footnote(sig)
        _prop_data = plot_data['FFD'].values
        plot.bar(out_path,
                    _x_data,
                    _prop_data,
                    bar1_color ='deepskyblue',
                    xlabel = '',
                    y1label = 'Average First Fixation Duration (ms)',
                    title = f'Attention Holding Power of {k}',
                    tag = "",
                    footnote = footnote,
                    footnoteLines = footnoteLines
                    )

        sig = significance.loc[(significance['Cluster']==f'{k}_TTFF') & (significance['pValue']<=0.055)]
        footnote,footnoteLines = get_significance_footnote(sig)
        _prop_data = plot_data['TTFF'].values
        plot.bar(out_path,
                    _x_data,
                    _prop_data,
                    bar1_color ='deepskyblue',
                    xlabel = '',
                    y1label = 'Average Time to First Fixation (ms)',
                    title = f'Attention Grabbing Power of {k}',
                    tag = "",
                    footnote = footnote,
                    footnoteLines = footnoteLines
                    )
    
    AOI_Results.to_excel(f'{out_path}{task}_AOI_Results.xlsx', index = False)
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


def mobile_shelf_exposure(in_folder,results_folder,task_tag=None,pack_graphs=False): 

    task = 'MobileShelfExposure'
    header(f"> Running: {task}")
    
    #Create directories and paths for filesave
    in_path = f"{in_folder}{task_tag}/"
    out_path = f"{results_folder}{task}_{task_tag}/"
    os.makedirs(out_path, exist_ok=True)  
    
    #Get input files
    files = get_files(in_path,tags=['.tsv',])

    #Intialise working dataframes
    data = pd.DataFrame()
    keep = ['Computer timestamp','Event']
    AOI_data = pd.DataFrame()
    raw_AOI_data = pd.DataFrame()

    for f in files:
        path = f"{in_path}{f}"
        df = pd.read_csv(path, delimiter='\t', low_memory=False)

        #For each aoi, get FFD and TTFF
        AOI_cols = [c for c in df.columns if 'AOI' in c]
        AOI_cols = [c for c in AOI_cols if task_tag in c]
        for c in AOI_cols:
            data = df[keep+[c,]].dropna(subset=[c,])

            ####
            task_ID = c.split('[')[1].split(' ')[0]
            interval = data.dropna().loc[data.dropna()['Event'].str.contains(task_ID)]
            if len(interval):
                start_time = interval['Computer timestamp'].values[0]
                ####
                data.insert(0, 't', data['Computer timestamp']-start_time, True)
                data = data.loc[data['t']>=150]
                fixation_count = 0
                fixations = pd.DataFrame()
                for i, event in data.groupby([(data[c] != data[c].shift()).cumsum()]):
                    if event[c].sum():
                        duration = event.t.values[-1]-event.t.values[0]
                        if (duration > 150) and (duration <900):
                            result = {}
                            result['Start'] = event.t.values[0]
                            result['Duration'] = duration
                            fixations = fixations.append(result, ignore_index=True)
                if len(fixations):
                    result = {}
                    fields = c.split('-')[1].split(' ')[1].split('_')
                    
                    
                    result['ID']=c
                    result['Respondent']=f
                    result['Route']=fields[3]
                    result['Category']=fields[2]

                    ### Adjustment for KOO
                    #result['Variant']=fields[3]

                    #result['Variant']='_'.join(fields[4:])
                    result['Variant']=fields[0]
                    result['AOI']= fields[3]
                    result['Instance']=fields[4][:-1]
                    result['TTFF']=fixations['Start'].values[0]
                    result['TFD']=fixations['Duration'].sum()
                    result['FFD']=fixations['Duration'].values[0]
                    AOI_data = AOI_data.append(result, ignore_index=True)
                    raw_AOI_data = raw_AOI_data.append(result, ignore_index=True)
            else:
                pass
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
    key_tag = key_path[:-4]
    in_path = f"{in_folder}Raw/"
    key_path = f"{in_folder}Keys/{key_path}"
    out_path = f"{results_folder}{task}{task_tag}{key_tag}/"
    os.makedirs(out_path, exist_ok=True)  
    
    keys = pd.read_csv(key_path)
    keyboards = [str(c) for c in keys.columns if len(c)==1]
    #Get input files
    files = get_files(in_path,tags=['.tsv',])

    #Intialise working dataframes
    keyboard_data = pd.DataFrame()
    keyboard_keep = ['Presented Stimulus name', 'Event', 'Event value']
    keep = ['Presented Stimulus name', 'Event', 'Event value','Computer timestamp']
    AOI_data = pd.DataFrame()
    raw_AOI_data = pd.DataFrame()
    

    for f in files:
        path = f"{in_path}{f}"
        df = pd.read_csv(path, delimiter='\t',low_memory=False)
        #df.rename(columns=lambda s: s.replace("bioDegradable", "biodegradable"), inplace=True)
        #df.rename(columns=lambda s: s.replace("T4_T5_recyclable_00", "T4_R5_recyclable_00"), inplace=True)
        #df.rename(columns=lambda s: s.replace("T4_T4_natural_00", "T4_R4_natural_00"), inplace=True)
        #df = df.replace(to_replace='Slide229_2',value='Slide229')
        #df = df.replace(to_replace='Slide240_2',value='Slide240')
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
    
    
    
    #Get all routes
    routes = []
    for k in keyboards:
        _k = keys[k].drop_duplicates().dropna().tolist()
        routes = routes + _k
    routes = get_unique(routes)
    goals = keyboard_data['Goal'].drop_duplicates().tolist()


    #Initialise results dataframes
    results = pd.DataFrame()
    significance = pd.DataFrame()
    stats_routes = {}

    ###########################
    # For each goal:::

    for g in goals:
        if isAOIData:
            goal_AOI = AOI_mean_data.loc[AOI_mean_data['Goal']==g]
        goal = keyboard_data.loc[keyboard_data['Goal']==g]
        
        stats_routes = {}
        for r in routes:
            route = goal.loc[goal['Shown'].str.contains(r)]
            if len(route):
                route.loc[route['Choice']==r, ['Preferred']] = 1
                route.loc[route['Choice']!=r, ['Preferred']] = 0
                stats_routes[r] = route['Preferred']
                chosen = sum(route['Preferred'])

                result = dict()
                result['Route'] = r
                result['Chosen'] = chosen/len(route)*100
                result['Cluster'] = g

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
    clusters = results['Cluster'].drop_duplicates().tolist()
    for cluster in clusters:
        _data = results.loc[results['Cluster']==cluster].sort_values(by='Route')
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
        _data = results.loc[results['Cluster']==cluster].sort_values(by='Route')
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
                title = 'Combined Results',
                ylim = 100,
                #footnote = footnote,
                #footnoteLines = footnoteLines
                )

    ###########################
    # For each category:::
    #Initialise results dataframes
    results = pd.DataFrame()
    significance = pd.DataFrame()
    stats_routes = {}

    for g in goals:
        if isAOIData:
            goal_AOI = AOI_mean_data.loc[AOI_mean_data['Goal']==g]
        goal = keyboard_data.loc[keyboard_data['Goal']==g]
        
        categories = goal['Category'].drop_duplicates().tolist()
        for c in categories:
            category = goal.loc[goal['Category']==c]
            stats_routes = {}

            for r in routes:
                route = category.loc[category['Shown'].str.contains(r)]
                if len(route):
                    route.loc[route['Choice']==r, ['Preferred']] = 1
                    route.loc[route['Choice']!=r, ['Preferred']] = 0
                    stats_routes[r] = route['Preferred']
                    chosen = sum(route['Preferred'])

                    result = dict()
                    result['Goal'] = g
                    result['Category'] = c
                    result['Route'] = r
                    result['Chosen'] = chosen/len(route)*100
                    result['Cluster'] = f"{r}-{c}"

                    if isAOIData:
                        AOI = AOI_mean_data.loc[(AOI_mean_data['Goal']==g) & (AOI_mean_data['Category']==c) & (AOI_mean_data['AOI']==r)]
                        AOI = AOI_mean_data.loc[(AOI_mean_data['Goal']==g) & (AOI_mean_data['Category']==c) & (AOI_mean_data['AOI']==r)]['TFD'].values[0] if len(AOI) else 0
                        result['TFD'] = AOI
                    results = results.append(result,ignore_index = True)     
            significance = pd.concat([significance, get_significance(stats_routes, routes,c)])
        


    results.to_excel(f'{out_path}{task}Category_Results.xlsx', index = False)
    significance.to_excel(f'{out_path}{task}Category_Significance.xlsx', index = False)
    significance = significance.drop_duplicates(subset=['Cluster','pValue'])

    #Plot results
    clusters = results['Cluster'].drop_duplicates().tolist()
    for cluster in clusters:
        _data = results.loc[results['Cluster']==cluster].sort_values(by='Goal')
        _x_data = _data['Goal']
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
    
    results = results.sort_values(by='Cluster')
    x_data = results['Goal'].drop_duplicates()
    y_data = dict()
    i = 0
    clusters = results['Cluster'].drop_duplicates().tolist()
    for cluster in clusters:
        _data = results.loc[results['Cluster']==cluster].sort_values(by='Route')
        y_data[cluster] = dict()
        y_data[cluster]['values'] = _data['Chosen'].values
        y_data[cluster]['label'] = cluster
        y_data[cluster]['bar_color'] = BAR_COLORS[i]
        i += 1

    ### Add footnote for significance
    #sig = significance.loc[(significance['pValue']<=0.055)]
    #footnote,footnoteLines = get_significance_footnote( sig, clusters=True)
    try:
        plot.multi_bar(out_path,
                    x_data,
                    y_data,
                    xlabel = '',
                    ylabel = 'Percentage Chosen (%)',
                    title = 'Combined Category Results',
                    ylim = 100,
                    #footnote = footnote,
                    #footnoteLines = footnoteLines
                    )
    except:
        pass
        
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
        data = data.dropna()

        tasks = data['Task'].drop_duplicates().tolist()
        for t in tasks:
            task = data.loc[data['Task']==t]
            goals = task['Goal'].drop_duplicates().tolist()
            for g in goals:
                goal = task.loc[task['Goal']==g]

                categories = goal['Category'].drop_duplicates().tolist()
                for c in categories:
                    category =  goal.loc[goal['Category']==c]
                    choices = category['Choice'].drop_duplicates().tolist()
                    for r in choices:
                        choice = category.loc[category['Choice']==r]
                        #Exclude first column
                        words = flatten([r.split(' ') for r in choice['SelfReport'].tolist()])       
                        words = ' '.join(words)
   
                        wc = WordCloud(font_path=font_path, colormap=colormap, background_color=background_color,width=width,height=height).generate_from_text(words)
        
                        plt.figure(figsize=(20,10))
                        plt.imshow(wc)
                        plt.axis('off')
                        plt.savefig(f'{out_path}{t}_{g}_{c}_{r}.png', dpi=300, transparent=True)
                        plt.close()
                        print_status('Completed',f'{out_path}{t}_{g}_{c}_{r}')
        
        choices = data['Choice'].drop_duplicates().dropna().tolist()
        choice_words = dict()
        choices = ['R1','R2','R3','C']
        for r in choices:
            choice = data.loc[data['Choice']==r]
            #Exclude first column
            
            words = flatten([r.split(' ') for r in choice['SelfReport'].tolist()])       
            words = ' '.join(words)
            choice_words[r]=words.split(' ')
            #wc = WordCloud(font_path=font_path, colormap=colormap, background_color=background_color,width=width,height=height).generate_from_text(words)
        
            #plt.figure(figsize=(20,10))
            #plt.imshow(wc)
            #plt.axis('off')
            #plt.savefig(f'{out_path}{r}.png', dpi=300, transparent=True)
            #plt.close()
            #print_status('Completed',f'{r}')
        
        unique_words=dict()
        for r in choices:
            other = [o for o in choices if o!=r]
            unique_words[r]=choice_words[r]
            for o in other:
                print(len(unique_words[r]))
                unique_words[r] = [w for w in unique_words[r] if w not in choice_words[o]]
                print(len(unique_words[r]))
            words = ' '.join(unique_words[r])
            wc = WordCloud(font_path=font_path, colormap=colormap, background_color=background_color,width=width,height=height).generate_from_text(words)
        
            plt.figure(figsize=(20,10))
            plt.imshow(wc)
            plt.axis('off')
            plt.savefig(f'{out_path}Only_in_{r}.png', dpi=300, transparent=True)
            plt.close()
            print_status('Completed',f'{r}')

if __name__ == "__main__":
    main()