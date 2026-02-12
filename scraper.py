import feedparser
import json
import urllib.parse
import re
from datetime import datetime, timedelta
from time import mktime

# --- CONFIGURATION ---
ELIGIBLE_TERMS = [
    "12th pass", "higher secondary", "ssc", "constable", "data entry", 
    "clerk", "railway", "group d", "technician", "gd", "police", "mts", 
    "forest guard", "jail warder", "army", "navy", "ldc", "udc", 
    "gram panchayat", "anganwadi", "fireman", "driver", "lab assistant"
]

# BLOCK WORDS: Removes Exams, Results, and Old Years
BLOCKLIST = [
    "admit card", "result", "answer key", "cutoff", "syllabus", "b.tech", "mba", 
    "hall ticket", "merit list", "previous year", "2023", "2024"
]

# --- HELPER: GET LOCATION ---
def get_location(text):
    text = text.lower()
    
    # WEST BENGAL DISTRICTS
    wb_districts = [
        "alipurduar", "bankura", "birbhum", "cooch behar", "dakshin dinajpur", 
        "darjeeling", "hooghly", "howrah", "jalpaiguri", "jhargram", 
        "kalimpong", "kolkata", "malda", "murshidabad", "nadia", 
        "north 24 parganas", "south 24 parganas", "paschim bardhaman", "paschim medinipur", 
        "purba bardhaman", "purba medinipur", "purulia", 
        "uttar dinajpur"
    ]
    
    for dist in wb_districts:
        if dist in text:
            return "West Bengal", dist.title()
            
    if "west bengal" in text or "wb " in text or "wbp" in text or "wbpsc" in text:
        return "West Bengal", "All WB"
    if "bihar" in text: return "Bihar", "All"
    if "assam" in text: return "Assam", "All"
    if "odisha" in text: return "Odisha", "All"
        
    return "All India", "All"

# --- HELPER: PARSE & CHECK DATES ---
def is_fresh_job(published_struct):
    if not published_struct: return False
    
    # Convert RSS date to Python Date
    pub_date = datetime.fromtimestamp(mktime(published_struct))
    today = datetime.now()
    
    # Calculate difference
    diff = today - pub_date
    
    # STRICT RULE: If older than 30 days, ignore it
    if diff.days > 30:
        return False
    return True

def get_display_date(published_struct):
    if not published_struct: return "Recent"
    dt = datetime.fromtimestamp(mktime(published_struct))
    return dt.strftime("%d %b %Y")

def get_end_date(title):
    end_date = "Check Notice"
    match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', title)
    if match:
        end_date = match.group(1)
    return end_date

# --- SEARCH ---
def make_rss_url(query):
    base_url = "https://news.google.com/rss/search?q="
    return base_url + urllib.parse.quote(query) + "&hl=en-IN&gl=IN&ceid=IN:en"

def get_jobs(is_upcoming=False):
    print(f"Searching jobs (Upcoming: {is_upcoming})...")
    keywords = ' OR '.join(ELIGIBLE_TERMS)
    
    # Added 'when:30d' to Google Search to help, but Python filter is the real guard
    if is_upcoming:
        query = f'("calendar" OR "short notice" OR "upcoming") AND ({keywords}) AND (site:gov.in OR site:nic.in OR site:wbp.gov.in) when:30d'
    else:
        query = f'(recruitment OR vacancy OR apply) AND ({keywords}) AND (site:gov.in OR site:nic.in OR site:wbp.gov.in OR site:indianrailways.gov.in) when:30d'

    jobs = []
    try:
        feed = feedparser.parse(make_rss_url(query))
        for entry in feed.entries:
            title = entry.title.lower()
            
            # 1. Check Keywords
            if not any(b in title for b in BLOCKLIST):
                
                # 2. STRICT DATE CHECK (The Fix)
                if is_fresh_job(entry.published_parsed):
                    
                    state, district = get_location(title)
                    
                    jobs.append({
                        "title": entry.title,
                        "link": entry.link,
                        "date": get_display_date(entry.published_parsed),
                        "end_date": get_end_date(entry.title),
                        "source": entry.source.title if 'source' in entry else "Govt Site",
                        "state": state,
                        "district": district,
                        "type": "upcoming" if is_upcoming else "active"
                    })
    except Exception as e:
        print(f"Error: {e}")
    return jobs

if __name__ == "__main__":
    active = get_jobs(False)
    upcoming = get_jobs(True)
    
    # NO DUMMY DATA. If it's empty, show empty. 
    # This prevents confusion.

    data = {
        "active": active,
        "upcoming": upcoming,
        "last_updated": datetime.now().strftime("%d %b %Y, %I:%M %p")
    }
    
    with open("jobs.json", "w") as f:
        json.dump(data, f, indent=4)
