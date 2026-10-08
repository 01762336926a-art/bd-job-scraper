import os
import requests

# পরিবেশ থেকে সিক্রেট বা ভ্যারিয়েবলগুলো নেওয়া
PAGE_ID = os.environ.get("PAGE_ID")
FB_PAGE_TOKEN = os.environ.get("FB_PAGE_TOKEN")
GREEN_API_INSTANCE_ID = os.environ.get("GREEN_API_INSTANCE_ID")
GREEN_API_TOKEN = os.environ.get("GREEN_API_TOKEN")
WHATSAPP_GROUP_ID = os.environ.get("WHATSAPP_GROUP_ID")

def send_to_facebook(message):
    """ফেসবুক পেজে পোস্ট পাঠানোর ফাংশন"""
    if not PAGE_ID or not FB_PAGE_TOKEN:
        print("Facebook credentials missing!")
        return
    
    url = f"https://graph.facebook.com/{PAGE_ID}/feed"
    payload = {
        "message": message,
        "access_token": FB_PAGE_TOKEN
    }
    
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        print("Successfully posted to Facebook Page!")
    else:
        print(f"Failed to post to Facebook: {response.text}")

def send_to_whatsapp(message):
    """হোয়াটসঅ্যাপ গ্রুপে মেসেজ পাঠানোর ফাংশন"""
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

def main():
    # টেস্ট মেসেজ যা রান করার সঙ্গে সঙ্গে ফেসবুক ও হোয়াটসঅ্যাপে চলে যাবে
    test_message = "🤖 এটি একটি টেস্ট অ্যালার্ট মেসেজ!\n\nঅনলাইন কম্পিউটার দোকান থেকে গিটহাব অ্যাকশনের মাধ্যমে সফলভাবে ফেসবুক পেজ এবং হোয়াটসঅ্যাপ গ্রুপে একযোগে টেস্ট পোস্ট পাঠানো হলো। সবকিছু ঠিকঠাক কাজ করছে!"
    
    print("Sending test alerts to Facebook and WhatsApp...")
    
    # একযোগে ফেসবুকে এবং হোয়াটসঅ্যাপে পাঠানো
    send_to_facebook(test_message)
    send_to_whatsapp(test_message)

if __name__ == "__main__":
    main()
