import feedparser
import json
import urllib.parse
import re
from datetime import datetime
from time import mktime

# --- 1. OFFICIAL DOMAINS ONLY ---
# We ONLY check these specific sites. No news sites.
OFFICIAL_SITES = [
    "site:ssc.gov.in", 
    "site:joinindianarmy.nic.in", 
    "site:rectt.bsf.gov.in",
    "site:indianrailways.gov.in",
    "site:wbp.gov.in",
    "site:wbpsc.gov.in",
    "site:ibps.in"
]

# --- 2. YOUR KEYWORDS (12th Pass / Defense) ---
ELIGIBLE_TERMS = [
    "constable", "gd", "chsl", "mts", "cgl", "10+2", "12th pass", 
    "army", "navy", "air force", "group d", "technician", "alp", 
    "sepoy", "agniveer", "assistant", "clerk"
]

# --- 3. BLOCKLIST (Remove Junk) ---
BLOCKLIST = ["admit card", "result", "answer key", "cutoff", "marks", "call letter"]

# --- HELPER: GET DATES ---
def get_dates(title, published_struct):
    pub_date = datetime.fromtimestamp(mktime(published_struct)).strftime("%d %b")
    end_date = "Check Notice"
    # Try to regex the last date
    match = re.search(r'last date\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2})', title.lower())
    if match:
        end_date = match.group(1)
    return pub_date, end_date

# --- SEARCH FUNCTION ---
def get_jobs(is_upcoming=False):
    print(f"Searching Official Sites (Upcoming: {is_upcoming})...")
    
    sites_query = ' OR '.join(OFFICIAL_SITES)
    keywords = ' OR '.join(ELIGIBLE_TERMS)
    
    if is_upcoming:
        # STRATEGY: Look for "Calendar", "Schedule" to analyze previous/future timing
        query = f'("calendar" OR "schedule" OR "tentative" OR "upcoming" OR "short notice") AND ({keywords}) AND ({sites_query}) when:30d'
    else:
        # STRATEGY: Look for active recruitment notices
        query = f'(recruitment OR notification OR vacancy OR apply) AND ({keywords}) AND ({sites_query}) when:7d'

    # Encode URL
    base_url = "https://news.google.com/rss/search?q="
    rss_url = base_url + urllib.parse.quote(query) + "&hl=en-IN&gl=IN&ceid=IN:en"

    jobs = []
    try:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries:
            title = entry.title.lower()
            
            if not any(b in title for b in BLOCKLIST):
                
                # Simple location logic
                state = "Central Govt"
                if "wbp" in title or "west bengal" in title:
                    state = "West Bengal"
                
                start, end = get_dates(entry.title, entry.published_parsed)

                jobs.append({
                    "title": entry.title,
                    "link": entry.link,
                    "date": start,
                    "end_date": end,
                    "source": entry.source.title, # Will show 'ssc.gov.in' etc.
                    "state": state,
                    "type": "upcoming" if is_upcoming else "active"
                })
    except Exception as e:
        print(f"Error: {e}")
    return jobs

if __name__ == "__main__":
    active = get_jobs(False)
    upcoming = get_jobs(True)
    
    # DUMMY DATA FOR TESTING (Remove later if you want)
    if not active:
        active.append({
            "title": "SSC CHSL Examination 2026 Notification",
            "link": "https://ssc.gov.in",
            "date": "Today",
            "end_date": "Check Notice",
            "source": "ssc.gov.in",
            "state": "Central Govt",
            "type": "active"
        })
    
    data = {
        "active": active,
        "upcoming": upcoming,
        "last_updated": datetime.now().strftime("%d %b %Y, 06:00 AM")
    }
    
    with open("jobs.json", "w") as f:
        json.dump(data, f, indent=4)
