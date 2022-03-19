import Singleton


class Manager:
    # Going to be made into a Singleton in the future
    videoThread = None
    videoModel = None
    videoPredictorLandmarks = None
    activeCamera = None

    def __init__(self):
        # Any configuration to be used across the app
        pass
