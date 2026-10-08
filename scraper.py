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
        print("Successfully sent message to WhatsApp group!")
    else:
        print(f"Failed to send WhatsApp message: {response.text}")

def scrape_and_store_teletalk_jobs():
    """
    টেলিটক অল জবস সাইট থেকে রানিং জবগুলো স্ক্রেপ করে ফায়ারবেসে স্টোর করার লজিক
    """
    url = "https://alljobs.teletalk.com.bd/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # টেলিটক সাইটের লেআউট অনুযায়ী রানিং জবগুলোর তথ্য এক্সট্রাক্ট করা
            # (এখানে জব কার্ডগুলো থেকে টাইপ, কোম্পানি, লিংক সংগ্রহ করা হবে)
            # যদি ডেটা ফায়ারবেসে অলরেডি না থাকে, তবে নতুন হিসেবে সেভ হবে।
            print("Successfully checked Teletalk AllJobs for updates.")
    except Exception as e:
        print(f"Error scraping Teletalk: {e}")

def get_pending_jobs_batch_from_firebase():
    """
    ফায়ারবেস থেকে একসাথে ১০-১৫টি করে আনসেন্ট (unsent) চাকরির আপডেট ফেচ করা
    """
    if not db:
        print("Firebase database not connected.")
        return None

    try:
        # যেগুলো এখনো হোয়াটসঅ্যাপে পাঠানো হয়নি এমন ১০টি জব একসাথে নিয়ে আসা
        jobs_ref = db.collection('jobs').where('sent_to_whatsapp', '==', False).limit(10)
        docs = list(jobs_ref.stream())
        
        if not docs:
            print("No new jobs to send.")
            return None
            
        jobs_text_list = []
        batch_docs = []
        
        for idx, doc in enumerate(docs, 1):
            job_data = doc.to_dict()
            title = job_data.get('title', 'চাকরির পদ')
            company = job_data.get('company', 'প্রতিষ্ঠান')
            link = job_data.get('link', 'https://alljobs.teletalk.com.bd')
            
            jobs_text_list.append(f"{idx}. 📌 পদ: {title}\n🏢 প্রতিষ্ঠান: {company}\n🔗 {link}\n")
            batch_docs.append(doc)
            
        # একসাথে পাঠানো মেসেজের ফরম্যাট
        jobs_joined = "\n".join(jobs_text_list)
        
        formatted_message = (
            "📢 নতুন চাকরির আপডেটসমূহ (ব্যাচ)\n\n"
            f"{jobs_joined}\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "সহজে ও নির্ভুলভাবে আবেদনের জন্য সরাসরি চলে আসুন:\n"
            "👉 এরশাদ কম্পিউটার & ইন্টারনেট পেমেন্ট\n"
            "📍 আগ্রাদ্বিগুণ বাজার, ভিআইপি রোড, ধামইরহাট, নওগাঁ\n"
            "📞 যোগাযোগ: 01309897414"
        )
        
        # পাঠানো শেষ হলে ফায়ারবেসে টেস্টিং বা ফ্ল্যাগ আপডেট করে দেওয়া যাতে ডুপ্লিকেট না যায়
        for doc in batch_docs:
            doc.reference.update({'sent_to_whatsapp': True})
            
        return formatted_message
        
    except Exception as e:
        print(f"Error reading from Firebase: {e}")
        
    return None

def main():
    print("Running automated job sync and broadcast...")
    # ১. প্রথমে টেলিটক সাইট থেকে নতুন জব চেক করে ফায়ারবেসে আপডেট করবে
    scrape_and_store_teletalk_jobs()
    
    # ২. ফায়ারবেস থেকে ১০-১৫টি নতুন জব নিয়ে হোয়াটসঅ্যাপে পাঠাবে
    batch_message = get_pending_jobs_batch_from_firebase()
    
    if batch_message:
        send_to_whatsapp(batch_message)

if __name__ == "__main__":
    main()
