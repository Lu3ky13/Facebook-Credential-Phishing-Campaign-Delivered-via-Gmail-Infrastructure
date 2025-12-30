#!/usr/bin/env python3
"""
Complete Message Extraction - Get ALL messages including those in reply_to_message
Extracts every message from all available sources including nested messages
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Set
from collections import defaultdict

# ==================================================
# CONFIGURATION
# ==================================================
DATA_FILES = [
    "11.json",
    "11_formatted.json",
    "telegram_data_20251230_174317.json",
    "all_chats_messages_20251230_172910.json",
    "all_old_messages_20251230_174756.json",
    "all_messages_combined_20251230_175007.json",
]

# ==================================================
# EXTRACTION FUNCTIONS
# ==================================================
def extract_message_from_object(msg_obj: Dict, source: str = "unknown") -> Dict:
    """Extract message data from any message object"""
    if not isinstance(msg_obj, dict):
        return None
    
    message = {
        "message_id": msg_obj.get("message_id"),
        "date": msg_obj.get("date"),
        "date_readable": datetime.fromtimestamp(msg_obj.get("date", 0)).isoformat() if msg_obj.get("date") else None,
        "edit_date": msg_obj.get("edit_date"),
        "edit_date_readable": datetime.fromtimestamp(msg_obj.get("edit_date", 0)).isoformat() if msg_obj.get("edit_date") else None,
        "from": {
            "id": msg_obj.get("from", {}).get("id"),
            "username": msg_obj.get("from", {}).get("username"),
            "first_name": msg_obj.get("from", {}).get("first_name"),
            "last_name": msg_obj.get("from", {}).get("last_name"),
            "is_bot": msg_obj.get("from", {}).get("is_bot"),
            "is_premium": msg_obj.get("from", {}).get("is_premium"),
        } if msg_obj.get("from") else None,
        "chat": {
            "id": msg_obj.get("chat", {}).get("id"),
            "type": msg_obj.get("chat", {}).get("type"),
            "title": msg_obj.get("chat", {}).get("title"),
            "username": msg_obj.get("chat", {}).get("username"),
            "is_forum": msg_obj.get("chat", {}).get("is_forum"),
        } if msg_obj.get("chat") else None,
        "text": msg_obj.get("text"),
        "caption": msg_obj.get("caption"),
        "message_thread_id": msg_obj.get("message_thread_id"),
        "source": source,
    }
    
    return message if message.get("message_id") else None


def extract_all_messages_recursive(obj: Any, messages: List[Dict], message_ids: Set[int], source: str = "unknown", depth: int = 0) -> None:
    """Recursively extract all messages from any object structure"""
    if depth > 10:  # Safety limit
        return
    
    if isinstance(obj, dict):
        # Check if this is a message object
        if "message_id" in obj and "date" in obj:
            msg = extract_message_from_object(obj, source)
            if msg and msg["message_id"] not in message_ids:
                message_ids.add(msg["message_id"])
                messages.append(msg)
        
        # Check for reply_to_message (nested message)
        if "reply_to_message" in obj and isinstance(obj["reply_to_message"], dict):
            extract_all_messages_recursive(obj["reply_to_message"], messages, message_ids, f"{source}_reply", depth + 1)
        
        # Check for forward_from (forwarded message info)
        if "forward_from" in obj:
            # This is user info, not a full message, but we can note it
            pass
        
        # Recursively check all values
        for value in obj.values():
            extract_all_messages_recursive(value, messages, message_ids, source, depth + 1)
    
    elif isinstance(obj, list):
        for item in obj:
            extract_all_messages_recursive(item, messages, message_ids, source, depth + 1)


def load_and_extract_all_messages(filepath: str) -> Dict[str, Any]:
    """Load JSON file and extract ALL messages including nested ones"""
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        messages = []
        message_ids = set()
        updates = []
        
        # Extract from various structures
        if isinstance(data, dict):
            # Check for updates in result
            if "result" in data and isinstance(data["result"], list):
                updates = data["result"]
            
            # Check for bot_1, bot_2 structure
            for bot_key in ["bot_1", "bot_2"]:
                if bot_key in data:
                    bot_data = data[bot_key]
                    # Check getUpdates
                    if "getUpdates" in bot_data and bot_data["getUpdates"]:
                        result = bot_data["getUpdates"].get("result", [])
                        if isinstance(result, list):
                            updates.extend(result)
                    # Check updates
                    if "updates" in bot_data:
                        if isinstance(bot_data["updates"], list):
                            updates.extend(bot_data["updates"])
                        elif isinstance(bot_data["updates"], dict) and "result" in bot_data["updates"]:
                            updates.extend(bot_data["updates"]["result"])
                    # Check messages
                    if "messages" in bot_data and isinstance(bot_data["messages"], list):
                        for msg in bot_data["messages"]:
                            if isinstance(msg, dict) and msg.get("message_id"):
                                msg_obj = extract_message_from_object(msg, f"{bot_key}_messages")
                                if msg_obj and msg_obj["message_id"] not in message_ids:
                                    message_ids.add(msg_obj["message_id"])
                                    messages.append(msg_obj)
            
            # Recursively extract from entire structure
            extract_all_messages_recursive(data, messages, message_ids, filepath)
        
        elif isinstance(data, list):
            # If data is directly a list
            extract_all_messages_recursive(data, messages, message_ids, filepath)
        
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
    message_ids = set()
    
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
    
    # Organize by user
    users = defaultdict(list)
    for msg in all_messages:
        user_id = msg.get("from", {}).get("id")
        if user_id:
            users[user_id].append(msg)
    
    return {
        "total_updates": len(all_updates),
        "total_messages": len(all_messages),
        "unique_message_ids": len(message_ids),
        "messages": all_messages,
        "chats": dict(chats),
        "users": dict(users),
        "sources": [s.get("file") for s in data_sources if "error" not in s],
    }


def main():
    """Extract ALL messages from all available data files"""
    print("=" * 80)
    print("COMPLETE MESSAGE EXTRACTION - ALL SOURCES")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    print("Extracting from:")
    print("  - Direct messages")
    print("  - Messages in reply_to_message fields")
    print("  - All nested message structures")
    print("  - All available data files\n")
    
    # Load data from all files
    print("[*] Loading and extracting from all files...")
    data_sources = []
    
    for filepath in DATA_FILES:
        print(f"    [*] Processing {filepath}...")
        data = load_and_extract_all_messages(filepath)
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
    print(f"[+] Unique message IDs: {combined['unique_message_ids']}")
    print(f"[+] Chats: {len(combined['chats'])}")
    print(f"[+] Users: {len(combined['users'])}")
    
    # Save results
    print("\n[*] Saving results...")
    
    output_file = f"ALL_MESSAGES_COMPLETE_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False, default=str)
    print(f"[+] Saved: {output_file}")
    
    # Generate summary
    print("\n" + "=" * 80)
    print("COMPLETE MESSAGE SUMMARY")
    print("=" * 80)
    
    for chat_id, messages in combined["chats"].items():
        chat_info = messages[0].get("chat", {}) if messages else {}
        print(f"\n Chat ID: {chat_id}")
        if chat_info.get("title"):
            print(f"   Title: {chat_info.get('title')}")
        print(f"   Total Messages: {len(messages)}")
        
        # Show all messages
        print(f"   Messages:")
        for msg in messages:
            date = msg.get("date_readable", "Unknown")
            from_user = msg.get("from", {})
            username = from_user.get("username", "N/A") if from_user else "N/A"
            text = msg.get("text", msg.get("caption", "[Media/Other]"))
            text_preview = (text[:80] + "...") if text and len(text) > 80 else (text or "[No text]")
            source = msg.get("source", "unknown")
            print(f"     [{date}] @{username} ({source}): {text_preview}")
    
    print("\n" + "=" * 80)
    print("COMPLETE!")
    print("=" * 80)
    print(f"\nAll messages saved to: {output_file}")
    
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


