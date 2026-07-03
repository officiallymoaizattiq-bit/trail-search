import requests
from bs4 import BeautifulSoup
import time
import json
import re

headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}


def get_report_urls(tripdate_min, tripdate_max, b_start):
    listing_url = (
        f"https://www.wta.org/@@search_tripreport_listing"
        f"?b_size=50&b_start:int={b_start}"
        f"&tripdate_min={tripdate_min}&tripdate_max={tripdate_max}"
    )
    resp = requests.get(listing_url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")
    urls = set()
    for a in soup.find_all("a", href=True):
        if "trip_report-" in a["href"]:
            urls.add(a["href"])
    return list(urls)


def parse_report(url):
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")

    report_id = re.search(r"(\d+)$", url).group(1)

    author = soup.find("span", itemprop="author").find("span", class_="wta-icon-headline__text").get_text().strip()

    h1 = soup.find("h1", class_="documentFirstHeading")
    trail_name = h1.find("a").get_text().strip()
    date = h1.find("a").next_sibling.strip()

    region = soup.find(id="hike-region").get_text().strip()
    body = soup.find(id="tripreport-body-text").get_text().strip()

    conditions = {}
    block = soup.find(id="trip-conditions")
    if block:
        for cond in block.find_all("div", class_="trip-condition"):
            key = cond.find("h4").get_text().strip()
            value = cond.find("span").get_text().strip()
            conditions[key] = value

    return {
        "id": report_id,
        "url": url,
        "trail_name": trail_name,
        "date": date,
        "region": region,
        "author": author,
        "body": body,
        "conditions": conditions,
    }


# four seasonal windows across a year -> vocabulary diversity for honest BM25
seasons = [
    ("2026-01-01", "2026-02-28"),   # winter: snow, ice, snowshoe, postholing
    ("2026-04-01", "2026-05-15"),   # spring: mud, melt, high water, blowdown
    ("2025-07-15", "2025-08-31"),   # summer: bugs, dusty, wildflowers, water sources
    ("2025-09-15", "2025-10-31"),   # fall: foliage, larches, early snow
]

all_urls = []
for tmin, tmax in seasons:
    for b_start in range(0, 100, 50):     # 2 pages (100 reports) per season
        print(f"fetching {tmin}..{tmax} b_start={b_start}")
        all_urls.extend(get_report_urls(tmin, tmax, b_start))
        time.sleep(1)

all_urls = list(set(all_urls))
print(f"collected {len(all_urls)} unique urls")

reports = []
for i, url in enumerate(all_urls):
    print(f"parsing {i+1}/{len(all_urls)}: {url}")
    try:
        reports.append(parse_report(url))
    except Exception as e:
        print(f"  skipped (error: {e})")
    time.sleep(1)

with open("data/reports.json", "w") as f:
    json.dump(reports, f)

print(f"saved {len(reports)} reports to data/reports.json")