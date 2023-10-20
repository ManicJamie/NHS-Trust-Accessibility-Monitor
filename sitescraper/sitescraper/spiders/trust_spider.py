import logging
from typing import Iterable
from urllib.parse import urlparse
import csv

from scrapy.spiders import CrawlSpider
from scrapy.http import Request, Response
from scrapy.linkextractors import LinkExtractor
from scrapy.link import Link

SITE_LIMIT = 10

DEBUG = False

logging.getLogger().addHandler(logging.FileHandler("crawl.log", mode="w"))

class TrustSpider(CrawlSpider):
    name="trusts"

    def start_requests(self) -> Iterable[Request]:
        if not DEBUG:
            with open("urls.csv") as f:
                self.urls = {urlparse(x['domain']).netloc: SITE_LIMIT for x in csv.DictReader(f, fieldnames=["name", "domain"])}

                for url in [url for url in self.urls.keys()]:
                    yield Request(url=f"http://{url}", callback=self.parse_start_url)
        else:
            logging.warning("Debug enabled!")
            url = urlparse("http://www.aintreehospitals.nhs.uk/").netloc
            self.urls = {url: SITE_LIMIT}
            
            yield Request(url=f"http://{url}", callback=self.parse_start_url)

    def parse_start_url(self, response, **kwargs):
        url = urlparse(response.url)
        logging.info(f"Parsing initial domain {response.request.url}")
        # Check for redirects (only on root domain!)
        if url.netloc not in self.urls.keys():
            if response.status not in range(300,320):
                logging.error(f"Redirect found but not real!")
            logging.info(f"Redirect found! Adding redirect from {urlparse(response.request.url).netloc} to {url.netloc}")
            self.urls[url.netloc] = SITE_LIMIT

        return self.extract_links(response)
    
    def parse(self, response: Response):
        logging.debug(f"Parsing {response.request.url}")

        return self.extract_links(response)

    def extract_links(self, response: Response):
        url = urlparse(response.request.url)
        links: list[Link] = LinkExtractor(allow_domains=self.urls.keys()).extract_links(response)

        if url.netloc not in self.urls and url.netloc.split(".", maxsplit=1)[1] not in self.urls:
            logging.warn(f"{url.netloc} not in urls!")
            yield {
                "domain": str(url.netloc),
                "path": str(url.path),
                "error": "Not in urls!"
            } 

        yield {
            "domain": str(url.netloc),
            "path": str(url.path),
            "body": str(response.body)
        }

        if self.urls[url.netloc] <= 0:
            return
        else:

            for l in links:
                if self.urls[url.netloc] > 0:
                    yield Request(url=l.url, callback=self.parse)
                    self.urls[url.netloc] -= 1
                else:
                    logging.info(f"Reached domain limit for {url.netloc}, halting crawl")
                    break
    