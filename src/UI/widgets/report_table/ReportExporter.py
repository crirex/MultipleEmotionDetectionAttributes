import time

from collections import Counter
from persistance import MongoDb
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

time_format = "%Y-%m-%d %H-%M"


def plot_bar(predictions, fig):
    if predictions is None or len(predictions) == 0:
        return

    emotions = [value[1] for value in predictions.values()]
    emotions_count = Counter(emotions)
    ax = fig.add_subplot(111)
    plt.bar(emotions_count.keys(), emotions_count.values(), color='red', lw=5)


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

        fig = plt.figure()
        plot_bar(predictions.audio_predictions, fig)

        # plt.plot(random_shit, [2, 1, 7, 1, 2], color='red', lw=5)
        # ax2 = fig.add_subplot(312)
        # plt.bar(random_shit, [3, 5, 1, 5, 3], color='green', lw=5)
        # plt.bar(random_shit, [11, 3, 4, 2, 9], color='blue', lw=5)
        # plt.plot(random_shit, [2, 1, 7, 1, 2], color='red', lw=5)

        # ax3 = fig.add_subplot(313)
        # plt.plot([1, 2, 3, 4, 5], color='yellow', lw=5)

        filename = self._path + f"\\{report['interviewee_name']}-" \
                                f"{report['interviewer_name']}-" \
                                f"{time.strftime(time_format, time.localtime(report['interview_start_date']))}.pdf"
        save_multi_image(filename)
