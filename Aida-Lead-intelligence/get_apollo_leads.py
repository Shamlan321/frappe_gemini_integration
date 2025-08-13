import http.client
import json

conn = http.client.HTTPSConnection("apollo-io-no-cookies-required.p.rapidapi.com")

# Use a dictionary and convert to JSON string
payload_dict = {
    "url": "https://app.apollo.io/#/companies?organizationNumEmployeesRanges[]=10001&page=1&sortByField=%5Bnone%5D&sortAscending=false",
    "page": 1
}
payload = json.dumps(payload_dict)  # Properly serializes to JSON

headers = {
    'x-rapidapi-key': "f56cec0939msh4083990fab47035p1adf74jsn8085b79e2d87",
    'x-rapidapi-host': "apollo-io-no-cookies-required.p.rapidapi.com",
    'Content-Type': "application/json"
}

conn.request("POST", "/search_organizations_via_url", payload, headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))