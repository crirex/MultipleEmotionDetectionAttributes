import time

from collections import Counter
from persistance import MongoDb
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

time_format = "%Y-%m-%d %H-%M"


def plot_bar(predictions, title, subplot, fig):
    ax = fig.add_subplot(subplot)
    plt.xlabel('Emotions')
    plt.ylabel('Count')
    if predictions is None or len(predictions) == 0:
        plt.title("No " + title)
        return

    emotions = [value[1] for value in predictions.values()]
    emotions_count = Counter(emotions)
    plt.title(title)
    plt.bar(emotions_count.keys(), emotions_count.values(), color='red', lw=5)


def plot(predictions, title, subplot, fig):
    ax = fig.add_subplot(subplot)
    plt.xlabel('Seconds')
    plt.ylabel('Emotions')
    if predictions is None or len(predictions) == 0:
        plt.title("No " + title)
        return

    emotions = [value[1] for value in predictions.values()]
    plt.title(title)

    plt.plot(np.arange(len(emotions)) * 4, emotions, color='blue')


def plot_bar_text(predictions, title, subplot, fig):
    ax = fig.add_subplot(subplot)
    plt.xlabel('Emotions')
    if predictions is None or len(predictions) == 0:
        plt.title("No " + title)
        return

    plt.title(title)
    plt.bar(predictions.keys(), predictions.values(), color='green', lw=5)


def save_multi_image(filename):
    pp = PdfPages(filename)
    fig_nums = plt.get_fignums()
    figs = [plt.figure(n) for n in fig_nums]
    for fig in figs:
        fig.savefig(pp, format='pdf')
    pp.close()


class ReportExporter:
    def __init__(self, path):
        self._mongo_db = MongoDb()
        self._path = path

    def export_report(self, report):
        predictions = self._mongo_db.get_prediction(report['predictions_id'])
        print(report)

        plt.rcParams["figure.figsize"] = [7.00, 3.50]
        plt.rcParams["figure.autolayout"] = True

        fig_audio = plt.figure()
        plot_bar(predictions.audio_predictions, "Total Audio Predictions", 211, fig_audio)
        plot(predictions.audio_predictions, "Audio Predictions Each Second", 212, fig_audio)

        fig_video = plt.figure()
        plot_bar(predictions.video_predictions, "Total Video Predictions", 211, fig_video)
        plot(predictions.video_predictions, "Video Predictions Each Second", 212, fig_video)

        fig_text = plt.figure()
        plot_bar_text(predictions.text_predictions, "Total Text Predictions", 111, fig_text)

        filename = self._path + f"\\{report['interviewee_name']}-" \
                                f"{report['interviewer_name']}-" \
                                f"{time.strftime(time_format, time.localtime(report['interview_start_date']))}.pdf"
        try:
            save_multi_image(filename)
        finally:
            plt.close("all")
