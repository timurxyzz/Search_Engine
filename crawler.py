from whoosh.index import create_in
import os 
from whoosh.fields import Schema, ID, TEXT
import requests
from bs4 import BeautifulSoup
from urllib.parse import urldefrag, urljoin

# Starting URL and scope boundary for the crawl
root = "https://www.uni-osnabrueck.de/fb1/geschichte/nghm"

agenda = [root]  # Stack/queue of URLs waiting to be crawled
visited = set()  # Tracks crawled URLs (including redirects) to prevent loops

os.makedirs("indexdir", exist_ok=True)
schema = Schema(url = ID(stored=True,unique=True),
                title = TEXT(stored=True,field_boost=2.0),
                content = TEXT(stored = True)
)
ix = create_in("indexdir",schema)
writer = ix.writer()

while agenda:
    url = agenda.pop()
    if url in visited:
        continue
    # Mark as visited before requesting so broken/failed URLs are not retried
    visited.add(url)

    # Fetch the page, skipping network/timeout errors without crashing the crawl
    try:
        r = requests.get(
            url,
            headers={"User-Agent": "AIWebPageCheck/1.0"},
            timeout=15,
        )
    except requests.exceptions.RequestException as e:
        print("Failed to retrieve Url")
        print(e,url)
        continue
    # Skip non-200 responses
    print("Get", r.status_code, r.url)
    if r.status_code != 200:
        continue
    # Also record the final URL in case of redirects
    visited.add(r.url)

    # Process only HTML responses (skip PDFs, images, etc.)
    t = r.headers.get("Content-Type", "").lower()
    if "text/html" not in t:
        continue

    # Parse HTML and extract the page title (fall back to empty string if missing)
    soup = BeautifulSoup(r.content, "html.parser")
    if soup.title:
        title = soup.title.get_text(strip=True)
    else:
        title = ""

    # Remove script and style elements before extracting visible text
    for element in soup.find_all(["script", "style"]):
        element.decompose()

    text = soup.get_text(separator=" ", strip=True)
    writer.add_document(url=r.url, title=title,content=text) # each pages is indexed once

    # Find all links and enqueue unvisited ones that stay under the root prefix
    for link in soup.select("a[href]"):
        # Resolve relative links to absolute URLs and strip #fragment identifiers
        target, _ = urldefrag(urljoin(r.url, link["href"]))
        if target == root or target.startswith(root + "/"):
            print("Found ", target)
            if target not in visited and target not in agenda:
                agenda.append(target)

writer.commit() # saving permanently to indexdir

