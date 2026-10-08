import os
import json
import requests
from bs4 import BeautifulSoup
from firebase_admin import credentials, initialize_app, firestore

# গ্রিন এপিআই ও ফায়ারবেস ক্রেডেনশিয়াল
GREEN_API_INSTANCE_ID = os.environ.get("GREEN_API_INSTANCE_ID")
GREEN_API_TOKEN = os.environ.get("GREEN_API_TOKEN")
WHATSAPP_GROUP_ID = os.environ.get("WHATSAPP_GROUP_ID")
FIREBASE_SERVICE_ACCOUNT = os.environ.get("FIREBASE_SERVICE_ACCOUNT")

# ফায়ারবেস কানেকশন সেটআপ
db = None
if FIREBASE_SERVICE_ACCOUNT:
    try:
        cred_dict = json.loads(FIREBASE_SERVICE_ACCOUNT)
        cred = credentials.Certificate(cred_dict)
        if not len(firebase_admin._apps):
            initialize_app(cred)
        db = firestore.client()
    except Exception as e:
        print(f"Firebase initialization error: {e}")

def send_to_whatsapp(message):
    """হোয়াটসঅ্যাপ গ্রুপে মেসেজ পাঠানোর ফাংশন"""
    if not GREEN_API_INSTANCE_ID or not GREEN_API_TOKEN or not WHATSAPP_GROUP_ID:
        print("Green API credentials missing!")
        return

    url = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE_ID}/sendMessage/{GREEN_API_TOKEN}"
    payload = {
        "chatId": WHATSAPP_GROUP_ID,
        "message": message
    }

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Successfully sent single job update to WhatsApp group!")
    else:
        print(f"Failed to send WhatsApp message: {response.text}")

def fetch_and_store_jobs():
    """
    বিডিজবস বা অন্যান্য পোর্টাল থেকে রানিং জব ফেচ করে ফায়ারবেসে স্টোর করা
    """
    if not db:
        return

    url = "https://jobs.bdjobs.com/jobsearch.asp?icatId=3"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            job_cards = soup.select('.job-title-text, .s-job-card, h2.title')
            
            for card in job_cards[:10]:
                title = card.get_text(strip=True)
                if not title:
                    continue
                link = card.find('a')['href'] if card.name == 'a' or card.find('a') else "https://jobs.bdjobs.com"
                if link and not link.startswith('http'):
                    link = "https://jobs.bdjobs.com/" + link
                
                jobs_ref = db.collection('jobs')
                query = jobs_ref.where('title', '==', title).limit(1).get()
                
                if not list(query):
                    jobs_ref.add({
                        'title': title,
                        'company': 'বিডিজবস পোর্টাল',
                        'link': link,
                        'sent_to_whatsapp': False
                    })
    except Exception as e:
        print(f"Error fetching jobs: {e}")

def send_single_job_from_firebase():
    """
    ফায়ারবেস থেকে ঠিক ১টি নতুন চাকরির আপডেট নিয়ে নির্দিষ্ট ফরম্যাটে পাঠানো
    """
    if not db:
        print("Firebase database not connected.")
        return

    try:
        # মাত্র ১টি আনসেন্ট জব ফেচ করা (.limit(1))
        jobs_ref = db.collection('jobs').where('sent_to_whatsapp', '==', False).limit(1)
        docs = list(jobs_ref.stream())
        
        if not docs:
            print("No new pending jobs to send.")
            return
            
        doc = docs[0]
        job_data = doc.to_dict()
        title = job_data.get('title', 'চাকরির পদ')
        company = job_data.get('company', 'প্রতিষ্ঠান')
        link = job_data.get('link', 'https://jobs.bdjobs.com')
        
        # একক চাকরির সুন্দর মেসেজ ফরম্যাট
        formatted_message = (
            "🔥 *নতুন চাকরির খবর* 🔥\n\n"
            f"📌 *পদ:* {title}\n"
            f"🏢 *প্রতিষ্ঠান:* {company}\n"
            f"🔗 {link}\n\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "💻 *জারি করেছেন:* এরশাদ কম্পিউটার & ইন্টারনেট পেমেন্ট\n"
            "📍 *ঠিকানা:* আগ্রাদ্বিগুণ বাজার, ভিআইপি রোড, ধামইরহাট, নওগাঁ\n"
            "👉 অনলাইনে নির্ভুল আবেদনের জন্য আমাদের দোকানে আসুন।\n"
            "📞 যোগাযোগ: 01309897414"
        )
        
        # হোয়াটসঅ্যাপে পাঠানো
        send_to_whatsapp(formatted_message)
        
        # পাঠানো শেষ হলে ফায়ারবেসে স্ট্যাটাস true করে দেওয়া
        doc.reference.update({'sent_to_whatsapp': True})
        
    except Exception as e:
        print(f"Error sending single job: {e}")

def main():
    print("Running automated single-job broadcast...")
    fetch_and_store_jobs()
    send_single_job_from_firebase()

if __name__ == "__main__":
    main()
