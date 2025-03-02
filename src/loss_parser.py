"""
Parsing losses from Oryx sourced html content
"""
from time import sleep
from datetime import datetime

from bs4 import BeautifulSoup


class OryxLossParser:
    def __init__(self):
        self.category_counter = 0
        self.category_name = None
        self.category_summary = None
        self.type_name = None
        self.type_ttl_count = 0
        self.type_img_links = None
        self.errors = []

    def parse_losses(self, html_content):
        all_losses = []
        soup = BeautifulSoup(html_content, 'html.parser')
        tags = soup.find_all(["h3", "h2", "li"])
        for tag in tags:
            print(f"tag: {tag}")
            self.parse_category(tag)
            self.parse_type(tag)
            self.add_losses(tag, all_losses)
            if self.completed(tag):
                return all_losses
        return all_losses

    def parse_category(self, tag):
        """
        Loss category (e.g. "Tanks") is stored in h3/mw-headline.
        Some <h3> exist without headline, we want to ignore those.
        :param tag:
        :return:
        """
        if tag.name == "h3":
            try:
                new_category_name = tag.find("span", class_="mw-headline").get_text()
            except Exception as e:
                return None
            if new_category_name:
                self.category_counter += 1
                self.category_name = new_category_name.strip()
                self.category_summary = self.parse_category_summary(tag, new_category_name)

    def parse_category_summary(self, tag, new_category_name: str) -> str:
        """Getting the high level breakdown (destroyed, damaged, abandoned) for the category:
        We need what comes after the category name, and we are cutting off the brackets with +-1"""
        full_text = tag.get_text()
        summary = full_text[len(new_category_name) + 1 :-1]
        return summary

    def parse_type(self, tag):
        if self.category_counter > 0 and tag.name == "li":
            words = tag.get_text(strip=True).split(":")[0].split()
            self.type_ttl_count = self.parse_type_count(words)
            self.type_name = " ".join(words[1:])  # rest of the text is the vehicle type, sometimes contains space
            self.type_img_links = self.parse_type_images(tag)

    def parse_type_count(self, type_text: list[str]) -> int:
        """
        Text starts with ttl loss count for the particular vehicle, but this is missing for some entries
        :param type_text:
        :return:
        """
        try:
            type_count = int(type_text[0])  # text starts with ttl loss count for the particular vehicle
        except Exception as e:  # some entries have loss count missing
            type_count = 0
            self.errors.append((e, type_text))
        return type_count

    def parse_type_images(self, tag) -> str:
        img_tags = tag.find_all("img")
        img_links = [img["src"] for img in img_tags if "src" in img.attrs]
        img_str = " ".join(img_links)
        return img_str

    def loop_item_parser(self, tag):
        loss_items = tag.find_all("a")
        for item_tag in loss_items:
            item = self.parse_loss_item(item_tag)

    def parse_loss_item(self, tag):
        text = tag.get_text(strip=True)
        proof = tag.get('href')
        return text, proof

    def create_longrow(self, text, proof):
        row = {}
        row["category_counter"] = self.category_counter
        row["category_name"] = self.category_name
        row["category_summary"] = self.category_summary
        row["type_name"] = self.type_name
        row["type_ttl_count"] = self.type_ttl_count
        row["type_img_links"] = self.type_img_links
        row["loss_item"] = text
        row["loss_proof"] = proof
        print(row)
        print(f"Item -> {row['loss_item']}")
        return row

    def add_losses(self, tag, loss_list):
        if tag.name == "li" and self.category_counter > 0:
            loss_items = tag.find_all("a")
            for item_tag in loss_items:
                item, link = self.parse_loss_item(item_tag)
                loss_list.append(self.create_longrow(item, link))
                sleep(0.05)

    def completed2(self, item_tag, expression: str):
        pass



    def completed(self, tag):
        if tag.name == "h3" and tag.get_text() == "Popular Articles":
            return True