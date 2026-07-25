from abc import ABC, abstractmethod

class BasePatch(ABC):
    name: str = ""
    description: str = ""

    @abstractmethod
    def is_applied(self, data: bytearray) -> bool:
        """Returns True if this patch is currently applied to the executable data."""
        pass

    @abstractmethod
    def apply(self, data: bytearray) -> bool:
        """Applies the patch to executable data in-place. Returns True if modified."""
        pass

    @abstractmethod
    def remove(self, data: bytearray) -> bool:
        """Removes the patch from executable data in-place. Returns True if modified."""
        pass
