
import requests
import csv
import os

API_KEY = os.getenv("OPENSEA_API_KEY")
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL2")
GRAPHQL_ENDPOINT = "https://live.api.footium.club/api/graphql"

# URL to fetch all active listings for the Footium Clubs collection from OpenSea
collection_slug = "footium-clubs"
url = f"https://api.opensea.io/api/v2/listings/collection/{collection_slug}/all"
params = {"limit": 100}
headers = {"accept": "application/json", "x-api-key": API_KEY}

# CSV file to track posted listings
CSV_FILE = "footium_clubs_listings.csv"

# Hardcoded clubs to monitor
specific_clubs = ["3-2878-4", "3-29-4", "3-1-4", "3-124-4"]

# Club ID range to monitor
club_range = list(range(117, 138))


# Function to get player metadata
def get_player_metadata(club_id, player_number):
    selected_player_id = f"3-{club_id}-{player_number}"
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
    variables = {"where": {"id": selected_player_id}}
    response = requests.post(GRAPHQL_ENDPOINT, json={"query": query, "variables": variables})
    
    if response.status_code == 200:
        data = response.json()
        if "data" in data and "player" in data["data"]:
            return data["data"]["player"]
    return None


# Function to check if a player has "Rare" rarity and is unminted
def has_unminted_rare_player(club_id):
    for player_number in range(5):  # Assuming player numbers 0 to 4
        metadata = get_player_metadata(club_id, player_number)
        if metadata and metadata.get("rarity") == "Rare":
            return True
    return False


# Function to log the result of each club check
def log_club_check(club_id):
    print(f"Checking club: {club_id}")
    found_rare = has_unminted_rare_player(club_id)
    if found_rare:
        print(f"Rare player found for club {club_id}!")
        opensea_url = f"https://opensea.io/assets/arbitrum/0xd0a8ba528dfe402d34d34f171e5ff3e65bd4c9d4/{club_id}"
        footium_url = f"https://footium.club/game/club/{club_id}"
        post_to_webhook(opensea_url, footium_url)
    else:
        print(f"No player metadata found for club {club_id}")


# Function to post to Discord webhook
def post_to_webhook(opensea_url, footium_url):
    message = (
        f"Rare player found!\n"
        f"OpenSea URL: {opensea_url}\n"
        f"Footium URL: {footium_url}"
    )
    data = {"content": message}
    response = requests.post(WEBHOOK_URL, json=data)
    if response.status_code == 204:
        print("Message successfully sent to Discord webhook.")
    else:
        print(f"Failed to send message to webhook. Status code: {response.status_code}")


# Function to fetch and check OpenSea listings
def fetch_opensea_listings():
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        listings_data = response.json()
        if 'listings' in listings_data:
            listings = listings_data['listings']
            print(f"Found {len(listings)} active listings in the Footium Clubs collection:")
            for listing in listings:
                try:
                    identifier = listing['protocol_data']['parameters']['offer'][0]['identifierOrCriteria']
                    log_club_check(identifier)
                except (KeyError, IndexError) as e:
                    print(f"Error processing listing: {e}. Skipping...\n")
        else:
            print("No listings found in the collection.")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


# Function to check hardcoded clubs
def check_hardcoded_clubs():
    print("Checking hardcoded clubs...")
    for club in specific_clubs:
        log_club_check(club)


# Function to check clubs in the specified range
def check_club_range():
    print("Checking clubs in range...")
    for club_id in club_range:
        log_club_check(f"3-{club_id}-4")


# Main function to run all checks
def main():
    fetch_opensea_listings()
    check_hardcoded_clubs()
    check_club_range()


# Run the script
if __name__ == "__main__":
    main()

