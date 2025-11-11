from scipy.signal import butter,welch, filtfilt
import numpy as np
from sklearn.impute import KNNImputer
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split

def butter_lowpass_filter(data, cutoff, fs, order=4):
    """
    # Arguments:
    data: np.array containing datapoint
    cutoff: cutoff frequency in Hz
    fs: sampling frequency in Hz
    order: butterworth filter order

    # Note:
    Higher order filters have a steeper cutoff but may reduce filter stability

    """
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = filtfilt(b, a, data,method="pad")
    return y


def butter_highpass_filter(data, cutoff, fs, order=4):
    """
    # Arguments:
    data: np.array containing datapoint
    cutoff: cutoff frequency in Hz
    fs: sampling frequency in Hz
    order: butterworth filter order

    # 
    """
    b, a = butter_highpass(cutoff, fs, order=order)
    y = filtfilt(b, a, data,method="pad")
    return y


def butter_bandpass_filter(data, cutoffs, fs, order=4):
    """
    # Arguments:
    data: np.array containing datapoint
    cutoffs: tuple containing cutoff frequencies in Hz
    fs: sampling frequency in Hz
    order: butterworth filter order

    # 
    """
    b, a = butter_bandpass(cutoffs, fs, order=order)
    y = filtfilt(b, a, data,method="pad")
    return y


def butter_lowpass(cutoff, fs, order=2):
    return butter(order, cutoff, fs=fs, btype='low', analog=False)


def butter_highpass(cutoff, fs, order=2):
    return butter(order, cutoff, fs=fs, btype='high', analog=False)


def butter_bandpass(cutoffs, fs, order=2):
    return butter(order, cutoffs, fs=fs, btype='band', analog=False)


def compute_welch_psd(data: list, fs: int, window_period: int):
    """
    # Arguments:
    data: np.array of datapoints
    fs: sampling frequency in Hz
    window_period: window period in milliseconds

    # Notes:
    A longer window period leads to higher frequncy resolution, but lower stability and confidence in result
    """
    window_period_sec = window_period / 1000.0
    nperseg = int(fs * window_period_sec)
    freqs, psd = welch(data, fs, nperseg=nperseg)
    return freqs, psd


def simulate_missing_data(df, missing_percentage=0.1, random_state=None):
    np.random.seed(random_state)  # For reproducibility
    modified_df = df.copy()

    nrows, ncols = df.shape
    total_values = nrows * ncols
    missing_values_count = int(total_values * missing_percentage)

    # Ensure row indices are within the DataFrame's index range
    missing_row_indices = np.random.randint(0, nrows, size=missing_values_count)

    # Ensure column indices are within the number of columns
    missing_col_indices = np.random.randint(0, ncols, size=missing_values_count)

    # Use np.ravel_multi_index with corrected indices
    try:
        flat_indices = np.ravel_multi_index((missing_row_indices, missing_col_indices), dims=modified_df.shape)
    except ValueError as e:
        print(f"Error in generating flat indices: {e}")
        return df  # Return original DataFrame in case of error

    # Flatten the DataFrame to apply NaNs and then reshape
    flat_data = modified_df.values.ravel()
    flat_data[flat_indices] = np.nan  # Set missing values
    modified_df.iloc[:, :] = flat_data.reshape(modified_df.shape)

    return modified_df


def custom_imputation_score(X, max_neighbors=10):
    """
    Custom function to evaluate KNN imputation performance by calculating MSE
    between original and imputed values for a range of neighbor values.
    X: The dataset with missing values marked as np.nan.
    max_neighbors: Maximum number of neighbors to consider.
    """
    # Split the dataset into training and testing sets
    X_train, X_test = train_test_split(X, test_size=0.2, random_state=42)
    
    # Introduce missing values in X_test for evaluation (simulate missingness)
    # Here, we're assuming X has missing values, and you're simulating additional missingness
    # for evaluation. Adjust this step based on your data's specific missingness pattern.
    X_missing = simulate_missing_data(X_test)
    
    # Placeholder for scores
    scores = []
    
    for k in range(1, max_neighbors + 1):
        # Initialize KNN imputer
        imputer = KNNImputer(n_neighbors=k)
        
        # Fit imputer on the training set and transform both training and test sets
        imputer.fit(X_train)
        X_test_imputed = imputer.transform(X_missing)
        
        # Calculate MSE using the original and imputed values
        # Note: This requires access to the original non-missing values in X_test
        # Adjust this calculation based on how you simulate missingness in X_test
        mse = mean_squared_error(X_test, X_test_imputed, squared=False)  # Adjust as necessary
        scores.append((k, mse))
    
    # Find the number of neighbors with the lowest MSE
    optimal_k, _ = min(scores, key=lambda x: x[1])
    
    return optimal_k

def main():
    pass

if __name__ == "__main__":
    main()