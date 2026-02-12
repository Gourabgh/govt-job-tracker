import feedparser
import json
import urllib.parse
from datetime import datetime

# --- CONFIGURATION ---
ELIGIBLE_TERMS = [
    "12th pass", "higher secondary", "ssc chsl", "ssc mts", "ssc gd", 
    "constable", "data entry", "clerk", "railway", "group d", "alp", "technician"
]

# 1. Blocklist (Clean up junk)
BLOCKLIST = ["admit card", "result", "answer key", "cutoff", "syllabus", "graduate", "b.tech", "mba"]

# 2. Helper to make Google News URLs
def make_rss_url(query):
    base_url = "https://news.google.com/rss/search?q="
    return base_url + urllib.parse.quote(query) + "&hl=en-IN&gl=IN&ceid=IN:en"

# --- SEARCH 1: ACTIVE JOBS (Apply Now) ---
def get_active_jobs():
    print("🔍 Searching for ACTIVE jobs...")
    # Look for "Recruitment" or "Vacancy" on Govt sites
    query = 'recruitment AND ({0}) AND (site:gov.in OR site:nic.in OR site:indianrailways.gov.in OR site:wbp.gov.in) when:2d'.format(' OR '.join(ELIGIBLE_TERMS))
    
    return fetch_feed(make_rss_url(query), is_upcoming=False)

# --- SEARCH 2: UPCOMING JOBS (Coming Soon) ---
def get_upcoming_jobs():
    print("📅 Searching for UPCOMING notifications...")
    # Look for "Calendar", "Short Notice", "Schedule" on Govt sites
    # This finds official PDFs that say "Exam coming in 2 months"
    query = '("calendar" OR "schedule" OR "short notice" OR "upcoming") AND ({0}) AND (site:gov.in OR site:nic.in OR site:ssc.nic.in OR site:rrbcdg.gov.in) when:7d'.format(' OR '.join(ELIGIBLE_TERMS))
    
    return fetch_feed(make_rss_url(query), is_upcoming=True)

# --- SHARED FETCHER FUNCTION ---
def fetch_feed(url, is_upcoming):
    jobs = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.title.lower()
            
            if not any(blocked in title for blocked in BLOCKLIST):
                # For Active: Must have "Recruitment/Apply"
                # For Upcoming: We are looser because "Calendar 2026" is a valid title
                if is_upcoming or ("recruitment" in title or "vacancy" in title or "apply" in title):
                    
                    jobs.append({
                        "title": entry.title,
                        "link": entry.link,
                        "date": entry.published,
                        "source": entry.source.title if 'source' in entry else "Official Govt Site"
                    })
    except Exception as e:
        print(f"Error: {e}")
    return jobs

if __name__ == "__main__":
    # Get both lists
    active = get_active_jobs()
    upcoming = get_upcoming_jobs()
    
    # Save as a Dictionary (Two sections)
    data = {
        "active": active,
        "upcoming": upcoming,
        "last_updated": datetime.now().strftime("%d %b %Y, %I:%M %p")
    }
    
    with open("jobs.json", "w") as f:
        json.dump(data, f, indent=4)
        
    print(f"✅ Done! Active: {len(active)}, Upcoming: {len(upcoming)}")
