import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# Environtment Variables (GitHub Secrets থেকে আসা)
instance_id = os.environ.get("GREEN_API_INSTANCE_ID")
api_token = os.environ.get("GREEN_API_TOKEN")
group_id = os.environ.get("WHATSAPP_GROUP_ID")
firebase_creds_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT")

# Firebase Initialization
db = None
if firebase_creds_json:
    try:
        cred_dict = json.loads(firebase_creds_json)
        cred = credentials.Certificate(cred_dict)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("Firebase successfully connected.")
    except Exception as e:
        print(f"Firebase initialization error: {e}")
else:
    print("FIREBASE_SERVICE_ACCOUNT missing.")

def send_whatsapp_job(title, organization, deadline, apply_url):
    if not instance_id or not api_token or not group_id:
        print("Green API credentials missing.")
        return

    url = f"https://api.green-api.com/waInstance{instance_id}/sendMessage/{api_token}"
    
    message = (
        f"📢 *নতুন চাকরির বিজ্ঞপ্তি*\n\n"
        f"📌 *পদ:* {title}\n"
        f"🏢 *প্রতিষ্ঠানের নাম:* {organization}\n"
        f"⏰ *আবেদনের শেষ তারিখ:* {deadline}\n"
        f"🔗 *আবেদন লিঙ্ক:* {apply_url}\n\n"
        f"সহজে ও নির্ভুলভাবে আবেদনের জন্য সরাসরি চলে আসুন:\n"
        f"👉 *এরশাদ কম্পিউটার & ইন্টারনেট পয়েন্ট*\n"
        f"📍 আগ্রাদ্বিগুণ বাজার, ধামইরহাট, নওগাঁ\n"
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
        print(f"Error sending WhatsApp message: {e}")

def scrape_teletalk_jobs():
    url = "https://alljobs.teletalk.com.bd"
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
                org = org_elem.get_text(strip=True) if org_elem else "সরকারি/বেসরকারি প্রতিষ্ঠান"
                
                link = link_elem['href']
                if not link.startswith("http"):
                    link = "https://alljobs.teletalk.com.bd" + link

                deadline = deadline_elem.get_text(strip=True) if deadline_elem else "বিস্তারিত সার্কুলারে"

                job_data = {
                    "id": str(hash(link)),
                    "title": title,
                    "organization": org,
                    "apply_url": link,
                    "deadline": deadline,
                    "created_at": datetime.now().isoformat()
                }

                job_list.append(job_data)

                # ফায়ারবেসে চেক ও সেভ
                if db:
                    doc_ref = db.collection("job_circulars").document(job_data["id"])
                    if not doc_ref.get().exists:
                        doc_ref.set(job_data)
                        send_whatsapp_job(title, org, deadline, link)

        return job_list

    except Exception as e:
        print(f"স্ক্র্যাপ করতে সমস্যা হয়েছে: {e}")
        return []

if __name__ == "__main__":
    extracted_jobs = scrape_teletalk_jobs()
    print(f"মোট {len(extracted_jobs)} টি চাকরির তথ্য পাওয়া গেছে।")
    
    # টেস্ট মেসেজ পাঠানোর জন্য (একবার মেসেজ পেয়ে গেলে নিচের লাইনটির শুরুতে # দিয়ে অফ করতে পারবে)
    send_whatsapp_job("টেস্ট চাকরির বিজ্ঞপ্তি", "এরশাদ কম্পিউটার", "আজই শেষ দিন", "https://alljobs.teletalk.com.bd")
