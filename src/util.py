"""
Helper functions/classes shared by the different parsers
"""

from abc import ABC, abstractmethod
from typing import Any, Self, Union, Optional
from pathlib import Path
from argparse import ArgumentParser, Namespace
import re

from bs4 import BeautifulSoup
from bs4.element import ResultSet
import pandas as pd


class Content(ABC):
    def __init__(self, source: Any):
        self._source = source
        self._content: Optional[Union[str, pd.DataFrame]] = None

    def __call__(self):
        return self._content

    @abstractmethod
    def load(self) -> Self:
        pass


class HTMLFileContent(Content):
    def __init__(self, source: Union[str, Path]):
        self.soup: Optional[BeautifulSoup] = None
        super().__init__(source)

    def load(self) -> Self:
        with open(self._source) as file:
            self._content = file.read()
        self.soup = BeautifulSoup(self._content, "html.parser")
        return self

    def truncate_content(
        self, exclude_from_str: str, tag_name: Optional[str] = None
    ) -> Self:
        """
        :param exclude_from_str:
        :param tag_name:
        :return:
        """
        tags = self.soup.find_all(tag_name) if tag_name else self.soup.find_all()
        position = self._find_str_pos(tags, exclude_from_str)
        self._content = self._content[:position]
        return self

    def _find_str_pos(self, tags: ResultSet, string: str) -> int:
        for tag in tags:
            if string in tag.get_text():
                value = str(self.soup).find(str(tag))
                return value
        raise Exception(f"String '{string}' not found in content!")


class ParsedContent(Content):
    def __init__(self, source: Union[list[dict], str, Path]):
        super().__init__(source)

    def load(self) -> Self:
        if isinstance(self._source, list):
            self._content = pd.DataFrame(self._source)
        elif isinstance(self._source, str) or isinstance(self._source, Path):
            self._content = pd.read_csv(self._source, index_col=0)
        else:
            raise TypeError(f"ParsedContent class supports only str, path and [list[dict]] sequence"
                            f" but received {type(self._source)}!")
        return self

    def clean_content(self) -> Self:
        invisible_pattern = r"[\t\u00A0\u2007\u202F\u200B-\u200D\uFEFF]"
        self._content.replace(invisible_pattern, " ", inplace=True, regex=True)
        return self

    def strip_archive_url(self) -> Self:
        archive_pattern = r"https?://web\.archive\.org/web/\d+[^/]*/(https?://[^\s\"'>]+)"
        self._content.replace(archive_pattern, r"\1", inplace=True, regex=True)
        return self

    def to_csv(self, output_file: Union[str, Path]) -> None:
        self._content.to_csv(output_file)


def parse_args() -> Namespace:
    parser = ArgumentParser(description="Moving html content into longrow csv file")
    parser.add_argument("--file", help="Path to file with html content", required=True)
    parser.add_argument(
        "--output_file", help="Name of output file (csv)", required=True
    )
    arguments = parser.parse_args()
    return arguments
