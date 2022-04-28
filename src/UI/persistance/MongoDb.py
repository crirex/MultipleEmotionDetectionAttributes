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
