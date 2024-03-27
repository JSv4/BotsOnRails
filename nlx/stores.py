import threading
from abc import ABC, abstractmethod
from typing import Any, Optional


class StateStore(ABC):

    @abstractmethod
    def cycle_start_id_ends_at_id(self, start_id) -> str:
        """
        Property to represent cycle ends in the state store.

        Returns:
            dict: Dictionary mapping string to string representing cycle ends.
        """
        pass

    @abstractmethod
    def register_cycle(self, start_id: str, end_id: str):
        """
        Register a cycle between two node ids.

        Args:
            start_id (str): ID of the start node.
            end_id (str): ID of the end node.
        """
        pass

    @abstractmethod
    def set_property_for_node(self, node_name: str, property_name: str, property_value: Any):
        pass

    @abstractmethod
    def get_property_for_node(self, node_name: str, property_name: str) -> Optional[Any]:
        pass

    @abstractmethod
    def dump_store(self) -> dict:
        pass


class InMemoryStateStore(StateStore):
    def __init__(self, state_store: Optional[dict] = None):
        if state_store is None:
            self.state_store = {}
        else:
            self.state_store = state_store

        self.cycle_end_node_lookup: dict[str, str] = {}
        self.lock = threading.Lock()

    def register_cycle(self, start_id: str, end_id: str):
        with self.lock:
            self.cycle_end_node_lookup[start_id] = end_id

    def cycle_start_id_ends_at_id(self, start_id: str) -> Optional[str]:
        with self.lock:
            if start_id not in self.cycle_end_node_lookup:
                return None
            return self.cycle_end_node_lookup[start_id]

    def set_property_for_node(self, node_name: str, property_name: str, property_value: Any):
        with self.lock:
            if node_name not in self.state_store:
                self.state_store[node_name] = {}
            self.state_store[node_name][property_name] = property_value

    def get_property_for_node(self, node_name: str, property_name: str) -> Optional[Any]:
        with self.lock:
            if node_name in self.state_store:
                node_store = self.state_store[node_name]
                if property_name in node_store:
                    return node_store[property_name]
            return None

    def dump_store(self) -> dict:
        with self.lock:
            return self.state_store
