import pandas as pd


# This Function will be used to create a DataFrame and handle missing values
def create_watch_history_dataframe(watch_history: list[dict]) -> pd.DataFrame:

    # Cast the dict into a DataFrame
    df = pd.DataFrame(watch_history)

    if 'Date' not in df.columns:
        raise ValueError('Watch History is missing Date Column')

    # Change the current Date String into a PD.DateTime object
    df['Date'] = pd.to_datetime(df['Date'])

    # Drop any rows with NA values on date
    df = df.dropna(subset=['Date'])

    return df

def add_watch_history_features(watch_history_df: pd.DataFrame) -> pd.DataFrame:
    featured_df = watch_history_df.copy()

    # Create features based off of what metrics we want to compute
    featured_df['Day'] = featured_df['Date'].dt.day_name()
    featured_df['DateOnly'] = featured_df['Date'].dt.date # Needed due to normal date returning the time
    featured_df['Hour'] = featured_df['Date'].dt.hour
    featured_df = featured_df.drop(columns=['Link']) # Drop unneeded link values.

    return featured_df

def get_hourly_counts(watch_history_df: pd.DataFrame) -> pd.Series:
    return watch_history_df['Hour'].value_counts()

def get_daily_counts(watch_history_df: pd.DataFrame) -> pd.Series:
    return watch_history_df.resample('D', on='Date').size()

def get_weekday_counts(watch_history_df: pd.DataFrame) -> pd.Series:
    return watch_history_df['Day'].value_counts()


def create_watch_history_summary(watch_history_df: pd.DataFrame) -> dict[str, int]:
    hourly_counts = get_hourly_counts(watch_history_df)
    daily_counts = get_daily_counts(watch_history_df)
    weekday_counts = get_weekday_counts(watch_history_df)

    summary = {
        'hourly_counts': hourly_counts,
        'daily_counts': daily_counts,
        'weekday_counts': weekday_counts,

        'most_active_hour': hourly_counts.idxmax(),
        'most_active_weekday': weekday_counts.idxmax(),
        'most_active_day': daily_counts.idxmax()
    }

    return summary
