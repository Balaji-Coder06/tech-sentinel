from abc import ABC, abstractmethod
from typing import List
from ..models import RawItem

class BaseCollector(ABC):
    def __init__(self, source_id: str, name: str, url: str, category: str = "development"):
        self.source_id = source_id
        self.name = name
        self.url = url
        self.category = category

    @abstractmethod
    def fetch(self) -> List[RawItem]:
        """Fetch items from the source and return normalized RawItems."""
        pass
