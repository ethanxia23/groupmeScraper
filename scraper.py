import os
import sys
import requests
import pandas as pd
import argparse
import openpyxl
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
        """
        Get all messages from GroupMe group
        """
        all_messages = []
        before_id = None
        print("Fetching messages...")

        while True:
            url = f"https://api.groupme.com/v3/groups{self.group_id}/messages"
            params = {"token": self.token, "limit": 100}
            if before_id:
                params["before_id"] = before_id

            response = requests.get(url, params=params)
            response.raise_for_status()
            messages = response.json()["response"]["messages"]
            if not messages:
                break

            all_messages.extend(messages)
            before_id = messages[-1]["id"]
            print(f"Fetched {len(all_messages)} messages so far...")

        print(f"Total messages fetched: {len(all_messages)}")
        return all_messages
        
        
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
        messages = self.get_groupme_data()
        df = self.format_for_excel(messages)
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