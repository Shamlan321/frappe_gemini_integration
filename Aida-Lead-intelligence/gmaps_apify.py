from apify_client import ApifyClient

# Initialize the ApifyClient with your API token
client = ApifyClient("apify_api_8ViThYsJGuDpcAQXNzKKdem6umJJS20PdRUV")

# Prepare the Actor input
run_input = {
    "searchStringsArray": ["restaurant"],
    "locationQuery": "New York, USA",
    "maxCrawledPlacesPerSearch": 5,
    "language": "en",
    "placeMinimumStars": "",
    "website": "allPlaces",
    "searchMatching": "all",
    "skipClosedPlaces": False,
}

# Run the Actor and wait for it to finish
run = client.actor("WnMxbsRLNbPeYL6ge").call(run_input=run_input)

# Fetch and print Actor results from the run's dataset (if there are any)
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item)