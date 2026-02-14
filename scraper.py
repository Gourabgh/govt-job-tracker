import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def scrape_ssc():
    url = "https://ssc.nic.in/Portal/Notices"
    jobs = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "lxml")

        rows = soup.select("table tbody tr")
        for row in rows[:10]:
            cols = row.find_all("td")
            if len(cols) >= 2:
                title = cols[1].get_text(strip=True)
                link_tag = cols[1].find("a")
                if link_tag:
                    link = "https://ssc.nic.in" + link_tag["href"]
                else:
                    link = url

                jobs.append({
                    "title": title,
                    "link": link,
                    "date": datetime.now().strftime("%d %b"),
                    "end_date": "Check PDF",
                    "source": "SSC",
                    "state": "Central Govt"
                })
    except:
        pass

    return jobs


def scrape_upsc():
    url = "https://www.upsc.gov.in/recruitment/recruitment-advertisements"
    jobs = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "lxml")

        links = soup.select("div.view-content a")
        for link in links[:8]:
            title = link.get_text(strip=True)
            href = link.get("href")

            if href and "Advertisement" in title:
                full_link = "https://www.upsc.gov.in" + href
                jobs.append({
                    "title": title,
                    "link": full_link,
                    "date": datetime.now().strftime("%d %b"),
                    "end_date": "Check PDF",
                    "source": "UPSC",
                    "state": "Central Govt"
                })
    except:
        pass

    return jobs


def scrape_army():
    url = "https://joinindianarmy.nic.in"
    jobs = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "lxml")

        notices = soup.find_all("a")
        for notice in notices[:10]:
            text = notice.get_text(strip=True)
            href = notice.get("href")

            if text and href and ("agniveer" in text.lower() or "rally" in text.lower()):
                full_link = url + "/" + href if not href.startswith("http") else href

                jobs.append({
                    "title": text,
                    "link": full_link,
                    "date": datetime.now().strftime("%d %b"),
                    "end_date": "Check Website",
                    "source": "Indian Army",
                    "state": "Central Govt"
                })
    except:
        pass

    return jobs


if __name__ == "__main__":
    active_jobs = []
    active_jobs.extend(scrape_ssc())
    active_jobs.extend(scrape_upsc())
    active_jobs.extend(scrape_army())

    data = {
        "active": active_jobs,
        "upcoming": [],
        "last_updated": datetime.now().strftime("%d %b %Y, %I:%M %p")
    }

    with open("jobs.json", "w") as f:
        json.dump(data, f, indent=4)
