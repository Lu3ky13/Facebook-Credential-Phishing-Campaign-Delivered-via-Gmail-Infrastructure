#!/usr/bin/env python3
"""
Extract Attack Data - Extract all credentials, IPs, and attack information
from the Telegram messages for security reporting
"""

import json
import re
from datetime import datetime
from collections import defaultdict

def extract_credentials(text):
    """Extract credentials from message text"""
    credentials = {
        "emails": [],
        "passwords": [],
        "phones": [],
        "birthdays": [],
        "names": [],
        "otp_codes": [],
        "domains": [],
        "ips": [],
        "user_agents": [],
        "locations": [],
    }
    
    if not text:
        return credentials
    
    # Extract emails
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    credentials["emails"] = re.findall(email_pattern, text)
    
    # Extract passwords (look for patterns like "Password: xxxx" or "Password1: xxxx")
    password_patterns = [
        r'Password:\s*([^\n]+)',
        r'Password1:\s*([^\n]+)',
        r'Password\s*:\s*([^\n]+)',
    ]
    for pattern in password_patterns:
        passwords = re.findall(pattern, text, re.IGNORECASE)
        credentials["passwords"].extend(passwords)
    
    # Extract phone numbers
    phone_pattern = r'Phone:\s*([^\n]+)'
    phones = re.findall(phone_pattern, text, re.IGNORECASE)
    credentials["phones"] = phones
    
    # Extract birthdays
    birthday_pattern = r'Birthday:\s*([^\n]+)'
    birthdays = re.findall(birthday_pattern, text, re.IGNORECASE)
    credentials["birthdays"] = birthdays
    
    # Extract names
    name_pattern = r'Name:\s*([^\n]+)'
    names = re.findall(name_pattern, text, re.IGNORECASE)
    credentials["names"] = names
    
    # Extract OTP codes
    otp_patterns = [
        r'Code\s*1:\s*([^\n]+)',
        r'Code\s*2:\s*([^\n]+)',
        r'Code\s*3:\s*([^\n]+)',
    ]
    for pattern in otp_patterns:
        codes = re.findall(pattern, text, re.IGNORECASE)
        credentials["otp_codes"].extend([c.strip() for c in codes if c.strip()])
    
    # Extract domains
    domain_pattern = r'Tên miền:\s*([^\n]+)'
    domains = re.findall(domain_pattern, text, re.IGNORECASE)
    credentials["domains"] = domains
    
    # Extract IPs
    ip_pattern = r'IP Người gửi:\s*([^\n]+)'
    ips = re.findall(ip_pattern, text, re.IGNORECASE)
    credentials["ips"] = ips
    
    # Extract User Agents
    ua_pattern = r'UserAgent:\s*([^\n]+)'
    uas = re.findall(ua_pattern, text, re.IGNORECASE)
    credentials["user_agents"] = uas
    
    # Extract locations
    location_patterns = [
        r'Quốc gia:\s*([^\n]+)',
        r'Nord IP:\s*([^\n]+)',
    ]
    for pattern in location_patterns:
        locations = re.findall(pattern, text, re.IGNORECASE)
        credentials["locations"].extend(locations)
    
    return credentials


def main():
    print("=" * 80)
    print("EXTRACTING ATTACK DATA FOR SECURITY REPORT")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    
    # Load messages
    with open("ALL_MESSAGES_COMPLETE_20251230_175301.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    messages = data.get("messages", [])
    print(f"[*] Processing {len(messages)} messages...")
    
    # Extract all attack data
    all_credentials = []
    all_ips = set()
    all_domains = set()
    all_user_agents = set()
    all_locations = set()
    attack_timeline = []
    
    for msg in messages:
        text = msg.get("text", "")
        if not text or "DATA PAGE" not in text:
            continue
        
        # Extract credentials
        creds = extract_credentials(text)
        
        # Get message metadata
        date = msg.get("date_readable", "Unknown")
        from_user = msg.get("from", {})
        username = from_user.get("username", "N/A") if from_user else "N/A"
        
        # Build attack record
        attack_record = {
            "timestamp": date,
            "source": username,
            "message_id": msg.get("message_id"),
            "credentials": creds,
        }
        
        all_credentials.append(attack_record)
        
        # Collect unique values
        all_ips.update(creds["ips"])
        all_domains.update(creds["domains"])
        all_user_agents.update(creds["user_agents"])
        all_locations.update(creds["locations"])
        
        attack_timeline.append({
            "date": date,
            "username": username,
            "email": creds["emails"][0] if creds["emails"] else "N/A",
            "ip": creds["ips"][0] if creds["ips"] else "N/A",
            "location": creds["locations"][0] if creds["locations"] else "N/A",
        })
    
    # Generate report data
    report_data = {
        "metadata": {
            "report_date": datetime.now().isoformat(),
            "total_messages_analyzed": len(messages),
            "attack_records_found": len(all_credentials),
            "description": "Security investigation report - Facebook phishing attack via Gmail",
        },
        "summary": {
            "total_emails_compromised": sum(len(c["credentials"]["emails"]) for c in all_credentials),
            "total_passwords_found": sum(len(c["credentials"]["passwords"]) for c in all_credentials),
            "unique_ips": list(all_ips),
            "unique_domains": list(all_domains),
            "unique_locations": list(all_locations),
            "unique_user_agents": list(all_user_agents),
        },
        "attack_timeline": attack_timeline,
        "detailed_credentials": all_credentials,
        "telegram_intelligence": {
            "bot_tokens": [
                "7871555324:AAHUSIAw2N0psJlFbJ7sfkq4D2L6e9qofGU",
                "8053731074:AAEWnpsgr82u-yoKWONk2eA1mqiVKBhL4bY",
            ],
            "chat_id": "-1003162196749",
            "chat_title": "BEE_SERVER_2",
            "suspected_attackers": list(set([c["source"] for c in all_credentials if c["source"] != "N/A"])),
        },
    }
    
    # Save JSON report
    json_file = f"SECURITY_REPORT_ATTACK_DATA_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    print(f"[+] JSON report saved: {json_file}")
    
    # Generate human-readable report
    report_text = generate_text_report(report_data)
    txt_file = f"SECURITY_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"[+] Text report saved: {txt_file}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("EXTRACTION SUMMARY")
    print("=" * 80)
    print(f"Attack records found: {len(all_credentials)}")
    print(f"Emails compromised: {report_data['summary']['total_emails_compromised']}")
    print(f"Passwords found: {report_data['summary']['total_passwords_found']}")
    print(f"Unique IPs: {len(all_ips)}")
    print(f"Unique domains: {len(all_domains)}")
    print(f"Unique locations: {len(all_locations)}")
    print("\n" + "=" * 80)
    
    return report_data


def generate_text_report(data):
    """Generate human-readable security report"""
    report = []
    report.append("=" * 80)
    report.append("SECURITY INVESTIGATION REPORT")
    report.append("Facebook Phishing Attack via Gmail")
    report.append("=" * 80)
    report.append(f"\nReport Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    report.append(f"Investigation Date: {data['metadata']['report_date']}")
    report.append("")
    
    # Executive Summary
    report.append("=" * 80)
    report.append("EXECUTIVE SUMMARY")
    report.append("=" * 80)
    report.append(f"This report documents a phishing attack targeting Facebook accounts")
    report.append(f"through Gmail credential harvesting. The attack data was discovered")
    report.append(f"in a Telegram bot channel used by attackers to share stolen credentials.")
    report.append("")
    report.append(f"Total Attack Records: {data['metadata']['attack_records_found']}")
    report.append(f"Emails Compromised: {data['summary']['total_emails_compromised']}")
    report.append(f"Passwords Harvested: {data['summary']['total_passwords_found']}")
    report.append("")
    
    # Attack Timeline
    report.append("=" * 80)
    report.append("ATTACK TIMELINE")
    report.append("=" * 80)
    for entry in data['attack_timeline']:
        report.append(f"\n[{entry['date']}]")
        report.append(f"  Attacker: @{entry['username']}")
        report.append(f"  Target Email: {entry['email']}")
        report.append(f"  Source IP: {entry['ip']}")
        report.append(f"  Location: {entry['location']}")
    report.append("")
    
    # Infrastructure
    report.append("=" * 80)
    report.append("ATTACK INFRASTRUCTURE")
    report.append("=" * 80)
    report.append(f"\nTelegram Chat: {data['telegram_intelligence']['chat_title']}")
    report.append(f"Chat ID: {data['telegram_intelligence']['chat_id']}")
    report.append(f"\nSuspected Attackers:")
    for attacker in data['telegram_intelligence']['suspected_attackers']:
        report.append(f"  - @{attacker}")
    report.append("")
    report.append(f"Phishing Domains Used:")
    for domain in data['summary']['unique_domains']:
        report.append(f"  - {domain}")
    report.append("")
    report.append(f"Source IP Addresses:")
    for ip in data['summary']['unique_ips']:
        report.append(f"  - {ip}")
    report.append("")
    report.append(f"Geographic Locations:")
    for loc in data['summary']['unique_locations']:
        report.append(f"  - {loc}")
    report.append("")
    
    # Detailed Credentials (redacted for security)
    report.append("=" * 80)
    report.append("COMPROMISED CREDENTIALS (REDACTED)")
    report.append("=" * 80)
    report.append("NOTE: Full credentials are available in the JSON report for law enforcement.")
    report.append("")
    for i, record in enumerate(data['detailed_credentials'], 1):
        report.append(f"\nAttack Record #{i}:")
        report.append(f"  Timestamp: {record['timestamp']}")
        report.append(f"  Source: @{record['source']}")
        if record['credentials']['emails']:
            report.append(f"  Email: {record['credentials']['emails'][0]}")
        if record['credentials']['passwords']:
            report.append(f"  Password: [REDACTED - {len(record['credentials']['passwords'][0])} chars]")
        if record['credentials']['ips']:
            report.append(f"  IP: {record['credentials']['ips'][0]}")
        if record['credentials']['domains']:
            report.append(f"  Phishing Domain: {record['credentials']['domains'][0]}")
    report.append("")
    
    # Recommendations
    report.append("=" * 80)
    report.append("RECOMMENDATIONS")
    report.append("=" * 80)
    report.append("1. All compromised accounts should change passwords immediately")
    report.append("2. Enable two-factor authentication (2FA) on all accounts")
    report.append("3. Report phishing domains to hosting providers and domain registrars")
    report.append("4. Report Telegram channels to Telegram for takedown")
    report.append("5. File reports with relevant law enforcement agencies")
    report.append("6. Monitor affected accounts for unauthorized access")
    report.append("")
    
    report.append("=" * 80)
    report.append("END OF REPORT")
    report.append("=" * 80)
    
    return "\n".join(report)


if __name__ == "__main__":
    try:
        report = main()
        print("\n[+] Security report generation complete!")
    except Exception as e:
        print(f"\n[!] Error: {e}")
        import traceback
        traceback.print_exc()

