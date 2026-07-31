

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ExtractionResult:
    title: str
    content: str
    summary: str | None
    extraction_method: str


class BaseExtractor(ABC):

    name: str

    @abstractmethod
    def extract(self, html: str, url: str) -> ExtractionResult | None:
        raise NotImplementedError
