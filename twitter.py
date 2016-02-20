from requests_oauthlib import OAuth1
from urlparse import parse_qs
import requests
import csv
import json
import os
import errno
import sys

# Metadata
OLDEST_TWEET_DATE = "2015-01-01"
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
    # Removes to write to if it already exists
    filename = "data/" + query.lower().replace(" ", "-") + ".csv"
    try:
        os.remove(filename)
    except OSError:
        pass
    stop = False
    oldest_id = -1
    with open(filename, "wb+") as outfile:
        f = csv.writer(outfile)
        f.writerow(["content"])      
        while not stop:
            # Sets the params
            params = {'q' : query, 'since' : OLDEST_TWEET_DATE, 'count' : 100, 'until', '2016-02-19'}
            if oldest_id != -1:
                params["max_id"] = oldest_id
            print "Oldest Id:", oldest_id
            # Makes a GET request
            response = requests.get(url=SEARCH_URL, auth=oauth, params=params)
            result =  json.loads(response.content)
            # Stops loop when no more results to show
            if len(result) == 0:
                stop = True
            else:
                # Writes to CSV 
                for r in result["statuses"]:
                    f.writerow([u''.join(r["text"]).encode('utf-8')])
                    if oldest_id == -1 or r["id"] < oldest_id:
                        oldest_id = r["id"]
# Executable Code
args = sys.argv
if len(sys.argv) != 2:
    print "Must have exactly 1 argument, the search query string"
else:
    oauth = get_oauth()
    print "Search: " + sys.argv[1]
    search(sys.argv[1], oauth)
