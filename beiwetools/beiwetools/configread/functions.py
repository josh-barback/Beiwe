'''
Functions for working with Beiwe study configurations.
'''
import os
import logging
from collections import OrderedDict
from beiwetools.helpers.time import convert_seconds, day_order
from beiwetools.helpers.functions import read_json


logger = logging.getLogger(__name__)


def load_settings(settings_list, settings_from_json):
    '''
    Read and organize device settings.
    
    Args:
        settings_list (dict):  A formatted list of settings from above.
        settings_from_json (OrderedDict): Settings from a JSON file.
        
    Returns:
        settings (OrderedDict): Organized device settings.        
    '''
    settings = OrderedDict()
    for s in settings_list:
        if s in settings_from_json.keys():
            settings[s] = settings_from_json[s]        
        else:
            settings[s] = 'Not found'
    return(settings)    
        
        
def load_timings(timings):
    '''
    Read survey timings.
    
    Args:
        timings (list):  Timings from a JSON file.

    Returns:
        readable (OrderedDict):  
    '''
    readable = OrderedDict()
    for i in range(7):
        t = []
        for j in range(len(timings[i])):
            s = timings[i][j]
            t.append(convert_seconds(s))
        readable[day_order[i][0:3]] = t
    return(readable)