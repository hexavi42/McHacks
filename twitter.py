from requests_oauthlib import OAuth1
from urlparse import parse_qs
import requests
import csv
import json
import os
import errno

# URLs 
REQUEST_TOKEN_URL = "https://api.twitter.com/oauth/request_token"
AUTHORIZE_URL = "https://api.twitter.com/oauth/authorize?oauth_token="
ACCESS_TOKEN_URL = "https://api.twitter.com/oauth/access_token"
SEARCH_URL = "https://api.twitter.com/1.1/search/tweets.json"
# Keys
TWITTER_API_KEY = "NfDO9jbf2hagelMo6DPiRWHas"
TWITTER_SECRET_KEY = "qjCfzFmWtNxtQv9lUmt5GNRni3yE1G4vtSkTLhpnzz38M7MEQU"
TWITTER_OAUTH_TOKEN = "701106749835579395-t56eQaw3yXlhjbVXdhNCBZ0snCBqgeb"
TWITTER_OAUTH_SECRET = "rBOyCHLnNxNEwKJA49ufN1kWhOeRBhqhYdyGWf2GVt0mT"

# Generates the OAUTH Keys; should only be ran once
def setup_oauth():
    # Request token
    oauth = OAuth1(TWITTER_API_KEY, client_secret=TWITTER_SECRET_KEY)
    r = requests.post(url=REQUEST_TOKEN_URL, auth=oauth)
    credentials = parse_qs(r.content)
    resource_owner_key = credentials.get('oauth_token')[0]
    resource_owner_secret = credentials.get('oauth_token_secret')[0]
    # Authorize
    authorize_url = AUTHORIZE_URL + resource_owner_key
    print 'Please go here and authorize: ' + authorize_url
    verifier = raw_input('Please input the verifier: ')
    oauth = OAuth1(TWITTER_API_KEY,
                   client_secret=TWITTER_SECRET_KEY,
                   resource_owner_key=resource_owner_key,
                   resource_owner_secret=resource_owner_secret,
                   verifier=verifier)
    # Finally, Obtain the Access Token
    r = requests.post(url=ACCESS_TOKEN_URL, auth=oauth)
    credentials = parse_qs(r.content)
    token = credentials.get('oauth_token')[0]
    secret = credentials.get('oauth_token_secret')[0]
    return token, secret
# With OAUTH Keys generated, gets the temporary access token and secret 
def get_oauth(): 
    oauth = OAuth1(TWITTER_API_KEY,
                client_secret=TWITTER_SECRET_KEY, 
                resource_owner_key=TWITTER_OAUTH_TOKEN,
                resource_owner_secret=TWITTER_OAUTH_SECRET)
    return oauth
# Uses Twitter REST API to search for tweets with the query and saves to csv
def search(query, oauth):
    # Makes a RESTful GET request
    params = {'q' : query}
    request = requests.get(url=SEARCH_URL, auth=oauth, params=params)
    result = request.json
    # Removes to write to if it already exists
    filename = "data/" + query + ".csv"
    try:
        os.remove(filename)
    except OSError:
        pass
    # Writes to CSV 
    with open(filename, "wb+") as outfile:
    	f = csv.writer(outfile)
    	f.writerow(["pk", "model", "codename", "name", "content_type"])
    return request.json

oauth = get_oauth()
print search("Bernie Sanders", oauth)
