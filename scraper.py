import requests
from bs4 import BeautifulSoup
import json
import datetime

# ১. পপুলার এবং হাইলাইটেড চাকরির কিওয়ার্ড তালিকা
POPULAR_KEYWORDS = [
    "সেনাবাহিনী", "নৌবাহিনী", "বিমানবাহিনী", "পুলিশ", "বিজিবি",
    "প্রাথমিক", "উপজেলা", "সমাজসেবা", "ব্যাংক", "বিসিএস",
    "রেলওয়ে", "কাস্টমস", "সচিবালয়", "মন্ত্রণালয়", "জেলা প্রশাসক",
    "আর্মড ফোর্সেস", "কোস্ট গার্ড", "আনসার", "কাউন্সিল"
]

def check_if_popular(title, organization):
    """সার্কুলারটি পপুলার বা টপ লেভেলের কিনা তা যাচাই করে"""
    combined_text = f"{title} {organization}"
    for keyword in POPULAR_KEYWORDS:
        if keyword in combined_text:
            return True
    return False

def scrape_teletalk_jobs():
    """টেলিটক অলজবস থেকে তথ্য সংগ্রহের ফাংশন"""
    url = "https://alljobs.teletalk.com.bd/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"ওয়েবসাইট থেকে তথ্য আনা যায়নি, স্ট্যাটাস কোড: {response.status_code}")
            return []

        soup = BeautifulSoup(response.content, "html.parser")
        job_list = []

        # অলজবস সাইটের জব কার্ডগুলো খোঁজা
        job_cards = soup.find_all("div", class_="job-item") or soup.find_all("div", class_="card")

        for card in job_cards:
            title_elem = card.find("h3") or card.find("a")
            org_elem = card.find("p", class_="company-name") or card.find("span", class_="org")
            link_elem = card.find("a", href=True)
            deadline_elem = card.find("span", class_="deadline") or card.find("p", class_="date")

            if title_elem and link_elem:
                title = title_elem.get_text(strip=True)
                org = org_elem.get_text(strip=True) if org_elem else "সরকারি প্রতিষ্ঠান"
                
                link = link_elem['href']
                if not link.startswith("http"):
                    link = "https://alljobs.teletalk.com.bd" + link
                
                deadline = deadline_elem.get_text(strip=True) if deadline_elem else "বিস্তারিত লিংকে দেখুন"

                # অটোমেটিক চেক করা এটি হাইলাইটেড বা পপুলার জব কিনা
                is_popular = check_if_popular(title, org)

                job_data = {
                    "id": str(hash(link)), # ইউনিক জব আইডি
                    "title": title,
                    "organization": org,
                    "apply_url": link,
                    "deadline": deadline,
                    "is_popular": is_popular,
                    "created_at": datetime.datetime.now().isoformat()
                }
                job_list.append(job_data)

        return job_list

    except Exception as e:
        print(f"স্ক্র্যাপিং করতে ত্রুটি হয়েছে: {e}")
        return []

if __name__ == "__main__":
    extracted_jobs = scrape_teletalk_jobs()
    print(f"মোট {len(extracted_jobs)} টি চাকরির তথ্য সংগ্রহ করা হয়েছে।")
    print(json.dumps(extracted_jobs, ensure_ascii=False, indent=2))
