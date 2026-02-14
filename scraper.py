import feedparser
import json
import urllib.parse
import re
from datetime import datetime
from time import mktime

# --- 1. STRICT OFFICIAL DOMAINS ONLY ---
# The link MUST contain one of these to be accepted.
ALLOWED_DOMAINS = [
    ".gov.in", ".nic.in", "indianrailways.gov.in", "wbp.gov.in", 
    "wbpsc.gov.in", "ibps.in", "joinindianarmy.nic.in", "rectt.bsf.gov.in"
]

# --- 2. YOUR KEYWORDS ---
ELIGIBLE_TERMS = [
    "constable", "gd", "chsl", "mts", "cgl", "10+2", "12th pass", 
    "army", "navy", "air force", "group d", "technician", "alp", 
    "sepoy", "agniveer", "assistant", "clerk", "forest guard"
]

# --- 3. BLOCKLIST (Remove Results/Admit Cards) ---
BLOCKLIST = ["admit card", "result", "answer key", "cutoff", "marks", "call letter"]

# --- HELPER: CHECK IF LINK IS OFFICIAL ---
def is_official_link(link):
    # This is the "Security Guard"
    for domain in ALLOWED_DOMAINS:
        if domain in link:
            return True
    return False

# --- HELPER: GET DATES ---
def get_dates(title, published_struct):
    pub_date = datetime.fromtimestamp(mktime(published_struct)).strftime("%d %b")
    end_date = "Check PDF"
    # Look for "Last Date: 25/03" patterns
    match = re.search(r'last date\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2})', title.lower())
    if match:
        end_date = match.group(1)
    return pub_date, end_date

# --- SEARCH FUNCTION ---
def get_jobs(is_upcoming=False):
    print(f"Searching Official Sites (Upcoming: {is_upcoming})...")
    
    # We search broadly on Google, but FILTER locally in Python
    keywords = ' OR '.join(ELIGIBLE_TERMS)
    
    # The Query: Strict site limits
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
            
            # 1. REMOVE JUNK TITLES
            if not any(b in title for b in BLOCKLIST):
                
                # 2. *** CRITICAL STEP: CHECK THE LINK DOMAIN ***
                # Only save if the link is actually .gov.in or .nic.in
                # Note: Google News redirects, so we check the 'source' text too
                source_name = entry.source.title.lower() if 'source' in entry else ""
                
                if is_official_link(link) or is_official_link(source_name):
                    
                    state = "Central Govt"
                    if "wbp" in title or "west bengal" in title or "wbpsc" in title:
                        state = "West Bengal"
                    
                    start, end = get_dates(entry.title, entry.published_parsed)

                    jobs.append({
                        "title": entry.title,
                        "link": entry.link,
                        "date": start,
                        "end_date": end,
                        "source": entry.source.title, # e.g. "ssc.gov.in"
                        "state": state,
                        "type": "upcoming" if is_upcoming else "active"
                    })
    except Exception as e:
        print(f"Error: {e}")
    return jobs

if __name__ == "__main__":
    active = get_jobs(False)
    upcoming = get_jobs(True)
    
    # TIMESTAMP
    # This format is easy to read: "14 Feb 2026, 06:00 AM"
    timestamp = datetime.now().strftime("%d %b %Y, %I:%M %p")

    data = {
        "active": active,
        "upcoming": upcoming,
        "last_updated": timestamp
    }
    
    with open("jobs.json", "w") as f:
        json.dump(data, f, indent=4)
