#!/usr/bin/env python3
"""
Get All Old Messages from Telegram Bots
Retrieves all historical messages/updates from bot tokens
"""

import requests
import json
from datetime import datetime
from typing import Dict, Any, List

# ==================================================
# CONFIGURATION
# ==================================================
CONFIG = {
    "bot_token": "7871555324:AAHUSIAw2N0psJlFbJ7sfkq4D2L6e9qofGU",
    "bot_token_journey": "8053731074:AAEWnpsgr82u-yoKWONk2eA1mqiVKBhL4bY",
    "chat_id": "-1003162196749",
}

BOT_TOKENS = {
    "bot_1": CONFIG["bot_token"],
    "bot_2": CONFIG["bot_token_journey"],
}

# ==================================================
# TELEGRAM API FUNCTIONS
# ==================================================
def telegram_api_call(bot_token: str, method: str, params: Dict = None) -> Dict[str, Any]:
    """Make a call to Telegram Bot API"""
    url = f"https://api.telegram.org/bot{bot_token}/{method}"
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_all_updates(bot_token: str, max_updates: int = 10000) -> List[Dict]:
    """
    Get ALL available updates (messages) from bot
    
    Args:
        bot_token: Bot token
        max_updates: Maximum number of updates to retrieve (default: 10000)
    
    Returns:
        List of all update objects
    """
    all_updates = []
    offset = 0
    batch_count = 0
    
    print(f"    [*] Starting to fetch updates (offset: {offset})...")
    
    while len(all_updates) < max_updates:
        # Get updates in batches of 100 (Telegram max)
        result = telegram_api_call(bot_token, "getUpdates", {
            "offset": offset,
            "limit": 100,
            "timeout": 0
        })
        
        if not result.get("ok"):
            error = result.get("error_code") or result.get("description", "Unknown error")
            print(f"    [!] Error: {error}")
            break
        
        updates = result.get("result", [])
        
        if not updates:
            print(f"    [+] No more updates available")
            break
        
        all_updates.extend(updates)
        batch_count += 1
        
        # Update offset to the next update_id + 1
        offset = updates[-1]["update_id"] + 1
        
        print(f"    [+] Batch {batch_count}: Got {len(updates)} updates (Total: {len(all_updates)})")
        
        # If we got less than 100, we've reached the end
        if len(updates) < 100:
            print(f"    [+] Reached end of updates")
            break
        
        # Safety check
        if len(all_updates) >= max_updates:
            print(f"    [+] Reached maximum limit ({max_updates})")
            break
    
    return all_updates[:max_updates]


def extract_messages_from_updates(updates: List[Dict]) -> List[Dict]:
    """Extract and organize all messages from updates"""
    messages = []
    
    for update in updates:
        msg_data = None
        msg_type = None
        
        # Check different message types
        if "message" in update:
            msg_data = update["message"]
            msg_type = "message"
        elif "edited_message" in update:
            msg_data = update["edited_message"]
            msg_type = "edited_message"
        elif "channel_post" in update:
            msg_data = update["channel_post"]
            msg_type = "channel_post"
        elif "edited_channel_post" in update:
            msg_data = update["edited_channel_post"]
            msg_type = "edited_channel_post"
        elif "callback_query" in update and "message" in update["callback_query"]:
            msg_data = update["callback_query"]["message"]
            msg_type = "callback_query"
        
        if msg_data:
            # Extract message information
            message = {
                "update_id": update.get("update_id"),
                "message_id": msg_data.get("message_id"),
                "type": msg_type,
                "date": msg_data.get("date"),
                "date_readable": datetime.fromtimestamp(msg_data.get("date", 0)).isoformat() if msg_data.get("date") else None,
                "edit_date": msg_data.get("edit_date"),
                "edit_date_readable": datetime.fromtimestamp(msg_data.get("edit_date", 0)).isoformat() if msg_data.get("edit_date") else None,
                "from": {
                    "id": msg_data.get("from", {}).get("id"),
                    "username": msg_data.get("from", {}).get("username"),
                    "first_name": msg_data.get("from", {}).get("first_name"),
                    "last_name": msg_data.get("from", {}).get("last_name"),
                    "is_bot": msg_data.get("from", {}).get("is_bot"),
                    "is_premium": msg_data.get("from", {}).get("is_premium"),
                } if msg_data.get("from") else None,
                "chat": {
                    "id": msg_data.get("chat", {}).get("id"),
                    "type": msg_data.get("chat", {}).get("type"),
                    "title": msg_data.get("chat", {}).get("title"),
                    "username": msg_data.get("chat", {}).get("username"),
                    "is_forum": msg_data.get("chat", {}).get("is_forum"),
                } if msg_data.get("chat") else None,
                "text": msg_data.get("text"),
                "caption": msg_data.get("caption"),
                "photo": msg_data.get("photo"),
                "document": msg_data.get("document"),
                "video": msg_data.get("video"),
                "audio": msg_data.get("audio"),
                "voice": msg_data.get("voice"),
                "sticker": msg_data.get("sticker"),
                "location": msg_data.get("location"),
                "contact": msg_data.get("contact"),
                "reply_to_message": {
                    "message_id": msg_data.get("reply_to_message", {}).get("message_id"),
                    "text": msg_data.get("reply_to_message", {}).get("text")[:200] if msg_data.get("reply_to_message", {}).get("text") else None,
                } if msg_data.get("reply_to_message") else None,
                "forward_from": msg_data.get("forward_from"),
                "forward_from_chat": msg_data.get("forward_from_chat"),
                "entities": msg_data.get("entities"),
                "message_thread_id": msg_data.get("message_thread_id"),
            }
            messages.append(message)
    
    # Sort by date (oldest first)
    messages.sort(key=lambda x: x.get("date", 0))
    
    return messages


def organize_messages_by_chat(messages: List[Dict]) -> Dict[int, List[Dict]]:
    """Organize messages by chat ID"""
    chats = {}
    
    for msg in messages:
        chat_id = msg.get("chat", {}).get("id")
        if chat_id:
            if chat_id not in chats:
                chats[chat_id] = []
            chats[chat_id].append(msg)
    
    return chats


def generate_report(all_data: Dict) -> str:
    """Generate a text report of all messages"""
    report = []
    report.append("=" * 80)
    report.append("ALL OLD MESSAGES REPORT")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    report.append("")
    
    for bot_name, bot_data in all_data.items():
        if bot_name == "metadata":
            continue
        
        report.append("=" * 80)
        report.append(f"BOT: {bot_name.upper()}")
        report.append("=" * 80)
        
        updates = bot_data.get("updates", [])
        messages = bot_data.get("messages", [])
        chats = bot_data.get("chats", {})
        
        report.append(f"Total Updates: {len(updates)}")
        report.append(f"Total Messages: {len(messages)}")
        report.append(f"Chats: {len(chats)}")
        report.append("")
        
        # Messages by chat
        for chat_id, chat_messages in chats.items():
            chat_info = chat_messages[0].get("chat", {}) if chat_messages else {}
            report.append("-" * 80)
            report.append(f"CHAT ID: {chat_id}")
            if chat_info.get("title"):
                report.append(f"Title: {chat_info.get('title')}")
            if chat_info.get("username"):
                report.append(f"Username: @{chat_info.get('username')}")
            report.append(f"Messages: {len(chat_messages)}")
            report.append("")
            
            # Show first few messages
            for msg in chat_messages[:5]:
                date = msg.get("date_readable", "Unknown")
                from_user = msg.get("from", {})
                username = from_user.get("username", "N/A") if from_user else "N/A"
                text = msg.get("text", msg.get("caption", "[Media/Other]"))
                text_preview = (text[:100] + "...") if text and len(text) > 100 else (text or "[No text]")
                
                report.append(f"  [{date}] @{username}: {text_preview}")
            
            if len(chat_messages) > 5:
                report.append(f"  ... and {len(chat_messages) - 5} more messages")
            report.append("")
    
    report.append("=" * 80)
    report.append("END OF REPORT")
    report.append("=" * 80)
    
    return "\n".join(report)


# ==================================================
# MAIN EXECUTION
# ==================================================
def main():
    """Get all old messages from all bots"""
    print("=" * 80)
    print("GETTING ALL OLD MESSAGES")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    
    all_data = {
        "metadata": {
            "extraction_date": datetime.now().isoformat(),
            "bots_analyzed": list(BOT_TOKENS.keys())
        }
    }
    
    # Process each bot
    for bot_name, bot_token in BOT_TOKENS.items():
        print(f"\n[*] Processing {bot_name}...")
        bot_data = {
            "updates": [],
            "messages": [],
            "chats": {}
        }
        
        # Get all updates
        print(f"    [*] Fetching all updates...")
        updates = get_all_updates(bot_token, max_updates=10000)
        bot_data["updates"] = updates
        print(f"    [+] Total updates retrieved: {len(updates)}")
        
        # Extract messages
        print(f"    [*] Extracting messages from updates...")
        messages = extract_messages_from_updates(updates)
        bot_data["messages"] = messages
        print(f"    [+] Total messages extracted: {len(messages)}")
        
        # Organize by chat
        print(f"    [*] Organizing messages by chat...")
        chats = organize_messages_by_chat(messages)
        bot_data["chats"] = chats
        print(f"    [+] Messages in {len(chats)} chat(s)")
        
        all_data[bot_name] = bot_data
        print(f"    [+] {bot_name} complete!")
    
    # Generate reports
    print("\n[*] Generating reports...")
    
    # JSON report
    json_file = f"all_old_messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False, default=str)
    print(f"[+] JSON report saved: {json_file}")
    
    # Text report
    text_report = generate_report(all_data)
    txt_file = f"all_old_messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write(text_report)
    print(f"[+] Text report saved: {txt_file}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    for bot_name, bot_data in all_data.items():
        if bot_name == "metadata":
            continue
        print(f"{bot_name}:")
        print(f"  Updates: {len(bot_data.get('updates', []))}")
        print(f"  Messages: {len(bot_data.get('messages', []))}")
        print(f"  Chats: {len(bot_data.get('chats', {}))}")
    
    print("\n" + "=" * 80)
    print("COMPLETE!")
    print("=" * 80)
    
    return all_data


if __name__ == "__main__":
    try:
        all_data = main()
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user")
    except Exception as e:
        print(f"\n[!] Error: {e}")
        import traceback
        traceback.print_exc()


