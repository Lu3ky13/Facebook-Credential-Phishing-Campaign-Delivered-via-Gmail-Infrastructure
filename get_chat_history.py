#!/usr/bin/bin/python3
"""
Get Chat History - Alternative method to retrieve messages
Uses available Telegram Bot API methods to get chat messages
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


def get_all_updates_with_pagination(bot_token: str) -> List[Dict]:
    """
    Get ALL updates by paginating through all available updates
    Note: This will consume all updates, so they won't be available again
    """
    all_updates = []
    offset = 0
    max_attempts = 1000  # Safety limit
    
    print(f"    [*] Fetching all updates (this will consume them)...")
    
    for attempt in range(max_attempts):
        result = telegram_api_call(bot_token, "getUpdates", {
            "offset": offset,
            "limit": 100,
            "timeout": 0
        })
        
        if not result.get("ok"):
            error_code = result.get("error_code")
            description = result.get("description", "Unknown error")
            print(f"    [!] Error {error_code}: {description}")
            break
        
        updates = result.get("result", [])
        
        if not updates:
            print(f"    [+] No more updates (attempt {attempt + 1})")
            break
        
        all_updates.extend(updates)
        offset = updates[-1]["update_id"] + 1
        
        print(f"    [+] Batch {attempt + 1}: Got {len(updates)} updates (Total: {len(all_updates)})")
        
        if len(updates) < 100:
            break
    
    return all_updates


def extract_all_message_data(updates: List[Dict]) -> Dict[str, Any]:
    """Extract comprehensive data from all updates"""
    messages = []
    chats = {}
    users = {}
    
    for update in updates:
        # Extract message from different update types
        msg = None
        if "message" in update:
            msg = update["message"]
        elif "edited_message" in update:
            msg = update["edited_message"]
        elif "channel_post" in update:
            msg = update["channel_post"]
        elif "edited_channel_post" in update:
            msg = update["edited_channel_post"]
        elif "callback_query" in update and "message" in update["callback_query"]:
            msg = update["callback_query"]["message"]
        
        if msg:
            # Store chat info
            chat = msg.get("chat", {})
            chat_id = chat.get("id")
            if chat_id and chat_id not in chats:
                chats[chat_id] = {
                    "id": chat_id,
                    "type": chat.get("type"),
                    "title": chat.get("title"),
                    "username": chat.get("username"),
                    "is_forum": chat.get("is_forum"),
                }
            
            # Store user info
            user = msg.get("from", {})
            if user:
                user_id = user.get("id")
                if user_id and user_id not in users:
                    users[user_id] = {
                        "id": user_id,
                        "username": user.get("username"),
                        "first_name": user.get("first_name"),
                        "last_name": user.get("last_name"),
                        "is_bot": user.get("is_bot"),
                        "is_premium": user.get("is_premium"),
                    }
            
            # Extract message
            message = {
                "update_id": update.get("update_id"),
                "message_id": msg.get("message_id"),
                "date": msg.get("date"),
                "date_readable": datetime.fromtimestamp(msg.get("date", 0)).isoformat() if msg.get("date") else None,
                "edit_date": msg.get("edit_date"),
                "edit_date_readable": datetime.fromtimestamp(msg.get("edit_date", 0)).isoformat() if msg.get("edit_date") else None,
                "from_user_id": user.get("id") if user else None,
                "chat_id": chat_id,
                "text": msg.get("text"),
                "caption": msg.get("caption"),
                "has_photo": bool(msg.get("photo")),
                "has_document": bool(msg.get("document")),
                "has_video": bool(msg.get("video")),
                "has_audio": bool(msg.get("audio")),
                "has_voice": bool(msg.get("voice")),
                "has_sticker": bool(msg.get("sticker")),
                "has_location": bool(msg.get("location")),
                "has_contact": bool(msg.get("contact")),
                "is_reply": bool(msg.get("reply_to_message")),
                "reply_to_message_id": msg.get("reply_to_message", {}).get("message_id") if msg.get("reply_to_message") else None,
                "message_thread_id": msg.get("message_thread_id"),
                "entities": msg.get("entities"),
            }
            messages.append(message)
    
    # Sort by date
    messages.sort(key=lambda x: x.get("date", 0))
    
    return {
        "messages": messages,
        "chats": chats,
        "users": users,
    }


def main():
    """Get all old messages from all bots"""
    print("=" * 80)
    print("GETTING ALL OLD MESSAGES FROM CHAT HISTORY")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    print("NOTE: getUpdates only returns unprocessed updates.")
    print("Once retrieved, updates are consumed and won't appear again.\n")
    
    all_data = {
        "metadata": {
            "extraction_date": datetime.now().isoformat(),
            "note": "getUpdates only returns unprocessed updates. Old messages that were already processed won't appear."
        }
    }
    
    # Process each bot
    for bot_name, bot_token in BOT_TOKENS.items():
        print(f"\n[*] Processing {bot_name}...")
        
        # Get bot info first
        bot_info = telegram_api_call(bot_token, "getMe")
        if bot_info.get("ok"):
            bot = bot_info["result"]
            print(f"    Bot: @{bot.get('username')} (ID: {bot.get('id')})")
        
        # Get all available updates
        print(f"    [*] Getting all available updates...")
        updates = get_all_updates_with_pagination(bot_token)
        print(f"    [+] Retrieved {len(updates)} update(s)")
        
        # Extract data
        if updates:
            print(f"    [*] Extracting message data...")
            extracted = extract_all_message_data(updates)
            
            bot_data = {
                "bot_info": bot_info,
                "total_updates": len(updates),
                "messages": extracted["messages"],
                "chats": extracted["chats"],
                "users": extracted["users"],
                "raw_updates": updates,  # Include raw updates for reference
            }
            
            print(f"    [+] Extracted {len(extracted['messages'])} message(s)")
            print(f"    [+] Found {len(extracted['chats'])} chat(s)")
            print(f"    [+] Found {len(extracted['users'])} user(s)")
        else:
            bot_data = {
                "bot_info": bot_info,
                "total_updates": 0,
                "messages": [],
                "chats": {},
                "users": {},
                "raw_updates": [],
            }
            print(f"    [!] No updates available (may have been consumed already)")
        
        all_data[bot_name] = bot_data
    
    # Save results
    print("\n[*] Saving results...")
    
    json_file = f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False, default=str)
    print(f"[+] Saved: {json_file}")
    
    # Generate summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    for bot_name, bot_data in all_data.items():
        if bot_name == "metadata":
            continue
        print(f"\n{bot_name}:")
        print(f"  Updates: {bot_data.get('total_updates', 0)}")
        print(f"  Messages: {len(bot_data.get('messages', []))}")
        print(f"  Chats: {len(bot_data.get('chats', {}))}")
        print(f"  Users: {len(bot_data.get('users', {}))}")
        
        # Show message preview
        messages = bot_data.get("messages", [])
        if messages:
            print(f"\n  Recent Messages:")
            for msg in messages[-5:]:  # Last 5
                date = msg.get("date_readable", "Unknown")
                text = msg.get("text", msg.get("caption", "[Media]"))
                text_preview = (text[:60] + "...") if text and len(text) > 60 else (text or "[No text]")
                print(f"    [{date}] {text_preview}")
    
    print("\n" + "=" * 80)
    print("NOTE: To get OLD messages that were already processed,")
    print("you need to access them before they're consumed, or use")
    print("a bot that was running and logging messages in real-time.")
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


