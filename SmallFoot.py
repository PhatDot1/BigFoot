import requests
import json
import csv
import os
import subprocess

# OpenSea API Key and Webhook URL from GitHub Secrets
API_KEY = os.getenv("OPENSEA_API_KEY")
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Early exit if API key is not found
if not API_KEY:
    print("Error: Missing OPENSEA_API_KEY. Exiting script.")
    exit(1)

print(f"API Key length: {len(API_KEY) if API_KEY else 'API Key is None'}")

# Footium Clubs collection slug (from the OpenSea URL: https://opensea.io/collection/footium-clubs)
collection_slug = "footium-clubs"

# URL to fetch all active listings for the collection
url = f"https://api.opensea.io/api/v2/listings/collection/{collection_slug}/all"

# Initial query parameters (limit and optional cursor)
params = {
    "limit": 100,  # Max number of listings to return (between 1 and 100)
}

headers = {
    "accept": "application/json",
    "x-api-key": API_KEY
}

# Define the updated GraphQL endpoint for player metadata
GRAPHQL_ENDPOINT = "https://live.api.footium.club/api/graphql"

# CSV file to track posted listings
CSV_FILE = "footium_clubs_listings.csv"

# Function to get player metadata
def get_player_metadata(club_id, player_number):
    selected_player_id = f"2-{club_id}-{player_number}"
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
        # Fixed issue: Removed the unmatched closing bracket
        if "data" in data and "player" in data["data"]:
            return data["data"]["player"]
        else:
            return None
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

# Function to check if a player has "Rare" rarity and is unminted
def has_unminted_rare_player(club_id):
    for player_number in range(5):  # Assuming player numbers 0 to 4
        metadata = get_player_metadata(club_id, player_number)
        if metadata and metadata.get("rarity") == "Rare":
            return True
    return False

# Function to fetch and format listings
def fetch_listings():
    # Ensure CSV file exists
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['OpenSea URL', 'Footium URL'])  # Header row

    while True:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            listings_data = response.json()

            if 'listings' in listings_data:
                listings = listings_data['listings']
                print(f"Found {len(listings)} active listings in the Footium Clubs collection:\n")

                for listing in listings:
                    try:
                        identifier = listing['protocol_data']['parameters']['offer'][0]['identifierOrCriteria']
                        token = listing['protocol_data']['parameters']['offer'][0]['token']

                        if has_unminted_rare_player(identifier):
                            opensea_url = f"https://opensea.io/assets/arbitrum/{token}/{identifier}"
                            footium_url = f"https://footium.club/game/club/{identifier}"

                            # Check if the listing is already in the CSV
                            if not is_listing_in_csv(opensea_url):
                                # Post to webhook
                                post_to_webhook(opensea_url, footium_url)

                                # Add the listing to the CSV
                                add_listing_to_csv(opensea_url, footium_url)

                                # Commit and push CSV changes
                                commit_and_push_changes()

                    except (KeyError, IndexError) as e:
                        print(f"Error processing listing: {e}. Skipping...\n")

                if 'next' in listings_data:
                    params['next'] = listings_data['next']
                    print(f"Next page cursor: {listings_data['next']}\n")
                else:
                    print("No more listings to fetch.")
                    break
            else:
                print("No listings found in the collection.")
                break
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            break

# Function to check if a listing is already in the CSV
def is_listing_in_csv(opensea_url):
    with open(CSV_FILE, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row and row[0] == opensea_url:
                return True
    return False

# Function to add a new listing to the CSV
def add_listing_to_csv(opensea_url, footium_url):
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([opensea_url, footium_url])

# Function to post to Discord webhook
def post_to_webhook(opensea_url, footium_url):
    message = f"New club with academy rare listed:\nOpenSea URL: {opensea_url}\nFootium URL: {footium_url}"
    data = {
        "content": message
    }
    response = requests.post(WEBHOOK_URL, json=data)
    if response.status_code == 204:
        print("Message successfully sent to Discord webhook.")
    else:
        print(f"Failed to send message to webhook. Status code: {response.status_code}")

# Function to commit and push changes to the CSV
def commit_and_push_changes():
    try:
        subprocess.run(["git", "add", CSV_FILE], check=True)
        subprocess.run(["git", "commit", "-m", "Update CSV with new listings"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("CSV changes committed and pushed.")
    except subprocess.CalledProcessError as e:
        print(f"Error committing or pushing changes: {e}")

# Start fetching listings
fetch_listings()
