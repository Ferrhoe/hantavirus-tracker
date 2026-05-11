#!/usr/bin/env python3
"""
Monitor news sources for hantavirus updates and update tracker data
Runs on GitHub Actions every hour
"""

import json
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import feedparser
import re

# Configuration
DATA_FILE = 'data/tracker-data.json'
NEWS_SOURCES = [
    'https://feeds.bloomberg.com/markets/news.rss',
    'https://feeds.reuters.com/reuters/businessNews',
    'https://feeds.bbc.co.uk/news/world/rss.xml',
    'https://feeds.cnbc.com/id/100003114/rss/feeds/rss-full.html'
]

# Health authority feeds
HEALTH_FEEDS = [
    'https://www.who.int/feeds/entity/cmo/en/feed/1/en',
    'https://feeds.cdc.gov/cdc_main.rss'
]

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
        "confirmed": 7,
        "probable": 5,
        "deaths": 3,
        "last_updated": datetime.now().isoformat(),
        "countries": {
            "Spain": {"confirmed": 2, "probable": 0, "deaths": 1},
            "United States": {"confirmed": 3, "probable": 1, "deaths": 0},
            "Switzerland": {"confirmed": 1, "probable": 0, "deaths": 0},
            "South Africa": {"confirmed": 0, "probable": 0, "deaths": 1},
            "France": {"confirmed": 2, "probable": 1, "deaths": 0},
            "United Kingdom": {"confirmed": 0, "probable": 2, "deaths": 0}
        },
        "timeline": [
            {"date": "Apr 11", "confirmed": 1, "probable": 0, "deaths": 1},
            {"date": "Apr 24", "confirmed": 1, "probable": 0, "deaths": 2},
            {"date": "May 2", "confirmed": 3, "probable": 0, "deaths": 2},
            {"date": "May 6", "confirmed": 4, "probable": 2, "deaths": 2},
            {"date": "May 11", "confirmed": 7, "probable": 5, "deaths": 3}
        ],
        "news": []
    }

def extract_numbers(text):
    """Extract case numbers from news text"""
    numbers = {
        'confirmed': None,
        'probable': None,
        'deaths': None
    }
    
    # Look for patterns like "X confirmed cases", "X deaths", etc.
    text_lower = text.lower()
    
    # Confirmed cases
    confirmed_match = re.search(r'(\d+)\s+(?:confirmed|confirm)\s+cases?', text_lower)
    if confirmed_match:
        numbers['confirmed'] = int(confirmed_match.group(1))
    
    # Probable/suspected cases
    probable_match = re.search(r'(\d+)\s+(?:probable|suspected)\s+cases?', text_lower)
    if probable_match:
        numbers['probable'] = int(probable_match.group(1))
    
    # Deaths
    death_match = re.search(r'(\d+)\s+deaths?(?:\s+(?:confirmed|suspected))?', text_lower)
    if death_match:
        numbers['deaths'] = int(death_match.group(1))
    
    return numbers

def fetch_news_feeds():
    """Fetch and parse news feeds"""
    all_entries = []
    
    feeds_to_check = NEWS_SOURCES + HEALTH_FEEDS
    
    for feed_url in feeds_to_check:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:  # Check last 5 entries per feed
                title = entry.get('title', '')
                summary = entry.get('summary', '')
                published = entry.get('published', '')
                
                # Check if entry mentions hantavirus or MV Hondius
                content = (title + ' ' + summary).lower()
                if 'hantavirus' in content or 'hondius' in content or 'andes virus' in content:
                    all_entries.append({
                        'title': title,
                        'summary': summary,
                        'link': entry.get('link', ''),
                        'published': published,
                        'source': feed_url
                    })
        except Exception as e:
            print(f"Error fetching {feed_url}: {e}")
            continue
    
    return all_entries

def process_news_entry(entry):
    """Process a news entry and extract data"""
    content = entry['title'] + ' ' + entry['summary']
    numbers = extract_numbers(content)
    
    # Try to parse publish date
    try:
        pub_date = datetime(*entry['published'][:6]) if entry.get('published') else datetime.now()
        date_str = pub_date.strftime('%B %d, %Y')
    except:
        date_str = datetime.now().strftime('%B %d, %Y')
    
    return {
        'date': date_str,
        'headline': entry['title'],
        'summary': entry['summary'][:150],
        'extracted_numbers': numbers,
        'link': entry.get('link', '')
    }

def update_tracker_data(data, news_entries):
    """Update tracker data based on latest news"""
    current_data = load_current_data()
    
    # Process recent news entries for case updates
    for entry in news_entries[:3]:  # Process top 3 most recent
        processed = process_news_entry(entry)
        numbers = processed['extracted_numbers']
        
        # Only update if we found higher numbers (never decrease)
        if numbers['confirmed'] and numbers['confirmed'] > current_data['confirmed']:
            current_data['confirmed'] = numbers['confirmed']
        
        if numbers['probable'] and numbers['probable'] > current_data['probable']:
            current_data['probable'] = numbers['probable']
        
        if numbers['deaths'] and numbers['deaths'] > current_data['deaths']:
            current_data['deaths'] = numbers['deaths']
    
    # Add news items (deduplicate by title)
    existing_titles = {n.get('headline', '') for n in current_data.get('news', [])}
    for entry in news_entries:
        processed = process_news_entry(entry)
        if processed['headline'] not in existing_titles:
            # Add new news item
            current_data['news'].insert(0, {
                'date': processed['date'],
                'text': processed['headline'],
                'badge': 'UPDATE',
                'link': processed['link']
            })
    
    # Keep only last 10 news items
    current_data['news'] = current_data['news'][:10]
    
    # Update timestamp
    current_data['last_updated'] = datetime.now().isoformat()
    
    return current_data

def save_data(data):
    """Save updated data to JSON file"""
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✓ Data saved to {DATA_FILE}")
        print(f"  - Confirmed: {data['confirmed']}")
        print(f"  - Probable: {data['probable']}")
        print(f"  - Deaths: {data['deaths']}")
        print(f"  - News items: {len(data.get('news', []))}")
    except Exception as e:
        print(f"✗ Error saving data: {e}")

def main():
    """Main execution"""
    print("🔍 Starting hantavirus news monitor...")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # Fetch news
    print("\n📰 Fetching news feeds...")
    news_entries = fetch_news_feeds()
    print(f"   Found {len(news_entries)} relevant articles")
    
    if news_entries:
        print("\n📊 Processing entries...")
        for i, entry in enumerate(news_entries[:3], 1):
            print(f"   {i}. {entry['title'][:60]}...")
    
    # Update data
    print("\n🔄 Updating tracker data...")
    updated_data = load_current_data()
    updated_data = update_tracker_data(updated_data, news_entries)
    
    # Save
    print("\n💾 Saving data...")
    save_data(updated_data)
    
    print("\n✅ Monitor completed successfully!")

if __name__ == '__main__':
    main()
