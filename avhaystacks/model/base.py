from abc import ABC, abstractmethod

class BaseModel(ABC):

    @abstractmethod
    def prepare_input(self, inputs):
        """
        the method to prepare image of different models
        """
        pass
    
    @abstractmethod
    def generate(self):
        """
        the method to response/infer of different models
        """
        pass
