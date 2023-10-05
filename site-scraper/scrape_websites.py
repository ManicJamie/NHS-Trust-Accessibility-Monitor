from argparse import ArgumentParser
import csv, json, logging
from bs4 import BeautifulSoup, SoupStrainer
from urllib.parse import urlparse, urlunparse
import asyncio, aiohttp, aiofiles
from yarl import URL

PARSER = "lxml"
TIMEOUT = 60
BACKOFF = 10

logging.getLogger().setLevel(logging.DEBUG)

async def recursive_scrape(url:str, explored:dict = {}):
    parsedUrl = urlparse(url)
    if parsedUrl.path in explored: return
    else: explored[parsedUrl.path] = None # Placeholder to prevent extra fetches

    while True:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(URL(url, encoded=True)) as response:
                    if "text/html" not in response.content_type:
                        logging.debug(f"Fetched {url} but wrong content-type {response.content_type} - skipping")
                        return
                    content = await response.content.read()
                    break
        except aiohttp.ClientConnectorError as e:
            logging.error(f"Client failed to connect to {url}, retrying after backoff: {e}")
            asyncio.sleep(BACKOFF)
        except asyncio.TimeoutError as e:
            logging.error(f"Client failed to connect to {url}, retrying after backoff: {e}")
            asyncio.sleep(BACKOFF)
                
    soup =  BeautifulSoup(content, parse_only=SoupStrainer("a"), features=PARSER)
    logging.info(f"Fetched {url}")
    if explored[parsedUrl.path] is not None: logging.error("collision!")
    explored[parsedUrl.path] = str(content)

    tasks = []
    for link in soup.find_all("a", attrs={"href": True}):
        href = urlparse(str(link["href"]))
        if href.netloc != parsedUrl.netloc: continue
        elif href.path in explored: continue
        else:
            tasks.append(asyncio.ensure_future(recursive_scrape(urlunparse(href), explored)))
    
    while True:
        try:
            await asyncio.gather(*tasks)
        except asyncio.TimeoutError as e:
            logging.error(f"Timed out! Retrying... {e}")
        else:
            return

async def scrape(url: str, explored: dict):
    await recursive_scrape(url, explored)
    """
    items = set(explored.items())
    for k, v in items:
        if v is None: explored.pop(k)
    """
    
    with open("scraped.json", "w") as out:
        json.dump(explored, out)

if __name__ == "__main__":
    parser = ArgumentParser(prog="Site Scraper", description="Recursively scrapes websites given a csv of format [Name : Url].")
    #parser.add_argument("input")
    #parser.add_argument("-o", "--output", default="./scraped.json")

    urls = {}
    with open("urls.csv") as i:
        for row in csv.reader(i):
            urls[row[0]] = row[1]
    
    explored = {}
    asyncio.run(scrape("http://www.awp.nhs.uk/", explored))