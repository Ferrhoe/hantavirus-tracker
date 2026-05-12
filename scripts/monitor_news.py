#!/usr/bin/env python3
"""
Hantavirus tracker updater
Uses Claude API with web search to find real case numbers and news headlines
"""

import json
import os
import requests
from datetime import datetime, timezone

DATA_FILE = 'data/tracker-data.json'
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')

def load_current_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return get_default_data()

def get_default_data():
    return {
        "confirmed": 11,
        "probable": 0,
        "deaths": 3,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "countries": {
            "Spain": {"confirmed": 2, "probable": 0, "deaths": 1},
            "United States": {"confirmed": 4, "probable": 0, "deaths": 0},
            "Switzerland": {"confirmed": 1, "probable": 0, "deaths": 0},
            "South Africa": {"confirmed": 0, "probable": 0, "deaths": 1},
            "France": {"confirmed": 2, "probable": 0, "deaths": 0},
            "United Kingdom": {"confirmed": 2, "probable": 0, "deaths": 0}
        },
        "timeline": [
            {"date": "Apr 11", "confirmed": 1, "probable": 0, "deaths": 1},
            {"date": "Apr 24", "confirmed": 1, "probable": 0, "deaths": 2},
            {"date": "May 2", "confirmed": 3, "probable": 0, "deaths": 2},
            {"date": "May 6", "confirmed": 4, "probable": 2, "deaths": 2},
            {"date": "May 11", "confirmed": 11, "probable": 0, "deaths": 3}
        ],
        "news": []
    }

def query_claude_with_web_search(current_data):
    """
    Call Claude API with web search enabled to get latest hantavirus data
    """
    print("\n🤖 Querying Claude with web search...")

    current_json = json.dumps({
        "confirmed": current_data["confirmed"],
        "probable": current_data["probable"],
        "deaths": current_data["deaths"],
        "countries": current_data["countries"]
    }, indent=2)

    prompt = f"""Search the web for the very latest news about the hantavirus outbreak linked to the MV Hondius cruise ship (2026).

Current data we have:
{current_json}

Please search for the most recent updates and return a JSON object with the following structure. Return ONLY the JSON, no other text, no markdown, no backticks:

{{
  "confirmed": <total confirmed cases as integer>,
  "probable": <total probable cases as integer>,
  "deaths": <total deaths as integer>,
  "countries": {{
    "Spain": {{"confirmed": 0, "probable": 0, "deaths": 0}},
    "United States": {{"confirmed": 0, "probable": 0, "deaths": 0}},
    "Switzerland": {{"confirmed": 0, "probable": 0, "deaths": 0}},
    "South Africa": {{"confirmed": 0, "probable": 0, "deaths": 0}},
    "France": {{"confirmed": 0, "probable": 0, "deaths": 0}},
    "United Kingdom": {{"confirmed": 0, "probable": 0, "deaths": 0}}
  }},
  "news": [
    {{
      "date": "Month DD, YYYY",
      "text": "Headline or summary of the news article",
      "badge": "LATEST",
      "link": "https://url-to-article.com"
    }}
  ],
  "changed": true
}}

Rules:
- Only update numbers if you find confirmed newer information. Never decrease numbers.
- Add up to 5 recent relevant news headlines in the news array (most recent first)
- If you find no new information, return the same numbers as current data and set "changed": false
- For countries not mentioned in new reports, keep the existing numbers
- If a new country is affected, add it to the countries object
"""

    response = requests.post(
        'https://api.anthropic.com/v1/messages',
        headers={
            'x-api-key': ANTHROPIC_API_KEY,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        },
        json={
            'model': 'claude-sonnet-4-20250514',
            'max_tokens': 2000,
            'tools': [
                {
                    'type': 'web_search_20250305',
                    'name': 'web_search'
                }
            ],
            'messages': [
                {'role': 'user', 'content': prompt}
            ]
        },
        timeout=60
    )

    if response.status_code != 200:
        print(f"   ✗ API error: {response.status_code} - {response.text}")
        return None

    data = response.json()
    
    # Extract text from response (may contain tool use blocks)
    text_content = ''
    for block in data.get('content', []):
        if block.get('type') == 'text':
            text_content += block.get('text', '')
    
    print(f"   Claude response: {text_content[:200]}...")
    
    # Parse JSON from response
    try:
        # Clean up in case there are any stray characters
        text_content = text_content.strip()
        parsed = json.loads(text_content)
        return parsed
    except json.JSONDecodeError as e:
        print(f"   ✗ JSON parse error: {e}")
        print(f"   Raw response: {text_content}")
        return None

def update_tracker_data():
    current_data = load_current_data()
    
    print("=" * 60)
    print("Hantavirus Tracker - Claude-Powered Update")
    print("=" * 60)
    print(f"Time (UTC): {datetime.now(timezone.utc).isoformat()}")
    print(f"\nCurrent data:")
    print(f"  Confirmed: {current_data['confirmed']}")
    print(f"  Probable:  {current_data['probable']}")
    print(f"  Deaths:    {current_data['deaths']}")

    # Check API key
    if not ANTHROPIC_API_KEY:
        print("\n✗ ANTHROPIC_API_KEY not set. Skipping update.")
        return current_data

    # Query Claude with web search
    new_data = query_claude_with_web_search(current_data)

    if not new_data:
        print("\n⚠ Could not get new data. Keeping current values.")
        current_data['last_updated'] = datetime.now(timezone.utc).isoformat()
        return current_data

    changed = new_data.get('changed', True)

    if not changed:
        print("\n✓ No new updates found. Data is current.")
        current_data['last_updated'] = datetime.now(timezone.utc).isoformat()
        return current_data

    # Update global numbers (never decrease)
    if new_data.get('confirmed', 0) > current_data['confirmed']:
        print(f"\n✓ Confirmed: {current_data['confirmed']} → {new_data['confirmed']}")
        current_data['confirmed'] = new_data['confirmed']

    if new_data.get('probable', 0) > current_data['probable']:
        print(f"✓ Probable: {current_data['probable']} → {new_data['probable']}")
        current_data['probable'] = new_data['probable']

    if new_data.get('deaths', 0) > current_data['deaths']:
        print(f"✓ Deaths: {current_data['deaths']} → {new_data['deaths']}")
        current_data['deaths'] = new_data['deaths']

    # Update country-level data (never decrease per country)
    for country, values in new_data.get('countries', {}).items():
        if country not in current_data['countries']:
            current_data['countries'][country] = values
            print(f"✓ New country added: {country}")
        else:
            for key in ['confirmed', 'probable', 'deaths']:
                if values.get(key, 0) > current_data['countries'][country].get(key, 0):
                    print(f"✓ {country} {key}: {current_data['countries'][country][key]} → {values[key]}")
                    current_data['countries'][country][key] = values[key]

    # Update news feed - add new headlines, avoid duplicates
    existing_titles = {n.get('text', '') for n in current_data.get('news', [])}
    new_articles = new_data.get('news', [])

    added = 0
    for article in new_articles:
        if article.get('text') and article['text'] not in existing_titles:
            current_data['news'].insert(0, article)
            existing_titles.add(article['text'])
            added += 1

    print(f"\n✓ Added {added} new news articles")

    # Keep only last 15 items
    current_data['news'] = current_data['news'][:15]

    # Update timestamp
    current_data['last_updated'] = datetime.now(timezone.utc).isoformat()

    print(f"\nFinal:")
    print(f"  Confirmed: {current_data['confirmed']}")
    print(f"  Probable:  {current_data['probable']}")
    print(f"  Deaths:    {current_data['deaths']}")
    print(f"  News items: {len(current_data['news'])}")

    return current_data

def save_data(data):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n✓ Saved to {DATA_FILE}")
        return True
    except Exception as e:
        print(f"✗ Error saving: {str(e)}")
        return False

if __name__ == '__main__':
    updated = update_tracker_data()
    save_data(updated)