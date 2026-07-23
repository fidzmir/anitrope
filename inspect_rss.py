import httpx
from bs4 import BeautifulSoup

res_ann = httpx.get("https://www.animenewsnetwork.com/news/rss.xml?ann-edition=us")
soup_ann = BeautifulSoup(res_ann.text, "xml")
print("--- ANN ITEM SAMPLE TAGS ---")
items_ann = soup_ann.find_all("item")
if items_ann:
    for elem in items_ann[0].children:
        if elem.name:
            print(f"Tag: {elem.name}, Attrs: {elem.attrs}")

res_cr = httpx.get("https://www.crunchyroll.com/news/feed")
soup_cr = BeautifulSoup(res_cr.text, "xml")
print("\n--- CRUNCHYROLL ITEM SAMPLE TAGS ---")
items_cr = soup_cr.find_all("item")
if items_cr:
    for elem in items_cr[0].children:
        if elem.name:
            print(f"Tag: {elem.name}, Attrs: {elem.attrs}")
