"""
Parsing losses from Oryx sourced html content
"""

from typing import Optional
import logging
import re

from bs4 import BeautifulSoup
from bs4.element import ResultSet


logger = logging.getLogger(__name__)


class OryxLossParser:
    def __init__(self):
        self.category_counter = 0
        self.category_name = None
        self.category_summary = None
        self.type_name = None
        self.type_ttl_count = 0
        self.type_img_links = None
        self.errors = []
        self.buffer = None

    def parse_losses(self, html_content: str) -> list:
        all_losses = []
        soup = BeautifulSoup(html_content, "html.parser")
        tags = soup.find_all(["h3", "h2", "li"])
        for tag in tags:
            self._parse_tag_data(tag, all_losses)
        return all_losses

    def truncate_content(
        self, html_content, exclude_from_str: str, tag_name: Optional[str] = None
    ) -> str:
        """
        :param html_content:
        :param exclude_from_str:
        :param tag_name:
        :return:
        """
        soup = BeautifulSoup(html_content, "html.parser")
        tags = soup.find_all(tag_name) if tag_name else soup.find_all()
        position = self._find_str_pos(tags, exclude_from_str, str(soup))
        return html_content[:position]

    def _find_str_pos(self, tags: ResultSet, string: str, content: str) -> int:
        """
        :param tags: ResultSet type from bs4 (is a list actually)
        :param exclude_from_str:
        :param content:
        :return:
        """
        for tag in tags:
            if string in tag.get_text():
                return content.find(str(tag))
        raise Exception(f"String '{string}' not found in content!")

    def _parse_tag_data(self, tag, losses_lst: list):
        self._parse_category(tag)
        self._parse_type(tag)
        self._add_losses(tag, losses_lst)

    def _parse_category(self, tag: ResultSet):
        """
        Loss category (e.g. "Tanks") is stored in h3/mw-headline.
        Some <h3> exist without headline, we want to ignore those.
        :param tag:
        :return:
        """
        if tag.name == "h3":
            # new_category = tag.find("span", class_="mw-headline")
            new_category = (
                tag.get_text()
                if "of which" in tag.get_text() and "(" in tag.get_text()
                else None
            )

            if new_category:
                self._update_category(tag, new_category)

    def _update_category(self, tag: ResultSet, new_category: str):
        self.category_counter += 1
        self.category_name = self._parse_category_name(new_category)
        self.category_summary = self._parse_category_summary(tag)

    def _parse_category_name(self, category: str) -> str:
        category = category[0 : re.search(r"\(\d", category).start()].strip()
        return category

    def _parse_category_summary(self, tag: ResultSet) -> str:
        """Getting the high level breakdown (destroyed, damaged, abandoned) for the category"""
        full_text = tag.get_text()
        summary = full_text[len(self.category_name) : -1]
        summary_cleaned = re.sub(r"[()]", "", summary).strip()
        return summary_cleaned

    def _parse_type(self, tag: ResultSet):
        if self.category_counter > 0 and tag.name == "li":
            words = tag.get_text(strip=True).split(":")[0].split()
            self.type_ttl_count = self._parse_type_count(words)
            self.type_name = " ".join(
                words[1:]
            )  # rest of the text is the vehicle type, sometimes contains space
            self.type_img_links = self._parse_type_images(tag)

    def _parse_type_count(self, type_text: list[str]) -> int:
        """
        Text starts with ttl loss count for the particular vehicle, but this is missing for some entries
        :param type_text:
        :return:
        """
        try:
            type_count = int(
                type_text[0]
            )  # text starts with ttl loss count for the particular vehicle
        except Exception as e:  # some entries have loss count missing
            type_count = 0
            self.errors.append((e, type_text))
        return type_count

    def _parse_type_images(self, tag: ResultSet) -> str:
        img_tags = tag.find_all("img")
        img_links = [img["src"] for img in img_tags if "src" in img.attrs]
        if img_links:
            img_str = " ".join(img_links)
            return img_str

    def _parse_loss_item(self, tag: ResultSet) -> (str, str):
        text = tag.get_text(strip=True)
        proof = tag.get("href")
        text = self._merge_broken_losses(text)
        if text:
            return text, proof
        else:
            return ("skip", "skip")

    def _merge_broken_losses(self, text: str) -> Optional[str]:
        """
        Some entries are not properly formed and get added in multiple places due to wrong html tag usage in source.
        These are merged here into a single entry.
        E.g. 152mm 2A65 Msta-B howitzer damaged with link https://postimg.cc/q6CYJkkd
        :param text:
        :return:
        """
        if ")" not in text and self.buffer is None:
            self.buffer = text
            return None
        if self.buffer and ")" not in text:
            self.buffer += text
            return None
        if self.buffer and (")") in text:
            text = self.buffer + text
            self.buffer = None
            logger.debug(f"Returning merged text: {text}")
            return text
        return text

    def _create_longrow(self, text: str, proof: str) -> dict:
        row = {}
        row["category_counter"] = self.category_counter
        row["category_name"] = self.category_name
        row["category_summary"] = self.category_summary
        row["type_name"] = self.type_name
        row["type_ttl_count"] = self.type_ttl_count
        row["type_img_links"] = self.type_img_links
        row["loss_item"] = text
        row["loss_proof"] = proof
        return row

    def _add_losses(self, tag: ResultSet, loss_list: list):
        if tag.name == "li" and self.category_counter > 0:
            loss_items = tag.find_all("a")
            for item_tag in loss_items:
                item, link = self._parse_loss_item(item_tag)
                if item != "skip" and "link" != "skip":
                    loss_list.append(self._create_longrow(item, link))
                else:
                    logger.debug("Skipping entry")
