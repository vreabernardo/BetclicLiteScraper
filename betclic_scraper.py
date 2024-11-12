"""
general scraper for /futebol-s1.
scrapes all urls for live matches and general info about odds/ current goals etc.

scrape_betclic_matches(self) -> Optional[Dict]:
    Scrapes live match data from the Betclic sports website.

get_clean_json(self) -> Dict:
    Clean up the raw JSON data to remove unnecessary information.

get_live_match_urls(self) -> Dict:
    Get the URLs for all live matches in the provided data.

get_all_data(self) -> Dict:
    Get the processed match data from the scraped matches.

get_all_match_stats(self) -> Dict:
    Scrapes every live match on betclic.pt/futebol-s1 and returns a dictionary with match stats.

get_match_odds(self, match_url: str) -> Dict:
    Get the match-specific odds for a specific match URL.
"""

import requests
import json
import logging
from bs4 import BeautifulSoup
from typing import Optional, Dict
import betclic_json_simplifier
from live_match_scraper import LiveMatchScraper
import time

# Constants for Betclic data structure
BETCLIC_LIVE_GAMES_KEY = "1791897521"  # Key identifying live games section
BETCLIC_MATCHES_PATH = ["b", "matches"]  # Path to matches data within the live games section

def get_nested_dict_value(data: Dict, path: list) -> Optional[Dict]:
    """
    Safely navigate through a nested dictionary using a path list.
    """
    for key in path:
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return None
    return data

class BetclicScraper:
    def __init__(self, url: str, log_file: str = "scraper.log"):
        """
        Initializes the scraper with the target URL and configures logging.
        """
        self.url = url
        # Configure logging to write to both console and log file
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(log_file, encoding='utf-8')
            ]
        )
        self.matches = self.scrape_betclic_matches()

    def scrape_betclic_matches(self) -> Optional[Dict]:
        """
        Scrapes live match data from the Betclic sports website.
        """
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            html_content = response.text

            # Parse the HTML to find the JSON in the script tag
            soup = BeautifulSoup(html_content, 'html.parser')
            script_tag = soup.find('script', {'id': 'ng-state', 'type': 'application/json'})

            if not script_tag:
                logging.error("JSON script tag with id 'ng-state' not found.")
                return None

            json_data = json.loads(script_tag.string)

            if BETCLIC_LIVE_GAMES_KEY not in json_data:
                logging.error(f"Live games key '{BETCLIC_LIVE_GAMES_KEY}' not found in JSON data.")
                return None

            live_games_data = json_data[BETCLIC_LIVE_GAMES_KEY]
            matches_data = get_nested_dict_value(live_games_data, BETCLIC_MATCHES_PATH)

            if matches_data is None:
                logging.error("Could not find matches data in the expected structure.")
                return None

            logging.info(f"Total matches found: {len(matches_data)}")
            return matches_data

        except requests.RequestException as e:
            logging.error(f"Failed to fetch URL: {e}")
            return None
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON: {e}")
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return None
    
    def get_clean_json(self) -> Dict:
        """
        Clean up the raw JSON data to remove unnecessary information.
        """
        return betclic_json_simplifier.MatchProcessor(self.matches).process_live_matches()

    def get_live_match_urls(self) -> Dict:
        """
        Get the URLs for all live matches in the provided data.
        """
        return betclic_json_simplifier.MatchProcessor(self.matches).get_match_urls()
    
    def get_all_data(self) -> Dict:
        """
        Get the processed match data from the scraped matches.
        """
        return self.matches

    def get_all_match_stats(self) -> Dict:
        """
        Scrapes every live match on betclic.pt/futebol-s1 and returns a dictionary with match stats.
        """
        try:
            # Step 1: Get all live match URLs
            live_match_urls = self.get_live_match_urls()
            if not live_match_urls:
                logging.error("No live match URLs found.")
                return {"status": "error", "message": "No live matches available"}

            all_match_stats = {}
            for name, url in live_match_urls.items():
                try:
                    time.sleep(5)  # add to avoid 403
                    match_scraper = LiveMatchScraper(url)
                    stats = match_scraper.parse_match_stats()
                    all_match_stats[name] = {"url": url, "stats": stats}
                except Exception as e:
                    logging.error(f"Failed to retrieve match stats for {url}: {e}")
                    all_match_stats[name] = {"url": url, "error": str(e)}

            return all_match_stats
        except Exception as e:
            logging.error(f"An error occurred while retrieving match stats: {e}")
            return {"status": "error", "message": str(e)}
        
    
    def get_match_odds(self, match_url: str) -> Dict:
        """
        Get the match-specific odds for a specific match URL.
        """
        try:
            # Initialize the match scraper with the match URL
            match_scraper = LiveMatchScraper(match_url)
            
            # Call the method to get the odds (assuming it's available in LiveMatchScraper)
            odds = match_scraper.get_match_odds()  # Replace with actual method for odds
            
            if odds is None:
                logging.error(f"No odds found for match: {match_url}")
                return {"status": "error", "message": "No odds available"}
            
            logging.info(f"Odds for match {match_url}: {odds}")
            return {"status": "success", "odds": odds}
        
        except Exception as e:
            logging.error(f"Failed to retrieve odds for {match_url}: {e}")
            return {"status": "error", "message": str(e)}
    