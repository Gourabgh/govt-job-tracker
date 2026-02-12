import feedparser
import json
import urllib.parse
from datetime import datetime

# --- CONFIGURATION ---
ELIGIBLE_TERMS = [
    "12th pass", "higher secondary", "ssc", "constable", "data entry", 
    "clerk", "railway", "group d", "technician", "gd", "police", "mts"
]

BLOCKLIST = ["admit card", "result", "answer key", "cutoff", "syllabus", "b.tech", "mba"]

# --- LOCATION DETECTOR ---
def get_location(text):
    text = text.lower()
    
    # 1. Check West Bengal Districts
    wb_districts = ["nadia", "kolkata", "howrah", "hooghly", "north 24 parganas", "south 24 parganas", "murshidabad", "malda", "siliguri"]
    for dist in wb_districts:
        if dist in text:
            return "West Bengal", dist.title() # Return State + District
            
    # 2. Check States
    if "west bengal" in text or "wb " in text or "wbp" in text:
        return "West Bengal", "All WB"
    if "delhi" in text or "ncr" in text:
        return "Delhi", "All"
    if "maharashtra" in text or "mumbai" in text or "pune" in text:
        return "Maharashtra", "All"
    if "up " in text or "uttar pradesh" in text:
        return "Uttar Pradesh", "All"
    if "bihar" in text:
        return "Bihar", "All"
        
    return "All India", "All" # Default if no location found

# --- SEARCH FUNCTION ---
def make_rss_url(query):
    base_url = "https://news.google.com/rss/search?q="
    return base_url + urllib.parse.quote(query) + "&hl=en-IN&gl=IN&ceid=IN:en"

def get_jobs(is_upcoming=False):
    print(f"Searching jobs (Upcoming: {is_upcoming})...")
    
    # Search Query
    keywords = ' OR '.join(ELIGIBLE_TERMS)
    if is_upcoming:
        query = f'("calendar" OR "short notice" OR "upcoming") AND ({keywords}) AND (site:gov.in OR site:nic.in OR site:wbp.gov.in) when:7d'
    else:
        query = f'recruitment AND ({keywords}) AND (site:gov.in OR site:nic.in OR site:wbp.gov.in) when:2d'

    jobs = []
    try:
        feed = feedparser.parse(make_rss_url(query))
        for entry in feed.entries:
            title = entry.title.lower()
            if not any(b in title for b in BLOCKLIST):
                
                # Detect Location
                state, district = get_location(title)
                
                jobs.append({
                    "title": entry.title,
                    "link": entry.link,
                    "date": entry.published,
                    "source": entry.source.title if 'source' in entry else "Govt Site",
                    "state": state,
                    "district": district
                })
    except Exception as e:
        print(f"Error: {e}")
    return jobs

if __name__ == "__main__":
    data = {
        "active": get_jobs(is_upcoming=False),
        "upcoming": get_jobs(is_upcoming=True),
        "last_updated": datetime.now().strftime("%d %b %Y, %I:%M %p")
    }
    
    with open("jobs.json", "w") as f:
        json.dump(data, f, indent=4)
    print("✅ Jobs updated with Location tags.")
