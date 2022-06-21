from persistance.MongoDb import MongoDb
from reports import DataStoreManager

data_store_manager = DataStoreManager()
mongo_db = MongoDb()


def generate_report():
    print(f"In generate report size is: {data_store_manager.audio_path}")
    report, report_predictions = data_store_manager.retrieve_data()
    save_to_mongo_db(report, report_predictions)


def save_to_mongo_db(report, report_predictions):
    report.predictions_id = mongo_db.save_predictions(report_predictions)
    collection = mongo_db.get_collection(report.interviewee_name)
    collection.insert_report(report)

    # from reports import Report
    # # all_reports = mongo_db.get_all_reports_of_candidate(report.interviewee_name)
    # all_reports = mongo_db.get_all_reports()
    # for candidate_report_dict in all_reports:
    #     candidate_report = Report().from_dict(candidate_report_dict)
    #     predictions = mongo_db.get_prediction(candidate_report.predictions_id)
