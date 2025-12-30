#!/usr/bin/env python3
"""
Extract All Messages from Existing Data Files
Combines messages from all available JSON files and data sources
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List
from collections import defaultdict

# ==================================================
# CONFIGURATION
# ==================================================
CONFIG = {
    "bot_token": "7871555324:AAHUSIAw2N0psJlFbJ7sfkq4D2L6e9qofGU",
    "bot_token_journey": "8053731074:AAEWnpsgr82u-yoKWONk2eA1mqiVKBhL4bY",
    "chat_id": "-1003162196749",
}

# Files to check for messages
DATA_FILES = [
    "11.json",
    "11_formatted.json",
    "telegram_data_20251230_174317.json",
    "all_chats_messages_20251230_172910.json",
    "all_old_messages_20251230_174756.json",
]

# ==================================================
# EXTRACTION FUNCTIONS
# ==================================================
def extract_messages_from_updates(updates: List[Dict]) -> List[Dict]:
    """Extract messages from update objects"""
    messages = []
    
    for update in updates:
        msg = None
        msg_type = None
        
        if "message" in update:
            msg = update["message"]
            msg_type = "message"
        elif "edited_message" in update:
            msg = update["edited_message"]
            msg_type = "edited_message"
        elif "channel_post" in update:
            msg = update["channel_post"]
            msg_type = "channel_post"
        elif "edited_channel_post" in update:
            msg = update["edited_channel_post"]
            msg_type = "edited_channel_post"
        elif "callback_query" in update and "message" in update["callback_query"]:
            msg = update["callback_query"]["message"]
            msg_type = "callback_query"
        
        if msg:
            message = {
                "update_id": update.get("update_id"),
                "message_id": msg.get("message_id"),
                "type": msg_type,
                "date": msg.get("date"),
                "date_readable": datetime.fromtimestamp(msg.get("date", 0)).isoformat() if msg.get("date") else None,
                "edit_date": msg.get("edit_date"),
                "edit_date_readable": datetime.fromtimestamp(msg.get("edit_date", 0)).isoformat() if msg.get("edit_date") else None,
                "from": {
                    "id": msg.get("from", {}).get("id"),
                    "username": msg.get("from", {}).get("username"),
                    "first_name": msg.get("from", {}).get("first_name"),
                    "last_name": msg.get("from", {}).get("last_name"),
                    "is_bot": msg.get("from", {}).get("is_bot"),
                    "is_premium": msg.get("from", {}).get("is_premium"),
                } if msg.get("from") else None,
                "chat": {
                    "id": msg.get("chat", {}).get("id"),
                    "type": msg.get("chat", {}).get("type"),
                    "title": msg.get("chat", {}).get("title"),
                    "username": msg.get("chat", {}).get("username"),
                } if msg.get("chat") else None,
                "text": msg.get("text"),
                "caption": msg.get("caption"),
                "reply_to_message": {
                    "message_id": msg.get("reply_to_message", {}).get("message_id"),
                    "text": msg.get("reply_to_message", {}).get("text"),
                } if msg.get("reply_to_message") else None,
                "message_thread_id": msg.get("message_thread_id"),
            }
            messages.append(message)
    
    return messages


def load_and_extract_from_file(filepath: str) -> Dict[str, Any]:
    """Load JSON file and extract all messages"""
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        messages = []
        updates = []
        
        # Try different data structures
        if isinstance(data, dict):
            # Check for updates in various locations
            if "result" in data and isinstance(data["result"], list):
                updates = data["result"]
            elif "updates" in data:
                updates = data["updates"] if isinstance(data["updates"], list) else []
            elif "bot_1" in data:
                # Structured format
                for bot_key in ["bot_1", "bot_2"]:
                    if bot_key in data:
                        bot_data = data[bot_key]
                        if "updates" in bot_data:
                            if isinstance(bot_data["updates"], list):
                                updates.extend(bot_data["updates"])
                            elif isinstance(bot_data["updates"], dict) and "result" in bot_data["updates"]:
                                updates.extend(bot_data["updates"]["result"])
                        if "getUpdates" in bot_data and bot_data["getUpdates"]:
                            result = bot_data["getUpdates"].get("result", [])
                            if isinstance(result, list):
                                updates.extend(result)
                        if "messages" in bot_data:
                            messages.extend(bot_data["messages"])
            
            # Extract from raw updates
            if updates:
                extracted = extract_messages_from_updates(updates)
                messages.extend(extracted)
        
        return {
            "file": filepath,
            "updates": updates,
            "messages": messages,
            "total_updates": len(updates),
            "total_messages": len(messages),
        }
    except Exception as e:
        return {"file": filepath, "error": str(e)}


def combine_all_messages(data_sources: List[Dict]) -> Dict[str, Any]:
    """Combine messages from all data sources"""
    all_messages = []
    all_updates = []
    message_ids = set()  # To avoid duplicates
    
    for source in data_sources:
        if "error" in source:
            continue
        
        # Add updates
        for update in source.get("updates", []):
            if update not in all_updates:
                all_updates.append(update)
        
        # Add messages (deduplicate by message_id)
        for msg in source.get("messages", []):
            msg_id = msg.get("message_id")
            if msg_id and msg_id not in message_ids:
                message_ids.add(msg_id)
                all_messages.append(msg)
    
    # Sort by date
    all_messages.sort(key=lambda x: x.get("date", 0))
    
    # Organize by chat
    chats = defaultdict(list)
    for msg in all_messages:
        chat_id = msg.get("chat", {}).get("id")
        if chat_id:
            chats[chat_id].append(msg)
    
    return {
        "total_updates": len(all_updates),
        "total_messages": len(all_messages),
        "unique_message_ids": len(message_ids),
        "messages": all_messages,
        "chats": dict(chats),
        "sources": data_sources,
    }


def main():
    """Extract all messages from all available data files"""
    print("=" * 80)
    print("EXTRACTING ALL MESSAGES FROM EXISTING DATA")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    
    # Load data from all files
    print("[*] Loading data from files...")
    data_sources = []
    
    for filepath in DATA_FILES:
        print(f"    [*] Checking {filepath}...")
        data = load_and_extract_from_file(filepath)
        if data:
            if "error" in data:
                print(f"        [!] Error: {data['error']}")
            else:
                print(f"        [+] Found {data['total_updates']} updates, {data['total_messages']} messages")
                data_sources.append(data)
        else:
            print(f"        [-] File not found")
    
    # Combine all messages
    print("\n[*] Combining messages from all sources...")
    combined = combine_all_messages(data_sources)
    
    print(f"[+] Total updates: {combined['total_updates']}")
    print(f"[+] Total messages: {combined['total_messages']}")
    print(f"[+] Unique messages: {combined['unique_message_ids']}")
    print(f"[+] Chats: {len(combined['chats'])}")
    
    # Save results
    print("\n[*] Saving results...")
    
    output_file = f"all_messages_combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False, default=str)
    print(f"[+] Saved: {output_file}")
    
    # Generate summary report
    print("\n" + "=" * 80)
    print("MESSAGE SUMMARY BY CHAT")
    print("=" * 80)
    
    for chat_id, messages in combined["chats"].items():
        chat_info = messages[0].get("chat", {}) if messages else {}
        print(f"\nChat ID: {chat_id}")
        if chat_info.get("title"):
            print(f"  Title: {chat_info.get('title')}")
        print(f"  Messages: {len(messages)}")
        
        # Show message preview
        print(f"  Recent Messages:")
        for msg in messages[-10:]:  # Last 10
            date = msg.get("date_readable", "Unknown")
            from_user = msg.get("from", {})
            username = from_user.get("username", "N/A") if from_user else "N/A"
            text = msg.get("text", msg.get("caption", "[Media]"))
            text_preview = (text[:60] + "...") if text and len(text) > 60 else (text or "[No text]")
            try:
                print(f"    [{date}] @{username}: {text_preview}")
            except UnicodeEncodeError:
                # Fallback for encoding issues
                text_preview_safe = text_preview.encode('ascii', 'ignore').decode('ascii') if text_preview else "[No text]"
                print(f"    [{date}] @{username}: {text_preview_safe}")
    
    print("\n" + "=" * 80)
    print("COMPLETE!")
    print("=" * 80)
    
    return combined


if __name__ == "__main__":
    try:
        result = main()
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user")
    except Exception as e:
        print(f"\n[!] Error: {e}")
        import traceback
        traceback.print_exc()

