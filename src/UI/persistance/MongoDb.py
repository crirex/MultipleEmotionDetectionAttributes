from persistance.MongoDbCollection import MongoDbCollection
from utils import Singleton
import pymongo
import gridfs
import pickle

connection_string = "mongodb://localhost:27017/"
database_name = "MultipleEmotionDetectionAttributes"


class MongoDb(metaclass=Singleton):
    def __init__(self):
        self._mongo_client = pymongo.MongoClient(connection_string)
        self._mongo_database = self._mongo_client[database_name]
        self._mongo_collections = {}

        self._mongo_fs_collection = gridfs.GridFS(self._mongo_database)

    def get_collection(self, interviewee_name):
        if interviewee_name not in self._mongo_collections:
            self._create_collection(interviewee_name)

        return self._mongo_collections[interviewee_name]

    def _create_collection(self, interviewee_name):
        self._mongo_collections[interviewee_name] = \
            MongoDbCollection(interviewee_name, self._mongo_database[interviewee_name])

    def save_predictions(self, predictions):
        return self._mongo_fs_collection.put(pickle.dumps(predictions, protocol=2))

    def get_all_reports_of_candidate(self, name):
        collections_name = self._mongo_database.list_collection_names()
        if name not in collections_name:
            return None

        return self.get_collection(name).get_all_reports()

    def get_all_reports(self):
        collections_name = self._mongo_database.list_collection_names()
        reports = [self.get_collection(collection_name).get_all_reports() for collection_name in collections_name
                   if collection_name not in ['fs.chunks', 'fs.files']]

        return [report for reports_group in reports for report in reports_group]

    def get_prediction(self, objectId):
        if objectId is None:
            return None

        binary_data = self._mongo_fs_collection.get(objectId).read()
        if binary_data is None:
            return None

        predictions = pickle.loads(binary_data)
        return predictions
