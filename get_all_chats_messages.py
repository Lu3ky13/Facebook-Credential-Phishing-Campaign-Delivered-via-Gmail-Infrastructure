#!/usr/bin/env python3
"""
Get All Chats and Messages from Bot Tokens
Extracts all chats the bots are in and retrieves all available messages
"""

import requests
import json
from datetime import datetime
from collections import defaultdict

# ==================================================
# CONFIG
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

REPORT_FILE = f"all_chats_messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
JSON_REPORT = f"all_chats_messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

# ==================================================
# TELEGRAM API FUNCTIONS
# ==================================================
def tg_api_call(bot_token, method, params=None):
    """Make Telegram Bot API call"""
    url = f"https://api.telegram.org/bot{bot_token}/{method}"
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e), "ok": False}


def get_all_updates(bot_token, limit=100, offset=0):
    """Get all available updates (messages) from bot"""
    all_updates = []
    current_offset = offset
    
    while True:
        result = tg_api_call(bot_token, "getUpdates", {
            "offset": current_offset,
            "limit": min(limit, 100),  # Telegram max is 100
            "timeout": 0
        })
        
        if not result.get("ok"):
            break
        
        updates = result.get("result", [])
        if not updates:
            break
        
        all_updates.extend(updates)
        current_offset = updates[-1]["update_id"] + 1
        
        # Safety limit
        if len(all_updates) >= 1000:
            break
    
    return all_updates


def extract_chat_ids_from_updates(updates):
    """Extract all unique chat IDs from updates"""
    chat_ids = set()
    
    for update in updates:
        # Message updates
        if "message" in update:
            chat = update["message"].get("chat", {})
            if chat.get("id"):
                chat_ids.add(chat["id"])
        
        # Edited message updates
        if "edited_message" in update:
            chat = update["edited_message"].get("chat", {})
            if chat.get("id"):
                chat_ids.add(chat["id"])
        
        # Channel post updates
        if "channel_post" in update:
            chat = update["channel_post"].get("chat", {})
            if chat.get("id"):
                chat_ids.add(chat["id"])
        
        # Edited channel post updates
        if "edited_channel_post" in update:
            chat = update["edited_channel_post"].get("chat", {})
            if chat.get("id"):
                chat_ids.add(chat["id"])
        
        # Callback query updates
        if "callback_query" in update and "message" in update["callback_query"]:
            chat = update["callback_query"]["message"].get("chat", {})
            if chat.get("id"):
                chat_ids.add(chat["id"])
        
        # Chat member updates
        if "chat_member" in update:
            chat = update["chat_member"].get("chat", {})
            if chat.get("id"):
                chat_ids.add(chat["id"])
        
        # My chat member updates
        if "my_chat_member" in update:
            chat = update["my_chat_member"].get("chat", {})
            if chat.get("id"):
                chat_ids.add(chat["id"])
    
    return list(chat_ids)


def get_chat_details(bot_token, chat_id):
    """Get detailed information about a chat"""
    details = {}
    
    # Basic chat info
    details["getChat"] = tg_api_call(bot_token, "getChat", {"chat_id": chat_id})
    
    # Member count
    details["getChatMemberCount"] = tg_api_call(bot_token, "getChatMemberCount", {"chat_id": chat_id})
    
    # Administrators
    details["getChatAdministrators"] = tg_api_call(bot_token, "getChatAdministrators", {"chat_id": chat_id})
    
    # Permissions
    details["getChatPermissions"] = tg_api_call(bot_token, "getChatPermissions", {"chat_id": chat_id})
    
    return details


def get_messages_for_chat(updates, chat_id):
    """Extract all messages for a specific chat from updates"""
    messages = []
    
    for update in updates:
        msg = None
        msg_type = None
        
        # Check different message types
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
        
        if msg and msg.get("chat", {}).get("id") == chat_id:
            message_data = {
                "update_id": update.get("update_id"),
                "message_id": msg.get("message_id"),
                "date": msg.get("date"),
                "date_readable": datetime.fromtimestamp(msg.get("date", 0)).isoformat() if msg.get("date") else None,
                "from": {
                    "id": msg.get("from", {}).get("id"),
                    "username": msg.get("from", {}).get("username"),
                    "first_name": msg.get("from", {}).get("first_name"),
                    "last_name": msg.get("from", {}).get("last_name"),
                    "is_bot": msg.get("from", {}).get("is_bot"),
                } if msg.get("from") else None,
                "text": msg.get("text"),
                "caption": msg.get("caption"),
                "photo": msg.get("photo"),
                "document": msg.get("document"),
                "video": msg.get("video"),
                "audio": msg.get("audio"),
                "voice": msg.get("voice"),
                "sticker": msg.get("sticker"),
                "location": msg.get("location"),
                "contact": msg.get("contact"),
                "entities": msg.get("entities"),
                "reply_to_message": {
                    "message_id": msg.get("reply_to_message", {}).get("message_id"),
                    "text": msg.get("reply_to_message", {}).get("text"),
                } if msg.get("reply_to_message") else None,
                "forward_from": msg.get("forward_from"),
                "forward_from_chat": msg.get("forward_from_chat"),
                "type": msg_type,
            }
            messages.append(message_data)
    
    # Sort by date
    messages.sort(key=lambda x: x.get("date", 0))
    return messages


def format_message(msg):
    """Format a message for display"""
    lines = []
    
    timestamp = msg.get("date_readable", "Unknown time")
    from_user = msg.get("from", {})
    username = from_user.get("username", "N/A") if from_user else "N/A"
    user_id = from_user.get("id", "N/A") if from_user else "N/A"
    first_name = from_user.get("first_name", "") if from_user else ""
    last_name = from_user.get("last_name", "") if from_user else ""
    full_name = f"{first_name} {last_name}".strip() or "N/A"
    
    lines.append(f"  [{timestamp}] @{username} ({user_id}) - {full_name}")
    
    if msg.get("text"):
        text = msg["text"][:200] + "..." if len(msg["text"]) > 200 else msg["text"]
        lines.append(f"    Text: {text}")
    
    if msg.get("caption"):
        lines.append(f"    Caption: {msg['caption']}")
    
    if msg.get("photo"):
        lines.append(f"    [PHOTO] {len(msg['photo'])} sizes")
    
    if msg.get("document"):
        doc = msg["document"]
        lines.append(f"    [DOCUMENT] {doc.get('file_name', 'N/A')} ({doc.get('file_size', 0)} bytes)")
    
    if msg.get("video"):
        lines.append(f"    [VIDEO]")
    
    if msg.get("audio"):
        lines.append(f"    [AUDIO]")
    
    if msg.get("voice"):
        lines.append(f"    [VOICE]")
    
    if msg.get("sticker"):
        lines.append(f"    [STICKER]")
    
    if msg.get("location"):
        loc = msg["location"]
        lines.append(f"    [LOCATION] Lat: {loc.get('latitude')}, Lon: {loc.get('longitude')}")
    
    if msg.get("reply_to_message"):
        lines.append(f"    [REPLY TO] Message ID: {msg['reply_to_message']['message_id']}")
    
    return "\n".join(lines)


def generate_report(all_data):
    """Generate comprehensive report"""
    report = []
    report.append("=" * 80)
    report.append("ALL CHATS AND MESSAGES REPORT")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    report.append("")
    
    for bot_name, bot_data in all_data.items():
        report.append("=" * 80)
        report.append(f"BOT: {bot_name.upper()}")
        report.append("=" * 80)
        
        bot_info = bot_data.get("bot_info", {})
        if bot_info.get("getMe", {}).get("ok"):
            me = bot_info["getMe"]["result"]
            report.append(f"Bot ID: {me.get('id')}")
            report.append(f"Username: @{me.get('username')}")
            report.append(f"Name: {me.get('first_name')}")
        report.append("")
        
        # Chats
        chats = bot_data.get("chats", {})
        report.append(f"[*] Found {len(chats)} unique chat(s)")
        report.append("")
        
        for chat_id, chat_data in chats.items():
            chat_info = chat_data.get("chat_info", {})
            messages = chat_data.get("messages", [])
            
            # Chat header
            report.append("-" * 80)
            report.append(f"CHAT ID: {chat_id}")
            report.append("-" * 80)
            
            if chat_info.get("getChat", {}).get("ok"):
                chat = chat_info["getChat"]["result"]
                report.append(f"Type: {chat.get('type')}")
                report.append(f"Title: {chat.get('title', 'N/A')}")
                report.append(f"Username: @{chat.get('username', 'N/A')}")
                report.append(f"Description: {chat.get('description', 'N/A')}")
                if chat.get("invite_link"):
                    report.append(f"Invite Link: {chat['invite_link']}")
            
            if chat_info.get("getChatMemberCount", {}).get("ok"):
                report.append(f"Member Count: {chat_info['getChatMemberCount']['result']}")
            
            report.append(f"Total Messages Found: {len(messages)}")
            report.append("")
            
            # Messages
            if messages:
                report.append("MESSAGES:")
                report.append("")
                for msg in messages:
                    report.append(format_message(msg))
                    report.append("")
            else:
                report.append("No messages found for this chat.")
                report.append("")
        
        report.append("")
    
    report.append("=" * 80)
    report.append("END OF REPORT")
    report.append("=" * 80)
    
    return "\n".join(report)


# ==================================================
# MAIN EXECUTION
# ==================================================
def main():
    print("\n" + "=" * 80)
    print("GETTING ALL CHATS AND MESSAGES")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    
    all_data = {}
    
    for bot_name, bot_token in BOT_TOKENS.items():
        print(f"[*] Processing {bot_name}...")
        bot_data = {
            "bot_info": {},
            "updates": [],
            "chats": {}
        }
        
        # Get bot info
        print(f"    [+] Getting bot information...")
        bot_data["bot_info"]["getMe"] = tg_api_call(bot_token, "getMe")
        if bot_data["bot_info"]["getMe"].get("ok"):
            me = bot_data["bot_info"]["getMe"]["result"]
            print(f"        Bot: @{me.get('username')} ({me.get('id')})")
        
        # Get all updates (messages)
        print(f"    [+] Fetching all updates (messages)...")
        updates = get_all_updates(bot_token)
        bot_data["updates"] = updates
        print(f"        Found {len(updates)} update(s)")
        
        # Extract chat IDs
        print(f"    [+] Extracting chat IDs...")
        chat_ids = extract_chat_ids_from_updates(updates)
        print(f"        Found {len(chat_ids)} unique chat(s)")
        
        # Get details for each chat
        for chat_id in chat_ids:
            print(f"    [+] Processing chat {chat_id}...")
            chat_data = {
                "chat_info": {},
                "messages": []
            }
            
            # Get chat details
            chat_data["chat_info"] = get_chat_details(bot_token, chat_id)
            if chat_data["chat_info"].get("getChat", {}).get("ok"):
                chat = chat_data["chat_info"]["getChat"]["result"]
                print(f"        Chat: {chat.get('title', chat_id)} ({chat.get('type')})")
            
            # Get messages for this chat
            messages = get_messages_for_chat(updates, chat_id)
            chat_data["messages"] = messages
            print(f"        Messages: {len(messages)}")
            
            bot_data["chats"][str(chat_id)] = chat_data
        
        all_data[bot_name] = bot_data
        print("")
    
    # Generate reports
    print("[*] Generating reports...")
    text_report = generate_report(all_data)
    
    # Save text report
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(text_report)
    
    # Save JSON report
    with open(JSON_REPORT, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "data": all_data
        }, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"[+] Text report saved: {REPORT_FILE}")
    print(f"[+] JSON report saved: {JSON_REPORT}")
    print("\n" + text_report)
    
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


