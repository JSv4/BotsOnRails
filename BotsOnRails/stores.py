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
    def node_id_in_cycle(self, node_id: str) -> Optional[list]:
        """
        Given a random node id, is it in a cycle, and, if so, return list of cycle node ids from start to finish
        """
        pass

    @abstractmethod
    def register_cycle(self, node_ids: list[str]):
        """
        Register a cycle between two node ids.

        Args:
            node_ids (list[str]): List of node ids in this cycle from start to end. ORDER MATTERS.
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

    @abstractmethod
    def dump_cycle_end_node_lookup(self) -> dict:
        pass

    @abstractmethod
    def to_json(self) -> dict:
        pass

    @abstractmethod
    def reset(self, *args, **kwargs):
        pass

    @classmethod
    @abstractmethod
    def from_json(cls, dict: dict) -> 'StateStore':
        pass



class InMemoryStateStore(StateStore):
    def __init__(
        self,
        state_store: Optional[dict] = None,
        cycle_end_node_lookup: Optional[dict[str, str]] = None,
        cycle_store: Optional[dict[str, list[str]]] = None
    ):
        if state_store is None:
            self.state_store = {}
        else:
            self.state_store = state_store

        if cycle_store is None:
            self.cycle_store = {}
        else:
            self.cycle_store = cycle_store

        if cycle_end_node_lookup is None:
            self.cycle_end_node_lookup = {}
        else:
            self.cycle_end_node_lookup = cycle_end_node_lookup

        self.lock = threading.Lock()

    def reset(
        self,
        state_store: Optional[dict] = None,
        cycle_end_node_lookup: Optional[dict[str, str]] = None,
        cycle_store: Optional[dict[str, list[str]]] = None
    ):
        if state_store is None:
            self.state_store = {}
        else:
            self.state_store = state_store

        if cycle_store is None:
            self.cycle_store = {}
        else:
            self.cycle_store = cycle_store

        if cycle_end_node_lookup is None:
            self.cycle_end_node_lookup = {}
        else:
            self.cycle_end_node_lookup = cycle_end_node_lookup

    def register_cycle(self, node_ids: list[str]):
        start_id = node_ids[0]
        end_id = node_ids[-1]
        with self.lock:
            self.cycle_end_node_lookup[start_id] = end_id
            for node_id in node_ids:
                self.cycle_store[node_id] = node_ids

    def node_id_in_cycle(self, node_id: str) -> Optional[list[str]]:
        if node_id in self.cycle_store:
            return self.cycle_store[node_id]
        else:
            return None

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

    def dump_cycle_end_node_lookup(self) -> dict:
        with self.lock:
            return self.cycle_end_node_lookup

    def dump_cycle_store(self):
        with self.lock:
            return self.cycle_store

    def to_json(self) -> dict:
        return {
            "cycle_end_node_lookup": self.cycle_end_node_lookup(),
            "cycle_store": self.dump_cycle_store(),
            "state_store": self.dump_store()
        }

    def from_json(cls, dict: dict) -> 'StateStore':
        return InMemoryStateStore(
            cycle_store=dict['cycle_store'],
            cycle_end_node_lookup=dict['cycle_end_node_lookup'],
            state_store=dict['state_store']
        )
