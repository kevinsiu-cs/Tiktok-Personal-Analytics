import pandas as pd


def create_login_history_dataframe(login_history: list[dict]) -> pd.DataFrame:
    login_history_df = pd.DataFrame(
        login_history,
        columns=['Date'],
    )

    if 'Date' not in login_history_df.columns:
        raise ValueError('Login History is missing Date Column')

    login_history_df['Date'] = pd.to_datetime(
        login_history_df['Date'],
        errors='coerce',
    )
    login_history_df = login_history_df.dropna(subset=['Date'])

    return login_history_df


def get_login_daily_counts(login_history_df: pd.DataFrame) -> pd.Series:
    if login_history_df.empty:
        return pd.Series(dtype='int64')

    return login_history_df.resample('D', on='Date').size()


def get_login_weekly_counts(login_history_df: pd.DataFrame) -> pd.Series:
    if login_history_df.empty:
        return pd.Series(dtype='int64')

    # rule: W-Mon, Weekly buckets starting from Monday
    # label: Label is using the left value of the 'bucket'
    # closed: We are including the left value and ignoring the right.
    return login_history_df.resample(
        'W-MON', on='Date', label='left', closed='left'
    ).size()


def get_login_monthly_counts(login_history_df: pd.DataFrame) -> pd.Series:
    if login_history_df.empty:
        return pd.Series(dtype='int64')

    # MS = Month start
    # Group rows by calendar month
    return login_history_df.resample('MS', on='Date').size()


def get_login_hourly_counts(login_history_df: pd.DataFrame) -> pd.Series:
    return login_history_df['Date'].dt.hour.value_counts()


def get_login_weekday_counts(login_history_df: pd.DataFrame) -> pd.Series:
    return login_history_df['Date'].dt.day_name().value_counts()


def get_average_logins_per_active_day(login_history_df: pd.DataFrame) -> float:
    daily_counts = get_login_daily_counts(login_history_df)

    # Remove days when user did not log in
    active_daily_counts = daily_counts[daily_counts > 0]

    if active_daily_counts.empty:
        return 0.0

    return float(active_daily_counts.mean())


def _get_most_active_value(counts: pd.Series):
    if counts.empty or counts.sum() == 0:
        return None

    return counts.idxmax()


def create_login_history_summary(
    login_history_df: pd.DataFrame,
) -> dict[str, object]:
    daily_counts = get_login_daily_counts(login_history_df)
    weekly_counts = get_login_weekly_counts(login_history_df)
    monthly_counts = get_login_monthly_counts(login_history_df)
    hourly_counts = get_login_hourly_counts(login_history_df)
    weekday_counts = get_login_weekday_counts(login_history_df)

    return {
        'total_login_events': len(login_history_df),
        'daily_counts': daily_counts,
        'weekly_counts': weekly_counts,
        'monthly_counts': monthly_counts,
        'hourly_counts': hourly_counts,
        'weekday_counts': weekday_counts,
        'most_active_login_hour': _get_most_active_value(hourly_counts),
        'most_active_login_weekday': _get_most_active_value(weekday_counts),
        'average_logins_per_active_day': (
            get_average_logins_per_active_day(login_history_df)
        ),
        'maximum_logins_in_one_day': (
            int(daily_counts.max()) if not daily_counts.empty else 0
        ),
    }
