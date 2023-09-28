import requests
from bs4 import BeautifulSoup
import re, csv, logging

logging.getLogger().setLevel(logging.INFO)

LIST_URL = "https://www.england.nhs.uk/publication/nhs-provider-directory/"

site = BeautifulSoup(requests.get(LIST_URL).content, features="lxml")
main = site.find(name="section", attrs={"id": "main-content"})

hrefs = filter(lambda x: x is not None, [x.findChild(name="a") for x in main.find_all(name="li")])

failed = {}

with open("urls.csv", "w") as f:
    writer = csv.DictWriter(f, ["Trust", "URL"])

    for name, index_url in {tag.text: tag.get("href") for tag in hrefs}.items():
        logging.info(f"Fetching {name} from {index_url}")
        content = BeautifulSoup(requests.get(index_url).content, features="lxml")

        websiteLabel = content.find(re.compile("^h[1-6]$"), string="Website")
        if websiteLabel is None:
            logging.warning(f"Failed to find website at {index_url}")
            failed[name] = index_url
            continue
        websiteURLLabel = websiteLabel.find_next_sibling("p").find("a")
        writer.writerow({"Trust": name, "URL": websiteURLLabel.get("href")})

if len(failed) > 0:
    logging.warning(f"Failed to find websites for the following list items: {failed}")