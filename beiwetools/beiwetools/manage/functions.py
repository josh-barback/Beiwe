'''
Classes for working with directories of raw Beiwe data.
'''
import os
from collections import OrderedDict
from beiwetools.helpers.functions import sort_by


def merge_contents(data_dirs, UTC_range = None):
    '''
    Helper function for registry_datastream and registry_surveys.
    Discards paths to duplicate files and chooses larger files whenever possible.
    
    Args:    
        data_dirs (list):  
            List of paths to directories that may contain files with duplicate names.
        UTC_range (list or Nonetype): Optional.  
            Ordered pair of date/times in filename_time_format, [start, end].
            If not None, ignore files before start and after end.
            
    Returns:
        merge (list):  
            A list of paths in which no basename is duplicated, sorted in order of basenames.
    '''    
    if len(data_dirs) == 1:
         d = data_dirs[0]
         file_names = sorted(os.listdir(d))
         if not UTC_range is None:
             start, end = [dt + '.csv' for dt in UTC_range]
             file_names = [n for n in file_names if n >= start and n <= end]
         merge = [os.path.join(d, f) for f in file_names]        
    else:
        file_dictionary = OrderedDict()
        for d in data_dirs:
            for f in os.listdir(d):
                if f in file_dictionary.keys():
                    file_dictionary[f].append(d)
                else:
                    file_dictionary[f] = [d]
        if not UTC_range is None:
            start, end = [dt + '.csv' for dt in UTC_range]
            file_names = list(file_dictionary.keys())
            for f in file_names:
                if f < start or f > end: del file_dictionary[f]
        for f in file_dictionary.keys():        
            file_paths = [os.path.join(d, f) for d in file_dictionary[f]]
            file_sizes = [os.path.getsize(p) for p in file_paths]
            file_dictionary[f] = file_paths[file_sizes.index(max(file_sizes))]
        # sort values by keys
        merge = sort_by(list(file_dictionary.values()), list(file_dictionary.keys()))
    return(merge)


def registry_passive(user_id, data_stream, raw_dirs, UTC_range = None):
    '''
    In some cases, downloaded Beiwe data may be located in multiple locations.
    These locations may contain duplicate filenames.
    This function collects all filepaths for a user's data stream data, drops duplicates, and chooses newer (larger) files whenever possible.
    
    Args:
        user_id (str):  Beiwe user id.
        data_stream (str):  The name of a Beiwe data stream.
            Should not be 'survey_answers', 'survey_timings', 'audio_recordings'.
        raw_dirs (list):  List of paths to raw data directories.
        UTC_range (list or Nonetype): Optional.  
            Ordered pair of date/times in filename_time_format, [start, end].
            If not None, ignore files before start and after end.

    Returns:        
        first, last (str): Date/times of first and last files in merge.
        merge (list):  List of paths to files.
    '''
    if type(raw_dirs) is str: raw_dirs = [raw_dirs]
    data_dirs = [os.path.join(os.path.join(d, user_id), data_stream) for d in raw_dirs]
    data_dirs = [d for d in data_dirs if os.path.exists(d)]
    merge = merge_contents(data_dirs, UTC_range)
    if len(merge) > 0:
        first = os.path.basename(merge[0]).split('.')[0]
        last = os.path.basename(merge[-1]).split('.')[0]
    else:
        first = None
        last = None
    return(first, last, merge)


def registry_survey(user_id, survey_id, raw_dirs, UTC_range = None):
    '''
    In some cases, downloaded Beiwe data may be located in multiple locations.
    These locations may contain duplicate filenames.
    This function collects all filepaths for a user's survey data, drops duplicates, and chooses newer (larger) files whenever possible.
    
    Args:
        user_id (str):  Beiwe user id.
        survey_id (str):  Beiwe tracking survey id.
        raw_dirs (list):  List of paths to raw data directories.
        UTC_range (list or Nonetype): Optional.  
            Ordered pair of date/times in filename_time_format, [start, end].
            If not None, ignore files before start and after end.

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
        merge[s] = merge_contents(data_dirs, UTC_range)
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


def registry_audio(user_id, audio_id, raw_dirs, UTC_range = None):
    '''
    In some cases, downloaded Beiwe data may be located in multiple locations.
    These locations may contain duplicate filenames.
    This function collects all filepaths for a user's audio survey data, drops duplicates, and chooses newer (larger) files whenever possible.
    
    Args:
        user_id (str):  Beiwe user id.
        audio_id (str):  Beiwe audio survey id.
        raw_dirs (list):  List of paths to raw data directories.
        UTC_range (list or Nonetype): Optional.  
            Ordered pair of date/times in filename_time_format, [start, end].
            If not None, ignore files before start and after end.

    Returns:        
        first, last (str): Date/times of first and last files in merge.
        merge (list):  List of paths to files.
    '''
    if type(raw_dirs) is str: raw_dirs = [raw_dirs]
    data_dirs = [os.path.join(os.path.join(os.path.join(d, user_id), 'audio_recordings'), audio_id) for d in raw_dirs]
    data_dirs = [d for d in data_dirs if os.path.exists(d)]
    merge = merge_contents(data_dirs, UTC_range)
    if len(merge) > 0:
        first = os.path.basename(merge[0]).split('.')[0]
        last = os.path.basename(merge[-1]).split('.')[0]
    else:
        first = None
        last = None
    return(first, last, merge)


def make_registry(user_id, raw_dirs, UTC_range = None):
    '''
    Merges all data streams for a user.

    Args:
        user_id (str):  Beiwe user id.
        raw_dirs (list):  List of paths to raw data directories.
        UTC_range (list or Nonetype): Optional.  
            Ordered pair of date/times in filename_time_format, [start, end].
            If not None, ignore files before start and after end.

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
        f, l, m = registry_passive(user_id, s, raw_dirs, UTC_range)
        first_dts.append(f)
        last_dts.append(l)
        merge_p[s] = m
    for s in survey_ids:
        f, l, m = registry_survey(user_id, s, raw_dirs, UTC_range)        
        first_dts.append(f)
        last_dts.append(l)        
        merge_s[s] = m
    for s in audio_ids:
        f, l, m = registry_audio(user_id, s, raw_dirs, UTC_range)            
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


