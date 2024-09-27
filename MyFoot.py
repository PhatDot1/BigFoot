import requests
import json
import csv
import os
import time

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL2")
OPENSEA_API_KEY = os.getenv("OPENSEA_API_KEY")
GRAPHQL_ENDPOINT = "https://live.api.footium.club/api/graphql"

# Randomn clubs to monitor
specific_clubs = [
    "3-2878-4", 
    "3-29-4",  
    "3-1-4",   
    "3-124-4"   
]

# Range of club IDs to check - likely candidates for early testing
club_range = list(range(117, 138))

# OpenSea specific parameters
opensea_collection_slug = "footium-clubs"
opensea_url = f"https://api.opensea.io/api/v2/listings/collection/{opensea_collection_slug}/all"

headers = {
    "accept": "application/json",
    "x-api-key": OPENSEA_API_KEY
}

# CSV file to track posted listings
CSV_FILE = "footium_clubs_listings.csv"

# Function to get player metadata
def get_player_metadata(selected_player_id):
    query = """
    query getPlayerMetadata($where: PlayerWhereUniqueInput!) {
        player(where: $where) {
            id
            rarity
            creationRating
            potential
            club {
                id
                name
            }
        }
    }
    """
    variables = {
        "where": {
            "id": selected_player_id
        }
    }

    response = requests.post(GRAPHQL_ENDPOINT, json={"query": query, "variables": variables})
    
    if response.status_code == 200:
        data = response.json()
        if "data" in data and "player" in data["data"]:
            return data
