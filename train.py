import numpy as np
import requests
import json
from pymldb import Connection
import csv

# TODO: Make less shitty by not having global fucking variables
candidates = [
    'bernie-sanders',
    'hillary-clinton',
    'donald-trump',
    'jeb-bush',
    'ben-carson',
    'ted-cruz',
    'john-kasich',
    'marco-rubio'
]
candidate_favor = {}
mldb = Connection(host="http://localhost:8080")
theta = []

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
    params = {"place": string, "apiKey": LOCATION_API_KEY}
    response = requests.get(url=LOCATION_API_URL, params=params)
    result = json.loads(response.content)
    if result["locations"]:
        return None
    result = result["locations"]
    if len(result) > 0 and result[0]["country"]["code"] == "US" and result[0]["state"]:
        return result[0]["state"]["name"]
    return None


# Returns the sentiment value stored in the database
def get_sentiment_value(candidate, state):
    candidate_favor[candidates[candidate]][state]


# Gets all the results stored in the database
def get_results():
    # Format: [[CANDIDATE_ID, STATE_ID, VOTE_PERCENTAGE], ...]
    pass


# Calculates all the sentiment values, then stores it in the db
def calculate_sentiments():
    mldb.put('/v1/procedures/sentiwordneter', {
        "type": "import.sentiwordnet",
        "params": {
            "dataFileUrl": "file:///mldb_data/SentiWordNet_3.0.0_20130122.txt",
            "outputDataset": "sentiwordnet",
            "runOnCreation": True
        }
    })
    mldb.put("/v1/procedures/baseWorder", {
        "type": "transform",
        "params": {
            "inputData": """
                select *, jseval('
                    return x.split("#")[0];
                ', 'x', rowName()) as baseWord
                from sentiwordnet
            """,
            "outputDataset": "senti_clean",
            "runOnCreation": True
        }
    })
    mldb.put("/v1/procedures/baseWorder", {
        "type": "transform",
        "params": {
            "inputData": """
                   select avg({* EXCLUDING(baseWord)}) as avg,
                          min({* EXCLUDING(baseWord)}) as min,
                          max({* EXCLUDING(baseWord)}) as max,
                   count(*) as cnt
                    NAMED baseWord
                    from senti_clean
                    group by baseWord
                    order by cnt desc
            """,
            "outputDataset": "senti_clean2",
            "runOnCreation": True
        }
    })
    for candidate in candidates:
        states = {}
        with open('data/{0}.csv'.format(candidate), 'rb') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in spamreader:
                if len(row) == 2 and row[1]:
                    state = normalize_state_name(row[1])
                    if state is None:
                        pass
                    else:
                        no_quote = row[0].replace("'", '')  # remove quotes because it messes with query
                        split = "'{0}'".format(no_quote.replace(' ', "','"))
                        sent_sent = mldb.query("select 'avg.NegSenti','avg.PosSenti' from senti_clean2 where rowName() in ({0})".format(split))
                        overall_senti = 0
                        if 'avg.NegSenti' in sent_sent.keys():
                            for word in sent_sent['avg.NegSenti'].keys():
                                overall_senti += sent_sent['avg.PosSenti'][word]-sent_sent['avg.NegSenti'][word]
                            if state not in states:
                                states[state] = overall_senti
                            else:
                                states[state] = states[state]+overall_senti
                else:
                    pass
        candidate_favor[candidate] = states


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


# Trains all the sentiment values based on the expected results
def train():
    calculate_sentiments()
    calculate_params()


# Predicts the situation for a given list of candidates for a specific state
# Returns a map of the percentage each candidate is predicted to have
def predict(candidates, state):
    results = {}
    for candidate in candidates:
        inp = [get_sentiment_value(candidate, state)]
        # TODO: WTF
        results[candidate] = np.multiply(theta, inp)
    return results


if __name__ == "__main__":
    calculate_sentiments()
    print(candidate_favor)
