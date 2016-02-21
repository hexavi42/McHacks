import numpy as np

ALABAMA = 1, ALASKA = 2, ARIZONA = 3, ARKANSAS = 4, CALIFORNIA = 5, COLORADO = 6, CONNECTICUT = 7,
DELAWARE = 8, FLORIDA = 9, GEORGIA = 10, HAWAII = 11, IDAHO = 12, ILLINOIS = 13, INDIANA = 14, IOWA = 15,
KANSAS = 16, KENTUCKY = 17, LOUISIANA = 18, MAINE = 19, MARYLAND = 20, MASSACHUSSETTS = 21, 
MICHIGAN = 22, MINNESOTA = 23, MISSISSIPPI = 24, MISSOURI = 25, MONTANA = 26, NEBRASKA = 27, NEVADA = 28,
NEW_HAMPSHIRE = 29, NEW_JERSEY = 30, NEW_MEXICO = 31, NEW_YORK = 32, NORTH_CAROLINA = 33, 
NORTH_DEKOTA = 34, OHIO = 35, OKLAHOMA = 36, OREGON = 37, PENNSYLVANIA = 38, RHODE_ISLAND = 39, SOUTH_CAROLINA = 40, SOUTH_DEKOTA = 41, TENNESSEE = 42, TEXAS = 43, UTAH = 44, VERMONT = 45, VIRGINIA = 46, WASHINGTON = 47, WEST_VIRGINIA = 48, WISCONSON = 49, WYOMING = 50

SANDERS = 1, CLINTON = 2, TRUMP = 3, BUSH = 4, CARSON = 5, CRUZ = 6, KASICH = 7, RUBIO = 8

# Should get the integer(constant) that most likely is the state of location string.
# Returns -1 if not in the US
def get_state_val(string):
    pass

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

def train():
    calculate_sentiments()
    calculate_params()
