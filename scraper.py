import feedparser
import json
import urllib.parse
import re
from datetime import datetime

# --- CONFIGURATION ---
ELIGIBLE_TERMS = [
    "12th pass", "higher secondary", "ssc", "constable", "data entry", 
    "clerk", "railway", "group d", "technician", "gd", "police", "mts", 
    "forest guard", "jail warder", "army", "navy", "ldc", "udc", "gram panchayat", "anganwadi"
]

BLOCKLIST = ["admit card", "result", "answer key", "cutoff", "syllabus", "b.tech", "mba", "hall ticket"]

# --- HELPER: GET LOCATION ---
def get_location(text):
    text = text.lower()
    
    # ALL 23 WEST BENGAL DISTRICTS
    wb_districts = [
        "alipurduar", "bankura", "birbhum", "cooch behar", "dakshin dinajpur", 
        "darjeeling", "hooghly", "howrah", "jalpaiguri", "jhargram", 
        "kalimpong", "kolkata", "malda", "murshidabad", "nadia", 
        "north 24 parganas", "paschim bardhaman", "paschim medinipur", 
        "purba bardhaman", "purba medinipur", "purulia", "south 24 parganas", 
        "uttar dinajpur"
    ]
    
    for dist in wb_districts:
        if dist in text:
            return "West Bengal", dist.title()
            
    # State Detection
    if "west bengal" in text or "wb " in text or "wbp" in text or "wbpsc" in text:
        return "West Bengal", "All WB"
    if "bihar" in text: return "Bihar", "All"
    if "assam" in text: return "Assam", "All"
    if "odisha" in text: return "Odisha", "All"
        
    return "All India", "All"

# --- HELPER: GET DATES ---
def get_dates(title, published_date):
    end_date = "Check Notification"
    # Look for dates like 25/03/2026
    match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', title)
    if match:
        end_date = match.group(1)
    return published_date, end_date

# --- SEARCH ---
def make_rss_url(query):
    base_url = "https://news.google.com/rss/search?q="
    return base_url + urllib.parse.quote(query) + "&hl=en-IN&gl=IN&ceid=IN:en"

def get_jobs(is_upcoming=False):
    print(f"Searching jobs (Upcoming: {is_upcoming})...")
    keywords = ' OR '.join(ELIGIBLE_TERMS)
    
    # WIDEN SEARCH: We search 'recruitment' OR 'vacancy' to catch everything
    query = f'(recruitment OR vacancy) AND ({keywords}) AND (site:gov.in OR site:nic.in OR site:wbp.gov.in OR site:indianrailways.gov.in) when:30d'
    
    if is_upcoming:
        query = f'("calendar" OR "short notice") AND ({keywords}) AND (site:gov.in OR site:nic.in) when:30d'

    jobs = []
    try:
        feed = feedparser.parse(make_rss_url(query))
        for entry in feed.entries:
            title = entry.title.lower()
            if not any(b in title for b in BLOCKLIST):
                
                state, district = get_location(title)
                start, end = get_dates(entry.title, entry.published)
                
                jobs.append({
                    "title": entry.title,
                    "link": entry.link,
                    "date": start,
                    "end_date": end,
                    "source": entry.source.title if 'source' in entry else "Govt Site",
                    "state": state,
                    "district": district
                })
    except Exception as e:
        print(f"Error: {e}")
    return jobs

if __name__ == "__main__":
    active = get_jobs(False)
    upcoming = get_jobs(True)
    
    # Dummy data for testing if empty
    if not active:
        active.append({
            "title": "WB Police Constable Recruitment 2026 - Nadia District",
            "link": "#",
            "date": "12 Feb 2026",
            "end_date": "15 Mar 2026",
            "source": "WBP Official",
            "state": "West Bengal",
            "district": "Nadia"
        })

    data = {
        "active": active,
        "upcoming": upcoming,
        "last_updated": datetime.now().strftime("%d %b %Y, %I:%M %p")
    }
    
    with open("jobs.json", "w") as f:
        json.dump(data, f, indent=4)
