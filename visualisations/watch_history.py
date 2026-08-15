import pandas as pd
import matplotlib.pyplot as plt

def plot_hourly_counts(hourly_counts: pd.Series) -> None:

    hourly_counts = hourly_counts.sort_index()

    ax = hourly_counts.plot(kind='bar')

    ax.set_xlabel('Hour of Day')
    ax.set_ylabel('Videos Scrolled')

    plt.show()

def plot_weekday_counts(weekday_counts: pd.Series) -> None:
    weekday_counts.plot(
        kind='pie',
        autopct = '%1.1f%%'
    )
    plt.show()
