"""
this is a helper class that processes the raw JSON data from the Betclic API and simplifies it into a structured format.
{
        "match_id": match id,
        "competition": {
            "name": match name, eg Sorting-Benfica,
            "country": country code,s
            "sport": "Futebol",
            "round": league and round
        },
        "teams": {
            "home": home team name,
            "away": away team name
        },
        "datetime": datetime,
        "odds": {
            "home_win": odds of home team winning,
            "draw": odds of draw,
            "away_win": odds of away team winning
        },
        "result": {
            "home_score": 0,
            "away_score": 0,
            "winner": home | away | draw,
            "current_minute": minutes
        },
        "match_status": {
            "is_live": true
        },
        "url": url
    }
"""

import re
from urllib.parse import urlparse, urlunparse, quote
from typing import List, Dict

class MatchProcessor:
    def __init__(self, data: List[Dict]):
        """Initialize the MatchProcessor with JSON data directly passed as a parameter."""
        self.data = data

    
    @staticmethod
    def clean_and_combine_urls(competition_url, match_url):
        """Combine competition and match URLs into a single valid URL."""
        combined_url = f"https://www.betclic.pt/{competition_url}/{match_url}"
        combined_url = urlunparse(
            urlparse(re.sub(r'[^\w:/.-]', '', combined_url))._replace(path=quote(urlparse(combined_url).path))
        )
        return combined_url

    @staticmethod
    def extract_odds(raw_match):
        """Extract odds for home, draw, and away from the raw match data."""
        odds = (
            raw_match.get("grouped_markets", [])
            and raw_match["grouped_markets"][0].get("markets", [])
            and raw_match["grouped_markets"][0]["markets"][0].get("selections", None)
        )
        return odds

    @staticmethod
    def extract_scoreboard(raw_match):
        """Extract scoreboard information from the raw match data."""
        scoreboard = raw_match.get("live_data", {}).get("scoreboard", {})
        home_score = int(scoreboard.get("current_score", {}).get("contestant1", 0))
        away_score = int(scoreboard.get("current_score", {}).get("contestant2", 0))
        return home_score, away_score, scoreboard

    @staticmethod
    def calculate_result(home_score, away_score, scoreboard):
        """Calculate the match result based on scores and elapsed time."""
        result = {
            "home_score": home_score,
            "away_score": away_score,
            "winner": "home" if home_score > away_score else ("away" if away_score > home_score else "draw"),
            "current_minute": scoreboard.get("elapsed_time", 0) // 60
        }
        return result

    def process_match(self, raw_match):
        """Process each match and return a structured dictionary with relevant details."""
        competition_url = raw_match["competition"]["relative_desktop_url"]
        match_url = raw_match["relative_desktop_url"]
        combined_url = self.clean_and_combine_urls(competition_url, match_url)
        
        odds = self.extract_odds(raw_match)
        home_score, away_score, scoreboard = self.extract_scoreboard(raw_match)
        result = self.calculate_result(home_score, away_score, scoreboard)

        processed_match = {
            "match_id": raw_match.get("id"),
            "competition": {
                "name": raw_match.get("competition", {}).get("name"),
                "country": raw_match.get("competition", {}).get("country", {}).get("code"),
                "sport": raw_match.get("competition", {}).get("sport", {}).get("name"),
                "round": raw_match.get("competition", {}).get("info", {}).get("round_name")
            },
            "teams": {
                "home": raw_match["contestants"][0]["name"],
                "away": raw_match["contestants"][1]["name"]
            },
            "datetime": raw_match.get("date"),
            "odds": {
                "home_win": odds[0][0].get("odds") if odds and len(odds) > 0 and len(odds[0]) > 0 else None,
                "draw": odds[1][0].get("odds") if len(odds) > 1 and len(odds[1]) > 0 else None,
                "away_win": odds[2][0].get("odds") if len(odds) > 2 and len(odds[2]) > 0 else None
            },
            "result": result,
            "match_status": {
                "is_live": raw_match.get("is_live")
            },
            "url": combined_url
        }
        
        return processed_match

    def process_live_matches(self):
        """Process the live matches from the provided data."""
        all_matches = []
        
        for raw_match in self.data:
            if raw_match.get("is_live"):
                processed_match = self.process_match(raw_match)
                all_matches.append(processed_match)
        
        return all_matches
    
    def get_match_urls(self):
        """Get the URLs for all live matches in the provided data."""
        urls = {}
        for raw_match in self.data:
            competition_url = raw_match["competition"]["relative_desktop_url"]
            match_url = raw_match["relative_desktop_url"]
            combined_url = self.clean_and_combine_urls(competition_url, match_url)
            match_name = f"{raw_match['contestants'][0]['name']}-{raw_match['contestants'][1]['name']}"
            urls[match_name] = combined_url
        return urls
