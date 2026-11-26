from abc import ABC, abstractmethod
from typing import List
from app.models.domain_models import RawJob

class BaseJobSource(ABC):
    """
    Abstract base class for all job sources (scrapers or APIs).
    Any new source must inherit from this and implement fetch_jobs.
    """
    
    @abstractmethod
    def fetch_jobs(self, keywords: List[str], location: str) -> List[RawJob]:
        """
        Fetches jobs based on keywords and location.
        Returns a list of RawJob objects containing unstructured data.
        """
        pass
