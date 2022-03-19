import threading


class Singleton(object):
    # resources shared by each and every
    # instance

    __singleton_lock = threading.Lock()
    __singleton_instance = None

    # define the class method
    @classmethod
    def instance(cls):

        # check for the singleton instance
        if not cls.__singleton_instance:
            with cls.__singleton_lock:
                if not cls.__singleton_instance:
                    cls.__singleton_instance = cls()

        # return the singleton instance
        return cls.__singleton_instance
