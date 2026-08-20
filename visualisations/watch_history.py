import base64
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


def create_figure(series: pd.Series, plot_type: str, xlabel: str, ylabel: str):

    fig, ax = plt.subplots()

    match plot_type:
        case 'bar':
            series.plot(kind='bar',ax=ax)

        case 'pie':
            series.plot(kind='pie',ax=ax,autopct='%1.1f%%')

        case 'line':
            series.plot(kind='line', ax=ax)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    return fig

def figure_to_buffer(fig) -> BytesIO:
    buffer = BytesIO()

    fig.savefig(buffer, format='png')
    buffer.seek(0)

    plt.close(fig)

    return buffer



def buffer_to_base64(buffer: BytesIO) -> str:

    encoded_image = base64.b64encode(buffer.getvalue())
    image_representation = encoded_image.decode('utf-8')

    buffer.close()
    return image_representation
