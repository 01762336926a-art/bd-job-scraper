import os
import json
import requests
from firebase_admin import credentials, initialize_app, firestore

# এনভায়রনমেন্ট থেকে ক্রেডেনশিয়াল রিড করা হচ্ছে
GREEN_API_INSTANCE_ID = os.environ.get("GREEN_API_INSTANCE_ID")
GREEN_API_TOKEN = os.environ.get("GREEN_API_TOKEN")
WHATSAPP_GROUP_ID = os.environ.get("WHATSAPP_GROUP_ID")
FIREBASE_SERVICE_ACCOUNT = os.environ.get("FIREBASE_SERVICE_ACCOUNT")

# ফায়ারবেস ইনিশিয়ালাইজেশন
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

def get_latest_job_from_firebase():
    """
    ফায়ারবেস থেকে অল জবস (Teletalk AllJobs) এর নতুন চাকরির তথ্য ফেচ করার লজিক।
    যেগুলো এখনো হোয়াটসঅ্যাপে পাঠানো হয়নি, সেগুলো চেক করে বের করবে।
    """
    if not db:
        print("Firebase database is not connected.")
        return None

    try:
        # ফায়ারবেসের 'jobs' কালেকশন থেকে সর্বশেষ জবগুলো চেক করা হচ্ছে
        jobs_ref = db.collection('jobs').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(1)
        docs = jobs_ref.stream()
        
        for doc in docs:
            job_data = doc.to_dict()
            
            # যদি জবটি ইতোমধ্যে হোয়াটসঅ্যাপে পাঠানো না হয়ে থাকে
            if not job_data.get('sent_to_whatsapp', False):
                title = job_data.get('title', 'নতুন চাকরির বিজ্ঞপ্তি')
                company = job_data.get('company', 'সরকারি/স্বায়ত্তশাসিত প্রতিষ্ঠান')
                deadline = job_data.get('deadline', 'শীঘ্রই সমাপ্য')
                link = job_data.get('link', 'https://alljobs.teletalk.com.bd')
                
                # ফায়ারবেসে মার্ক করে দেওয়া হচ্ছে যে এটি পাঠানো হয়ে গেছে (যাতে ডুপ্লিকেট না যায়)
                doc.reference.update({'sent_to_whatsapp': True})
                
                # তোমার কাঙ্ক্ষিত ফরম্যাট ও দোকানের ঠিকানা সহ মেসেজ তৈরি
                formatted_message = (
                    "📢 নতুন চাকরির বিজ্ঞপ্তি\n\n"
                    f"📌 পদ: {title}\n"
                    f"🏢 প্রতিষ্ঠানের নাম: {company}\n"
                    f"⏰ আবেদনের শেষ তারিখ: {deadline}\n"
                    f"🔗 আবেদন লিঙ্ক: {link}\n\n"
                    "সহজে ও নির্ভুলভাবে আবেদনের জন্য সরাসরি চলে আসুন:\n"
                    "👉 এরশাদ কম্পিউটার & ইন্টারনেট পেমেন্ট\n"
                    "📍 আগ্রাদ্বিগুণ বাজার, ভিআইপি রোড, ধামইরহাট, নওগাঁ\n"
                    "📞 যোগাযোগ: 01309897414"
                )
                return formatted_message
        
        print("No new un-sent jobs found in Firebase.")
    except Exception as e:
        print(f"Error fetching from Firebase: {e}")
        
    return None

def main():
    print("Checking for latest job circulars from Firebase...")
    job_message = get_latest_job_from_firebase()
    
    if job_message:
        send_to_whatsapp(job_message)

if __name__ == "__main__":
    main()
