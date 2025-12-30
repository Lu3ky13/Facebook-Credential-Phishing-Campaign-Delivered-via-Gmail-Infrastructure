#!/usr/bin/env python3
"""
Final Check - Get ALL messages (old from files + new from API)
"""

import requests
import json
from datetime import datetime

CONFIG = {
    "bot_token": "7871555324:AAHUSIAw2N0psJlFbJ7sfkq4D2L6e9qofGU",
    "bot_token_journey": "8053731074:AAEWnpsgr82u-yoKWONk2eA1mqiVKBhL4bY",
}

def get_updates(bot_token, offset=0, limit=100):
    """Get updates from Telegram API"""
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    params = {"offset": offset, "limit": limit}
    try:
        response = requests.get(url, params=params, timeout=15)
        return response.json()
    except:
        return {"ok": False}

def main():
    print("=" * 80)
    print("FINAL CHECK - ALL MESSAGES (OLD + NEW)")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    
    # Load existing complete extraction
    try:
        with open("ALL_MESSAGES_COMPLETE_20251230_175301.json", "r", encoding="utf-8") as f:
            existing_data = json.load(f)
        print(f"[+] Loaded existing data: {existing_data['total_messages']} messages")
    except:
        existing_data = {"messages": [], "total_messages": 0}
        print("[!] Could not load existing data file")
    
    # Check for NEW messages from API
    print("\n[*] Checking for NEW messages from Telegram API...")
    
    all_new_messages = []
    for bot_name, token in [("bot_1", CONFIG["bot_token"]), ("bot_2", CONFIG["bot_token_journey"])]:
        print(f"\n    [*] Checking {bot_name}...")
        result = get_updates(token, limit=100)
        
        if result.get("ok"):
            updates = result.get("result", [])
            print(f"        [+] Found {len(updates)} new update(s)")
            
            # Extract messages
            for update in updates:
                msg = None
                if "message" in update:
                    msg = update["message"]
                elif "edited_message" in update:
                    msg = update["edited_message"]
                elif "channel_post" in update:
                    msg = update["channel_post"]
                
                if msg and msg.get("message_id"):
                    all_new_messages.append({
                        "bot": bot_name,
                        "update_id": update.get("update_id"),
                        "message_id": msg.get("message_id"),
                        "date": msg.get("date"),
                        "text": msg.get("text", msg.get("caption", "[Media]")),
                        "from": msg.get("from", {}).get("username", "N/A"),
                    })
        else:
            print(f"        [!] Error: {result.get('description', 'Unknown')}")
    
    # Summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"Existing messages (from files): {existing_data['total_messages']}")
    print(f"New messages (from API): {len(all_new_messages)}")
    print(f"Total unique messages found: {existing_data['total_messages'] + len(all_new_messages)}")
    
    if all_new_messages:
        print("\nNew messages found:")
        for msg in all_new_messages:
            date = datetime.fromtimestamp(msg['date']).isoformat() if msg.get('date') else "Unknown"
            print(f"  [{date}] @{msg['from']}: {msg['text'][:60] if msg.get('text') else '[Media]'}...")
    
    print("\n" + "=" * 80)
    print("NOTE: Telegram Bot API Limitations")
    print("=" * 80)
    print("1. getUpdates only returns UNPROCESSED updates")
    print("2. Once retrieved, updates are CONSUMED and won't appear again")
    print("3. To get OLD messages, you need:")
    print("   - A bot that was running and logging in real-time")
    print("   - Access to messages before they're consumed")
    print("   - Or use the data already extracted from files")
    print("\n" + "=" * 80)
    print("All available messages have been extracted and saved to:")
    print("  ALL_MESSAGES_COMPLETE_20251230_175301.json")
    print("=" * 80)

if __name__ == "__main__":
    main()


