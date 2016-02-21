import numpy as np
import requests
import json

# API Info
LOCATION_API_URL = "http://api.fullcontact.com/v2/address/locationEnrichment.json"
LOCATION_API_KEY = "82eeccbc6e96bcd1"
# Candidates
SANDERS = 1
CLINTON = 2
TRUMP = 3
BUSH = 4
CARSON = 5
CRUZ = 6
KASICH = 7
RUBIO = 8

# Should get the normalized state name that most likely is the state of location string.
# Returns None if not in the US or not enough info
def normalize_state_name(string):
    if not string:
        return None
    params = {"place" : string, "apiKey" : LOCATION_API_KEY}
    response = requests.get(url=LOCATION_API_URL, params=params)
    result = json.loads(response.content)["locations"]
    if len(result) > 0 and result[0]["country"]["code"] == "US" and result[0]["state"]:
        return result[0]["state"]["name"]
    return None
# Returns the sentiment value stored in the database
def get_sentiment_value(candidate, state):
    pass

# Gets all the results stored in the database
def get_results():
    # Format: [[CANDIDATE_ID, STATE_ID, VOTE_PERCENTAGE], ...]
    pass

# Calculates all the sentiment values, then stores it in the db
def calculate_sentiments():
    pass

# Stores the parameters for the linear regression into the db
def set_params(params):
    pass

# Calculates the parameteres using normal equations
def calculate_params():
    inp = []
    out = []
    results = get_results()
    for r in results:
        candidate = r[0]
        state = r[1]
        # TODO: More inputs
        inp.append(get_sentiment_value(candidate, state))
        out.append(r[3])
    # Linear regression
    x = np.array(inp)
    theta = np.multiply(np.multiply(np.linalg.inv(np.multiply(np.transpose(x), x)), np.transpose(x)), out)
    set_params(theta)

# Trains all the sentiment values based on the expected results
def train():
    calculate_sentiments()
    calculate_params()

# Predicts the situation for a given list of candidates for a specific state
# Returns a map of the percentage each candidate is predicted to have
def predict(candidates, state):
    pass

