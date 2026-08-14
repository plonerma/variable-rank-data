#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "click",
#     "requests",
#     "rich",
#     "pymupdf",
# ]
# ///


import requests
from requests.exceptions import ConnectionError

from rich.console import Console

import click
import pymupdf
from urllib.request import url2pathname
from urllib.parse import urlparse
import json

console = Console()


class ZoteroInterface():
    debug = False

    URL = "http://127.0.0.1:23119/better-bibtex/export?/library;name:My%20Library/collection/Variable-rank%20Adaptation/Methods/test.jzon"
    SELECT_URL = "zotero://select/library/items/{itemKey}"


    @classmethod
    def select_link(cls, item=None, itemKey: str | None = None):
        if itemKey is None:
            assert item is not None
            itemKey = item["item-key"]
        selectURL = cls.SELECT_URL.format(itemKey=itemKey)

        text = itemKey
        return f"[link={selectURL}]{text}[/link]"



    @classmethod
    def get_all_items(cls):
        try:
            r = requests.get(cls.URL)
            r.raise_for_status()

            json = r.json()

            return json["items"]
        except ConnectionError:
            console.print(
                "Could retrieve Zotero collection: Make sure zotero is running!",
                style="red",
            )
            quit(1)

    @classmethod
    def has_tag(cls, item, tag: str):
        if "tags" not in item:
            return False

        for t in item["tags"]:
            if t["tag"] == tag:
                return True
        return False

    @classmethod
    def get_result_tables(cls):
        for item in cls.get_all_items():
            if item["itemType"] == "note":
                continue

            item_properties = {
                "item-key": item["key"],
                "cite-key": item["citationKey"],
                "title": item["title"],
                "date": item["date"],
                "doi": item.get("DOI"),
            }


            if cls.debug:
                console.rule(cls.select_link(item_properties))
                console.print(item)


    @classmethod
    def get_items(cls, itemKey: str | None = None, **kw):
        url = "http://localhost:23119/api/users/0/items"

        if itemKey is not None:
            url += f"/{itemKey}"

        if len(kw) > 0:
            params = "&".join(f"{k}={v}" for k, v in kw.items())
            url += f"?{params}"

        try:
            r = requests.get(url)
            r.raise_for_status()

            return r.json()

        except ConnectionError:
            console.print(
                "Could retrieve Zotero collection: Make sure zotero is running!",
                style="red",
            )
            quit(1)


    @classmethod
    def get_annotation_tree(cls):
        pdf_items = {}

        for item in cls.get_items(itemType="annotation"):
            if not cls.has_tag(item["data"], "results-table"):
                continue

            #console.print(item)

            parentKey = item["data"]["parentItem"]

            if parentKey not in pdf_items:
                pdf = cls.get_items(parentKey)
                paper = cls.get_items(pdf["data"]["parentItem"])["data"]


                del paper["collections"]
                del paper["tags"]
                del paper["dateAdded"]
                del paper["dateModified"]
                del paper["relations"]

                pdf_items[parentKey] = {
                    "annotations": [],
                    "pdf": pdf,
                    **paper,
                }

            item_data = item["data"]
            item_data["annotationPosition"] = json.loads(item_data["annotationPosition"])

            del item_data["tags"]
            del item_data["dateAdded"]
            del item_data["dateModified"]
            del item_data["relations"]

            pdf_items[parentKey]["annotations"].append(item_data)

        return pdf_items







@click.command()
@click.option("--debug", is_flag=True)
def run(debug: bool = False):
    console.print("Extracting result tables")


    #ZoteroInterface.get_result_tables()
    for paperKey, paperData in ZoteroInterface.get_annotation_tree().items():
        console.rule(ZoteroInterface.select_link(itemKey=paperKey))
        console.print(paperData)

        p = urlparse(paperData["pdf"]["links"]["enclosure"]["href"])
        pdf_path = url2pathname(p.path)

        doc = pymupdf.open(pdf_path)

        for annotation in paperData["annotations"]:
            pos = annotation["annotationPosition"]
            console.print("Extracting:", pos)
            page = doc[pos["pageIndex"]]

            left, bottom, right, top = pos["rects"][0]

            clip = pymupdf.Rect(left, page.rect.height - top, right, page.rect.height - bottom)
            pixmap = page.get_pixmap(dpi=150, clip=clip)
            annotation_key = annotation["key"]
            pixmap.save(f"data/tables/{annotation_key}.png")

            with open(f"data/tables/{annotation_key}.txt", "w") as f:
                f.write(annotation["annotationComment"])
            
            break

        del paperData["pdf"]

        with open(f"data/papers/{paperKey}.json", "w") as f:
            json.dump(paperData, f)




if __name__ == "__main__":
    run()
