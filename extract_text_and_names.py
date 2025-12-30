#!/usr/bin/env python3
"""
Extract all "text" and "name" fields from 11_formatted.json
"""

import json
import re
from datetime import datetime

def extract_text_and_names(data, results=None):
    """Recursively extract all 'text' and 'name' fields from JSON structure"""
    if results is None:
        results = {"texts": [], "names": []}
    
    if isinstance(data, dict):
        # Check for 'text' field
        if "text" in data and data["text"]:
            text_value = data["text"]
            if isinstance(text_value, str) and text_value.strip():
                results["texts"].append({
                    "text": text_value,
                    "context": {k: v for k, v in data.items() if k != "text" and not isinstance(v, (dict, list))}
                })
        
        # Check for 'name' field
        if "name" in data and data["name"]:
            name_value = data["name"]
            if isinstance(name_value, str) and name_value.strip():
                results["names"].append({
                    "name": name_value,
                    "context": {k: v for k, v in data.items() if k != "name" and not isinstance(v, (dict, list))}
                })
        
        # Check for 'first_name' field (also a name)
        if "first_name" in data and data["first_name"]:
            name_value = data["first_name"]
            if isinstance(name_value, str) and name_value.strip():
                results["names"].append({
                    "name": name_value,
                    "type": "first_name",
                    "context": {k: v for k, v in data.items() if k != "first_name" and not isinstance(v, (dict, list))}
                })
        
        # Check for 'title' field (often contains names)
        if "title" in data and data["title"]:
            title_value = data["title"]
            if isinstance(title_value, str) and title_value.strip():
                results["names"].append({
                    "name": title_value,
                    "type": "title",
                    "context": {k: v for k, v in data.items() if k != "title" and not isinstance(v, (dict, list))}
                })
        
        # Recursively process all values
        for value in data.values():
            extract_text_and_names(value, results)
    
    elif isinstance(data, list):
        for item in data:
            extract_text_and_names(item, results)
    
    return results

def extract_names_from_text(text):
    """Extract names from text using pattern matching"""
    names = []
    
    if not text:
        return names
    
    # Pattern: Name: <name>
    name_pattern = r'Name:\s*([^\n]+)'
    matches = re.findall(name_pattern, text, re.IGNORECASE)
    for match in matches:
        name = match.strip()
        if name and name not in names:
            names.append(name)
    
    return names

def main():
    print("=" * 80)
    print("EXTRACTING TEXT AND NAMES FROM 11_formatted.json")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    
    # Load JSON file
    print("[*] Loading 11_formatted.json...")
    with open("11_formatted.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Extract all text and name fields
    print("[*] Extracting text and name fields...")
    results = extract_text_and_names(data)
    
    # Also extract names from text fields
    print("[*] Extracting names from text content...")
    for text_item in results["texts"]:
        text = text_item["text"]
        names_from_text = extract_names_from_text(text)
        for name in names_from_text:
            if name not in [n["name"] for n in results["names"]]:
                results["names"].append({
                    "name": name,
                    "type": "extracted_from_text",
                    "source_text": text[:100] + "..." if len(text) > 100 else text
                })
    
    # Remove duplicates from names
    unique_names = []
    seen_names = set()
    for name_item in results["names"]:
        name = name_item["name"]
        if name not in seen_names:
            seen_names.add(name)
            unique_names.append(name_item)
    results["names"] = unique_names
    
    # Save results
    print("\n[*] Saving results...")
    
    # JSON output
    json_file = f"extracted_text_and_names_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"[+] JSON saved: {json_file}")
    
    # Text output - just the values
    txt_file = f"extracted_text_and_names_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("EXTRACTED TEXT FIELDS\n")
        f.write("=" * 80 + "\n\n")
        for i, text_item in enumerate(results["texts"], 1):
            f.write(f"Text #{i}:\n")
            f.write(f"{text_item['text']}\n")
            f.write("-" * 80 + "\n\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("EXTRACTED NAME FIELDS\n")
        f.write("=" * 80 + "\n\n")
        for i, name_item in enumerate(results["names"], 1):
            f.write(f"Name #{i}: {name_item['name']}\n")
            if "type" in name_item:
                f.write(f"  Type: {name_item['type']}\n")
            f.write("\n")
    
    print(f"[+] Text file saved: {txt_file}")
    
    # Summary
    print("\n" + "=" * 80)
    print("EXTRACTION SUMMARY")
    print("=" * 80)
    print(f"Total text fields found: {len(results['texts'])}")
    print(f"Total name fields found: {len(results['names'])}")
    print(f"\nUnique names:")
    for name_item in results["names"]:
        print(f"  - {name_item['name']}")
    
    print("\n" + "=" * 80)
    print("COMPLETE!")
    print("=" * 80)
    
    return results

if __name__ == "__main__":
    try:
        results = main()
    except Exception as e:
        print(f"\n[!] Error: {e}")
        import traceback
        traceback.print_exc()

