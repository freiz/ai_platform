from abc import abstractmethod
from typing import Any, Dict

from src.activities.activity import Activity


class ToolActivity(Activity):
    """
    An abstract base class for tool-based activities that inherits from Activity.
    This class serves as a semantic layer to distinguish tool-based activities.
    """
    
    @abstractmethod
    def run(self, **inputs: Any) -> Dict[str, Any]:
        """
        Abstract method that must be implemented by tool-based activities.
        
        Args:
            **inputs: Input values for the activity
        
        Returns:
            Dict[str, Any]: Output values from the activity
        """
        pass 