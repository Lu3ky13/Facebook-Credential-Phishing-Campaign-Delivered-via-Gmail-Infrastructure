import requests
import json
from datetime import datetime

# ================== CONFIG ==================
BOT_TOKENS = {
    "bot_1": "7871555324:AAHUSIAw2N0psJlFbJ7sfkq4D2L6e9qofGU",
    "bot_2": "8053731074:AAEWnpsgr82u-yoKWONk2eA1mqiVKBhL4bY"
}

CHAT_ID = "-1003162196749"
IPINFO_TOKEN = "b61cb983a2e24b"

TEST_IPS = [
    "1.1.1.1",
    "8.8.8.8"
]
# ============================================


def pretty(title, data):
    print(f"\n{'='*15} {title} {'='*15}")
    print(json.dumps(data, indent=2, ensure_ascii=False))


def tg_call(bot_token, method, params=None):
    url = f"https://api.telegram.org/bot{bot_token}/{method}"
    r = requests.get(url, params=params, timeout=10)
    return r.json()


def ipinfo_lookup(ip):
    url = f"https://ipinfo.io/{ip}"
    r = requests.get(url, params={"token": IPINFO_TOKEN}, timeout=10)
    return r.json()


print("\n🕵️ TELEGRAM + IPINFO RECON STARTED")
print("Time:", datetime.utcnow(), "UTC")

# ================== TELEGRAM RECON ==================
for name, token in BOT_TOKENS.items():
    print(f"\n\n🔍 RECON FOR {name.upper()}")

    pretty("getMe", tg_call(token, "getMe"))
    pretty("getWebhookInfo", tg_call(token, "getWebhookInfo"))
    pretty("getMyCommands", tg_call(token, "getMyCommands"))
    pretty("getUpdates", tg_call(token, "getUpdates"))

    # Chat-based info
    pretty("getChat", tg_call(token, "getChat", {"chat_id": CHAT_ID}))
    pretty("getChatMemberCount", tg_call(token, "getChatMemberCount", {"chat_id": CHAT_ID}))
    pretty("getChatAdministrators", tg_call(token, "getChatAdministrators", {"chat_id": CHAT_ID}))


# ================== IPINFO RECON ==================
print("\n\n🌍 IPINFO LOOKUPS")

for ip in TEST_IPS:
    pretty(f"IPINFO {ip}", ipinfo_lookup(ip))


print("\n✅ RECON FINISHED")
