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
    "Gloucestershire Health and Care NHS Foundation Trust": "https://www.ghc.nhs.uk/", # Incorrect domain
    "University Hospitals Dorset NHS Foundation Trust": "https://www.uhd.nhs.uk/", # URL missing
    "North West Anglia NHS Foundation Trust": "https://www.nwangliaft.nhs.uk/", # Incorrect domain
    "Bolton NHS Foundation Trust": "https://www.boltonft.nhs.uk/", # HTTPS missing
    "Cumbria, Northumberland, Tyne and Wear NHS Foundation Trust": "https://www.cntw.nhs.uk/", # Incorrect domain
    "Greater Manchester Mental Health NHS Foundation Trust": "https://www.gmmh.nhs.uk/", # Incorrect domain
    "Lancashire and South Cumbria NHS Foundation Trust": "https://www.lscft.nhs.uk/", # Incorrect domain
    "Milton Keynes University Hospital NHS Foundation Trust": "https://www.mkuh.nhs.uk/", # Incorrect domain
    "North West Anglia NHS Foundation Trust": "https://www.nwangliaft.nhs.uk/", # Incorrect domain (DNS missing)
    "Wrightington, Wigan and Leigh NHS Foundation Trust": "https://www.wwl.nhs.uk/", # Incorrect domain
    "Black Country Healthcare NHS Foundation Trust": "https://www.blackcountryhealthcare.nhs.uk/", # New trust
}

MANUAL_EXCLUDE = [
    "Yeovil District Hospital NHS Foundation Trust", # Absorbed into "Somerset NHS Foundation Trust (formerly Somerset Partnership NHS Foundation Trust)""
]

def scrape_list_site(url):
    site = BeautifulSoup(requests.get(url).content, features="lxml")
    main = site.find(name="section", attrs={"id": "main-content"})

    hrefs = filter(lambda x: x is not None, [x.findChild(name="a") for x in main.find_all(name="li")])
    # This is a dirty scrape, including an additional element from the end of the page - this will trigger a warning.

    failed = {}

    with open(FILE_NAME, "w", encoding="utf-8", newline='') as f:
        writer = csv.DictWriter(f, ["Trust", "URL"])

        trust_hrefs = {tag.text: tag.get("href") for tag in hrefs}
        trust_hrefs.pop("Register of licensed healthcare providers") # remove end element

        for name, index_url in trust_hrefs.items():
            logging.debug(f"Fetching {name} from {index_url}")
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
    with open(FILE_NAME, "r", encoding="utf-8", newline='') as f:
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
            logging.info(f"Trust {k} has correct url {v}; consider removal from MANUAL_URLS")

    for exclusion in MANUAL_EXCLUDE:
        if exclusion in trusts:
            url = trusts.pop(exclusion)
            logging.warning(f"Popped {exclusion} w/ url {url}")
        else:
            logging.info(f"Trust {exclusion} in MANUAL_EXCLUDES does not exist, consider removal")
    
    with open(FILE_NAME, "w", encoding="utf-8", newline='') as f:
        writer = csv.DictWriter(f, ["Trust", "URL"])
        writer.writerows([{"Trust": k, "URL": v} for k, v in trusts.items()])
    logging.info("Trust URLs cleaned")

if __name__ == "__main__":
    scrape_list_site(LIST_URL)
    cleanup()