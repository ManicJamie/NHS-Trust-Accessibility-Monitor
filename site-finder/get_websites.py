"""
This script takes a list of English NHS trusts from the NHS website & returns a list of URLs to the trusts' own websites.

Note that some may be missing due to incomplete data on the NHS website; check output against the warning logs to find omitted trusts.
To alleviate this for the purpose of this project, some manual trust URLs have been included - ensure these are correct & that the output is complete for your own uses.
"""

import requests
from bs4 import BeautifulSoup
import re, csv, logging

logging.getLogger().setLevel(logging.INFO)

LIST_URL = "https://www.england.nhs.uk/publication/nhs-provider-directory/"

FILE_NAME = "urls.csv"

MANUAL_URLS = {
    "Gloucestershire Health and Care NHS Foundation Trust": "https://www.ghc.nhs.uk/", # Incorrect URL
    "University Hospitals Dorset NHS Foundation Trust": "https://www.uhd.nhs.uk/" # URL missing
}

MANUAL_EXCLUDE = [
    
]

def scrape_list_site(url):
    site = BeautifulSoup(requests.get(url).content, features="lxml")
    main = site.find(name="section", attrs={"id": "main-content"})

    hrefs = filter(lambda x: x is not None, [x.findChild(name="a") for x in main.find_all(name="li")])
    # This is a dirty scrape, including an additional element from the end of the page - this will trigger a warning.

    failed = {}

    with open(FILE_NAME, "w", encoding="utf-8") as f:
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

def cleanup():
    logging.info("Cleaning up trusts URLs")
    with open(FILE_NAME, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, ["Trust", "URL"])
        trusts = {row["Trust"]:row["URL"] for row in reader}
    
    for k, v in MANUAL_URLS.items():
        if k not in trusts:
            logging.warning(f"{k} not found, adding URL {v}")
            trusts.update({k:v})
        elif trusts.get(k) != v:
            logging.warning(f"Wrong URL for {k} ({trusts.get(k)}), replacing with {v}")
            trusts.update({k:v})
        else:
            logging.info(f"Trust {k} has correct url {v}; consider removing from MANUAL_URLS")
    
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, ["Trust", "URL"])
        writer.writerows([{"Trust": k, "URL": v} for k, v in trusts.items()])
    logging.info("Trust URLs cleaned")

if __name__ == "__main__":
    scrape_list_site(LIST_URL)
    cleanup()