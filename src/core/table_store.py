from typing import Optional, Callable
from src.core.warehouse import DataWarehouse
from src.core.data_table import DataTable
from src.core.schema import Schema

class TableStore:
    """
    Singleton store for managing the currently active table across all views.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        """Initialize instance attributes."""
        self.warehouse = DataWarehouse()
        self._active_table_name: Optional[str] = None
        self._observers: list[Callable[[str], None]] = []

    @property
    def active_table_name(self) -> Optional[str]:
        """Get the name of currently active table."""
        return self._active_table_name
    
    def set_active_table(self, table_name: str) -> None:
        """Set the currently active table and notify all observers."""
        if table_name not in self.warehouse.tables and table_name is not None:
            raise KeyError(f"Table '{table_name}' not found in warehouse.")
        self._active_table_name = table_name
        self._notify_observers()
    
    def get_active_table(self) -> DataTable:
        """Get the currently active DataTable instance."""
        if not self._active_table_name:
            raise ValueError("No active table set")
        return self.warehouse.get_table(self._active_table_name)

    def add_observer(self, observer: Callable[[str], None]) -> None:
        """Add an observer to be notified of table changes."""
        if observer not in self._observers:
            self._observers.append(observer)
    
    def _notify_observers(self) -> None:
        """Notify all observers of table change."""
        for observer in self._observers:
            observer(self._active_table_name)

    @property 
    def schema(self) -> Schema:
        """Get the schema from warehouse."""
        return self.warehouse.schema