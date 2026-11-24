import requests
from bs4 import BeautifulSoup
from urllib.parse import urldefrag, urljoin

# where to start crawling
root = "https://www.uni-osnabrueck.de/fb8/en/ikw"

agenda = [root] # what to crawl next
visited = set()

while agenda:
    url = agenda.pop()
    if url in visited:
        continue
    visited.add(url)
    # Get the page
    try:
        r = requests.get(
            url,
            headers={"User-Agent": "AIWebPageCheck/1.0"},
            timeout=15,
        )

    except requests.exceptions.RequestException:
        print("Failed to retrieve Url")
        continue
    # Check the status code and skip if not 200 OK
    print("Get", r.status_code, r.url)
    if r.status_code != 200:
        continue
    visited.add(r.url)
    t = r.headers.get("Content-Type","").lower()
    
    if "text/html" not in t:
        continue
    # Parse the page and find all links
    soup = BeautifulSoup(r.content, "html.parser")
    if  soup.title:
        title = soup.title.get_text(strip=True)
    else:
        title = ""     
    
    for  element in soup.find_all(["script","style"]):
        element.decompose()
    
    text = soup.get_text(separator=" ", strip=True) 
    
    for link in soup.select("a[href]"):

        # Get the absolute URL of the link, and remove any fragment (the part after #)
        target, _ = urldefrag(urljoin(r.url, link["href"]))
        if (target == root or target.startswith(root + "/")):
               
            print("Found ", target)
            if target not in visited and target not in agenda:
                agenda.append(target)

