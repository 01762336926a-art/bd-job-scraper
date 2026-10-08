import os
import requests

# পরিবেশ থেকে ক্রেডেনশিয়ালগুলো রিড করা হচ্ছে
GREEN_API_INSTANCE_ID = os.environ.get("GREEN_API_INSTANCE_ID")
GREEN_API_TOKEN = os.environ.get("GREEN_API_TOKEN")
WHATSAPP_GROUP_ID = os.environ.get("WHATSAPP_GROUP_ID")
# ফায়ারবেস বা অন্যান্য ডেটাবেস কানেকশন যদি থাকে
FIREBASE_SERVICE_ACCOUNT = os.environ.get("FIREBASE_SERVICE_ACCOUNT")

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

def fetch_latest_jobs():
    """
    এখানে টেলিটক অল জবস বা ফায়ারবেস থেকে রিয়েল-টাইম চাকরির আপডেট ফেচ করার লজিক থাকবে।
    প্রতি ২ ঘণ্টা পর পর স্ক্রিপ্ট রান হলে নতুন জবগুলো এখানে স্ক্রেপ বা লোড হবে।
    """
    # উদাহরণস্বরূপ একটি ডামি বা রিয়েল স্ক্রেপিং টেক্সট:
    job_alerts = "🔥 নতুন চাকরির আপডেট (Teletalk AllJobs / Firebase):\n- পদ: কম্পিউটার অপারেটর বা অন্যান্য পদ\n- বিস্তারিত দেখতে ভিজিট করুন। (প্রতি ২ ঘণ্টার স্বয়ংক্রিয় আপডেট)"
    return job_alerts

def main():
    print("Checking for latest job circulars...")
    latest_jobs = fetch_latest_jobs()
    
    if latest_jobs:
        # হোয়াটসঅ্যাপে মেসেজ পাঠানো হচ্ছে
        send_to_whatsapp(latest_jobs)

if __name__ == "__main__":
    main()
