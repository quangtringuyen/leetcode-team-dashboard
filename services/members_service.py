# services/members_service.py
from __future__ import annotations
from typing import List, Dict, Any

from core.storage import Storage

DATA_PATH = "data/members.json"


class MembersService:
    def __init__(self, storage: Storage):
        self.storage = storage

    def load_all_members(self) -> Dict[str, Any]:
        return self.storage.read_json(DATA_PATH, default={})

    def save_all_members(self, all_members: Dict[str, Any]) -> None:
        self.storage.write_json(DATA_PATH, all_members)

    def load_members(self, owner: str) -> List[Dict[str, str]]:
        return self.load_all_members().get(owner, [])

    def save_members(self, owner: str, members: List[Dict[str, str]]) -> None:
        full = self.load_all_members()
        full[owner] = members
        self.save_all_members(full)

    def add_member(self, owner: str, name: str, username: str) -> bool:
        members = self.load_members(owner)
        if any(m["username"] == username for m in members):
            return False
        members.append({"name": name, "username": username})
        self.save_members(owner, members)
        return True

    def remove_member(self, owner: str, username: str) -> None:
        members = [m for m in self.load_members(owner) if m["username"] != username]
        self.save_members(owner, members)
