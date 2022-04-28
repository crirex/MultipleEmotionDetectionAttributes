class MongoDbCollection:
    def __init__(self, name, collection):
        self._collection = collection
        self._name = name

    def insert_report(self, report):
        self._collection.insert_one(report.__dict__)

    def get_all_reports(self):
        return [report for report in self._collection.find()]
