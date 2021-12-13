import random


class Api:
    class __impl:
        """ Implementation of the Singleton class """
        def get_result(self): 
            return self.result
        def __init__(self):
            self.result = random.randint(0,1000)

    # The private class attribute holding the "one and only instance"
    __instance = __impl()

    def __getattr__(self, attr):
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        return setattr(self.__instance, attr, value)



