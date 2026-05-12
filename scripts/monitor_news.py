#!/usr/bin/env python3
"""
Monitor web for hantavirus updates and extract case numbers
Uses web search to find real case data
"""

import json
import subprocess
from datetime import datetime, timezone
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

def search_web(query):
    """
    Search the web using curl and return results
    This simulates web search functionality
    """
    try:
        # Using DuckDuckGo which doesn't require API key
        url = f"https://duckduckgo.com/?q={query}&format=json"
        result = subprocess.run(
            ['curl', '-s', url],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return result.stdout
        else:
            print(f"Search error: {result.stderr}")
            return None
    except Exception as e:
        print(f"Error during web search: {str(e)}")
        return None

def extract_case_numbers(text):
    """
    Extract case numbers from search results or article text
    """
    numbers = {
        'confirmed': None,
        'probable': None,
        'deaths': None,
        'total': None
    }
    
    text_lower = text.lower()
    
    # Look for confirmed cases
    # Patterns: "X confirmed cases", "X confirmed", "confirmed: X"
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
        r'mortality[:\s]+(\d+)'
    ]
    for pattern in death_patterns:
        match = re.search(pattern, text_lower)
        if match:
            numbers['deaths'] = int(match.group(1))
            break
    
    # Look for total cases
    total_patterns = [
        r'total[:\s]+(\d+)',
        r'(\d+)\s+total\s+cases?',
        r'(\d+)\s+cases?'
    ]
    for pattern in total_patterns:
        match = re.search(pattern, text_lower)
        if match:
            numbers['total'] = int(match.group(1))
            break
    
    return numbers

def search_for_hantavirus_data():
    """
    Search for latest hantavirus case information
    """
    print("\n🔍 Searching for latest hantavirus data...")
    
    search_queries = [
        "hantavirus MV Hondius cases 2026",
        "hantavirus outbreak May 2026 cases deaths",
        "andes virus cruise ship cases confirmed",
        "hantavirus cases confirmed deaths 2026"
    ]
    
    all_data = {
        'confirmed': [],
        'probable': [],
        'deaths': [],
        'news': []
    }
    
    for query in search_queries:
        print(f"   Searching: {query}")
        results = search_web(query)
        
        if results:
            # Extract numbers from search results
            numbers = extract_case_numbers(results)
            
            if numbers['confirmed']:
                all_data['confirmed'].append(numbers['confirmed'])
                print(f"   Found confirmed: {numbers['confirmed']}")
            if numbers['probable']:
                all_data['probable'].append(numbers['probable'])
                print(f"   Found probable: {numbers['probable']}")
            if numbers['deaths']:
                all_data['deaths'].append(numbers['deaths'])
                print(f"   Found deaths: {numbers['deaths']}")
    
    return all_data

def update_tracker_data():
    """
    Update tracker data based on web search results
    """
    current_data = load_current_data()
    
    print("Starting hantavirus news monitor...")
    print(f"Current confirmed: {current_data['confirmed']}")
    print(f"Current deaths: {current_data['deaths']}")
    
    # Search for new data
    search_results = search_for_hantavirus_data()
    
    # Update with highest numbers found (never decrease)
    if search_results['confirmed']:
        max_confirmed = max(search_results['confirmed'])
        if max_confirmed > current_data['confirmed']:
            print(f"\n✓ Updating confirmed: {current_data['confirmed']} → {max_confirmed}")
            current_data['confirmed'] = max_confirmed
    
    if search_results['probable']:
        max_probable = max(search_results['probable'])
        if max_probable > current_data['probable']:
            print(f"✓ Updating probable: {current_data['probable']} → {max_probable}")
            current_data['probable'] = max_probable
    
    if search_results['deaths']:
        max_deaths = max(search_results['deaths'])
        if max_deaths > current_data['deaths']:
            print(f"✓ Updating deaths: {current_data['deaths']} → {max_deaths}")
            current_data['deaths'] = max_deaths
    
    # Update timestamp
    current_data['last_updated'] = datetime.now(timezone.utc).isoformat()
    
    print(f"\nFinal data:")
    print(f"Confirmed: {current_data['confirmed']}")
    print(f"Probable: {current_data['probable']}")
    print(f"Deaths: {current_data['deaths']}")
    
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