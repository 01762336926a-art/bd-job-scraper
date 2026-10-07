import os
import requests
import json
import datetime
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore

# ১. ফায়ারবেস ইনিশিয়ালাইজেশন
firebase_config = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
if firebase_config:
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
else:
    db = None

# ২. জনপ্রিয় কিওয়ার্ড তালিকা
POPULAR_KEYWORDS = [
    "সরকারি", "শিক্ষক", "প্রাথমিক", "পুলিশ", "ব্যাংক",
    "প্রশাসন", "রেলওয়ে", "মন্ত্রণালয়", "ডাক", "অফিসার",
    "উপজেলা", "রাজস্ব", "ডিজিটাল", "সহকারী", "জেলা পরিষদ",
    "জাস্টিস", "জরুরি", "জব", "গার্ড", "কম্পিউটার"
]

def check_if_popular(title, organization):
    combined_text = f"{title} {organization}"
    for keyword in POPULAR_KEYWORDS:
        if keyword in combined_text:
            return True
    return False

# ৩. হোয়াটসঅ্যাপে মেসেজ পাঠানোর ফাংশন (Green API)
def send_whatsapp_job(title, organization, deadline, apply_url):
    instance_id = os.environ.get("GREEN_API_INSTANCE_ID")
    api_token = os.environ.get("GREEN_API_TOKEN")
    group_id = os.environ.get("WHATSAPP_GROUP_ID")
    
    if not instance_id or not api_token or not group_id:
        print("Green API credentials missing.")
        return

    url = f"https://api.green-api.com/waInstance{instance_id}/sendMessage/{api_token}"
    
    message = (
        f"📢 *নতুন চাকরির বিজ্ঞপ্তি!*\n\n"
        f"🔹 *পদের নাম:* {title}\n"
        f"🏢 *প্রতিষ্ঠানের নাম:* {organization}\n"
        f"📅 *আবেদনের শেষ তারিখ:* {deadline}\n"
        f"🔗 *আবেদন লিংক:* {apply_url}\n\n"
        f"📍 সঠিক ও নির্ভুলভাবে আবেদনের জন্য সরাসরি চলে আসুন:\n"
        f"*এরশাদ কম্পিউটার এন্ড ইন্টারনেট পয়েন্ট*\n"
        f"ঠিকানা: আগ্রাদ্বিগুণ বাজার, চার মাথার মোড় (ভিআইপি রোড)\n"
        f"📞 যোগাযোগ: 01309897414"
    )
    
    payload = {
        "chatId": group_id,
        "message": message
    }
    
    try:
        response = requests.post(url, json=payload)
        print("WhatsApp Message Response:", response.json())
    except Exception as e:
        print("Error sending WhatsApp message:", e)

# ৪. AllJobs Teletalk থেকে ডাটা স্ক্র্যাপ করা
def scrape_teletalk_jobs():
    url = "https://alljobs.teletalk.com.bd/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"ওয়েবসাইট থেকে সাড়া পাওয়া যায়নি, স্ট্যাটাস কোড: {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.content, "html.parser")
        job_list = []
        
        job_cards = soup.find_all("div", class_="job-box") or soup.find_all("div", class_="card")
        
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
                    
                deadline = deadline_elem.get_text(strip=True) if deadline_elem else "বিজ্ঞপ্তি দেখুন"
                
                is_popular = check_if_popular(title, org)
                
                job_data = {
                    "id": str(hash(link)),
                    "title": title,
                    "organization": org,
                    "apply_url": link,
                    "deadline": deadline,
                    "is_popular": is_popular,
                    "created_at": datetime.datetime.now().isoformat()
                }
                
                job_list.append(job_data)
                
                # ফায়ারবেসে সেভ
                if db:
                    db.collection("job_circulars").document(job_data["id"]).set(job_data, merge=True)
                
                # জনপ্রিয় ও নতুন চাকরি হলে সরাসরি হোয়াটসঅ্যাপে পাঠানো
                if is_popular:
                    send_whatsapp_job(title, org, deadline, link)
                    
        return job_list
        
    except Exception as e:
        print(f"স্ক্র্যাপ করতে সমস্যা হয়েছে: {e}")
        return []

if __name__ == "__main__":
    extracted_jobs = scrape_teletalk_jobs()
    print(f"মোট {len(extracted_jobs)} টি চাকরির তথ্য পাওয়া গেছে।")
    print(json.dumps(extracted_jobs, ensure_ascii=False, indent=2))
