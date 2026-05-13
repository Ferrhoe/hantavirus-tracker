#!/usr/bin/env python3
"""
Hantavirus tracker updater.
Uses Google Gemini API (free tier) with web grounding to find real
case numbers and news articles about the MV Hondius outbreak.
Requires GEMINI_API_KEY set as a GitHub Actions secret.
"""

import json
import os
import requests
import time
from datetime import datetime, timezone

DATA_FILE = 'data/tracker-data.json'
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

def load_current_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return get_default_data()

def get_default_data():
    return {
        "confirmed": 9,
        "probable": 2,
        "deaths": 3,
        "monitoring": 119,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "countries": {
            "Spain":          {"confirmed": 2, "probable": 0, "deaths": 1, "monitoring": 14},
            "United States":  {"confirmed": 1, "probable": 0, "deaths": 0, "monitoring": 19},
            "Switzerland":    {"confirmed": 1, "probable": 0, "deaths": 0, "monitoring": 0},
            "South Africa":   {"confirmed": 1, "probable": 0, "deaths": 1, "monitoring": 62},
            "France":         {"confirmed": 1, "probable": 1, "deaths": 0, "monitoring": 8},
            "United Kingdom": {"confirmed": 1, "probable": 1, "deaths": 1, "monitoring": 30},
            "Netherlands":    {"confirmed": 2, "probable": 0, "deaths": 0, "monitoring": 0}
        },
        "timeline": [
            {"date": "Apr 11", "confirmed": 1,  "probable": 0, "deaths": 1, "monitoring": 0},
            {"date": "Apr 24", "confirmed": 1,  "probable": 0, "deaths": 2, "monitoring": 0},
            {"date": "May 2",  "confirmed": 3,  "probable": 0, "deaths": 2, "monitoring": 10},
            {"date": "May 6",  "confirmed": 4,  "probable": 2, "deaths": 2, "monitoring": 30},
            {"date": "May 11", "confirmed": 9,  "probable": 2, "deaths": 3, "monitoring": 60}
        ],
        "news": []
    }

def ask_gemini(prompt, retries=3):
    """
    Call Gemini API with Google Search grounding enabled.
    Retries on rate limit errors with exponential backoff.
    """
    if not GEMINI_API_KEY:
        print("✗ GEMINI_API_KEY not set")
        return None

    # gemini-2.5-flash is the current free tier model
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

    body = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "tools": [
            {
                "google_search": {}
            }
        ],
        "generationConfig": {
            "temperature": 0.1
        }
    }

    for attempt in range(retries):
        try:
            response = requests.post(url, json=body, timeout=60)

            if response.status_code == 429:
                wait = 30 * (attempt + 1)  # 30s, 60s, 90s
                print(f"   Rate limited, waiting {wait}s before retry {attempt + 1}/{retries}...")
                time.sleep(wait)
                continue

            response.raise_for_status()
            data = response.json()

            candidates = data.get('candidates', [])
            if candidates:
                parts = candidates[0].get('content', {}).get('parts', [])
                text_parts = [p['text'] for p in parts if 'text' in p]
                return '\n'.join(text_parts)

            return None

        except requests.exceptions.HTTPError as e:
            if attempt < retries - 1:
                wait = 30 * (attempt + 1)
                print(f"   HTTP error: {e}, retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"✗ Gemini API error after {retries} attempts: {str(e)}")
                return None
        except Exception as e:
            print(f"✗ Gemini API error: {str(e)}")
            return None

    return None

def get_latest_case_numbers(current_data):
    """
    Ask Gemini to search for the latest case numbers.
    Very conservative - only updates if clearly sourced numbers are found.
    """
    print("\n🔍 Searching for latest case numbers...")

    prompt = f"""Search the web right now for the latest official case numbers for the MV Hondius hantavirus outbreak in 2026.

Only look for numbers explicitly stated by official sources such as WHO, CDC, ECDC, national health ministries, or major news outlets (Reuters, BBC, AP).

Current known numbers (do NOT change these unless you find a clearly sourced update):
- Confirmed: {current_data['confirmed']}
- Probable: {current_data['probable']}
- Deaths: {current_data['deaths']}
- Under monitoring/contact tracing: {current_data.get('monitoring', 0)}
- Spain: {current_data['countries']['Spain']}
- United States: {current_data['countries']['United States']}
- Switzerland: {current_data['countries']['Switzerland']}
- South Africa: {current_data['countries']['South Africa']}
- France: {current_data['countries']['France']}
- United Kingdom: {current_data['countries']['United Kingdom']}
- Netherlands: {current_data['countries'].get('Netherlands', {'confirmed': 0, 'probable': 0, 'deaths': 0, 'monitoring': 0})}

IMPORTANT RULES:
- Do NOT guess or infer numbers
- Do NOT add countries unless explicitly mentioned in a source
- Do NOT reduce existing numbers
- Only return updated numbers if you find a direct quote or official report with new figures
- If you are not 100% certain of a number from a real source, keep the existing value
- "monitoring" means people under contact tracing or quarantine watch, not cases

If you find clearly sourced new numbers, respond with ONLY this JSON (no markdown):
{{
  "confirmed": <number>,
  "probable": <number>,
  "deaths": <number>,
  "monitoring": <total people under monitoring across all countries>,
  "countries": {{
    "Spain":          {{"confirmed": <n>, "probable": <n>, "deaths": <n>, "monitoring": <n>}},
    "United States":  {{"confirmed": <n>, "probable": <n>, "deaths": <n>, "monitoring": <n>}},
    "Switzerland":    {{"confirmed": <n>, "probable": <n>, "deaths": <n>, "monitoring": <n>}},
    "South Africa":   {{"confirmed": <n>, "probable": <n>, "deaths": <n>, "monitoring": <n>}},
    "France":         {{"confirmed": <n>, "probable": <n>, "deaths": <n>, "monitoring": <n>}},
    "United Kingdom": {{"confirmed": <n>, "probable": <n>, "deaths": <n>, "monitoring": <n>}},
    "Netherlands":    {{"confirmed": <n>, "probable": <n>, "deaths": <n>, "monitoring": <n>}}
  }}
}}

If you find NO clearly sourced updates, respond with only: NO_UPDATE"""

    result = ask_gemini(prompt)
    if not result:
        return None

    result = result.strip()
    print(f"   Response: {result[:300]}...")

    if 'NO_UPDATE' in result:
        print("   No new case numbers found.")
        return None

    try:
        start = result.find('{')
        end = result.rfind('}') + 1
        if start >= 0 and end > start:
            new_data = json.loads(result[start:end])

            # Safety check: never allow any country to go below current values
            for country, values in new_data.get('countries', {}).items():
                if country in current_data['countries']:
                    current = current_data['countries'][country]
                    values['confirmed'] = max(values.get('confirmed', 0), current.get('confirmed', 0))
                    values['probable']  = max(values.get('probable',  0), current.get('probable',  0))
                    values['deaths']    = max(values.get('deaths',    0), current.get('deaths',    0))
                    values['monitoring'] = values.get('monitoring', current.get('monitoring', 0))

            return new_data
    except json.JSONDecodeError as e:
        print(f"   ✗ Could not parse JSON: {e}")

    return None

def get_latest_news(current_data):
    """
    Ask Gemini to find recent news articles about the outbreak.
    """
    print("\n📰 Searching for latest news articles...")

    existing_titles = [n.get('text', '') for n in current_data.get('news', [])[:5]]

    prompt = f"""Search the web right now for recent news articles about the MV Hondius hantavirus outbreak in 2026.

Find up to 5 of the most recent and relevant articles.

Already known headlines (do not include these):
{json.dumps(existing_titles, indent=2)}

Respond with ONLY a valid JSON array, no markdown, no explanation:
[
  {{
    "date": "Month DD, YYYY",
    "text": "Exact article headline",
    "link": "https://full-url-to-article",
    "badge": "UPDATE"
  }}
]

If no articles are found at all, respond with only: NO_UPDATE"""

    result = ask_gemini(prompt)
    if not result:
        return []

    result = result.strip()
    print(f"   Response: {result[:300]}...")

    if 'NO_UPDATE' in result:
        print("   No new articles found.")
        return []

    try:
        start = result.find('[')
        end = result.rfind(']') + 1
        if start >= 0 and end > start:
            articles = json.loads(result[start:end])
            print(f"   Found {len(articles)} new articles")
            return articles
    except json.JSONDecodeError as e:
        print(f"   ✗ Could not parse JSON: {e}")

    return []

def update_timeline(current_data):
    """Add a new timeline entry for today if numbers changed."""
    today = datetime.now(timezone.utc).strftime('%b %-d')
    last_entry = current_data['timeline'][-1] if current_data['timeline'] else {}

    if (last_entry.get('confirmed') != current_data['confirmed'] or
        last_entry.get('probable') != current_data['probable'] or
        last_entry.get('deaths') != current_data['deaths'] or
        last_entry.get('monitoring') != current_data['monitoring']):

        current_data['timeline'].append({
            "date": today,
            "confirmed": current_data['confirmed'],
            "probable": current_data['probable'],
            "deaths": current_data['deaths'],
			"monitoring": current_data['monitoring']
        })
        print(f"   ✓ Added timeline entry for {today}")

    return current_data

def main():
    print("=" * 60)
    print("Hantavirus Tracker - Gemini-powered update")
    print("=" * 60)
    print(f"Time: {datetime.now(timezone.utc).isoformat()}\n")

    current_data = load_current_data()
    print(f"Current: {current_data['confirmed']} confirmed, {current_data['deaths']} deaths")

    updated = False

    # 1. Get latest case numbers
    new_numbers = get_latest_case_numbers(current_data)
    if new_numbers:
        if new_numbers.get('confirmed', 0) >= current_data['confirmed']:
            print(f"\n✓ Confirmed: {current_data['confirmed']} → {new_numbers['confirmed']}")
            current_data['confirmed'] = new_numbers['confirmed']
            updated = True

        if new_numbers.get('probable', 0) >= current_data['probable']:
            current_data['probable'] = new_numbers['probable']

        if new_numbers.get('deaths', 0) >= current_data['deaths']:
            print(f"✓ Deaths: {current_data['deaths']} → {new_numbers['deaths']}")
            current_data['deaths'] = new_numbers['deaths']
            updated = True

        if 'countries' in new_numbers:
            current_data['countries'] = new_numbers['countries']
            print("✓ Updated country breakdown")

        # Recalculate top-level totals from country data to ensure consistency
        current_data['confirmed'] = sum(c.get('confirmed', 0) for c in current_data['countries'].values())
        current_data['probable'] = sum(c.get('probable', 0) for c in current_data['countries'].values())
        current_data['deaths'] = sum(c.get('deaths', 0) for c in current_data['countries'].values())
		current_data['monitoring'] = sum(c.get('monitoring', 0) for c in current_data['countries'].values())
        print(f"✓ Recalculated totals from countries: {current_data['confirmed']} confirmed, {current_data['probable']} probable, {current_data['deaths']} deaths, {current_data['monitoring']} monitoring")

    # 2. Wait briefly before second API call
    time.sleep(10)

    # 3. Get latest news articles
    new_articles = get_latest_news(current_data)
    if new_articles:
        existing_titles = {n.get('text', '') for n in current_data.get('news', [])}
        for article in new_articles:
            if article.get('text') not in existing_titles:
                current_data['news'].insert(0, article)
                existing_titles.add(article.get('text', ''))
                updated = True
        current_data['news'] = current_data['news'][:15]

    # 3. Update timeline if numbers changed
    if updated:
        current_data = update_timeline(current_data)

    # 4. Always update timestamp
    current_data['last_updated'] = datetime.now(timezone.utc).isoformat()

    # 5. Save
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(current_data, f, indent=2)
        print(f"\n✓ Saved to {DATA_FILE}")
    except Exception as e:
        print(f"✗ Error saving: {e}")

    print("\n" + "=" * 60)
    print(f"Done: {current_data['confirmed']} confirmed, {current_data['deaths']} deaths, {len(current_data['news'])} news items")
    print("=" * 60)

if __name__ == '__main__':
    main()