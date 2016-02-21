import numpy as np
import requests
import json
from pymldb import Connection
import csv

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
def normalize_state_name(self, string):
    if not string:
        return None
    params = {"place": string, "apiKey": LOCATION_API_KEY}
    response = requests.get(url=LOCATION_API_URL, params=params)
    result = json.loads(response.content)
    if "locations" not in result:
        return None
    result = result["locations"]
    if len(result) > 0 and "country" in result[0] and result[0]["country"]["code"] == "US" and "state" in result[0] and result[0]["state"]:
        return result[0]["state"]["name"]
    return None


class Candidate_Predictor:
    candidates = []
    candidate_favor = {}
    mldb = None
    theta = []

    def __init__(self, port=8080, pool=candidates):
        self.mldb = Connection(host="http://localhost:{0}".format(port))
        self.set_wordnet()
        self.candidates = pool

    # Tickles SentiWordnet, removing POS data
    def set_wordnet(self):
        self.mldb.put('/v1/procedures/sentiwordneter', {
            "type": "import.sentiwordnet",
            "params": {
                "dataFileUrl": "file:///mldb_data/SentiWordNet_3.0.0_20130122.txt",
                "outputDataset": "sentiwordnet",
                "runOnCreation": True
            }
        })
        self.mldb.put("/v1/procedures/baseWorder", {
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
        self.mldb.put("/v1/procedures/baseWorder", {
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

    # check sentiment of sentence
    def return_sent(self, sentence):
        # remove quotes because it messes with query
        no_quote = sentence.replace("'", '')
        split = list(set(no_quote.split(' ')))
        join = "','".join(split)
        sent_sent = self.mldb.query("select 'avg.NegSenti','avg.PosSenti' from senti_clean2 where rowName() in ('{0}'')".format(join))
        overall_senti = 0
        if 'avg.NegSenti' in sent_sent.keys():
            for word in sent_sent['avg.NegSenti'].keys():
                overall_senti += sent_sent['avg.PosSenti'][word]-sent_sent['avg.NegSenti'][word]
        return overall_senti

    # run tweet csvs about candidates through sentiment analysis
    def run_candidates(self):
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
                                overall_senti = self.return_sent(row[0])
                                if state not in states:
                                    states[state] = overall_senti
                                else:
                                    states[state] = states[state]+overall_senti
                    else:
                        pass
            self.candidate_favor[candidate] = states

    # Returns the sentiment value stored in the database
    def get_sentiment_value(self, candidate, state):
        self.candidate_favor[candidates[candidate]][state]

    # Gets all the results stored in the database
    def get_results(self):
        # Format: [[CANDIDATE_ID, STATE_ID, VOTE_PERCENTAGE], ...]
        pass

    # Calculates the parameteres using normal equations
    def calculate_params(self):
        inp = []
        out = []
        results = self.get_results()
        for r in results:
            candidate = r[0]
            state = r[1]
            # TODO: More inputs
            inp.append(self.get_sentiment_value(candidate, state))
            out.append(r[3])
        # Linear regression
        x = np.array(inp)
        self.theta = np.multiply(np.multiply(np.linalg.inv(np.multiply(np.transpose(x), x)), np.transpose(x)), out)

    # Trains all the sentiment values based on the expected results
    def train(self):
        self.run_candidates()
        self.calculate_params()

    # Predicts the situation for a given list of candidates for a specific state
    # Returns a map of the percentage each candidate is predicted to have
    def predict(self, candidates, state):
        results = {}
        for candidate in candidates:
            inp = [self.get_sentiment_value(candidate, state)]
            # TODO: WTF
            results[candidate] = np.multiply(self.theta, inp)
        return results


if __name__ == "__main__":
    test = Candidate_Predictor(pool=['bernie-sanders'])
    test.run_candidates()
    print(test.candidate_favor)
