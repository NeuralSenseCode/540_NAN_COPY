
from matplotlib import font_manager
import matplotlib.ticker as tck
from wordcloud import WordCloud, ImageColorGenerator
from PIL import Image
from nltk.stem import WordNetLemmatizer
from .clean import *
import seaborn as sns
import matplotlib.text as mtext
from matplotlib.colors import to_rgba

#Venera900 = 'Font/Venera/Venera 900/Venera-900.otf'  
#Venera100 = 'Font/Venera/Venera 100/Venera-100.otf'
#font_manager.fontManager.addfont(Venera900)
#font_manager.fontManager.addfont(Venera100)
#font1 = font_manager.FontProperties(fname=Venera100)
#font2 = font_manager.FontProperties(fname=Venera900)

def flatten_list(nested_list):
    """Flatten a nested list into a single list."""
    flat_list = []
    for item in nested_list:
        if isinstance(item, list):
            # If the item is a list, extend the flat list with the flattened item
            flat_list.extend(flatten_list(item))
        else:
            # If the item is not a list, append it to the flat list
            flat_list.append(item)
    return flat_list

def time_proportions(input_folder,results_folder, tags = ['',]):
    #header("> Running: Plotting Proportions Time Series")
    out_path = f"{results_folder}"
    os.makedirs(out_path, exist_ok=True) 

    dfs = {f"{f[12:-4]}": pd.read_csv(f'{input_folder}{f}', low_memory = False) for f in os.listdir(f'{input_folder}') if '.csv' in f and all(x in f for x in tags)}

    for ad,df in dfs.items():
        print(f">> Now Plotting: {ad}")
        y_dim = 3.6417323
        x_dim = 13.3346457
        labels = ['Alpha','Eng','WL']

        colors = {'Alpha':'black',
             'Eng':'steelblue',
             'WL':'deepskyblue'}

        xs = {'Alpha':df['Time Alpha'].dropna().to_numpy(),
             'Eng':df['Time Engagement'].dropna().to_numpy(),
             'WL':df['Time Workload'].dropna().to_numpy()}
        ys = {'Alpha':df['Frontal Asymmetry Alpha Filtered'].dropna().to_numpy(),
             'Eng':df['High Engagement Proportion Filtered'].dropna().to_numpy(),
             'WL':df['Optimal Workload Proportion Filtered'].dropna().to_numpy()}

        plt.rcParams['axes.edgecolor']='#333F4B'
        plt.rcParams['axes.linewidth']=0.8
        plt.rcParams['xtick.color']='#333F4B'
        plt.rcParams['ytick.color']='#333F4B'
        plt.rcParams['text.color']='#333F4B'

        fig = plt.figure()

        ax = fig.add_subplot(111)

        # change the style of the axis spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        ax.spines['left'].set_position(('outward', 8))
        ax.spines['bottom'].set_position(('outward', 5))

        axes = plt.gca()
        axes.get_xaxis().set_visible(False)

        #plt.title(title, fontsize=12)
        plt.xlim(0,xs['Alpha'].max())
        plt.ylim(0,100)
        plt.yticks(ha='left',rotation=90,fontsize=7,  )

        for label in labels:
            plt.plot(xs[label],ys[label],label = label, color = colors[label],linewidth=3)
        #if legend:
        #    plt.legend()

        fig.set_size_inches(x_dim, y_dim)
        plt.savefig(f'{out_path}plot_{ad}.png', dpi=300, transparent=True)
        plt.close()
    
    #header("> Completed: Plotting Proportions Time Series")


def bar(out_folder, xcol, y1col, bar1_color = [], xlabel = '', y1label = '', title = '', tags =['',], highlight = {'':'',}, y1lim =None, tag = None, footnote = None, footnoteLines=None, minorTicks = None, rotate_ticks = None):
    plt.rcParams['font.family'] = "Century Gothic"
    out_path = f"{out_folder}"
    os.makedirs(out_path, exist_ok=True)    
    
    print(f">> Running: Plotting Data for {title}")

    width = 0.65

    x_data = xcol
    y1_data = y1col
    
    fig = plt.figure()
    ax1 = std_axes(fig.add_subplot(111),
                  spines=['left','bottom'],
                  annotation_color = 'black',
                  x_labels=x_data,
                  ylabel=y1label,
                  title=title,
                  ylim=y1lim,
                  tickf = 8,
                  labelf = 12,
                  titlef = 12,
                  )

    bar1 = ax1.bar(x_data,y1_data, width= width, color= bar1_color, label = y1label)

    if rotate_ticks is not None:
        plt.xticks(rotation=45, ha = 'right', color= 'black')

    if minorTicks is not None:
        ax1.yaxis.set_minor_locator(tck.AutoMinorLocator())

    title = title.replace('\n', '')
    plt.savefig(f"{out_path}plot_bar_{title}{tag}.png", dpi=300, transparent=True, bbox_inches="tight" )
    
    plt.close()

    if footnote is not None:
        plt.figtext(0.5,0.5, footnote, ha="center", fontsize=8, bbox={"facecolor":'lightgrey', "alpha":0.5, "pad":5})

    # try:
    #     plt.savefig(f"{out_path}plot_sig_{title}{tag}.png", dpi=300, transparent=True, bbox_inches="tight" )
    #     plt.close()
    #     print(f">>> Plotted: {title}")
    # except:
    #     print(f">>> Failed: {title}")

def line_dot(out_folder, xcol, y1col, bar1_color ='#dadfe2', xlabel = '', y1label = '', title = '', tags =['',], highlight = {'':'',}, y1lim =None, tag = None, footnote = None, footnoteLines=None, minorTicks = None, spacing = False):
    plt.rcParams['font.family'] = "Century Gothic"
    out_path = f"{out_folder}"
    os.makedirs(out_path, exist_ok=True)    
    
    print(f">> Running: Plotting Data for {title}")

    width = 1.3

    # If spacing is True, adjust the x_data by the width factor
    if spacing:
        x_data = [i * width for i, _ in enumerate(xcol)]
    else:
        x_data = list(range(len(xcol)))  # Use simple range if no spacing
    
    y1_data = y1col
    
    if spacing:
        fig = plt.figure(figsize=(10, 5))  # You can adjust the size as needed
    else:
        fig = plt.figure()

    title = title.replace('\n', '')
    ax1 = std_axes(fig.add_subplot(111),
                  spines=['left','bottom'],
                  annotation_color = 'black',
                  x_labels=x_data,
                  ylabel=y1label,
                  title=title,
                  ylim=y1lim,
                  tickf = 12,
                  labelf = 12,
                  titlef = 12,
                  )

    prices = [16.99,
        19.99,
        19.99,
        19.99,
        21.99,
        19.99,
        24.99,
        24.99,
        24.99,
        24.99,
        34.99,
        39.99,
        39.99,
        39.99,
        39.99,
        49.99
        ]
    
    if len(x_data)==16:   
        error = [p * 0.3 for p in prices]
        ax1.errorbar(x_data, prices, yerr=error, fmt='none', ecolor='gray', capsize=3)
        ax1.scatter(x_data,prices,color = 'black',marker='*')
        

    line1 = ax1.plot(x_data,y1_data, color= bar1_color, label = y1label, marker='o')

    


    if spacing:
        ax1.set_xticks(x_data)
        ax1.set_xticklabels(xcol)

    #plt.xticks(rotation=45, ha = 'right', color= 'black')

    if minorTicks is not None:
        ax1.yaxis.set_minor_locator(tck.AutoMinorLocator())

    plt.savefig(f"{out_path}plot_lineDot_{title}{tag}.png", dpi=300, transparent=True, bbox_inches="tight" )
    
    plt.close()

    if footnote is not None:
        plt.figtext(0.5,0.5, footnote, ha="center", fontsize=8, bbox={"facecolor":'lightgrey', "alpha":0.5, "pad":5})

    try:
        plt.savefig(f"{out_path}plot_sig_{title}{tag}.png", dpi=300, transparent=True, bbox_inches="tight" )
        plt.close()
        print(f">>> Plotted: {title}")
    except:
        print(f">>> Failed: {title}")


def eeg_heatmap(out_folder, df, xcol, y1col, metric, title):
    """
    Used for EEG
    Generates and saves a heatmap from a DataFrame, positioning the specified
    (xcol, y1col) coordinates from bottom-left to top-right in the plotted heatmap.

    Parameters:
    - out_folder (str): Directory to save the output heatmap image.
    - df (pandas.DataFrame): DataFrame containing the data to plot.
    - xcol (str): Column name to use as the x-axis.
    - y1col (str): Column name to use as the y-axis.
    - metric (str): Column name whose values will determine the color intensity.
    - title (str): Title for the heatmap.

    The function saves the heatmap image in the specified output folder with
    a filename based on the title.
    """
    plt.rcParams['font.family'] = "Century Gothic"
    out_path = os.path.join(out_folder, f"heatmap_{title.replace(' ', '_')}.png")
    os.makedirs(out_folder, exist_ok=True)
    
    print(f">> Running: Plotting Heatmap for {title}")

    # Pivot the DataFrame to format suitable for heatmap plotting.
    # Ensure that the resulting pivot table orders 'xcol' ascending and 'y1col' descending
    # to match the desired bottom-left to top-right orientation.
    pivot_df = df.pivot_table(index=y1col, columns=xcol, values=metric, aggfunc='sum').iloc[::-1]
    # Explicitly reorder the index to ensure F, C, P from top to bottom
    desired_order = ['F', 'C', 'P']
    pivot_df = pivot_df.reindex(desired_order)
    
    fig, ax = plt.subplots()
    sns.heatmap(pivot_df, cmap='YlOrRd', linewidths=0.5, ax=ax)
    
    ax.set_title(title)
    plt.ylabel(y1col)
    plt.xlabel(xcol)

    plt.savefig(out_path, dpi=300, transparent=True, bbox_inches="tight")
    plt.close()

    print(f">>> Heatmap Plotted and Saved: {title}")


def heatmap(out_folder, df, xcol, y1col, metric, cmap = 'YlOrRd', linewidths=0.5, xlabel = '', y1label = '', title = '', tags =['',], highlight = {'':'',}, y1lim =None, tag = None, footnote = None, footnoteLines=None, minorTicks = None):
    """
    Generates and saves a heatmap based on the provided DataFrame and column specifications.

    Parameters:
    - out_folder (str): The output directory where the heatmap image will be saved.
    - df (pandas.DataFrame): The DataFrame containing the data to plot.
    - xcol (str): The name of the column to use as the x-axis in the heatmap.
    - y1col (str): The name of the column to use as the y-axis in the heatmap.
    - metric (str): The name of the column whose values will determine the color intensity in the heatmap.
    - cmap (str, optional): The colormap for the heatmap. Defaults to 'YlOrRd'.
    - linewidths (float, optional): The width of the lines that will divide each cell. Defaults to 0.5.
    - xlabel (str, optional): The label for the x-axis. Defaults to an empty string.
    - y1label (str, optional): The label for the y-axis. Defaults to an empty string.
    - title (str, optional): The title of the heatmap. Defaults to an empty string.
    - tags (list of str, optional): Tags for additional information. Defaults to an empty list.
    - highlight (dict, optional): A dictionary to highlight specific cells or areas in the heatmap. Defaults to an empty dictionary.
    - y1lim (tuple, optional): A tuple specifying the y-axis limits (min, max). Defaults to None.
    - tag (str, optional): An additional tag for the output filename. Defaults to None.

    Returns:
    - None: This function does not return a value but saves the generated heatmap to a file.

    Notes:
    - The function saves the heatmap as a PNG file with a resolution of 300 dpi and applies a transparent background.
    - The function automatically creates the output directory if it does not exist.
    - Adjust `plt.rcParams['font.family']` as needed based on available fonts in your environment.
    """
    plt.rcParams['font.family'] = "Century Gothic"
    out_path = f"{out_folder}"
    os.makedirs(out_path, exist_ok=True)    
    
    print(f">> Running: Plotting Data for {title}")

    pivot_df = df.pivot(xcol, y1col, metric)

    fig = plt.figure()
    ax1 = std_axes(fig.add_subplot(111),
                  spines=['left','bottom'],
                  annotation_color = 'black',
                  title=title,
                  ylim=y1lim,
                  tickf = 12,
                  labelf = 12,
                  titlef = 12,
                  )

    
    sns.heatmap(pivot_df, cmap=cmap, linewidths=linewidths, ax=ax1)

    plt.savefig(f"{out_path}plot_heatmap_{title}{tag}.png", dpi=300, transparent=True, bbox_inches="tight" )
    
    plt.close()

    if footnote is not None:
        plt.figtext(0.5,0.5, footnote, ha="center", fontsize=8, bbox={"facecolor":'lightgrey', "alpha":0.5, "pad":5})
        plt.savefig(f"{out_path}plot_sig_{title}{tag}.png", dpi=300, transparent=True, bbox_inches="tight" )
        plt.close()

    print(f">>> Plotted: {title}")

    


def double_bar(out_folder, xcol, y1col, y2col, bar1_color ='#dadfe2', bar2_color='#dadfe2', xlabel = '', ylabel='', y1label = '', y2label = '', title = '', tags =['',], highlight = {'':'',}, y1lim =None, ymin =None ,ymax =None  ):
    out_path = f"{out_folder}"
    os.makedirs(out_path, exist_ok=True)    
    
    print(f">> Running: Plotting Data for {title}")

    #df = df.replace(to_replace=np.nan,value=0)
    #df = df.sort_values(by=y1col,ascending=True)
    width = 0.35

    #x_data = df[xcol].values
    #y1_data = df[y1col].values
    #y2_data = df[y2col].values

    x_data = xcol
    y1_data = y1col
    y2_data = y2col

    x = np.arange(len(x_data))  # the label locations
    
    fig = plt.figure()
    ax1 = std_axes(fig.add_subplot(111),
                  spines=['left','bottom'],
                  annotation_color = 'black',
                  x_ticks=x,
                  x_labels=x_data,
                  xlabel=xlabel,
                  ylabel=ylabel,
                  title=title,
                  ymin = ymin,
                  ymax = ymax,
                  )

    bar1 = ax1.bar(x- width/2,y1_data,width, color= bar1_color, label = y1label)
    bar2 = ax1.bar(x + width/2,y2_data, width, color= bar2_color, label = y2label)
    
    ax1.legend(loc=2, bbox_to_anchor=(0.01,1),fontsize=4)
    #ax2.legend(loc=2, bbox_to_anchor=(0.01,0.965),fontsize=4)

    plt.tight_layout()
    plt.savefig(f"{out_path}plot_group_bar_{title}.png", dpi=300, transparent=True )

    print(f">>> Plotted: {title}")


def triple_bar(out_folder, xcol, y1col, y2col, y3col, bar1_color ='#dadfe2', bar2_color='#dadfe2', bar3_color='#dadfe2', xlabel = '', ylabel='', y1label = '', y2label = '', y3label = '', title = '', tags =['',], highlight = {'':'',}, y1lim =None ):
    out_path = f"{out_folder}"
    os.makedirs(out_path, exist_ok=True)    
    
    print(f">> Running: Plotting Data for {title}")

    #df = df.replace(to_replace=np.nan,value=0)
    #df = df.sort_values(by=y1col,ascending=True)
    width = 0.25

    #x_data = df[xcol].values
    #y1_data = df[y1col].values
    #y2_data = df[y2col].values

    x_data = xcol
    y1_data = y1col
    y2_data = y2col
    y3_data = y3col

    x = np.arange(len(x_data))  # the label locations
    
    fig = plt.figure()
    ax1 = std_axes(fig.add_subplot(111),
                  spines=['left','bottom'],
                  annotation_color = 'black',
                  x_ticks=x,
                  x_labels=x_data,
                  xlabel=xlabel,
                  ylabel=ylabel,
                  title=title,
                  ylim=y1lim,
                  )

    bar1 = ax1.bar(x- width,y1_data,width, color= bar1_color, label = y1label)
    bar2 = ax1.bar(x,y2_data, width, color= bar2_color, label = y2label)
    bar3 = ax1.bar(x + width,y3_data, width, color= bar3_color, label = y3label)
    
    ax1.legend(loc=2, bbox_to_anchor=(0.01,1),fontsize=4)
    #ax2.legend(loc=2, bbox_to_anchor=(0.01,0.965),fontsize=4)

    plt.tight_layout()
    plt.savefig(f"{out_path}plot_group_bar_{title}.png", dpi=300, transparent=True )

    print(f">>> Plotted: {title}")

def group_bar(out_folder, df, xcol, y1col, y2col, bar1_color ='#dadfe2', bar2_color='#dadfe2', xlabel = '', y1label = '', y2label = '', title = '', tags =['',], highlight = {'':'',}, y1lim =None, y2lim= None ):
    out_path = f"{out_folder}"
    os.makedirs(out_path, exist_ok=True)    
    
    print(f">> Running: Plotting Data for {title}")

    df = df.replace(to_replace=np.nan,value=0)
    df = df.sort_values(by=y1col,ascending=False)
    width = 0.35

    x_data = df[xcol].values
    y1_data = df[y1col].values
    y2_data = df[y2col].values
    x = np.arange(len(x_data))  # the label locations
    
    fig = plt.figure()
    ax1 = std_axes(fig.add_subplot(111),
                  spines=['left','right','bottom'],
                  x_ticks=x,
                  x_labels=x_data,
                  xlabel=xlabel,
                  ylabel=y1label,
                  title=title,
                  ylim=y1lim,
                  )

    ax2 = std_axes(ax1.twinx(),
                  ylabel=y2label,
                  ylim=y2lim,
                  )

    bar1 = ax1.bar(x- width/2,y1_data,width, color= bar1_color, label = y1label[:-3] )
    bar2 = ax2.bar(x + width/2,y2_data, width, color= bar2_color, label = y2label[:-3])
    
    ax1.legend(loc=2, bbox_to_anchor=(0,1),fontsize=4)
    ax2.legend(loc=2, bbox_to_anchor=(0,0.965),fontsize=4)
    
    plt.savefig(f"{out_path}plot_group_bar_{title}.png", dpi=300, transparent=True )

    print(f">>> Plotted: {title}")


def std_axes(ax, spines=[], annotation_color = 'white' , x_ticks=None, x_labels=None, xlabel=None, ylabel=None, title=None, ylim=None, ymin = None, ymax= None, titlef=12, tickf=6, labelf=8, second = False ):   
    # change the style of the axis spines
    plt.rcParams['font.family'] = "Century Gothic"
    #plt.rcParams['font.sans-serif'] = font1.get_name()
    #plt.rcParams['text.color'] = 'white'

    all = ['top','bottom','left','right']
    for spine in all:
        ax.spines[spine].set_linewidth(0.8)
        if spine in spines:
            #ax.spines[spine].set_position(('outward',0.5))
            ax.spines[spine].set_color(annotation_color)
        else:
            ax.spines[spine].set_visible(False)
   

    # ax.set_xticks(x_ticks) if x_ticks is not None else None
    # ax.set_xticklabels(x_labels, fontsize=tickf, rotation=45, ha = 'right', color= annotation_color) if x_labels is not None else None
    if x_ticks is not None:
        ax.set_xticks(x_ticks)
        if x_labels is not None:
            ax.set_xticklabels(x_labels, fontsize=tickf, rotation=45, ha='right', color=annotation_color)
    ax.tick_params(axis='both', labelsize=tickf, color= annotation_color, labelcolor= annotation_color)
    
    ax.set_xlabel(xlabel,fontsize=labelf, color=annotation_color) if xlabel is not None else None
    ax.set_ylabel(ylabel,fontsize=labelf, color=annotation_color, labelpad = 20) if ylabel is not None else None
    ax.set_ylabel(ylabel,fontsize=labelf, color=annotation_color, rotation=270, labelpad = 20) if ylabel is not None and second is True else None
    ax.set_title(title, fontsize=titlef, color=annotation_color) if title is not None else None 
    
    if ylim is not None:
        ax.set_ylim(0,ylim)
    elif ymin is not None:
        ax.set_ylim(ymin,ymax)  
    else:
        pass
    
    #ax.yaxis.grid()
    return ax


def str_extract_rows(df, col1, mark):
    for index, row in df.iterrows():
        df.at[index, col1] = row[col1][0:row[col1].find(mark)]
    return df


def pie(out_folder, vals, labels, colors, title=None, explode=None, startangle = 90, circle = 0.14,  annotation_color = 'white'):  
    out_path = f"{out_folder}"
    os.makedirs(out_path, exist_ok=True)   

    print(f">> Running: Plotting Data for {title}")

    y_dim = 5 /2.54
    x_dim = 7.5 /2.54
    
    fig = plt.figure()

    ax = fig.add_subplot(111)
                
    ax.pie(vals,
           startangle = startangle,
           labels=labels,
           colors =colors,
           explode=explode,
           radius = 0.4*x_dim,
           autopct='%1.0f%%',
           pctdistance=0.83,
           labeldistance=1.1,
           wedgeprops=dict(width=circle*x_dim),
           textprops={'color':annotation_color,
                      'fontsize':14})
    
    ax.set_title(title, fontsize=14, pad=25, color = annotation_color) if title is not None else None 
    #ax.add_artist(centre_circle)

    plt.tight_layout()
    plt.savefig(f"{out_path}plot_pie_chart_{title}.png", dpi=300, transparent=True )

    print(f">>> Plotted: {title}")


def box(out_folder, vals, labels, colors,xlabel=None, ylabel=None, xlim=None,  title=None,  annotation_color = 'white', vline=None):  
    out_path = f"{out_folder}"
    os.makedirs(out_path, exist_ok=True)   

    print(f">> Running: Plotting Data for {title}")
    
    fig = plt.figure()

    ax = std_axes(fig.add_subplot(111),
                  spines=['left','bottom'],
                  title=title,
                  tickf=14,
                  labelf=14,
                  titlef=14
                  )
                
    bp = ax.boxplot(vals, patch_artist = True, vert = 0)
    ax.set_xlabel(xlabel,fontsize=14, color=annotation_color) if xlabel is not None else None   
    ax.set_xlim(xlim) if xlim is not None else None

    colors = [colors[l] for l in labels]

    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
 
    # changing color and linewidth of
    # whiskers
    for whisker in bp['whiskers']:
        whisker.set(color =annotation_color,
                    linewidth = 1.5,
                    linestyle =":")
 
    # changing color and linewidth of
    # caps
    for cap in bp['caps']:
        cap.set(color =annotation_color,
                linewidth = 2)
 
    # changing color and linewidth of
    # medians
    for median in bp['medians']:
        median.set(color =annotation_color,
                    linewidth = 3)
 
    # changing style of fliers
    for flier in bp['fliers']:
        flier.set(marker ='D',
                    color =annotation_color,
                    alpha = 0.5)
     
    # x-axis labels
    ax.set_yticklabels(labels)   
    ax.set_title(title, fontsize=14, pad=25, color = annotation_color) if title is not None else None 
    #ax.add_artist(centre_circle)
    plt.axvline(vline, linestyle='dashed', color=annotation_color,linewidth=1) if vline is not None else None  

    plt.tight_layout()
    plt.savefig(f"{out_path}plot_box_plot_{title}.png", dpi=300, transparent=True )

    print(f">>> Plotted: {title}")


def quadrant(out_folder, yy,yn,ny,nn, title=None,):  
    out_path = f"{out_folder}"
    os.makedirs(out_path, exist_ok=True)   

    print(f">> Running: Plotting Quadrant for {title}")

    fig, ax = plt.subplots()

    size = 0.4
    vals = np.array([[yy,ny],[yn,nn]])
      
    # Set x-axis range
    ax.set_xlim((0,10))
    # Set y-axis range
    ax.set_ylim((0,10))
    # Draw lines to split quadrants
    ax.plot([5,5],[0,10], linewidth=4, color='slategray' )
    ax.plot([0,10],[5,5], linewidth=4, color='slategray' )
    ax.set_title(title, pad=50, fontsize = 18, color= 'white') if title is not None else None 
    #Title
    ax.text(5,11,'Reported', fontsize =14, fontweight = 'bold',ha='center', va='center',color = 'white')
    ax.text(-1,5,'Actual', fontsize =14, fontweight = 'bold',ha='center', va='center', rotation = 90, color = 'white')
    #Inner
    ax.text(2.5,10,'Yes', fontsize =12, fontweight = 'bold',ha='center', va='center', color = 'white')
    ax.text(7.5,10,'No', fontsize =12, fontweight = 'bold',ha='center', va='center', color = 'white')
    ax.text(0,2.5,'No', fontsize =12, fontweight = 'bold',ha='center', va='center',rotation = 90, color = 'white')
    ax.text(0,7.5,'Yes', fontsize =12, fontweight = 'bold',ha='center', va='center',rotation = 90, color = 'white')

    ax.text(2.5,7.5,f'{yy:1.0f}%', fontsize =30, fontweight = 'bold',ha='center', va='center', color = 'deepskyblue')
    ax.text(7.5,7.5,f'{yn:1.0f}%', fontsize =30, fontweight = 'bold',ha='center', va='center', color = 'deepskyblue')
    ax.text(2.5,2.5,f'{ny:1.0f}%', fontsize =30, fontweight = 'bold',ha='center', va='center',color = 'deepskyblue')
    ax.text(7.5,2.5,f'{nn:1.0f}%', fontsize =30, fontweight = 'bold',ha='center', va='center',color = 'deepskyblue')

    ax.axis('off')
    plt.tight_layout()
    plt.savefig(f"{out_path}plot_quadrant_chart_{title}.png", dpi=300, transparent=True )
    
    print(f">>> Plotted: {title}")


def bar_line(out_folder, xcol, y1col, y2col, bar_color ='#dadfe2', line_color='#dadfe2', xlabel = '', y1label = '', y2label = '', title = '', tags =['',], highlight = {'':'',}, y1lim =None, y2min= None, y2max= None, tag = None ):
    out_path = f"{out_folder}"
    os.makedirs(out_path, exist_ok=True)    
    
    print(f">> Running: Plotting Data for {title}")

    width = 0.65

    x_data = xcol
    y1_data = y1col
    y2_data = y2col
    x = np.arange(len(x_data))  # the label locations
    
    fig = plt.figure()
    ax1 = std_axes(fig.add_subplot(111),
                   annotation_color = 'black',
                  spines=['left','right','bottom'],
                  x_ticks=x,
                  x_labels=x_data,
                  xlabel=xlabel,
                  ylabel=y1label,
                  title=title,
                  ylim=y1lim,
                  tickf = 12,
                  labelf = 12,
                  titlef = 12,
                  )
    bar = ax1.bar(x,y1_data,width, color= bar_color, label = y1label)
    
    ax2 = std_axes(ax1.twinx(),
                   annotation_color = 'black',
                    ylabel=y2label,
                    ymin = y2min,
                    ymax = y2max,
                    tickf = 12,
                    labelf = 12,
                    titlef = 12,
                    second = True,
                    )

    #plt.axhline(y=0, color='steelblue', linestyle='--',)
    line = ax2.plot(x,y2_data, color= line_color, label = y2label)
    fsize = 6

    #ax1.legend(loc=2, bbox_to_anchor=(1.2,1),fontsize=fsize)
    #ax2.legend(loc=2, bbox_to_anchor=(1.2,(1-0.035/4*fsize)),fontsize=fsize)
    
    plt.tight_layout()
    #plt.savefig(f"{out_path}plot_bar_line_{title}.png", dpi=300)
    plt.savefig(f"{out_path}plot_bar_line_{title}{tag}.png", dpi=300, transparent=True )

    print(f">>> Plotted: {title}")


def bar_bar_line(out_folder, xcol, y1col, y2col, y3col, bar1_color ='#dadfe2', bar2_color ='#dadfe2', line_color='#dadfe2', xlabel = '', yax1label='', yax2label='', y1label = '', y2label = '', y3label = '', title = '', tags =['',], highlight = {'':'',}, y1lim =None, y3min= None, y2lim =None, y3max= None, tag = None ):
    out_path = f"{out_folder}"
    os.makedirs(out_path, exist_ok=True)    
    
    print(f">> Running: Plotting Data for {title}")

    width = 0.35

    x_data = xcol
    y1_data = y1col
    y2_data = y2col
    y3_data = y3col

    x = np.arange(len(x_data))  # the label locations
    
    fig = plt.figure()
    ax1 = std_axes(fig.add_subplot(111),
                   annotation_color = 'black',
                  spines=['left','right','bottom'],
                  x_ticks=x,
                  x_labels=x_data,
                  xlabel=xlabel,
                  ylabel=yax1label,
                  title=title,
                  ylim=y1lim,
                  tickf = 12,
                  labelf = 12,
                  titlef = 12,
                  )

    bar1 = ax1.bar(x- width/2,y1_data,width, color= bar1_color, label = y1label)
    bar2 = ax1.bar(x + width/2,y2_data, width, color= bar2_color, label = y2label)


    ax2 = std_axes(ax1.twinx(),
                   annotation_color = 'black',
                    ylabel=yax2label,
                    ymin = y3min,
                    ymax = y3max,
                    tickf = 12,
                    labelf = 12,
                    titlef = 12,
                    second = True,
                    )

    line = ax2.plot(x,y3_data, color= line_color, label = y3label)
    fsize = 6

    ax1.legend(loc=2, bbox_to_anchor=(1.2,1),fontsize=fsize)
    ax2.legend(loc=2, bbox_to_anchor=(1.2,(1-2*0.035/4*fsize)),fontsize=fsize)
    
    plt.tight_layout()
    #plt.savefig(f"{out_path}plot_bar_line_{title}.png", dpi=300)
    plt.savefig(f"{out_path}plot_bar_line_{title}_{tag}.png", dpi=300, transparent=True )

    print(f">>> Plotted: {title}")

def bar_bar(out_folder, xcol, y1col, y2col, bar1_color='#dadfe2', bar2_color='#dadfe2', xlabel='', yax1label='', yax2label='', y1label='', y2label='', title='', tags=[''], highlight={'':''}, y1lim=None, y2lim=None, tag=None):
    """
    Creates and saves a dual bar plot with two y-axes.

    Parameters:
    ----------
    out_folder : str
        The directory where the plot image will be saved.
    xcol : list
        A list of labels for the x-axis.
    y1col : list
        A list of values for the first set of bars.
    y2col : list
        A list of values for the second set of bars.
    bar1_color : str, optional
        The color for the first set of bars (default is '#dadfe2').
    bar2_color : str, optional
        The color for the second set of bars (default is '#dadfe2').
    xlabel : str, optional
        The label for the x-axis (default is an empty string).
    yax1label : str, optional
        The label for the first y-axis (default is an empty string).
    yax2label : str, optional
        The label for the second y-axis (default is an empty string).
    y1label : str, optional
        The label for the first set of bars in the legend (default is an empty string).
    y2label : str, optional
        The label for the second set of bars in the legend (default is an empty string).
    title : str, optional
        The title of the plot (default is an empty string).
    tags : list of str, optional
        Tags to include in the plot (default is a list with an empty string).
    highlight : dict, optional
        A dictionary for highlighting specific parts of the plot (default is a dictionary with an empty string as both key and value).
    y1lim : tuple, optional
        The y-axis limits for the first y-axis (default is None).
    y2lim : tuple, optional
        The y-axis limits for the second y-axis (default is None).
    tag : str, optional
        An additional tag to include in the filename of the saved plot (default is None).

    Returns:
    -------
    None
    """
    out_path = f"{out_folder}"
    os.makedirs(out_path, exist_ok=True)    
    
    print(f">> Running: Plotting Data for {title}")

    width = 0.35

    x_data = xcol
    y1_data = y1col
    y2_data = y2col

    x = np.arange(len(x_data))  # the label locations
    
    fig = plt.figure()
    ax1 = std_axes(fig.add_subplot(111),
                   annotation_color = 'black',
                  spines=['left','right','bottom'],
                  x_ticks=x,
                  x_labels=x_data,
                  xlabel=xlabel,
                  ylabel=yax1label,
                  title=title,
                  ylim=y1lim,
                  tickf = 12,
                  labelf = 12,
                  titlef = 12,
                  )

    bar1 = ax1.bar(x- width/2,y1_data,width, color= bar1_color, label = y1label)
    

    ax2 = std_axes(ax1.twinx(),
                   annotation_color = 'black',
                    ylabel=yax2label,
                    tickf = 12,
                    labelf = 16,
                    titlef = 16,
                    second = True,
                    )

    bar2 = ax2.bar(x + width/2,y2_data, width, color= bar2_color, label = y2label)
    fsize = 6

    ax1.legend(loc=2, bbox_to_anchor=(1.2,1),fontsize=fsize)
    ax2.legend(loc=2, bbox_to_anchor=(1.2,(1-2*0.035/4*fsize)),fontsize=fsize)
    
    plt.tight_layout()
    #plt.savefig(f"{out_path}plot_bar_line_{title}.png", dpi=300)
    plt.savefig(f"{out_path}plot_bar_bar_{title}_{tag}.png", dpi=300, transparent=True )

    print(f">>> Plotted: {title}")


def multi_bar(out_folder, x_data, y_data, xlabel='', ylabel='', title='', tags=[''], highlight={'':''}, ylim=None, footnote=None, footnoteLines=None, tag=None, minorTicks=None, legend=False):
    """
    Creates and saves a multi-bar plot with specified parameters.

    Parameters:
    ----------
    out_folder : str
        The directory where the plot images will be saved.
    x_data : list
        A list of labels for the x-axis.
    y_data : dict
        A dictionary containing data for the y-axis. Each key should map to a dictionary with keys 'values' (a list of y-values),
        'color' (the color of the bars), and 'label' (the label for the legend).
    xlabel : str, optional
        The label for the x-axis (default is an empty string).
    ylabel : str, optional
        The label for the y-axis (default is an empty string).
    title : str, optional
        The title of the plot (default is an empty string).
    tags : list of str, optional
        Tags to include in the plot (default is a list with an empty string).
    highlight : dict, optional
        A dictionary for highlighting specific parts of the plot (default is a dictionary with an empty string as both key and value).
    ylim : tuple, optional
        The y-axis limits (default is None).
    footnote : str, optional
        A footnote to add to the plot (default is None).
    footnoteLines : int, optional
        Number of lines in the footnote (default is None).
    tag : str, optional
        An additional tag to include in the filename of the saved plot (default is None).
    minorTicks : bool, optional
        Whether to include minor ticks on the y-axis (default is None).
    legend : bool, optional
        Whether to display the legend (default is False).

    Returns:
    -------
    None
    """
    out_path = f"{out_folder}"
    os.makedirs(out_path, exist_ok=True)    
    
    print(f">> Running: Plotting Data for {title}")

    n = len(y_data)
    pad = 0.25
    width = (1-2*pad)/n

    x_placement = np.arange(-0.5+(pad+(width/2)),0.5, width)

    x = np.arange(len(x_data))  # the label locations
    
    fig = plt.figure()
    

    ax1 = std_axes(fig.add_subplot(111),
                  spines=['left','bottom'],
                  annotation_color = 'black',
                  x_ticks=x,
                  x_labels=x_data,
                  xlabel=xlabel,
                  ylabel=ylabel,
                  title=title,
                  ylim=ylim,
                  tickf = 12,
                  labelf = 16,
                  titlef = 16,
                  )

    i=0
    for y in y_data:
        x_adjusted = x+[x_placement[i]]
        ax1.bar(x_adjusted ,y_data[y]['values'],width, color= y_data[y]['color'], label = y_data[y]['label'])
        i += 1
    
    if legend:
        ax1.legend(loc=2, bbox_to_anchor=(0.01,1),fontsize=4)
    else:
        ax1.legend().set_visible(False)

    if minorTicks is not None:
        ax1.yaxis.set_minor_locator(tck.AutoMinorLocator())

    plt.title(title,pad=20)
    title = title.replace('\n', '')
    if tag is not None:
        plt.savefig(f"{out_path}plot_multibar_{title}_{tag}.png", dpi=300, transparent=True,bbox_inches="tight" )
    else:
        plt.savefig(f"{out_path}plot_multibar_{title}.png", dpi=300, transparent=True,bbox_inches="tight" )

    plt.close()
    plt.clf()
    if footnote is not None:
        plt.figtext(0.5, 0.5, footnote, ha="center", fontsize=8, bbox={"facecolor":'lightgrey', "alpha":0.5, "pad":5})

    if tag is not None:
        plt.savefig(f"{out_path}plot_sig_{title}_{tag}.png", dpi=300, transparent=True,bbox_inches="tight" )
    else:
        plt.savefig(f"{out_path}plot_sig_{title}.png", dpi=300, transparent=True,bbox_inches="tight" )
    plt.close()
    plt.clf()
    print(f">>> Plotted: {title}")


def multi_line_dot(out_folder, x_data, y_data, xlabel = '', ylabel='', title = '', tags =['',], highlight = {'':'',}, ylim =None, footnote = None, footnoteLines=None, tag = None, minorTicks=None, spacing = False, legend = True):
    out_path = f"{out_folder}"
    os.makedirs(out_path, exist_ok=True)    
    
    print(f">> Running: Plotting Data for {title}")

    # n = len(y_data)
    # pad = 0.1
    # width = (1-2*pad)/n
    # x_placement = np.arange(-0.5+(pad+(width/2)),0.5, width)

    x = np.arange(len(x_data))  # the label locations
    
    if spacing:
        fig = plt.figure(figsize=(10, 5))  # You can adjust the size as needed
    else:
        fig = plt.figure()

    

    ax1 = std_axes(fig.add_subplot(111),
                  spines=['left','bottom'],
                  annotation_color = 'black',
                  x_ticks=x,
                  x_labels=x_data,
                  xlabel=xlabel,
                  ylabel=ylabel,
                  title=title,
                  ylim=ylim,
                  tickf = 12,
                  labelf = 16,
                  titlef = 16,
                  )

    prices = [16.99,
        19.99,
        19.99,
        19.99,
        21.99,
        19.99,
        24.99,
        24.99,
        24.99,
        24.99,
        34.99,
        39.99,
        39.99,
        39.99,
        39.99,
        49.99
        ]
    
    if len(x)==16:
        error = [p * 0.3 for p in prices]
        ax1.errorbar(x_data, prices, yerr=error, fmt='none', ecolor='gray', capsize=3)
        ax1.scatter(x,prices,color = 'black',marker='*')
        

    i=0
    for y in y_data:
        x_adjusted = x #+[x_placement[i]]
        ax1.plot(x_adjusted,y_data[y]['values'], color= y_data[y]['bar_color'], label = y_data[y]['label'], marker='o')
        i += 1
    


    if legend:
        ax1.legend(loc=2, bbox_to_anchor=(0.01,1),fontsize=4)
    else:
        ax1.legend().set_visible(False)


    if minorTicks is not None:
        ax1.yaxis.set_minor_locator(tck.AutoMinorLocator())

    title = title.replace('\n', '')
    if tag is not None:
        plt.savefig(f"{out_path}plot_multiline_{title}_{tag}.png", dpi=300, transparent=True,bbox_inches="tight" )
    else:
        plt.savefig(f"{out_path}plot_multiline_{title}.png", dpi=300, transparent=True,bbox_inches="tight" )

    plt.close()
    plt.clf()
    if footnote is not None:
        plt.figtext(0.5, 0.5, footnote, ha="center", fontsize=8, bbox={"facecolor":'lightgrey', "alpha":0.5, "pad":5})

    if tag is not None:
        plt.savefig(f"{out_path}plot_sig_{title}_{tag}.png", dpi=300, transparent=True,bbox_inches="tight" )
    else:
        plt.savefig(f"{out_path}plot_sig_{title}.png", dpi=300, transparent=True,bbox_inches="tight" )
    plt.close()
    plt.clf()
    print(f">>> Plotted: {title}")


def multi_box(out_folder, x_data, y_data, xlabel = '', ylabel='', title = '', tags =['',], highlight = {'':'',}, ylim =None, footnote = None, footnoteLines=None, tag = None, minorTicks=None):
    """
        Generates and saves boxplot visualizations for given datasets.

        This function creates boxplots for multiple datasets, allowing customization of labels, titles, colors, and other plot features. It saves the generated plots to specified output folders, with options for additional tagging and minor tick adjustments.

        Parameters:
        - out_folder (str): The path to the output folder where the plots will be saved.
        - x_data (list): The x-axis labels for the boxplot.
        - y_data (dict): A dictionary where keys are groups and values contain 'values' (list of data points), 'label' (str for the legend), and 'color' (str for the box color).
        - xlabel (str, optional): The label for the x-axis. Default is an empty string.
        - ylabel (str, optional): The label for the y-axis. Default is an empty string.
        - title (str, optional): The title of the plot. Default is an empty string.
        - tags (list, optional): A list of tags for categorizing plots. Default is a list with an empty string.
        - highlight (dict, optional): A dictionary to specify elements to highlight, with keys as element identifiers and values as styles/colors. Default is an empty dictionary.
        - ylim (tuple, optional): A tuple specifying the limits for the y-axis (min, max). Default is None.
        - footnote (str, optional): Text for a footnote to be added to the plot. Default is None.
        - footnoteLines (int, optional): The number of lines for the footnote. This parameter is currently unused in the function. Default is None.
        - tag (str, optional): A specific tag to append to the filename for the saved plot. Default is None.
        - minorTicks (bool, optional): Whether to include minor ticks on the y-axis. If True, minor ticks are added. Default is None.

        Returns:
        - None: The function saves the generated plots to files and does not return any value.

        Notes:
        - The function saves two sets of plots: one set with the 'box' prefix and another with the 'sig' prefix in the filenames. The distinction or purpose of these sets should be clarified as needed.
        - The function makes use of `plt.figtext` for adding footnotes, but it seems to be misplaced outside of the plot generation context (after `plt.close()`), which might not work as intended.
        - Ensure the 'out_folder' exists or has the appropriate permissions for file operations.
        - The function prints progress and completion messages to the console.
    """
    out_path = f"{out_folder}"
    os.makedirs(out_path, exist_ok=True)    
    
    print(f">> Running: Plotting Data for {title}")

    # n = len(y_data)
    # pad = 0.1
    # width = (1-2*pad)/n
    # x_placement = np.arange(-0.5+(pad+(width/2)),0.5, width)

    x = np.arange(len(x_data))  # the label locations
    #xb = np.arange(len(x_data)+1)  # the label locations
    
    fig = plt.figure()
    # ax1 = std_axes(fig.add_subplot(111),
    #               spines=['left','bottom'],
    #               annotation_color = 'black',
    #               x_ticks=x,
    #               x_labels=x_data,
    #               xlabel=xlabel,
    #               ylabel=ylabel,
    #               title=title,
    #               ylim=ylim,
    #               )
    
    ax1 = std_axes(fig.add_subplot(111),
                spines=['left','bottom'],
                annotation_color = 'black',
                xlabel=xlabel,
                ylabel=ylabel,
                title=title,
                tickf=14,
                titlef=14,
                labelf=14
                )

    data = []
    labels = []
    colors = []
    for y in y_data:
        og = y_data[y]['values']
        og = [i for i in og if i is not np.nan]
        data = data + [og]
        labels = labels + [y_data[y]['label']]
        colors = colors + [y_data[y]['color']]


    bp = ax1.boxplot(data, patch_artist = True, manage_ticks = True, labels=labels, showfliers=False,)#,width, color= y_data[y]['bar_color'], label = y_data[y]['label'])

    # ax1.set_xticks(x)
    # ax1.set_xticklabels(x_data)
    # ax1.set_xlim(0.5)
    
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
 
    # changing color and linewidth of
    # whiskers
    for whisker in bp['whiskers']:
        whisker.set(color ='black',
                    linewidth = 1.5,
                    linestyle =":")
 
    # changing color and linewidth of
    # caps
    for cap in bp['caps']:
        cap.set(color ='black',
                linewidth = 2)
 
    # changing color and linewidth of
    # medians
    for median in bp['medians']:
        median.set(color ='black',
                    linewidth = 3)
 
    ## changing style of fliers
    #for flier in bp['fliers']:
    #    flier.set(marker ='D',
    #                color ='black',
    #                alpha = 0.5)

    #ax1.legend(loc=2, bbox_to_anchor=(0.01,1),fontsize=4)

    if minorTicks is not None:
        ax1.yaxis.set_minor_locator(tck.AutoMinorLocator())

    plt.xticks(rotation=45)

    if tag is not None:
        plt.savefig(f"{out_path}plot_box_{title}_{tag}.png", dpi=300, transparent=True,bbox_inches="tight" )
    else:
        plt.savefig(f"{out_path}plot_box_{title}.png", dpi=300, transparent=True,bbox_inches="tight" )

    plt.close()

    # if footnote is not None:
    #     plt.figtext(0.5, 0.5, footnote, ha="center", fontsize=8, bbox={"facecolor":'lightgrey', "alpha":0.5, "pad":5})

    # if tag is not None:
    #     plt.savefig(f"{out_path}plot_sig_{title}_{tag}.png", dpi=300, transparent=True,bbox_inches="tight" )
    # else:
    #     plt.savefig(f"{out_path}plot_sig_{title}.png", dpi=300, transparent=True,bbox_inches="tight" )
    
    #plt.close()

    print(f">>> Plotted: {title}")


def multi_line(out_folder, x_data, y_data, xlabel = '', ylabel='', title = '', tags =['',], highlight = {'':'',}, ylim =None, footnote = None, footnoteLines=None, tag = None, minorTicks=None):
    out_path = f"{out_folder}"
    os.makedirs(out_path, exist_ok=True)    
    
    print(f">> Running: Plotting Data for {title}")

    x = np.arange(len(x_data))  # the label locations
    
    fig = plt.figure()
    ax1 = std_axes(fig.add_subplot(111),
                  spines=['left','bottom'],
                  annotation_color = 'black',
                  x_ticks=x,
                  x_labels=x_data,
                  xlabel=xlabel,
                  ylabel=ylabel,
                  title=title,
                  ylim=ylim,
                  tickf = 12,
                  labelf = 16,
                  titlef = 16,
                  )

    i=0
    for y in y_data:
        ax1.plot(x,y_data[y]['values'], color= y_data[y]['bar_color'], label = y_data[y]['label'])
        i += 1
    
    ax1.legend(loc=2, bbox_to_anchor=(0.01,1),fontsize=4)

    if minorTicks is not None:
        ax1.yaxis.set_minor_locator(tck.AutoMinorLocator())

    if tag is not None:
        plt.savefig(f"{out_path}plot_multiline_{title}_{tag}.png", dpi=300, transparent=True,bbox_inches="tight" )
    else:
        plt.savefig(f"{out_path}plot_multiline_{title}.png", dpi=300, transparent=True,bbox_inches="tight" )

    plt.close()
    plt.clf()
    # if footnote is not None:
    #     plt.figtext(0.5, 0.5, footnote, ha="center", fontsize=8, bbox={"facecolor":'lightgrey', "alpha":0.5, "pad":5})

    # if tag is not None:
    #     plt.savefig(f"{out_path}plot_sig_{title}_{tag}.png", dpi=300, transparent=True,bbox_inches="tight" )
    # else:
    #     plt.savefig(f"{out_path}plot_sig_{title}.png", dpi=300, transparent=True,bbox_inches="tight" )
    #plt.close()
    #plt.clf()
    print(f">>> Plotted: {title}")

def plot_scatter_with_trendline(out_path, x, y, xlabel = '', ylabel='', title = '', tags =['',], highlight = {'':'',}, ylim =None,):
    # Scatter plot with light grey dots
    fig = plt.figure()
    ax1 = std_axes(fig.add_subplot(111),
                  spines=['left','bottom'],
                  annotation_color = 'black',
                  xlabel=xlabel,
                  ylabel=ylabel,
                  title=title,
                  ylim=ylim,
                  )

    ax1.scatter(x, y, color='lightgrey')

    # Calculate the trendline
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)

    # Generate x values for the trendline
    x_trend = np.linspace(min(x), max(x), 100)

    # Plot the trendline in deepskyblue color
    ax1.plot(x_trend, p(x_trend), color='deepskyblue')


    # Display the plot
    plt.savefig(f"{out_path}plot_trendline_{title}.png", dpi=300, transparent=True,bbox_inches="tight" )


def table(out_path, data,title, color, cell_height = .06, title_position = 0.6 ):
    # Convert the color to RGBA format with 20% opacity for data cells
    light_color = to_rgba(color, alpha=0.2)
    plt.rcParams['font.family'] = "Century Gothic"
    # Calculate figure size
    fig_size = (data.shape[1]*2, data.shape[0]*0.625 + 8)  # Adjusted for less vertical space
    fig, ax = plt.subplots(figsize=fig_size)
    
    # Hide axes
    ax.axis('off')
    ax.axis('tight')
    
    # Add table at the bottom of the axes
    the_table = ax.table(cellText=data.values, colLabels=data.columns, rowLabels=data.index, 
                         cellLoc='center', loc='center', 
                         colColours=[color]*data.shape[1], rowColours=[color]*data.shape[0])
    
    # Set table font size
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(8)  # Setting table font size

    # Adjusting cell colors
    for pos, cell in the_table.get_celld().items():
        cell.set_height(cell_height)
        if pos[0] == 0 or pos[1] < 0:  # Header or index cells
            cell.set_text_props(color='white')
            cell.set_facecolor(color)
        else:
            cell.set_text_props(color='black')
            if pos[0] % 2 == 0:
                cell.set_facecolor('none')  # No fill
            else:
                cell.set_facecolor(light_color)  # Light color fill
    
    # Adding and adjusting the title
    plt.suptitle(title, color='black', fontsize=12, y=title_position)  # Adjust title font size and position
    

    # Save the figure
    plt.savefig(f"{out_path}table_{title}.png", dpi=300, transparent=True,bbox_inches="tight" )



def main():
    pass


if __name__ == "__main__":
    main()