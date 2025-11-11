
from neurallib.clean import * 


try:
    import msvcrt
    def get_key(z):
        print()
        print('-- Exception Raised --')
        print(f'>> Warning due to {z}')
        print('-- Press any key to continue...--')
        #msvcrt.getch()
        print()
except:
    pass


def get_duplicate_column_data(df, column):
    for col in df.columns:
        if column in col:  # Check if 'column' is in the column name
            # Check if the column is not entirely null
            if df[col].notna().any():
                return df[col]


def join_to_df(in_folder, tags =['',]):
    print('> Now Running: Join_to_df')
    files = get_files(in_folder,tags)
    all_data = pd.DataFrame()
    for file in files:
            _data = pd.read_csv(in_folder + '/' + file, header=0, index_col = 0)
            all_data = pd.concat([all_data, _data])
            print(f"> Completed: {file}")

    print('> Completed: Join_to_df')
    return all_data

def joined():
    files = [f for f in os.listdir('./outfiles') if not f.startswith('.')] 
    #labels = ['Frontal Asymmetry', 'High Engagement', 'Workload', 'AOIs Active', 'AOI Gaze', 'Scene']
    labels = ['Row','Frontal Asymmetry', 'AOIs Active', 'AOI Gaze', 'Scene']
    all_data = pd.DataFrame(columns = labels )
    res = 1
    
    for file in files:
        print(f"> Collected: {file}")
        #_data = pd.read_csv(f"./outfiles/{file}", header=0, usecols=[0,1,2,3,4,5], names = labels)
        _data = pd.read_csv(f"./outfiles/{file}", header=0, usecols=[0,1,2,3,4], names = labels)
        _data.insert(0, 'Respondant',res)
        all_data = pd.concat([all_data, _data])
        res = res + 1
    pprint.pprint(len(all_data))
    all_data.to_csv('results.csv')


def get_files(folder, tags=['',]):
    return [f for f in os.listdir(folder) if not f.startswith('.') and all(x in f for x in tags)] 


def combine_files(in_folder, results_folder, axis = 0):
    ##Combine all data
    files = get_files(in_folder)
    all_data = pd.DataFrame()
    
    for file in files:
        print(f"> Joined: {file}")
        _data = pd.read_csv(f"{results_folder}{file}", header=0)
        all_data = pd.concat([all_data, _data], axis = axis)

    pprint.pprint(len(all_data))
    all_data.to_csv(f"{results_folder}combined_{data}.csv")  

if __name__ == "__main__":
    main()