from .util import to_unicode as to_unicode
from typing import Any

class Envelope: ...
class Address: ...

class SearchIds(list):
    modseq: Any = ...
    def __init__(self, *args: Any) -> None: ...

class BodyData(tuple):
    @classmethod
    def create(cls, response: Any): ...
    @property
    def is_multipart(self): ...
