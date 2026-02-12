import feedparser
import json
import urllib.parse
import time

# --- YOUR CUSTOM CONFIGURATION ---
# 1. Search Terms (12th Pass, Defense, Clerk)
ELIGIBLE_TERMS = [
    "12th pass", "higher secondary", "intermediate", "hsc",
    "ssc chsl", "ssc mts", "ssc gd", "constable",
    "data entry", "clerk", "assistant", "trainee",
    "railway", "group d", "technician"
]

# 2. Blocklist (Ignore these)
BLOCKLIST = [
    "admit card", "result", "answer key", "cutoff", "syllabus", 
    "graduate", "b.tech", "mba", "experience", "manager"
]

# 3. Google News RSS Search Link (The Magic Part)
# Searches only trusted government sites (gov.in, nic.in, indianrailways.gov.in, wbp.gov.in)
def get_rss_url():
    base_url = "https://news.google.com/rss/search?q="
    query = 'recruitment AND ({0}) AND (site:gov.in OR site:nic.in OR site:indianrailways.gov.in OR site:wbp.gov.in) when:2d'.format(' OR '.join(ELIGIBLE_TERMS))
    return base_url + urllib.parse.quote(query) + "&hl=en-IN&gl=IN&ceid=IN:en"

def get_jobs():
    print("👮 Checking Official Govt Sources for 12th Pass/Defense jobs...")
    rss_url = get_rss_url()
    found_jobs = []

    try:
        feed = feedparser.parse(rss_url)

        for entry in feed.entries:
            title = entry.title.lower()

            # Filter 1: Must NOT contain blocked words
            if not any(blocked in title for blocked in BLOCKLIST):

                # Filter 2: Must look like a recruitment
                if "recruitment" in title or "vacancy" in title or "apply" in title or "notification" in title:

                    found_jobs.append({
                        "title": entry.title,
                        "link": entry.link,
                        "date": entry.published,
                        "source": entry.source.title if 'source' in entry else "Govt Official"
                    })

    except Exception as e:
        print(f"Error: {e}")

    return found_jobs

if __name__ == "__main__":
    jobs = get_jobs()
    print(f"✅ Found {len(jobs)} jobs.")

    # Save to file
    with open("jobs.json", "w") as f:
        json.dump(jobs, f, indent=4)
