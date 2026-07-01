import requests
from bs4 import BeautifulSoup

url="https://www.wta.org/go-hiking/trip-reports/trip_report-2026-06-30.210341804556"
headers ={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}
resp=requests.get(url, headers=headers)
print(resp.status_code) 

soup = BeautifulSoup(resp.text, "html.parser")

author = soup.find("span", itemprop="author").find("span", class_="wta-icon-headline__text").get_text().strip()
print(author)

report_id = url.split(".")[-1]
print(report_id)

h1 = soup.find("h1", class_="documentFirstHeading")

mountname = h1.find("a").get_text()
print(mountname)

date = h1.find("a").next_sibling.strip()
print(date)


region = soup.find(id="hike-region").get_text().strip()
print(region)

body = soup.find(id="tripreport-body-text").get_text().strip()
print(body)

conditions = {}
block = soup.find(id="trip-conditions")
for cond in block.find_all("div", class_="trip-condition"):
    key = cond.find("h4").get_text().strip()
    value = cond.find("span").get_text().strip()
    conditions[key] = value

print(conditions)
