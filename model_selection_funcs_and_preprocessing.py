import numpy as np
import pandas as pd
import scipy.stats as stats
from sklearn.linear_model import Ridge, Lasso, LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, KFold
from sklearn.utils._testing import ignore_warnings


def clean_transform_df(df, test_cols):
    """
    Runs all data cleaning and transformation functions
    Arg:
        df: a Dataframe object, loaded from pickle!
        test_cols: bool, whether or not to drop some columns (for testing)
    Returns:
        df: a DataFrame object.
        log_transformed_cols: list, which columns have been log + .01 transformed for skewness
    """
    get_offense_density(df)
    transform_and_drop_tuition(df)
    drop_some_cols(df, test_cols=True)
    map_categories(df)
    df = pd.get_dummies(data = df, columns=['setting', 'relig', 'min_serv_inst', 'sector'], drop_first=True)
    log_transformed_added_cols = log_transform_skewed(df)
    remove_outliers(df)
    return df, log_transformed_added_cols


def remove_outliers(df):
    """
    Removes rows that have an outlier.

    Args:
        df: a DataFrame object.

    Returns:
        None.
    """
    df[(np.abs(stats.zscore(df)) < 3).all(axis=1)]
    return


def log_transform_skewed(df):
    """
    Log + .01 transforms skewed columns.

    Args:
        df: a DataFrame object.

    Returns:
        log_transformed_added_cols: columns that were log +.01 transformed
    """
    skews = df.skew(axis=0)
    log_transformed_added_cols = []
    cat_cols = ['perc_fem', 'setting_Rural', 'min_serv_inst_Historically Black', 'setting_Suburb', 'setting_Town',
                'sector_Public', 'relig_Yes', 'min_serv_inst_Not Applicable']
    for feature in skews.index:
        if feature not in cat_cols:
            df[feature] = np.log(df[feature] + .01)
            log_transformed_added_cols.append(feature)
    return log_transformed_added_cols


def map_categories(df):
    """
    Maps setting column down to simpler categories.

    Args:
        df: a DataFrame object.

    Returns:
        None.
    """
    setting_dict = {}
    for setting in ['City: Small', 'City: Midsize', 'City: Large']:
        setting_dict[setting] = 'City'
    for setting in ['Suburb: Small', 'Suburb: Midsize', 'Suburb: Large']:
        setting_dict[setting] = 'Suburb'
    for setting in ['Town: Distant', 'Town: Remote', 'Town: Fringe']:
        setting_dict[setting] = 'Town'
    for setting in ['Rural: Distant', 'Rural: Fringe', 'Rural: Remote']:
        setting_dict[setting] = 'Rural'
    df.setting = df.setting.map(setting_dict)
    return


def drop_some_cols(df, test_cols=False):
    """
    Drops some multicollinear columns.

    Args:
        df: a DataFrame object.
        test_cols: bool, whether or not to drop those columns.

    Returns:
        None.
    """
    if test_cols == True:
        df.drop(['perc_bl', 'perc_pt', 'avg_fresh_gpa', 'avg_def_rate', 'six_grad_rate', 'perc_pell_fresh',
                 'first_year_ret'], inplace=True, axis=1)
    df.drop(
        ['perc_male', 'four_grad_rate', 'five_grad_rate', 'IPEDS_ID', 'med_debt_after_comp', 'perc_wh', 'perc_nat_hori',
         'perc_other'], inplace=True, axis=1)
    return


def transform_and_drop_tuition(df):
    """
    Multiplies out/in state tuition puts that in column, then drops tuition after grant, and
    individual tuition columns.

    Args:
        df: A DataFrame object.

    Returns:
        None.
    """
    df['mult_tuition'] = df['out_tui_fees'] * df['in_tui_fees']
    df.drop(['out_tui_fees', 'in_tui_fees', 'avg_net_price_after_grant'], inplace=True, axis=1)
    return

def get_offense_density(df):
    """
    Adds offense density column by counting up offense counts and dividing by student pop
    Args:
        df: A DataFrame object
    Returns:
        None
    """
    offense_cols = ['crimi_off', 'vawa_off', 'arrests', 'discip_actions']
    df[offense_cols] = df[offense_cols].div(df.student_pop, axis=0)
    df.drop(['name', 'student_pop', 'full_fac', 'part_fac'], inplace=True, axis=1, errors='ignore')
    sums = df.loc[:, offense_cols].sum(axis=1)
    df['offense_density'] = sums
    df.drop(offense_cols, inplace=True, axis=1)
    return


def get_train_test_sets(df):
    """
   Splits df into holdout set and train/valid set.

    Args:
        df: a DataFrame object.

    Returns:
        X, X_test, y, y_test: train/valid and holdout sets, DataFrame objects.
    """
    X, y = df.drop('med_income_after_10', axis=1), df.med_income_after_10
    X, X_test, y, y_test = train_test_split(X, y, test_size=.2)
    return X, X_test, y, y_test


def run_cv(X, y, model):
    """
    Runs n_fold cross validation with scaler on given model, returns mean R2 of all folds.

    Args:
        X: train/valid feature set, a DataFrame object
        y: train/valid target set, a Series object
        model: an SKlearn model

    Returns:
        returns: mean of R^2s of all folds
    """
    r2s = []
    X, y = np.array(X), np.array(y)
    kf = KFold(shuffle=True)
    for train_idx, val_idx in kf.split(X, y):
        X_train, y_train = X[train_idx], y[train_idx]
        X_val, y_val = X[val_idx], y[val_idx]
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)

        model.fit(X_train_scaled, y_train)
        r2s.append(model.score(X_val_scaled, y_val))
    return np.mean(r2s)

@ignore_warnings(category=UserWarning)
def get_max_r2_lasso(X, y):
    """
    Performs rudimentary grid search to find best regularization parameter for
    Lasso regression.

    Args:
        X: train/valid feature set, a DataFrame object
        y: train/valid target set, a Series object

    Returns:
        max_r2: the best R2, flaot
        best_alpha: the best regularization parameter, float
    """
    max_r2 = 0
    best_alpha = 0
    for alpha in np.linspace(0, 1, 1000):
        model = Lasso(alpha=alpha)
        r2 = run_cv(X, y, model)
        if r2 > max_r2:
            best_alpha = alpha
            max_r2 = r2

    for alpha in np.linspace(1, 10000, 1000):
        model = Lasso(alpha=alpha)
        r2 = run_cv(X, y, model)
        if r2 > max_r2:
            best_alpha = alpha
            max_r2 = r2
    return max_r2, best_alpha


def get_max_r2_ridge(X, y):
    """
    Performs rudimentary grid search to find best regularization parameter for
    Ridge regression.

    Args:
        X: train/valid feature set, a DataFrame object
        y: train/valid target set, a Series object

    Returns:
        max_r2: the best R2, flaot
        best_alpha: the best regularization parameter, float
    """
    max_r2 = 0
    best_alpha = 0
    for alpha in np.linspace(0, 1, 1000):
        model = Ridge(alpha=alpha)
        r2 = run_cv(X, y, model)
        if r2 > max_r2:
            best_alpha = alpha
            max_r2 = r2

    for alpha in np.linspace(1, 10000, 1000):
        model = Ridge(alpha=alpha)
        r2 = run_cv(X, y, model)
        if r2 > max_r2:
            best_alpha = alpha
            max_r2 = r2
    return max_r2, best_alpha

def run_lm_cv(X, y, model):
    """
    Runs plain n_fold cross vfalidation on linear model, returns mean R2 of all folds.

    Args:
        X: train/valid feature set, a DataFrame object
        y: train/valid target set, a Series object
        model: an SKlearn model

    Returns:
        returns: mean of R^2s of all folds
    """
    r2s = []
    X, y = np.array(X), np.array(y)
    kf = KFold(shuffle=True)
    for train_idx, val_idx in kf.split(X, y):
        X_train, y_train = X[train_idx], y[train_idx]
        X_val, y_val = X[val_idx], y[val_idx]

        model.fit(X_train, y_train)
        r2s.append(model.score(X_val, y_val))
    return np.mean(r2s)
