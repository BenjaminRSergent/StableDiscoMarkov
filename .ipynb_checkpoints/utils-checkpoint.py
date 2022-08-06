import datetime
import os
import pickle
import pytz

_DATA_PATH = "data"

def get_data_path(filename):
    return os.path.join(_DATA_PATH, filename)

def load_data_file(filename):
    with open(get_data_path(filename), 'rb') as infile:
        return pickle.load(infile)
    
def save_data_file(obj, filename):
    with open(get_data_path(filename), 'wb+') as outfile:
        pickle.dump(obj, outfile)
    

def remove_none_and_dups(lst):
    return list({x for x in lst if x})



def get_utc_now():
    return datetime.datetime.now(pytz.timezone('UTC'))