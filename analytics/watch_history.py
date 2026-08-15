import pandas as pd


# This Function will be used to create a DataFrame and handle missing values
def create_watch_history_dataframe(watch_history: list[dict]) -> pd.DataFrame:

    df = pd.DataFrame(watch_history)

    if 'Date' not in df.columns:
        raise ValueError('Watch History is missing Date Column')

    df['Date'] = pd.to_datetime(df['Date'])
    df = df.dropna(subset=['Date'])

    return df

def add_watch_history_features(watch_history_df: pd.DataFrame) -> pd.DataFrame:
    featured_df = watch_history_df.copy()

    featured_df['Day'] = featured_df['Date'].dt.day_name()
    featured_df['DateOnly'] = featured_df['Date'].dt.date
    featured_df['Hour'] = featured_df['Date'].dt.hour
    featured_df = featured_df.drop(columns=['Link'])

    return featured_df

def get_hourly_counts(watch_history_df: pd.DataFrame) -> pd.Series:
    return watch_history_df['Hour'].value_counts()

def get_daily_counts(watch_history_df: pd.DataFrame) -> pd.Series:
    return watch_history_df.resample('D', on='Date').size()

def get_weekday_counts(watch_history_df: pd.DataFrame) -> pd.Series:
    return watch_history_df['Day'].value_counts()




