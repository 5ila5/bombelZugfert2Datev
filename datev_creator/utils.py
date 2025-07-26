from abc import ABC, abstractmethod
from dataclasses import dataclass

from lxml import etree  # nosec B410

SOFTWARE_NAME = "BombelczykDatevCreator"


class XmlBuilder(ABC):
    """Abstract base class for XML builders."""

    @property
    @abstractmethod
    def xml(self) -> etree._Element | etree._ElementTree:
        """Return the XML representation of the object."""
        pass


@dataclass
class XmlAttribute(ABC):
    """Abstract base class for XML builders."""

    key: str
    value: str
