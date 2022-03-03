from abc import abstractmethod, ABC


class BaseIntegerationManager(ABC):
    @abstractmethod
    def get_invalid_token_objects(self):
        pass

