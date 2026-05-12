#!/usr/bin/env python3
"""
Monitor news sources for hantavirus updates and update tracker data
Simplified version that's more reliable
"""

import json
import requests
from datetime import datetime, timezone
import feedparser
import re

# Configuration
DATA_FILE = 'data/tracker-data.json'

def load_current_data():
    """Load the current tracker data"""
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return get_default_data()

def get_default_data():
    """Return default data structure"""
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

def fetch_news_feeds():
    """Fetch and parse news feeds"""
    all_entries = []
    
    news_sources = [
        'https://feeds.bloomberg.com/markets/news.rss',
        'https://feeds.reuters.com/reuters/businessNews',
        'https://feeds.bbc.co.uk/news/world/rss.xml',
    ]
    
    for feed_url in news_sources:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:  # Check last 10 entries per feed
                title = entry.get('title', '')
                summary = entry.get('summary', '')
                published = entry.get('published', '')
                
                # Check if entry mentions hantavirus or MV Hondius
                content = (title + ' ' + summary).lower()
                if 'hantavirus' in content or 'hondius' in content or 'andes' in content:
                    all_entries.append({
                        'title': title,
                        'summary': summary,
                        'link': entry.get('link', ''),
                        'published': published,
                    })
                    print(f"Found: {title}")
        except Exception as e:
            print(f"Error fetching {feed_url}: {str(e)}")
            continue
    
    return all_entries

def extract_numbers(text):
    """Extract case numbers from news text"""
    numbers = {
        'confirmed': None,
        'probable': None,
        'deaths': None
    }
    
    text_lower = text.lower()
    
    # Look for patterns like "X confirmed cases", "X deaths", etc.
    confirmed_match = re.search(r'(\d+)\s+(?:confirmed|confirm)\s+cases?', text_lower)
    if confirmed_match:
        numbers['confirmed'] = int(confirmed_match.group(1))
    
    probable_match = re.search(r'(\d+)\s+(?:probable|suspected)\s+cases?', text_lower)
    if probable_match:
        numbers['probable'] = int(probable_match.group(1))
    
    death_match = re.search(r'(\d+)\s+deaths?', text_lower)
    if death_match:
        numbers['deaths'] = int(death_match.group(1))
    
    return numbers

def update_tracker_data():
    """Update tracker data based on latest news"""
    current_data = load_current_data()
    
    print("Starting news monitor...")
    print(f"Current confirmed cases: {current_data['confirmed']}")
    print(f"Current deaths: {current_data['deaths']}")
    
    # Fetch news
    print("\nFetching news feeds...")
    news_entries = fetch_news_feeds()
    print(f"Found {len(news_entries)} relevant articles")
    
    # Process recent news entries for case updates
    for entry in news_entries[:5]:
        content = entry['title'] + ' ' + entry['summary']
        numbers = extract_numbers(content)
        
        print(f"\nAnalyzing: {entry['title'][:60]}...")
        print(f"Extracted numbers: {numbers}")
        
        # Only update if we found higher numbers (never decrease)
        if numbers['confirmed'] and numbers['confirmed'] > current_data['confirmed']:
            print(f"Updating confirmed: {current_data['confirmed']} -> {numbers['confirmed']}")
            current_data['confirmed'] = numbers['confirmed']
        
        if numbers['probable'] and numbers['probable'] > current_data['probable']:
            print(f"Updating probable: {current_data['probable']} -> {numbers['probable']}")
            current_data['probable'] = numbers['probable']
        
        if numbers['deaths'] and numbers['deaths'] > current_data['deaths']:
            print(f"Updating deaths: {current_data['deaths']} -> {numbers['deaths']}")
            current_data['deaths'] = numbers['deaths']
    
    # Add news items (deduplicate by title)
    existing_titles = {n.get('text', '') for n in current_data.get('news', [])}
    for entry in news_entries[:5]:
        if entry['title'] not in existing_titles:
            current_data['news'].insert(0, {
                'date': datetime.now(timezone.utc).strftime('%B %d, %Y'),
                'text': entry['title'],
                'badge': 'UPDATE',
                'link': entry.get('link', '')
            })
    
    # Keep only last 10 news items
    current_data['news'] = current_data['news'][:10]
    
    # Update timestamp
    current_data['last_updated'] = datetime.now(timezone.utc).isoformat()
    
    print(f"\nFinal data:")
    print(f"Confirmed: {current_data['confirmed']}")
    print(f"Deaths: {current_data['deaths']}")
    print(f"News items: {len(current_data['news'])}")
    
    return current_data

def save_data(data):
    """Save updated data to JSON file"""
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n✓ Data saved to {DATA_FILE}")
        return True
    except Exception as e:
        print(f"✗ Error saving data: {str(e)}")
        return False

def main():
    """Main execution"""
    print("=" * 50)
    print("Hantavirus News Monitor")
    print("=" * 50)
    print(f"Time: {datetime.now(timezone.utc).isoformat()}\n")
    
    # Update data
    updated_data = update_tracker_data()
    
    # Save
    save_data(updated_data)
    
    print("\n" + "=" * 50)
    print("Monitor completed successfully!")
    print("=" * 50)

if __name__ == '__main__':
    main()