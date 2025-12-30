#!/usr/bin/env python3
"""
Complete JSON formatter - extracts all JSON from mixed text and creates clean structured output
"""

import json
import re
from datetime import datetime

def extract_all_json(text):
    """Extract all valid JSON objects from text"""
    json_objects = []
    
    # Find all JSON objects by matching balanced braces
    i = 0
    while i < len(text):
        if text[i] == '{':
            start = i
            depth = 0
            in_string = False
            escape = False
            
            for j in range(i, len(text)):
                char = text[j]
                
                if escape:
                    escape = False
                    continue
                
                if char == '\\':
                    escape = True
                    continue
                
                if char == '"' and not escape:
                    in_string = not in_string
                    continue
                
                if not in_string:
                    if char == '{':
                        depth += 1
                    elif char == '}':
                        depth -= 1
                        if depth == 0:
                            json_str = text[start:j+1]
                            try:
                                json_obj = json.loads(json_str)
                                json_objects.append(json_obj)
                            except json.JSONDecodeError:
                                pass
                            i = j + 1
                            break
            else:
                i += 1
        else:
            i += 1
    
    return json_objects

def organize_all_data(json_objects):
    """Organize all extracted JSON into comprehensive structure"""
    result = {
        "metadata": {
            "extraction_date": datetime.now().isoformat(),
            "total_objects": len(json_objects)
        },
        "bot_1": {
            "getMe": None,
            "getWebhookInfo": None,
            "getMyCommands": None,
            "getUpdates": None,
            "getChat": None,
            "getChatMemberCount": None,
            "getChatAdministrators": None
        },
        "bot_2": {
            "getMe": None,
            "getWebhookInfo": None,
            "getMyCommands": None,
            "getUpdates": None,
            "getChat": None,
            "getChatMemberCount": None,
            "getChatAdministrators": None
        },
        "ipinfo": []
    }
    
    bot_1_id = 7871555324
    bot_2_id = 8053731074
    
    # Track which responses we've seen
    bot_1_seen = {"getMe": False, "getWebhookInfo": False, "getMyCommands": False, 
                  "getChat": False, "getChatMemberCount": False, "getChatAdministrators": False}
    bot_2_seen = {"getMe": False, "getWebhookInfo": False, "getMyCommands": False,
                  "getChat": False, "getChatMemberCount": False, "getChatAdministrators": False}
    
    for obj in json_objects:
        if not isinstance(obj, dict):
            continue
        
        # Check if it's IPinfo (direct JSON, no "ok" field, has "ip" and "country")
        if "ip" in obj and "country" in obj and "ok" not in obj:
            result["ipinfo"].append(obj)
            continue
        
        api_result = obj.get("result")
        if not api_result:
            continue
        
        # Check if it's bot info (getMe)
        if isinstance(api_result, dict) and api_result.get("is_bot"):
            bot_id = api_result.get("id")
            if bot_id == bot_1_id and not bot_1_seen["getMe"]:
                result["bot_1"]["getMe"] = obj
                bot_1_seen["getMe"] = True
            elif bot_id == bot_2_id and not bot_2_seen["getMe"]:
                result["bot_2"]["getMe"] = obj
                bot_2_seen["getMe"] = True
        
        # Check if it's webhook info
        elif isinstance(api_result, dict) and ("url" in api_result or "pending_update_count" in api_result):
            # Determine bot from context - check if we've seen bot_1's getMe
            if result["bot_1"]["getMe"] and not bot_1_seen["getWebhookInfo"]:
                result["bot_1"]["getWebhookInfo"] = obj
                bot_1_seen["getWebhookInfo"] = True
            elif result["bot_2"]["getMe"] and not bot_2_seen["getWebhookInfo"]:
                result["bot_2"]["getWebhookInfo"] = obj
                bot_2_seen["getWebhookInfo"] = True
        
        # Check if it's commands
        elif isinstance(api_result, list) and (len(api_result) == 0 or (len(api_result) > 0 and isinstance(api_result[0], dict) and "command" in api_result[0])):
            if result["bot_1"]["getMe"] and not bot_1_seen["getMyCommands"]:
                result["bot_1"]["getMyCommands"] = obj
                bot_1_seen["getMyCommands"] = True
            elif result["bot_2"]["getMe"] and not bot_2_seen["getMyCommands"]:
                result["bot_2"]["getMyCommands"] = obj
                bot_2_seen["getMyCommands"] = True
        
        # Check if it's updates
        elif isinstance(api_result, list) and len(api_result) > 0 and isinstance(api_result[0], dict) and "update_id" in api_result[0]:
            if not result["bot_1"]["getUpdates"]:
                result["bot_1"]["getUpdates"] = obj
            elif not result["bot_2"]["getUpdates"]:
                result["bot_2"]["getUpdates"] = obj
        
        # Check if it's chat info
        elif isinstance(api_result, dict) and api_result.get("type") in ["supergroup", "group", "channel"]:
            if not bot_1_seen["getChat"]:
                result["bot_1"]["getChat"] = obj
                bot_1_seen["getChat"] = True
            elif not bot_2_seen["getChat"]:
                result["bot_2"]["getChat"] = obj
                bot_2_seen["getChat"] = True
        
        # Check if it's member count
        elif isinstance(api_result, int) and 0 < api_result < 1000000:
            if not bot_1_seen["getChatMemberCount"]:
                result["bot_1"]["getChatMemberCount"] = api_result
                bot_1_seen["getChatMemberCount"] = True
            elif not bot_2_seen["getChatMemberCount"]:
                result["bot_2"]["getChatMemberCount"] = api_result
                bot_2_seen["getChatMemberCount"] = True
        
        # Check if it's administrators
        elif isinstance(api_result, list) and len(api_result) > 0 and isinstance(api_result[0], dict) and "user" in api_result[0] and "status" in api_result[0]:
            if not bot_1_seen["getChatAdministrators"]:
                result["bot_1"]["getChatAdministrators"] = obj
                bot_1_seen["getChatAdministrators"] = True
            elif not bot_2_seen["getChatAdministrators"]:
                result["bot_2"]["getChatAdministrators"] = obj
                bot_2_seen["getChatAdministrators"] = True
        
    
    return result

# Read input
print("[*] Reading 11.json...")
with open('11.json', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract all JSON
print("[*] Extracting all JSON objects...")
json_objects = extract_all_json(content)
print(f"[+] Found {len(json_objects)} JSON objects")

# Organize
print("[*] Organizing data...")
organized = organize_all_data(json_objects)

# Write output
output_file = '11.json'
print(f"[*] Writing formatted JSON to {output_file}...")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(organized, f, indent=2, ensure_ascii=False)

print(f"\n[+] Successfully formatted JSON!")
print(f"    File: {output_file}")
print(f"    Total objects: {len(json_objects)}")
print(f"    Bot 1 updates: {len(organized['bot_1']['getUpdates']['result']) if organized['bot_1']['getUpdates'] else 0}")
print(f"    Bot 2 updates: {len(organized['bot_2']['getUpdates']['result']) if organized['bot_2']['getUpdates'] else 0}")
print(f"    IPinfo entries: {len(organized['ipinfo'])}")

