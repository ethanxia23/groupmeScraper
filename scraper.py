import os
import sys
import requests
import pandas as pd
import argparse
import openpyxl
import pytesseract
from PIL import Image
from io import BytesIO
from datetime import datetime 

class groupmeDataScrape():
    def __init__(self, token, group_id):
        self.token = token
        self.group_id = group_id
    
    
    def get_groupme_groups(self):
        response = requests.get(f"https://api.groupme.com/v3/groups?token={self.token}")
        groups = response.json()["response"]

        for group in groups:
            print(f"Name: {group['name']}, ID: {group['id']}")

        
    def get_groupme_data(self):
        """Fetch and print the latest messages from the group."""
        url = f"https://api.groupme.com/v3/groups/{self.group_id}/messages"
        params = {
            "token": self.token,
            "limit": 1
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        print(response.json())
        exit(0)
        messages = response.json()["response"]["messages"]

        for msg in messages:
            user = msg["name"]
            date = datetime.fromtimestamp(msg["created_at"])

            text = msg.get("text")
            if not text:
                attachments = msg.get("attachments", [])
                if attachments:
                    if attachments[0]["type"] == "image":
                        text = f"[Photo] {attachments[0]['url']}"
                    else:
                        text = f"[Attachment: {attachments[0]['type']}]"
                else:
                    text = "[No content]"

            print(f"[{date}] {user}: {text}")
            
        #user_id = messages[0].get("user_id") or messages[0].get("sender_id")
        #return user_id
        
        
    def get_data_from_image(self, url):
        # Download the image
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))

        # Run OCR
        text = pytesseract.image_to_string(img)

        # Try to find distances (e.g. "5000m", "5k", etc.)
        import re
        match = re.search(r"(\d{3,5})\s?m", text.lower())
        if match:
            return match.group(1) + "m"
        else:
            return text  # fallback: return raw OCR text    
        
        
    def get_user_from_id(self):
        url = f"https://api.groupme.com/v3/groups/{self.group_id}"
        params = {"token": self.token}
        response = requests.get(url, params=params)
        response.raise_for_status()
        group = response.json()["response"]

        member_map = {}
        for m in group["members"]:
            member_map[m["user_id"]] = {
                "account_name": m["name"],
                "nickname": m["nickname"]
            }
        return member_map    
        
        
    def format_for_excel(self, messages):
        """
        Filters messages for workouts and formats for Excel / Output
        """
        workouts = []
        for msg in messages:
            text = msg.get("text", "")
            if text and any(keyword in text.lower() for keyword in ["row", "bike", "run", "lift", "swim", "erg"]):
                workouts.append({
                    "user": msg["name"],
                    "text": text,
                    "date": datetime.fromtimestamp(msg["created_at"])
                })

        df = pd.DataFrame(workouts)
        return df
        
        
    def main(self):
        ### for loop
        
        id = self.get_groupme_data(limit=1) # get data, return user_id
        person = self.get_user_from_id(id) # input id into format for excel
        df = self.format_for_excel(messages) # get person
        df.to_excel("workouts.xlsx", index=False)
        print("✅ Workouts saved to workouts.xlsx")
        
        
        
if __name__ == "__main__":
    TOKEN = "vxbq1LOoeklMvQjM591DeHpasy4OtsdX8oFySiRS"
    GROUP_ID = "98882721"
    
    scraper = groupmeDataScrape(TOKEN, GROUP_ID)
    try:
        scraper.main()
    except Exception as e:
        print(f"Error: {e}")
    