import numpy as np
import requests
import json
from pymldb import Connection
import csv
import re
from dateutil import parser
import operator
from state_code import state_code

all_candidates = [
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
def normalize_state_name(string):
    if not string:
        return None
    elif re.search(', [A-Z]{2}$', string):
        match = re.search(', ([A-Z]{2})$', string)
        try:
            return state_code[match.group(1)]
        except:
            return None
    # last resort - extreeeeemely limited API calls
    else:
        params = {"place": string, "apiKey": LOCATION_API_KEY}
        response = requests.get(url=LOCATION_API_URL, params=params)
        result = json.loads(response.content)
        if "locations" not in result:
            return None
        result = result["locations"]
        for loc in result:
            if "country" in loc and 'code' in loc["country"] and\
             loc["country"]['code'] == 'US':
                try:
                    return loc["state"]["name"]
                except:
                    return None


class Candidate_Predictor:
    states = {}
    mldb = None
    theta = []
    depth = False
    results = []
    candidate_favor = {}
    total_pop = 0
    gone_count = 0

    def __init__(self, port=8080, pool=all_candidates, depth=False):
        self.mldb = Connection(host="http://localhost:{0}".format(port))
        self.set_wordnet()
        self.candidates = pool
        self.depth = depth

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
        sent_sent = self.mldb.query("select avg* from senti_clean2 where rowName() in ('{0}')".format(join))
        overall_senti = 0
        if 'avg.NegSenti' in sent_sent.keys():
            for word in sent_sent['avg.NegSenti'].keys():
                overall_senti += sent_sent['avg.PosSenti'][word]-sent_sent['avg.NegSenti'][word]
        return overall_senti

    # run tweet csvs about candidates through sentiment analysis
    def run_candidates(self):
        for candidate in self.candidates:
            counter = 0
            with open('data2/{0}.csv'.format(candidate), 'rb') as csvfile:
                spamreader = csv.DictReader(csvfile)
                for row in spamreader:
                    if self.depth and counter > self.depth:
                        break
                    else:
                        try:
                            state = normalize_state_name(row['location'])
                        except:
                            state = None
                        if state is None:
                            self.gone_count += 1
                            pass
                        else:
                            overall_senti = self.return_sent(row['text'])
                            if state not in self.states:
                                self.states[state] = {row['user_id']: {candidate: overall_senti}, 'pop': 1}
                            elif row['user_id'] not in self.states[state]:
                                self.states[state][row['user_id']] = {candidate: overall_senti}
                                self.total_pop += 1
                                self.states[state]['pop'] += 1
                            elif candidate not in self.states[state][row['user_id']]:
                                self.states[state][row['user_id']][candidate] = overall_senti
                            else:
                                self.states[state][row['user_id']][candidate] = self.states[state][row['user_id']][candidate]+overall_senti
                            counter += 1
                            if candidate not in self.candidate_favor:
                                self.candidate_favor[candidate] = {}
                            if state not in self.candidate_favor[candidate]:
                                self.candidate_favor[candidate][state] = {'minTime': parser.parse(row['created_at']),
                                                                   'maxTime': parser.parse(row['created_at']),
                                                                   'RT': int(row['retweets'] if row['retweets'] else 0)} 
                            else:
                                if parser.parse(row['created_at']) > self.candidate_favor[candidate][state]['maxTime']:
                                    self.candidate_favor[candidate][state]['maxTime'] = parser.parse(row['created_at'])
                                elif parser.parse(row['created_at']) < self.candidate_favor[candidate][state]['minTime']:
                                    self.candidate_favor[candidate][state]['minTime'] = parser.parse(row['created_at'])
                                self.candidate_favor[candidate][state]['RT'] = int(row['retweets'] if row['retweets'] else 0)

    def calc_supporters(self):
        for state in state_code.values():
            for citizen in self.states[state]:
                try:
                    top_pick = max(self.states[state][citizen].iteritems(), key=operator.itemgetter(1))[0]
                except:
                    print(self.states[state][citizen])
                if state not in self.candidate_favor[top_pick]:
                    self.candidate_favor[top_pick][state] = {'pop': 1}
                    self.candidate_favor[top_pick][state]['perc'] = float(1)/self.states[state]['pop']*100
                else:
                    self.candidate_favor[top_pick][state]['pop'] += 1
                    self.candidate_favor[top_pick][state]['perc'] = float(self.candidate_favor[top_pick][state]['pop'])/self.states[state]['pop']*100

    # Returns the sentiment value stored in the database
    def get_sentiment_value(self, candidate, state):
        self.candidate_favor[all_candidates[candidate]][state]

    # Hardcoded, because hackathon
    def generate_results(self):
        # Democratic Nevada
        self.results.append([2, "Nevada", 52.7]) # Clinton
        self.results.append([1, "Nevada", 47.2]) # Sanders
        # Republican South Carolina
        self.results.append([3, "South Carolina", 32.5]) # Trump
        self.results.append([8, "South Carolina", 22.5]) # Rubio
        self.results.append([6, "South Carolina", 22.3]) # Cruz
        self.results.append([4, "South Carolina", 7.8]) # Bush
        self.results.append([7, "South Carolina", 7.6]) # Kasich
        self.results.append([5, "South Carolina", 7.2]) # Carson
    
    def get_input(self, candidate, state):
        inp = []
        max_tweet_time = (self.candidate_favor[candidate][state]['maxTime'] - self.candidate_favor[candidate][state]['minTime']).total_seconds() / 100
        inp.append(self.candidate_favor[candidate][state]['perc'])
        inp.append(self.candidate_favor[candidate][state]['RT'])
        inp.append(self.candidate_favor[candidate][state]['count'])
        inp.append(max_tweet_time)
        return inp

    # Calculates the parameteres using normal equations
    def calculate_params(self):
        inp = []
        out = []
        results = self.get_results()
        for r in results:
            candidate = r[0]
            state = r[1]
            inp.append(self.get_input(candidate, state))
            out.append(r[3])
        # Linear regression
        x = np.array(inp)
        self.theta = np.multiply(np.multiply(np.linalg.inv(np.multiply(np.transpose(x), x)), np.transpose(x)), out)

    # Trains all the sentiment values based on the expected results
    def train(self):
        results = self.generate_results()
        self.run_candidates()
        self.calculate_params()

    # Predicts the situation for a given list of candidates for a specific state
    # Returns a map of the percentage each candidate is predicted to have
    def predict(self, state):
        results = {}
        total = 0
        for candidate in self.candidates:
            inp = self.get_input(candidate, state)
            results[candidate] = np.multiply(self.theta, inp)
            total += results[candidate]
        # Normalize the results so they add to 100%
        factor = 100 / results
        for candidate in self.candidates:
            results[candidate] = results[candidate] * factor
        return results

    def load(self, json_file):
        with open(json_file, 'r') as backup:
            temp = json.load(backup)
            self.states = temp['states']
            self.candidate_favor = temp['candidate_favor']

    def dump(self, file="dump.json"):
        with open(file, 'w') as dumpfile:
            json.dump({"states":self.states}, dumpfile)

    def save(self, file='sentiment.csv'):
        with open(file, 'w') as csvfile:
            fieldnames = ['candidate']+state_code.values()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for candidate in self.candidates:
                self.candidate_favor[candidate]['candidate'] = candidate
                writer.writerow(self.candidate_favor[candidate]['perc'])
    
    # Generate predictions for all states
    def generate_all_predictions(self):
        # Writes header
        with open("predict.csv", 'w') as csvfile:
          fieldnames = ["candidate"] + state_code.values()
          writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
          # Generates results
          results = {}
          for state in state_code.values():
              results[state] = predict(state)
          # Inverts the dict to write in correct format
          formatted = {}
          for state in results:
              for candidate in results[state]:
                  if candidate not in formatted:
                      formatted[candidate] = { 'candidate' : candidate }
                  formatted[candidate][state] = results[state][candidate]
          # Writes
          for candidate in formatted:
              writer.writerow(self.candidate_favor[candidate]['perc'])

if __name__ == "__main__":
    test = Candidate_Predictor()
    test.run_candidates()
    test.calc_supporters()
    print(test.candidate_favor)
    test.save()
