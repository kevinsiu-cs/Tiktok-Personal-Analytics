from io import BytesIO

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



def create_hourly_figure(hourly_counts: pd.Series):
    fig, ax = plt.subplots()

    hourly_counts.sort_index().plot(kind='bar', ax = ax)

    ax.set_xlabel('Hour of Day')
    ax.set_ylabel('Videos Scrolled')

    return fig


def create_weekday_pie(weekday_counts: pd.Series):
    fig, ax = plt.subplots()
    weekday_counts.plot(kind='pie', autopct='%1.1f%%', ax=ax)
    return fig



def figure_to_buffer(fig) -> BytesIO:
    buffer = BytesIO()

    fig.savefig(buffer, format='png')
    buffer.seek(0)

    plt.close(fig)

    return buffer