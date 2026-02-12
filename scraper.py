import feedparser
import json
import urllib.parse
import re
from datetime import datetime

# --- CONFIGURATION ---
ELIGIBLE_TERMS = [
    "12th pass", "higher secondary", "ssc", "constable", "data entry", 
    "clerk", "railway", "group d", "technician", "gd", "police", "mts", 
    "forest guard", "jail warder", "army", "navy", "ldc", "udc"
]

BLOCKLIST = ["admit card", "result", "answer key", "cutoff", "syllabus", "b.tech", "mba", "hall ticket"]

# --- HELPER: GET LOCATION ---
def get_location(text):
    text = text.lower()
    
    # West Bengal Districts
    wb_districts = ["nadia", "kolkata", "howrah", "hooghly", "north 24 parganas", "south 24 parganas", "murshidabad", "malda", "siliguri", "bankura", "birbhum", "purulia"]
    for dist in wb_districts:
        if dist in text:
            return "West Bengal", dist.title()
            
    # States
    if "west bengal" in text or "wb " in text or "wbp" in text or "wbpsc" in text:
        return "West Bengal", "All WB"
    if "delhi" in text or "dsssb" in text:
        return "Delhi", "All"
    if "maharashtra" in text or "mpsc" in text:
        return "Maharashtra", "All"
    if "bihar" in text or "bssc" in text:
        return "Bihar", "All"
    if "up " in text or "uttar pradesh" in text:
        return "Uttar Pradesh", "All"
    if "assam" in text:
        return "Assam", "All"
        
    return "All India", "All"

# --- HELPER: TRY TO FIND DATES ---
def get_dates(title, published_date):
    # This tries to find a date pattern like "Last Date: 25 March" in the title
    # If not found, it defaults to "See Notification"
    end_date = "Check Notification"
    
    # Regex to look for dates in text (e.g., 25/03/2026 or 25th March)
    match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', title)
    if match:
        end_date = match.group(1)
    
    return published_date, end_date

# --- SEARCH FUNCTION ---
def make_rss_url(query):
    base_url = "https://news.google.com/rss/search?q="
    return base_url + urllib.parse.quote(query) + "&hl=en-IN&gl=IN&ceid=IN:en"

def get_jobs(is_upcoming=False):
    print(f"Searching jobs (Upcoming: {is_upcoming})...")
    
    keywords = ' OR '.join(ELIGIBLE_TERMS)
    # 30 day lookback to ensure we find jobs
    query = f'recruitment AND ({keywords}) AND (site:gov.in OR site:nic.in OR site:wbp.gov.in OR site:indianrailways.gov.in) when:30d'
    if is_upcoming:
        query = f'("calendar" OR "short notice") AND ({keywords}) AND (site:gov.in OR site:nic.in) when:30d'

    jobs = []
    try:
        feed = feedparser.parse(make_rss_url(query))
        for entry in feed.entries:
            title = entry.title.lower()
            if not any(b in title for b in BLOCKLIST):
                
                state, district = get_location(title)
                start_date, end_date = get_dates(entry.title, entry.published)
                
                jobs.append({
                    "title": entry.title,
                    "link": entry.link,
                    "date": start_date,         # Published Date
                    "end_date": end_date,       # Extracted or 'Check Notification'
                    "source": entry.source.title if 'source' in entry else "Govt Site",
                    "state": state,             # Fixed: Always has a value
                    "district": district        # Fixed: Always has a value
                })
    except Exception as e:
        print(f"Error: {e}")
    return jobs

if __name__ == "__main__":
    active_jobs = get_jobs(is_upcoming=False)
    upcoming_jobs = get_jobs(is_upcoming=True)

    # ADD DUMMY DATA FOR TESTING if list is empty
    if not active_jobs:
        active_jobs.append({
            "title": "SSC CHSL Recruitment 2026 - Data Entry Operator (Sample)",
            "link": "https://ssc.nic.in",
            "date": "12 Feb 2026",
            "end_date": "15 Mar 2026",
            "source": "SSC Official",
            "state": "All India",
            "district": "All"
        })

    data = {
        "active": active_jobs,
        "upcoming": upcoming_jobs,
        "last_updated": datetime.now().strftime("%d %b %Y, %I:%M %p")
    }
    
    with open("jobs.json", "w") as f:
        json.dump(data, f, indent=4)
    print("✅ Jobs updated with Dates and Location fix.")
