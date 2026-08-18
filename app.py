from pathlib import Path

from flask import Flask, render_template
import base64

from services import file_services
from analytics import watch_history as watch_history_analytics
from visualisations import watch_history as watch_history_visualisations

app = Flask(__name__)


def prepare_watch_history_dataframe(path: Path):
    tiktok_data = file_services.load_file_as_json(path)
    watch_history_records = file_services.get_watch_history(tiktok_data)

    watch_history_df = watch_history_analytics.create_watch_history_dataframe(
        watch_history_records
    )

    return watch_history_analytics.add_watch_history_features(watch_history_df)


@app.route('/')
def index():
    data_path = (
        Path(__file__).parent
        / 'data'
        / 'user_data_tiktok.json'
    )

    watch_history_df = prepare_watch_history_dataframe(data_path)
    summary = watch_history_analytics.create_watch_history_summary(
        watch_history_df
    )

    hourly_counts = summary['hourly_counts']

    fig1 = watch_history_visualisations.create_hourly_figure(hourly_counts)
    buffer1 = watch_history_visualisations.figure_to_buffer(fig1)
    hourly_graph = base64.b64encode(buffer1.getvalue()).decode('utf-8')

    weekday_counter = summary['weekday_counts']
    fig2 = watch_history_visualisations.create_weekday_pie(weekday_counter)
    buffer2 = watch_history_visualisations.figure_to_buffer(fig2)
    weekday_graph = base64.b64encode(buffer2.getvalue()).decode('utf-8')

    return render_template(
        'index.html',
        hourly_graph=hourly_graph,
        weekday_graph=weekday_graph
    )


if __name__ == '__main__':
    app.run(debug=True)
