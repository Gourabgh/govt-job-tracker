import feedparser
import json
import urllib.parse
import re
from datetime import datetime
from time import mktime

# --- 1. THE STRICT WHITELIST ---
# We ONLY allow links that contain these specific official domain patterns.
# If a link does not match these, it is thrown in the trash.
OFFICIAL_DOMAINS = [
    ".gov.in",           # Catches ssc.gov.in, wbp.gov.in, etc.
    ".nic.in",           # Catches joinindianarmy.nic.in
    "indianrailways.gov.in",
    "ibps.in",           # Official Banking
    "upsc.gov.in",
    "drdo.gov.in",
    "isro.gov.in"
]

# --- 2. YOUR KEYWORDS ---
ELIGIBLE_TERMS = [
    "constable", "gd", "chsl", "mts", "cgl", "10+2", "12th pass", 
    "army", "navy", "air force", "group d", "technician", "alp", 
    "sepoy", "agniveer", "assistant", "clerk", "forest guard", 
    "bsf", "crpf", "cisf", "ssb", "itbp"
]

# --- HELPER: IS THIS LINK OFFICIAL? ---
def is_truly_official(link):
    # This is the "Nuclear Filter"
    # We check the actual URL. If it's not government, it's gone.
    for domain in OFFICIAL_DOMAINS:
        if domain in link:
            return True
    return False

# --- HELPER: GET DATES ---
def get_dates(title, published_struct):
    pub_date = datetime.fromtimestamp(mktime(published_struct)).strftime("%d %b")
    end_date = "Check PDF"
    match = re.search(r'last date\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2})', title.lower())
    if match:
        end_date = match.group(1)
    return pub_date, end_date

# --- SEARCH FUNCTION ---
def get_jobs(is_upcoming=False):
    print(f"Searching STRICT Official Sites (Upcoming: {is_upcoming})...")
    
    # We search specifically for site:gov.in
    keywords = ' OR '.join(ELIGIBLE_TERMS)
    sites = "site:gov.in OR site:nic.in OR site:ibps.in"
    
    if is_upcoming:
        query = f'("calendar" OR "schedule" OR "short notice") AND ({keywords}) AND ({sites}) when:30d'
    else:
        query = f'(recruitment OR notification OR vacancy) AND ({keywords}) AND ({sites}) when:15d'

    base_url = "https://news.google.com/rss/search?q="
    rss_url = base_url + urllib.parse.quote(query) + "&hl=en-IN&gl=IN&ceid=IN:en"

    jobs = []
    try:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries:
            title = entry.title.lower()
            link = entry.link.lower()
            
            # --- THE FILTER ---
            # We ignore the 'source name' (because Adda247 lies).
            # We look strictly at the LINK or the GUID.
            if is_truly_official(link) or is_truly_official(entry.id):
                
                state = "Central Govt"
                if "wbp" in title or "west bengal" in title or "wbpsc" in title:
                    state = "West Bengal"
                
                start, end = get_dates(entry.title, entry.published_parsed)

                jobs.append({
                    "title": entry.title,
                    "link": entry.link,
                    "date": start,
                    "end_date": end,
                    "source": entry.source.title, 
                    "state": state,
                    "type": "upcoming" if is_upcoming else "active"
                })
            else:
                # Debugging: Print what we blocked to prove it works
                # print(f"BLOCKED: {entry.source.title} - {link}")
                pass

    except Exception as e:
        print(f"Error: {e}")
    return jobs

if __name__ == "__main__":
    active = get_jobs(False)
    upcoming = get_jobs(True)
    
    # If the list is empty, it means NO official government site posted today.
    # We prefer an empty list over a fake list.
    
    data = {
        "active": active,
        "upcoming": upcoming,
        "last_updated": datetime.now().strftime("%d %b %Y, %I:%M %p")
    }
    
    with open("jobs.json", "w") as f:
        json.dump(data, f, indent=4)
