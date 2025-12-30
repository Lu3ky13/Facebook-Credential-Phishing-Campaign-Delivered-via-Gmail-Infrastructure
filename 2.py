import asyncio
import json
import os
import re
import sqlite3
from datetime import datetime, timezone

import requests
from telegram import Update
from telegram.ext import (
    Application,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

# ==================================================
# CONFIG
# ==================================================
CONFIG = {
    # Bot tokens (env first, fallback hardcoded)
    "bot_token": os.getenv(
        "BOT_TOKEN",
        "7871555324:AAHUSIAw2N0psJlFbJ7sfkq4D2L6e9qofGU",
    ),
    "bot_token_journey": os.getenv(
        "BOT_TOKEN_2",
        "8053731074:AAEWnpsgr82u-yoKWONk2eA1mqiVKBhL4bY",
    ),

    # Target group / channel
    "chat_id": int(os.getenv("CHAT_ID", "-1003162196749")),

    # IPinfo token
    "ipinfo_token": os.getenv("IPINFO_TOKEN", "b61cb983a2e24b"),

    # ✅ ADMIN IDS (your ID is FIXED here)
    "admin_ids": set(
        int(x)
        for x in os.getenv("ADMIN_IDS", "937596812").split(",")
        if x.strip().isdigit()
    ),

    # Keywords to flag hosting / VPN / cloud ASNs
    "suspicious_keywords": [
        "hosting",
        "cloud",
        "vps",
        "datacenter",
        "data center",
        "server",
        "ovh",
        "digitalocean",
        "hetzner",
        "amazon",
        "google",
        "microsoft",
        "linode",
        "vultr",
        "leaseweb",
        "contabo",
    ],

    # Storage
    "db_path": "osint_bot.sqlite",
    "log_txt": "joins_and_iplookups.txt",
}

CHAT_ID = CONFIG["chat_id"]

# ==================================================
# DATABASE
# ==================================================
def db_init():
    conn = sqlite3.connect(CONFIG["db_path"])
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_joins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bot_name TEXT,
            chat_id INTEGER,
            user_id INTEGER,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            joined_at_utc TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ip_lookups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bot_name TEXT,
            requested_by_user_id INTEGER,
            requested_by_username TEXT,
            ip TEXT,
            looked_up_at_utc TEXT,
            asn TEXT,
            org TEXT,
            country TEXT,
            region TEXT,
            city TEXT,
            loc TEXT,
            privacy_json TEXT
        )
        """
    )

    conn.commit()
    conn.close()


def db_insert_join(bot_name, chat_id, u):
    conn = sqlite3.connect(CONFIG["db_path"])
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO user_joins
        (bot_name, chat_id, user_id, username, first_name, last_name, joined_at_utc)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            bot_name,
            chat_id,
            u.id,
            u.username,
            u.first_name,
            u.last_name,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def db_insert_iplookup(bot_name, by_user, ip, info):
    conn = sqlite3.connect(CONFIG["db_path"])
    cur = conn.cursor()

    org = info.get("org")
    asn = None
    if isinstance(org, str):
        m = re.match(r"^(AS\d+)", org)
        if m:
            asn = m.group(1)

    cur.execute(
        """
        INSERT INTO ip_lookups
        (bot_name, requested_by_user_id, requested_by_username, ip,
         looked_up_at_utc, asn, org, country, region, city, loc, privacy_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            bot_name,
            by_user.id,
            by_user.username,
            ip,
            datetime.now(timezone.utc).isoformat(),
            asn,
            org,
            info.get("country"),
            info.get("region"),
            info.get("city"),
            info.get("loc"),
            json.dumps(info.get("privacy")),
        ),
    )

    conn.commit()
    conn.close()


# ==================================================
# TXT LOG
# ==================================================
def log_txt(line):
    with open(CONFIG["log_txt"], "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ==================================================
# IPINFO
# ==================================================
def ipinfo_lookup(ip):
    r = requests.get(
        f"https://ipinfo.io/{ip}",
        params={"token": CONFIG["ipinfo_token"]},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def detect_suspicious(info):
    hits = []
    text = " ".join(
        [
            str(info.get("org", "")),
            str(info.get("hostname", "")),
            str(info.get("company", "")),
        ]
    ).lower()

    for kw in CONFIG["suspicious_keywords"]:
        if kw in text:
            hits.append(kw)

    privacy = info.get("privacy")
    if isinstance(privacy, dict):
        for k in ["vpn", "proxy", "tor", "hosting"]:
            if privacy.get(k) is True:
                hits.append(f"privacy:{k}")

    return hits


# ==================================================
# TELEGRAM HANDLERS
# ==================================================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "OSINT Bot is running.\n\n"
        "Commands:\n"
        "/ip <ip>  → IP intelligence (admin only)"
    )


def is_admin(uid: int) -> bool:
    return uid in CONFIG["admin_ids"]


async def ip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_admin(user.id):
        await update.message.reply_text("⛔ Not allowed.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /ip 8.8.8.8")
        return

    ip = context.args[0].strip()
    if not re.match(r"^\d{1,3}(\.\d{1,3}){3}$", ip):
        await update.message.reply_text("Invalid IPv4 address.")
        return

    info = ipinfo_lookup(ip)
    flags = detect_suspicious(info)

    msg = (
        f"IP: {ip}\n"
        f"Org: {info.get('org')}\n"
        f"City: {info.get('city')}\n"
        f"Region: {info.get('region')}\n"
        f"Country: {info.get('country')}\n"
        f"Location: {info.get('loc')}\n"
    )
    if flags:
        msg += "⚠️ Flags: " + ", ".join(flags)

    await update.message.reply_text(msg)

    db_insert_iplookup(
        context.application.bot.username or "bot", user, ip, info
    )
    log_txt(
        f"[IP] bot={context.application.bot.username} "
        f"user={user.id} ip={ip} flags={flags}"
    )


async def new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.new_chat_members:
        return
    if msg.chat_id != CHAT_ID:
        return

    bot_name = context.application.bot.username or "bot"
    for u in msg.new_chat_members:
        db_insert_join(bot_name, msg.chat_id, u)
        log_txt(
            f"[JOIN] bot={bot_name} chat={msg.chat_id} "
            f"user={u.id} @{u.username}"
        )


# ==================================================
# RUN BOTS
# ==================================================
async def run_bot(token: str):
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("ip", ip_cmd))
    app.add_handler(
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_members)
    )

    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    return app


async def main():
    db_init()

    app1_task = asyncio.create_task(run_bot(CONFIG["bot_token"]))
    app2_task = asyncio.create_task(run_bot(CONFIG["bot_token_journey"]))

    app1 = await app1_task
    app2 = await app2_task

    print("✅ Both bots running. Press CTRL+C to stop.")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
