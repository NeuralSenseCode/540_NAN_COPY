
from .clean import * 
import pingouin as pg
import scikit_posthocs as sp
from itertools import permutations
import warnings
import statsmodels.api as sm
from statsmodels.formula.api import ols

BAR_COLORS = ['lightgrey',
              'lightskyblue',
              'steelblue',
              'slategrey',
              'deepskyblue']

def bootstrap_test(pre, post, n_bootstrap=10000):
    observed_difference = np.mean(post) - np.mean(pre)
    combined = np.concatenate([pre, post])
    count = 0

    for _ in range(n_bootstrap):
        # Resampling without replacement to maintain data integrity
        np.random.shuffle(combined)
        new_pre = combined[:len(pre)]
        new_post = combined[len(pre):]
        new_difference = np.mean(new_post) - np.mean(new_pre)
        
        # Count how often the bootstrap difference is greater than the observed
        if np.abs(new_difference) >= np.abs(observed_difference):
            count += 1

    # P-value estimation
    p_value = count / n_bootstrap

    result = pd.DataFrame()
    result['p-val']=[p_value]
    result['n_bootstrap']=[n_bootstrap]

    return result

def get_significance(group_data: dict, cluster: str, groups = [], paired = False, one_sample = False):
    """Analysis of significance between arrays

    Args:
        data: A dictionary containg arrays, with keys set as group name
        cluster: The label attatched to this analysis
        groups: A list of all the groups
        paired: indicating is paired sample across groups

    Returns:
        dataframe: containing results
    """


    if not isinstance(groups, list) and groups is not None:
        raise TypeError("Expected 'groups' to be a list or None, got {}".format(type(groups).__name__))

    if len(groups) == 0:
        groups = list(group_data.keys())

    if len(groups) == 1:
        print(f'Failed to get stats for {cluster}: Only one group ({groups})')
        return pd.DataFrame()
    else:
        sample_check = True
        for i in groups:
            if len(group_data[i])<3:
                sample_check = False
                control = i
                nC = len(group_data[i])
            if len(group_data[i])==3:
                group_data[i] = np.append(group_data[i],0)

                

        significance = pd.DataFrame()

        if sample_check:

            data = pd.DataFrame()
            for key,value in group_data.items():
                res = pd.DataFrame()
                res['Group']=[key]*len(value)
                res['Value']=value
                data = pd.concat([data,res])

            ### Test for parametric or non-parametric
            normality = pg.normality(data=data, dv='Value', group='Group')
            homoscedasticity = pg.homoscedasticity(data=data, dv='Value', group='Group')
            normal = all(normality['normal'])
            equal_var = all(homoscedasticity['equal_var'])
            
            if len(groups)>2:            
                if equal_var:
                    aov = pg.anova(dv='Value', between='Group', data=data,
                        detailed=True)
                    pval = aov['p-unc'].values[0]
                    test_type = 'ANOVA'
                    
                    # Check if residuals are normally distributed
                    model = ols('Value ~ C(Group)', data=data).fit()
                    data['Residuals'] = model.resid
                    normality_test_results = pg.normality(data['Residuals'])
                    residuals_normal = all(normality_test_results['normal'])

                    if not residuals_normal:
                        kru = pg.kruskal(dv='Value', between='Group', data=data)
                        pval = kru['p-unc'].values[0]
                        test_type = 'Kruskal-Wallis'
        
                else:
                    wel = pg.welch_anova(dv='Value', between='Group', data=data)
                    pval = wel['p-unc'].values[0]
                    test_type = 'ANOVA Welch'

                sig = True if pval<0.05 else False  
                result = {'Groups':'Group',
                                'pValue':pval,
                                'Type':test_type,
                                'nC':'-',
                                'nT':'-',
                                'Cluster':cluster}
                result_df = pd.DataFrame([result], index=[0]) #, index=[0])  # Creating a DataFrame with a single row
                significance = pd.concat([significance, result_df])

                if sig:
                    if normal:
                        if equal_var:
                            ph = pg.pairwise_tukey(dv='Value', between='Group', data=data, effsize = 'r')
                            ph['Control']= ph['A']
                            ph['Treatment']= ph['B']
                            ph['pval']=ph['p-tukey']
                            test_type = 'Post-Hoc Tukey'
                        else:
                            ph = pg.pairwise_gameshowell(dv='Value', between='Group', data=data, effsize='r')
                            ph['Control']= ph['A']
                            ph['Treatment']= ph['B']
                            test_type = 'Post-Hoc Games'
                    else:
                        #What to do?
                        res = sp.posthoc_dunn(data, val_col='Value', group_col= 'Group', p_adjust = 'holm')
                        test_type = 'Post-Hoc Dunn'
                        groups = res.columns
                        pair_permutations = set('--'.join(sorted([p1, p2])) for p1, p2 in permutations(groups, 2))
                        ph = pd.DataFrame()
                        for pair in pair_permutations:
                            control = pair.split('--')[0]
                            treatment = pair.split('--')[1]
                            _ph = pd.DataFrame()
                            _ph['Control']=[control]
                            _ph['Treatment']=[treatment]
                            _ph['pval']=res.loc[control,treatment]
                            ph = pd.concat([ph,_ph])

                    
                    for index, row in ph.iterrows():
                        groups = [f"{row['Control']}",f"{row['Treatment']}"]
                        groups.sort()
                        result = {'Groups':(' and ').join(groups),
                            'pValue':row['pval'],
                            'Control':row['Control'],
                            'Treatment':row['Treatment'],
                            'Type':test_type,
                            'nC':len(data.loc[data['Group']==row['Control']]),
                            'nT':len(data.loc[data['Group']==row['Treatment']]),
                            'Cluster':cluster}
                        result_df = pd.DataFrame([result], index=[0]) #, index=[0])  # Creating a DataFrame with a single row
                        significance = pd.concat([significance, result_df])
            else:
                treatment = data.loc[data['Group']==groups[0]]['Value'].values
                control = data.loc[data['Group']==groups[1]]['Value'].values
                
                if paired:
                    if normal:
                        res = pg.ttest(control,treatment, paired=True)
                        test_type = 'Paired T-Test'
                    else:
                        with warnings.catch_warnings(record=True) as caught_warnings:
                            warnings.simplefilter("always")  # Catch any warnings
                            res = pg.wilcoxon(control, treatment)
                            test_type = 'Wilcoxin'
                            # Check if any caught warnings are UserWarning
                            user_warning_issued = any(issubclass(w.category, UserWarning) for w in caught_warnings)
                            
                            if user_warning_issued:
                                print("UserWarning detected, proceeding with bootstrap analysis.")
                                # Assume pre_scores and post_scores are defined or obtained as needed
                                res = bootstrap_test(control,treatment)
                                test_type = 'Bootstrap'
                    
                elif normal:
                    res = pg.ttest(control,treatment, paired=False)
                    test_type = 'Independent T-Test'
                else:
                    res = pg.mwu(control,treatment)
                    test_type = 'Mann-Whitney U'
                    
                groups = [f'{groups[1]}',f'{groups[0]}']
                groups.sort()

                result = {'Groups':(' and ').join(groups),
                        'Control':groups[1],
                        'Treatment':groups[0],
                        'pValue':res['p-val'].values[0],
                        'Type':test_type,
                        'nC':len(control),
                        'nT':len(treatment),
                        'Cluster':cluster}
                result_df = pd.DataFrame([result], index=[0])   # Creating a DataFrame with a single row
                significance = pd.concat([significance, result_df])
        else:
            result = {'Groups':(' and ').join(groups),
                        'pValue':1,
                        'Control':control,
                        'Treatment':'Not enough samples',
                        'nC':nC,
                        'nT':'Not enough samples',
                        'Cluster':cluster}
            result_df = pd.DataFrame([result], index=[0]) #, index=[0])  # Creating a DataFrame with a single row
            significance = pd.concat([significance, result_df])

        return significance

def get_significance_one_sample(data,x,cluster):

    sample_check = True
    if len(data)<5:
        sample_check = False
        nC = len(data)

    significance = pd.DataFrame()

    if sample_check:
        
        y = np.full_like(data, fill_value=x)

        normality = pg.normality(data=data, dv='Value', group='Group')
        #homoscedasticity = pg.homoscedasticity(data=data, dv='Value', group='Group')
        normal = all(normality['normal'])
        #equal_var = all(homoscedasticity['equal_var'])
        
        if normal:
            res = pg.ttest(data,y, paired=True)
            test_type = 'Paired T-Test'
        else:
            res = pg.wilcoxon(data,y)
            test_type = 'Wilcoxin'
   
        result = {'Groups':cluster,
                'Control':x,
                'Treatment':cluster,
                'pValue':res['p-val'].values[0],
                'Type':test_type,
                'nC':len(data),
                'nT':len(data),
                'Cluster':cluster}
        
        result_df = pd.DataFrame(result)  # Creating a DataFrame with a single row
        significance = pd.concat([significance, result_df])
    else:
        result = {'Groups':cluster,
                    'pValue':1,
                    'Control':x,
                    'Treatment':'Not enough samples',
                    'nC':len(data),
                    'nT':'Not enough samples',
                    'Cluster':cluster}
        result_df = pd.DataFrame(result)  # Creating a DataFrame with a single row
        significance = pd.concat([significance, result_df])


    return significance


def get_significance_footnote(sig,clusters = False):
    footnote = str()
    footnoteLines = 0
    if len(sig):
        footnote = 'Result are statistically significant, with a value of\n'
        for index, row in sig.iterrows():
            if row['Groups']== 'Group':
                if (row['pValue'] < 0.001):
                    if clusters:
                        text = f"p<0.001 across groups in {row['Cluster']}"
                    else:
                        text = f"p<0.001 across groups"
                else:
                    if clusters:
                        text = f"p<0.05 across groups in {row['Cluster']}"
                    else:
                        text = f"p<0.05 across groups"
            else:
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


def main():
    pass

if __name__ == "__main__":
    main()