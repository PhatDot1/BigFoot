import requests
import json
import time
import os

# Define the updated GraphQL endpoint for player metadata
GRAPHQL_ENDPOINT = "https://live.api.footium.club/api/graphql"
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL2")

# Function to get player data by ID
def get_player_data_with_attributes(player_id):
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
            playerAttributes {
                age
            }
            imageUrls {
                player
                card
                thumb
            }
        }
    }
    """
    
    variables = {
        "where": {
            "id": player_id
        }
    }
    
    try:
        response = requests.post(GRAPHQL_ENDPOINT, json={"query": query, "variables": variables})
        response.raise_for_status()  # Raise an exception for HTTP errors

        data = response.json()
        
        # Return player data if found
        if "data" in data and "player" in data["data"]:
            return data["data"]["player"]
        else:
            print(f"Player {player_id} not found.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to post the player metadata to Discord webhook
def post_to_discord(player_metadata):
    content = {
        "content": f"Player Metadata Found:\n{json.dumps(player_metadata, indent=4)}"
    }
    try:
        response = requests.post(DISCORD_WEBHOOK, json=content)
        response.raise_for_status()
        print("Successfully posted to Discord.")
    except requests.exceptions.RequestException as e:
        print(f"Error posting to Discord: {e}")

# Loop through player IDs and check for metadata
def check_players():
    for player_number in range(181, 192):
        player_id = f"5-125-{player_number}-REWARD"
        print(f"Checking player: {player_id}")
        player_metadata = get_player_data_with_attributes(player_id)
        if player_metadata:
            print(f"Player metadata found for {player_id}:")
            print(json.dumps(player_metadata, indent=4))
            post_to_discord(player_metadata)
            return  # Exit once metadata is found

# Test the function
if __name__ == "__main__":
    check_players()
