"""
OpenAIHelper is a class that provides methods to interact with the OpenAI API for processing raw football match data and calculating positive expected value (EV) odds.
Methods:
    raw2json(raw_text: str) -> dict:
        Takes raw text, sends it to the OpenAI API, and parses it into a structured JSON format for stat data.
    get_positive_ev_odds(odds_json: dict, match_stats_json: dict) -> dict:
        Returns the odds with a positive expected value (EV) and justifications.
"""

from openai import OpenAI
import os
import json

class OpenAIHelper:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


    def raw2json(self, raw_text: str) -> dict:
        """
        Takes raw text, sends it to the OpenAI API, 
        and parses it into a structured JSON format for stat data.
        
        :param raw_text: The raw extracted text to be parsed.
        :return: A dictionary containing structured JSON data.
        """


        prompt = f"""
        Translate the following raw football match text data into JSON format, following this specific order of fields for both teams in the raw text:

        Probabilities: Probability of win for the home team, probability of draw, and probability of win for the away team.
        Head-to-Head Stats: Number of victories of the home team against the away team, draws between the teams, and losses of the home team against the away team.
        Goals and Probabilities: Average goals scored, 'AEM' metric, probability of more than 1.5 goals, probability of more than 2.5 goals.
        Cards and Corners: Average number of cards for each team (home and away), and average number of corners for each team (home and away).
        Recent Games: Last games for each team, including date, competition, opponent, and result.

        Raw Text:{raw_text}"""

        completion = self.client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        functions=[{
            "name": "get_teams_data",
            "description": "Parse and structure raw football match data into JSON, detailing win probabilities, team statistics, head-to-head records, and recent game results for home and away teams.",
            "parameters": {
                "type": "object",
                "properties": {
                    "home_team": {
                        "type": "object",
                        "properties": {
                            "probability_win": {"type": "number"},
                            "probability_draw": {"type": "number"},
                            "probability_away_win": {"type": "number"},
                            "victories_home_vs_away": {"type": "number"},
                            "draws_home_vs_away": {"type": "number"},
                            "losses_home_vs_away": {"type": "number"},
                            "goals_scored": {"type": "number"},
                            "AEM": {"type": "number"},
                            "more_than_1_5_probability": {"type": "number"},
                            "more_than_2_5_probability": {"type": "number"},
                            "cards_home": {"type": "number"},
                            "cards_away": {"type": "number"},
                            "corners_home": {"type": "number"},
                            "corners_away": {"type": "number"},
                            "stats": {
                                "type": "object",
                                "properties": {
                                    "home_team_stats": {"type": "string"}
                                }
                            },
                            "last_games": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "date": {"type": "string"},
                                        "competition": {"type": "string"},
                                        "match": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "away_team": {
                        "type": "object",
                        "properties": {
                            "probability_win": {"type": "number"},
                            "probability_draw": {"type": "number"},
                            "probability_home_win": {"type": "number"},
                            "victories_home_vs_away": {"type": "number"},
                            "draws_home_vs_away": {"type": "number"},
                            "losses_home_vs_away": {"type": "number"},
                            "goals_scored": {"type": "number"},
                            "AEM": {"type": "number"},
                            "more_than_1_5_probability": {"type": "number"},
                            "more_than_2_5_probability": {"type": "number"},
                            "cards_home": {"type": "number"},
                            "cards_away": {"type": "number"},
                            "corners_home": {"type": "number"},
                            "corners_away": {"type": "number"},
                            "stats": {
                                "type": "object",
                                "properties": {
                                    "away_team_stats": {"type": "string"}
                                }
                            },
                            "last_games": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "date": {"type": "string"},
                                        "competition": {"type": "string"},
                                        "match": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                },
                "required": ["home_team", "away_team"]
            }
        }]
    )

        try:
            generated_json = completion.choices[0].message.function_call.arguments

        except Exception as e:
            print(f"Error parsing the JSON data: {e}")
            generated_json = None

        return json.loads(generated_json)
    
    def get_positive_ev_odds(self, odds_json, match_stats_json):
        function_definition = {
            "name": "get_positive_ev_odds",
            "description": "Returns the odds with a positive expected value (EV) and justifications.",
            "parameters": {
                "type": "object",
                "properties": {
                    "positive_ev_odds": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "odd_id": {"type": "integer"},
                                "name": {"type": "string"},
                                "odds": {"type": "number"},
                                "expected_value": {"type": "number"},
                                "justification": {"type": "string"}
                            },
                            "required": ["odd_id", "name", "odds", "expected_value", "justification"]
                        }
                    }
                },
                "required": ["positive_ev_odds"]
            }
        }

        system_message = {
            "role": "system",
            "content": "You are a sports betting analyst. Calculate expected value (EV) for each bet and return only those with positive EV."
        }

        user_message = {
            "role": "user",
            "content": f"""
            You are provided with JSON data for a match's odds and relevant statistics. For each betting odd, calculate the Expected Value (EV) using the formula:

            EV = (Fair Win Probability x Profit if Win) - (Fair Loss Probability x Stake)

            1. Extract and interpret data: Identify the fair probabilities for each outcome.
            2. Calculate EV: Use the formula above with Profit if Win = Odds - 1 and a Stake of 1 unit.
            3. Adjust probabilities based on stats provided home_team: (probability_win, probability_draw, probability_away_win, victories_home_vs_away, draws_home_vs_away, losses_home_vs_away, goals_scored, AEM, more_than_1_5_probability, more_than_2_5_probability, cards_home, cards_away, corners_home, corners_away, stats: home_team_stats, last_games: (date, competition, match)), away_team: (probability_win, probability_draw, probability_home_win, victories_home_vs_away, draws_home_vs_away, losses_home_vs_away, goals_scored, AEM, more_than_1_5_probability, more_than_2_5_probability, cards_home, cards_away, corners_home, corners_away, stats: away_team_stats, last_games: (date, competition, match))
            4. Document only positive EV bets with 400-character justifications.

            JSON Data:
            1. Odds data:
            {odds_json}

            2. Match and Team Stats data:
            {match_stats_json}
            """
        }
        
        completion = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[system_message, user_message],
            functions=[function_definition]
        )

        # Retrieve and return the JSON result
        try:
            generated_json = completion.choices[0].message.function_call.arguments
            return json.loads(generated_json)
        except Exception as e:
            print(f"Error parsing the JSON data: {e}")
            return None
        
        
