'''
Functions for processing Beiwe data.
'''
import os
import logging
import numpy as np
from pandas import Series, DataFrame
from collections import OrderedDict
from .functions import sort_by
from .time import min_ms, filename_time_format, to_timestamp


logger = logging.getLogger(__name__)


def to_1Darray(x, name = None):
    '''
    Convert list or pandas series to a 1D numpy array.
    If x is a pandas dataframe, converts x[name] to a numpy array.
    '''
    if   isinstance(x, DataFrame): 
        try:
            return(x[name].to_numpy())
        except:
            logger.warning('Must provide a column name in the dataframe.')
    elif isinstance(x, Series):     return(x.to_numpy())
    elif isinstance(x, list):       return(np.array(x))
    elif isinstance(x, np.ndarray): return(x)
    else: 
        logger.warning('Unable to convert this type to numpy array.')


def directory_range(directory):
	'''
	Finds the first and last date/time in a directory that contains Beiwe data.  Searches all subdirectories.

	Args:
		directory (str): Path to a directory that contains files named using the Beiwe convention (%Y-%m-%d %H_%M_%S.csv).

	Returns:
		first (str): Earliest date/time (%Y-%m-%d %H_%M_%S) found among filenames in the directory..
		last (str): Last date/time (%Y-%m-%d %H_%M_%S) found among filenames in the directory.
	'''
	start = True
	for path, dirs, filenames in os.walk(directory):
		for f in filenames:
			dt = f.split('.')[0]
			if start:
				first = dt
				last = dt
				start = False
			else:
				if dt < first: first = dt
				if dt > last: last = dt
	return(first, last)


def merge_contents(data_dirs):
    '''
    Helper function for registry_datastream and registry_surveys.
    Discards paths to duplicate files and chooses larger files whenever possible.
    
    Args:    
        data_dirs (list):  
            List of paths to directories that may contain files with duplicate names.
            
    Returns:
        merge (list):  A list of paths in which no basename is duplicated, sorted in order of basenames.
    '''    
    file_dictionary = OrderedDict()
    if len(data_dirs) == 1:
         d = data_dirs[0]
         file_names = sorted(os.listdir(d))
         merge = [os.path.join(d, f) for f in file_names]        
    else:
        for d in data_dirs:
            for f in os.listdir(d):
                if f in file_dictionary.keys():
                    file_dictionary[f].append(d)
                else:
                    file_dictionary[f] = [d]
        for f in file_dictionary.keys():        
            file_paths = [os.path.join(d, f) for d in file_dictionary[f]]
            file_sizes = [os.path.getsize(p) for p in file_paths]
            file_dictionary[f] = file_paths[file_sizes.index(max(file_sizes))]
        # sort values by keys
        merge = sort_by(list(file_dictionary.values()), list(file_dictionary.keys()))
    return(merge)


def registry_passive(user_id, data_stream, raw_dirs):
    '''
    In some cases, downloaded Beiwe data may be located in multiple locations.
    These locations may contain duplicate filenames.
    This function collects all filepaths for a user's data stream data, drops duplicates, and chooses newer (larger) files whenever possible.
    
    Args:
        user_id (str):  Beiwe user id.
        data_stream (str):  The name of a Beiwe data stream.
            Should not be 'survey_answers', 'survey_timings', 'audio_recordings'.
        raw_dirs (list):  List of paths to raw data directories.

    Returns:        
        first, last (str): Date/times of first and last files in merge.
        merge (list):  List of paths to files.
    '''
    if type(raw_dirs) is str: raw_dirs = [raw_dirs]
    data_dirs = [os.path.join(os.path.join(d, user_id), data_stream) for d in raw_dirs]
    data_dirs = [d for d in data_dirs if os.path.exists(d)]
    merge = merge_contents(data_dirs)
    if len(merge) > 0:
        first = os.path.basename(merge[0]).split('.')[0]
        last = os.path.basename(merge[-1]).split('.')[0]
    else:
        first = None
        last = None
    return(first, last, merge)


def registry_survey(user_id, survey_id, raw_dirs):
    '''
    In some cases, downloaded Beiwe data may be located in multiple locations.
    These locations may contain duplicate filenames.
    This function collects all filepaths for a user's survey data, drops duplicates, and chooses newer (larger) files whenever possible.
    
    Args:
        user_id (str):  Beiwe user id.
        survey_id (str):  Beiwe tracking survey id.
        raw_dirs (list):  List of paths to raw data directories.

    Returns:        
        first, last (str): Date/times of first and last files in merge.
        merge (OrderedDict):  Keys are 'survey_answers', 'survey_timings'.
            Values are merged files for the corresponding data stream.
    '''
    if type(raw_dirs) is str: raw_dirs = [raw_dirs]
    merge = OrderedDict()
    first_dts = []
    last_dts = []
    for s in ['survey_answers', 'survey_timings']:               
        data_dirs = [os.path.join(os.path.join(os.path.join(d, user_id), s), survey_id) for d in raw_dirs]
        data_dirs = [d for d in data_dirs if os.path.exists(d)]
        merge[s] = merge_contents(data_dirs)
        if len(merge[s]) > 0:
            first_dts.append(os.path.basename(merge[s][0]).split('.')[0])
            last_dts.append(os.path.basename(merge[s][-1]).split('.')[0])
    if len(first_dts) > 0:
        first = min(first_dts)
        last = max(last_dts)
    else:
        first = None
        last = None
    return(first, last, merge)


def registry_audio(user_id, audio_id, raw_dirs):
    '''
    In some cases, downloaded Beiwe data may be located in multiple locations.
    These locations may contain duplicate filenames.
    This function collects all filepaths for a user's audio survey data, drops duplicates, and chooses newer (larger) files whenever possible.
    
    Args:
        user_id (str):  Beiwe user id.
        audio_id (str):  Beiwe audio survey id.
        raw_dirs (list):  List of paths to raw data directories.

    Returns:        
        first, last (str): Date/times of first and last files in merge.
        merge (list):  List of paths to files.
    '''
    if type(raw_dirs) is str: raw_dirs = [raw_dirs]
    data_dirs = [os.path.join(os.path.join(os.path.join(d, user_id), 'audio_recordings'), audio_id) for d in raw_dirs]
    data_dirs = [d for d in data_dirs if os.path.exists(d)]
    merge = merge_contents(data_dirs)
    if len(merge) > 0:
        first = os.path.basename(merge[0]).split('.')[0]
        last = os.path.basename(merge[-1]).split('.')[0]
    else:
        first = None
        last = None
    return(first, last, merge)


def make_registry(user_id, raw_dirs):
    '''
    Merges all data streams for a user.

    Args:
        user_id (str):  Beiwe user id.
        raw_dirs (list):  List of paths to raw data directories.

    Returns:        
        merge (OrderedDict):  
            For keys 'first', 'last':  Values are date/time of first or last observations.
            For keys 'passive', 'tracking', 'audio': Values are corresponding merged file lists.
    '''
    if type(raw_dirs) is str: raw_dirs = [raw_dirs]
    # get all survey ids and names of data streams
    data_streams = []
    survey_ids = []
    audio_ids = []
    for d in raw_dirs:
        for top, dirs, filenames in os.walk(d):            
            if user_id in top:
                if 'audio' in top:                
                    audio_ids.append(os.path.basename(top))                
                elif 'survey' in top:
                    survey_ids.append(os.path.basename(top))
                else:
                    data_streams.append(os.path.basename(top))
    data_streams = list(set([i for i in data_streams if user_id not in i]))
    survey_ids = list(set([i for i in survey_ids if 'survey' not in i]))    
    audio_ids = list(set([i for i in audio_ids if 'audio' not in i]))    
    # merge everything
    first_dts = []
    last_dts = []
    merge_p = OrderedDict()
    merge_s = OrderedDict()
    merge_a = OrderedDict()
    for s in data_streams:
        f, l, m = registry_passive(user_id, s, raw_dirs)
        first_dts.append(f)
        last_dts.append(l)
        merge_p[s] = m
    for s in survey_ids:
        f, l, m = registry_survey(user_id, s, raw_dirs)        
        first_dts.append(f)
        last_dts.append(l)        
        merge_s[s] = m
    for s in audio_ids:
        f, l, m = registry_audio(user_id, s, raw_dirs)            
        first_dts.append(f)
        last_dts.append(l)                
        merge_a[s] = m
    first_dts = [i for i in first_dts if not i is None]
    last_dts = [i for i in last_dts if not i is None]
    if len(first_dts) > 0:
        first = min(first_dts)
        last = max(last_dts)
    else:
        first = None
        last = None
    merge = OrderedDict(zip(['first', 'last', 'passive', 'tracking', 'audio'], 
                            [first, last, merge_p, merge_s, merge_a]))
    return(merge)


def clean_dataframe(df, 
                    drop_duplicates = True, 
                    sort = True, 
                    update_index = True):
    '''
    Clean up a pandas dataframe.
    
    Args:
        df (DataFrame): A pandas dataframe.        
        drop_duplicates (bool):  Drop extra copies of rows, if any exist.
        sort (bool):  Sort by timestamp.  
            If True, df must have a timestamp column.
        update_index (bool):  Set index to range(len(df)).
            
    Returns:
        None
    '''
    if drop_duplicates:
        df.drop_duplicates(inplace = True)
    if sort:
        try:
            df.sort_values(by = ['timestamp'], inplace = True)
        except:
            logger.exception('Unable to sort by timestamp.')
    if update_index:
        df.set_index(np.arange(len(df)), inplace = True)


def summarize_filepath(filepath = None, ndigits = 3, basename_only = False):
    '''
    Get some basic information from a single raw Beiwe data file.
    
    Args:
        filepath (str): Path to a raw Beiwe data file.
            If None, then just returns a list of summary names.
        ndigits (int):  For rounding disk_MB.
    
    Returns:
        timestamp (int): Millisecond timestamp.  The start of the hour covered by the file.
        filename (str): The basename of the file.
        disk_MB (float): Size of the file on disk in Megabytes.
    '''
    returns = ['timestamp', 'file', 'disk_MB']
    if filepath is None:
        return(returns)
    else:
        basename = os.path.basename(filepath)
        if basename_only: file = basename
        else: file = filepath
        timestamp = to_timestamp(basename.split('.')[0], filename_time_format)
        return(timestamp, file, round(os.path.getsize(filepath)/(1000**2), ndigits))
        

def summarize_timestamps(t = None, ndigits = 3, unit = 'seconds'):
    '''
    Get some basic information from a list, Series or 1-D array of timestamps.
    
    Args:
        t (list, Series or 1-D array): List of millisecond timestamps.
            If None, then just returns a list of summary names.
        ndigits (int):  For rounding duration.
        unit (str): 'seconds' or 'ms'.
    
    Returns:
        first_observation, last_observation (int):  
            Millisecond timestamps of the first and last observations.
        n_observations (int): Number of rows in the csv.
        duration_minutes (float): Elapsed time (minutes) between first and last observation.
    '''
    returns = ['first_observation', 'last_observation',
               'n_observations', 'duration_%s' % unit]
    if t is None:
        return(returns)
    else:
        t = np.array(t) # avoid future warning with np.ptp() and pandas series objects
        if len(t) > 0:
            if unit == 'seconds': d = 1000
            elif unit == 'ms': d = 1
            
            return(np.min(t), np.max(t), 
                   len(t), round(np.ptp(t) / d, ndigits))
        else:
            return(None, None, 0, None)


def get_windows(df, start, stop, window_length_ms):
    '''
    Generate evenly spaced windows over a time period (e.g. one hour).
    For each window, figure out which rows of a data frame were observed during the window.

    Args:
        
    Returns:
        
    '''    
    if (stop - start) % window_length_ms != 0:
        logger.warning('The window length doesn\'t evenly divide the interval.')
    else:
        windows = OrderedDict.fromkeys(np.arange(start, stop, window_length_ms))
        for i in range(len(df)):
            key = df.timestamp[i] - (df.timestamp[i] % window_length_ms)
            if windows[key] is None:
                windows[key] = [i]
            else:
                windows[key].append(i)
        return(windows)