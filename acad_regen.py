import requests
import json
import os

# Discord Webhook URL from environment variables
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
GRAPHQL_ENDPOINT = "https://live.api.footium.club/api/graphql"

# Expected URL for comparison
EXPECTED_CARD_URL = "https://d3pnl4e3sr8zku.cloudfront.net/images/card/4-1-4/713e3e7cdf2e374f3e40b937ec0928d9.svg"

# Function to get player metadata with all attributes for Club ID 1
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
                leadership
                condition
                stamina
                gamesSuspended
                accumulatedYellows
                isLatest
                timestamp
                footedness
                weakFootAbility
                unlockedPotential
                usedPotential
                accumulatedMinutes
            }
            imageUrls {
                player
                card
                thumb
            }
        }
    }
    """
    
    variables = {"where": {"id": player_id}}
    
    try:
        response = requests.post(GRAPHQL_ENDPOINT, json={"query": query, "variables": variables})
        response.raise_for_status()
        
        data = response.json()
        
        if "data" in data and "player" in data["data"]:
            return data["data"]["player"]
        else:
            print(f"No data found for player ID {player_id}.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request error for player ID {player_id}: {e}")
        return None

# Function to check if the card image is different and send a message
def check_card_image_and_notify(player_data):
    card_url = player_data.get("imageUrls", {}).get("card", "")
    player_id = player_data.get("id")
    
    if card_url != EXPECTED_CARD_URL:
        message = f"ACADEMY'S REFRESHED! QUERY NUMBER 4-X-{player_id.split('-')[-1]}"
        data = {"content": message}
        response = requests.post(WEBHOOK_URL, json=data)
        
        if response.status_code == 204:
            print("Notification successfully sent to Discord.")
        else:
            print(f"Failed to send notification to Discord. Status code: {response.status_code}")

# Retrieve data for Club ID 1 players and check images
def retrieve_and_check_players(club_id=1):
    players_metadata = []
    for player_number in range(5):  # Assuming players numbered 0 to 4
        player_id = f"4-{club_id}-{player_number}"
        player_data = get_player_data_with_attributes(player_id)
        
        if player_data:
            players_metadata.append(player_data)
            check_card_image_and_notify(player_data)
        else:
            print(f"Failed to retrieve data for player ID {player_id}")

# Run the function for Club ID 1
retrieve_and_check_players()
