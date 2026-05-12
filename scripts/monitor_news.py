#!/usr/bin/env python3
"""
Monitor web for hantavirus updates, extract case numbers, and fetch real news
"""

import json
import requests
from datetime import datetime, timezone
import feedparser
import re
from urllib.parse import quote

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

def fetch_rss_feeds():
    """
    Fetch news from RSS feeds
    """
    print("\n?? Fetching news feeds...")
    
    feeds = [
        'https://feeds.reuters.com/reuters/businessNews',
        'https://feeds.bbc.co.uk/news/world/rss.xml',
        'https://feeds.bloomberg.com/markets/news.rss',
    ]
    
    articles = []
    
    for feed_url in feeds:
        try:
            print(f"   Parsing: {feed_url}")
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:20]:  # Get last 20 entries per feed
                title = entry.get('title', '')
                summary = entry.get('summary', '')
                published = entry.get('published', '')
                link = entry.get('link', '')
                
                # Check if article mentions hantavirus, hondius, or andes virus
                content = (title + ' ' + summary).lower()
                
                if any(keyword in content for keyword in ['hantavirus', 'hondius', 'andes virus', 'andes', 'cruise ship outbreak']):
                    articles.append({
                        'title': title,
                        'summary': summary[:200] if summary else '',  # First 200 chars
                        'link': link,
                        'published': published,
                        'source': feed_url.split('/')[-2] if '/' in feed_url else 'News'
                    })
                    print(f"      ? Found: {title[:60]}...")
        
        except Exception as e:
            print(f"      ? Error: {str(e)}")
            continue
    
    return articles

def extract_case_numbers(text):
    """
    Extract case numbers from text
    """
    numbers = {
        'confirmed': None,
        'probable': None,
        'deaths': None
    }
    
    text_lower = text.lower()
    
    # Look for confirmed cases
    confirmed_patterns = [
        r'(\d+)\s+(?:confirmed|confirm)\s+cases?',
        r'confirmed[:\s]+(\d+)',
        r'(\d+)\s+confirmed\s+(?:cases?|patients?|people?)'
    ]
    for pattern in confirmed_patterns:
        match = re.search(pattern, text_lower)
        if match:
            numbers['confirmed'] = int(match.group(1))
            break
    
    # Look for probable cases
    probable_patterns = [
        r'(\d+)\s+(?:probable|suspected)\s+cases?',
        r'probable[:\s]+(\d+)',
        r'(\d+)\s+(?:probable|suspected)\s+(?:cases?|patients?)'
    ]
    for pattern in probable_patterns:
        match = re.search(pattern, text_lower)
        if match:
            numbers['probable'] = int(match.group(1))
            break
    
    # Look for deaths
    death_patterns = [
        r'(\d+)\s+deaths?',
        r'deaths?[:\s]+(\d+)',
        r'(\d+)\s+(?:dead|fatalities?|died)',
    ]
    for pattern in death_patterns:
        match = re.search(pattern, text_lower)
        if match:
            numbers['deaths'] = int(match.group(1))
            break
    
    return numbers

def search_for_hantavirus_data():
    """
    Search for latest hantavirus case information
    """
    print("\n?? Searching for case numbers...")
    
    # Fetch news articles
    articles = fetch_rss_feeds()
    
    all_numbers = {
        'confirmed': [],
        'probable': [],
        'deaths': []
    }
    
    # Extract numbers from each article
    for article in articles:
        content = article['title'] + ' ' + article['summary']
        numbers = extract_case_numbers(content)
        
        if numbers['confirmed']:
            all_numbers['confirmed'].append(numbers['confirmed'])
            print(f"   Found confirmed: {numbers['confirmed']}")
        if numbers['probable']:
            all_numbers['probable'].append(numbers['probable'])
            print(f"   Found probable: {numbers['probable']}")
        if numbers['deaths']:
            all_numbers['deaths'].append(numbers['deaths'])
            print(f"   Found deaths: {numbers['deaths']}")
    
    return all_numbers, articles

def update_tracker_data():
    """
    Update tracker data based on web search results
    """
    current_data = load_current_data()
    
    print("Starting hantavirus news monitor...")
    print(f"Current confirmed: {current_data['confirmed']}")
    print(f"Current deaths: {current_data['deaths']}")
    
    # Search for new data and articles
    case_numbers, articles = search_for_hantavirus_data()
    
    # Update case numbers with highest found (never decrease)
    updated = False
    
    if case_numbers['confirmed']:
        max_confirmed = max(case_numbers['confirmed'])
        if max_confirmed > current_data['confirmed']:
            print(f"\n? Updating confirmed: {current_data['confirmed']} ? {max_confirmed}")
            current_data['confirmed'] = max_confirmed
            updated = True
    
    if case_numbers['probable']:
        max_probable = max(case_numbers['probable'])
        if max_probable > current_data['probable']:
            print(f"? Updating probable: {current_data['probable']} ? {max_probable}")
            current_data['probable'] = max_probable
            updated = True
    
    if case_numbers['deaths']:
        max_deaths = max(case_numbers['deaths'])
        if max_deaths > current_data['deaths']:
            print(f"? Updating deaths: {current_data['deaths']} ? {max_deaths}")
            current_data['deaths'] = max_deaths
            updated = True
    
    # Update news feed with latest articles
    print(f"\n?? Adding {len(articles)} news articles...")
    
    # Get existing news titles to avoid duplicates
    existing_titles = {n.get('text', '') for n in current_data.get('news', [])}
    
    # Add new articles (most recent first)
    for article in articles:
        if article['title'] not in existing_titles:
            current_data['news'].insert(0, {
                'date': article['published'][:10] if article['published'] else datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                'text': article['title'],
                'badge': 'UPDATE',
                'link': article['link']
            })
            existing_titles.add(article['title'])
    
    # Keep only last 15 news items
    current_data['news'] = current_data['news'][:15]
    
    # Update timestamp
    current_data['last_updated'] = datetime.now(timezone.utc).isoformat()
    
    print(f"\nFinal data:")
    print(f"Confirmed: {current_data['confirmed']}")
    print(f"Probable: {current_data['probable']}")
    print(f"Deaths: {current_data['deaths']}")
    print(f"News items: {len(current_data['news'])}")
    
    return current_data

def save_data(data):
    """Save updated data to JSON file"""
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n? Data saved to {DATA_FILE}")
        return True
    except Exception as e:
        print(f"? Error saving data: {str(e)}")
        return False

def main():
    """Main execution"""
    print("=" * 60)
    print("Hantavirus News Monitor & Case Tracker")
    print("=" * 60)
    print(f"Time: {datetime.now(timezone.utc).isoformat()}\n")
    
    # Update data
    updated_data = update_tracker_data()
    
    # Save
    save_data(updated_data)
    
    print("\n" + "=" * 60)
    print("? Monitor completed successfully!")
    print("=" * 60)

if __name__ == '__main__':
    main()