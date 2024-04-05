import threading
from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel, Field


class StateStore(BaseModel, ABC):
    @abstractmethod
    def cycle_start_id_ends_at_id(self, start_id) -> str:
        pass

    @abstractmethod
    def node_id_in_cycle(self, node_id: str) -> Optional[list]:
        pass

    @abstractmethod
    def register_cycle(self, node_ids: list[str]):
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
    def reset(self, *args, **kwargs):
        pass

    class Config:
        arbitrary_types_allowed = True  # Allow arbitrary types


class InMemoryStateStore(StateStore):
    state_store: dict = Field(default_factory=dict)
    cycle_end_node_lookup: dict[str, str] = Field(default_factory=dict)
    cycle_store: dict[str, list[str]] = Field(default_factory=dict)
    lock: threading.Lock = Field(default_factory=threading.Lock, exclude=True)

    def __init__(self, **data: Any):
        super().__init__(**data)

    def reset(self, **data: Any):
        self.__init__(**data)

    def register_cycle(self, node_ids: list[str]):
        start_id = node_ids[0]
        end_id = node_ids[-1]
        with self.lock:
            self.cycle_end_node_lookup[start_id] = end_id
            for node_id in node_ids:
                self.cycle_store[node_id] = node_ids

    def node_id_in_cycle(self, node_id: str) -> Optional[list[str]]:
        return self.cycle_store.get(node_id)

    def cycle_start_id_ends_at_id(self, start_id: str) -> Optional[str]:
        with self.lock:
            return self.cycle_end_node_lookup.get(start_id)

    def set_property_for_node(self, node_name: str, property_name: str, property_value: Any):
        with self.lock:
            if node_name not in self.state_store:
                self.state_store[node_name] = {}
            self.state_store[node_name][property_name] = property_value

    def get_property_for_node(self, node_name: str, property_name: str) -> Optional[Any]:
        with self.lock:
            node_store = self.state_store.get(node_name)
            if node_store:
                return node_store.get(property_name)
        return None

    def dump_store(self) -> dict:
        with self.lock:
            return self.state_store

    def dump_cycle_end_node_lookup(self) -> dict:
        with self.lock:
            return self.cycle_end_node_lookup

    def dump_cycle_store(self) -> dict:
        with self.lock:
            return self.cycle_store
