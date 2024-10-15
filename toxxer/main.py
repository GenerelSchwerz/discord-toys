import asyncio
from typing import Literal, Union
import aiohttp

from dataclasses import dataclass
from enum import Enum


from .helper import get_basic_headers_with_super_properties


@dataclass
class ReportParams:
    # defaults as of October 14, 2024 for a USER REPORT.
    channel_id: int
    message_id: int
    reason: str
    breadcrumbs: list[int]


class VersionType(Enum):
    V1 = "1.0"


class VariantTypes(Enum):
    USER = 5


class Tox:
    def __init__(
        self, client: aiohttp.ClientSession, version: VersionType, variant: VariantTypes
    ):
        self._client = client
        self.version = version

        self.__headers = self.__setup_default_headers()

        # for caching purposes, re-use the same headers as much as possible.

    def __setup_default_headers(self, ua=None) -> dict[str, str]:
        if ua is None:
            ua = get_linux_useragent()  # lazy, replace with more robust UA code.

        headers = get_basic_headers_with_super_properties(ua)
        return headers

    def report(self, channel_id: int, message_id: int):
        self.version.value
        pass


if __name__ == "__main__":
    from .helper import get_basic_headers_with_super_properties, get_linux_useragent

    uc = get_linux_useragent()
    print(get_basic_headers_with_super_properties(uc))
    print("Hello, World!")
