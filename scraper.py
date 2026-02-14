import feedparser
import json
import urllib.parse
import re
from datetime import datetime
from time import mktime

# --- 1. THE KILL LIST (BANNED SOURCES) ---
# We will instantly delete jobs from these sites.
BANNED_SOURCES = [
    "adda247", "career power", "times of india", "hindustan times", 
    "jagran", "josh", "shiksha", "sarkari", "result", "testbook", 
    "news18", "india.com", "careerindia", "fresherslive", "naukri"
]

# --- 2. OFFICIAL DOMAINS (WHITELIST) ---
# The link must contain one of these, OR the source must be trusted
OFFICIAL_DOMAINS = [
    ".gov.in", ".nic.in", "indianrailways.gov.in", "wbp.gov.in", 
    "wbpsc.gov.in", "ibps.in", "joinindianarmy.nic.in", "rectt.bsf.gov.in"
]

ELIGIBLE_TERMS = [
    "constable", "gd", "chsl", "mts", "cgl", "10+2", "12th pass", 
    "army", "navy", "air force", "group d", "technician", "alp", 
    "sepoy", "agniveer", "assistant", "clerk", "forest guard"
]

BLOCKLIST = ["admit card", "result", "answer key", "cutoff", "marks", "call letter"]

# --- HELPER: CHECK IS OFFICIAL ---
def is_clean_source(source_name, link):
    source_name = source_name.lower()
    link = link.lower()
    
    # 1. CHECK BANNED LIST (The "Kill Switch")
    for bad in BANNED_SOURCES:
        if bad in source_name:
            return False # DELETE IT
            
    # 2. CHECK DOMAIN (Double Security)
    # If the link actually contains .gov.in, keep it.
    for domain in OFFICIAL_DOMAINS:
        if domain in link:
            return True
            
    # 3. If it's not banned, and we are searching site:gov.in, 
    # we trust it UNLESS it's in the banned list.
    return True

def get_dates(title, published_struct):
    pub_date = datetime.fromtimestamp(mktime(published_struct)).strftime("%d %b")
    end_date = "Check Notice"
    match = re.search(r'last date\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2})', title.lower())
    if match:
        end_date = match.group(1)
    return pub_date, end_date

def get_jobs(is_upcoming=False):
    print(f"Searching Official Sites (Upcoming: {is_upcoming})...")
    
    keywords = ' OR '.join(ELIGIBLE_TERMS)
    
    # STRICT SEARCH QUERY
    sites = "site:gov.in OR site:nic.in OR site:ibps.in"
    
    if is_upcoming:
        query = f'("calendar" OR "schedule" OR "short notice") AND ({keywords}) AND ({sites}) when:30d'
    else:
        query = f'(recruitment OR notification OR vacancy) AND ({keywords}) AND ({sites}) when:7d'

    base_url = "https://news.google.com/rss/search?q="
    rss_url = base_url + urllib.parse.quote(query) + "&hl=en-IN&gl=IN&ceid=IN:en"

    jobs = []
    try:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries:
            title = entry.title.lower()
            link = entry.link.lower()
            source = entry.source.title if 'source' in entry else ""
            
            # FILTER 1: Remove Junk Keywords
            if not any(b in title for b in BLOCKLIST):
                
                # FILTER 2: THE KILL SWITCH
                if is_clean_source(source, link):
                    
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
    except Exception as e:
        print(f"Error: {e}")
    return jobs

if __name__ == "__main__":
    active = get_jobs(False)
    upcoming = get_jobs(True)
    
    data = {
        "active": active,
        "upcoming": upcoming,
        "last_updated": datetime.now().strftime("%d %b %Y, %I:%M %p")
    }
    
    with open("jobs.json", "w") as f:
        json.dump(data, f, indent=4)
