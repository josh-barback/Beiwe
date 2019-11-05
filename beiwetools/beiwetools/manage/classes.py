'''
Classes for working with directories of raw Beiwe data.
'''
import os
import logging
from collections import OrderedDict
from beiwetools.helpers.process import make_registry
from beiwetools.helpers.classes import Summary
from beiwetools.helpers.functions import (sort_by, read_json, write_json, check_same,
                                          setup_directories, setup_csv, write_to_csv)


logger = logging.getLogger(__name__)


class DeviceInfo():
    '''
    Class for reading identifier files from raw Beiwe data.

    Args:  
        paths (str or list):  One or more paths to the user's identifier files.
    
    Attributes:
        identifiers (OrderedDict):  
            Keys are paths to identifier files.  
            Values are OrderedDicts that contain information from the corresponding identifier file.
        phone_history (OrderedDict):
            Obtained from the 'device_os' column in identifiers.
            Keys are timestamps when phone info was observed.
            Values are either 'iPhone' or 'Android'.
    '''
    def __init__(self, paths):
        if type(paths) is str:
            paths = [paths]
        # sort paths according to file creation date
        paths = sort_by(paths, [os.path.basename(p) for p in paths])
        # read identifiers in order of creation
        self.identifiers = OrderedDict()
        for p in paths:
            f = open(p, 'r')
            lines = list(f)
            f.close()
            keys = lines[0].replace('\n', '').split(',')
            values = lines[1].split(',')
            # iPhone identifier files have an extra comma.
            # Replace comma with an underscore:
            if len(values) > len(keys):
                values = values[:-2] + ['_'.join(values[-2:])]        
            self.identifiers[p] = OrderedDict(zip(keys, values))  
        self.phone_history = self.get_phone_history()
    
    def get_history(self, header):
        '''
        Return a dictionary with history of a particular device attribute.
        
        Args:
            header (str): Column header from identifiers CSV.
                e.g. 'device_os', 'beiwe_version'

        Returns:
            history (OrderedDict):
                Keys are ordered timestamps.
                Values are device attributes observed at those times.        
        '''        
        history = OrderedDict()
        for d in self.identifiers.values():
            try:
                history[d['timestamp']] = d[header]
            except:
                logger.warning('%s isn\'t a device attribute.' % header)
        return(history)
    
    def get_phone_history(self):
        '''
        Get history of phone type.
        Log a warning if more than one phone type is found.
        '''        
        h = self.get_history('device_os')
        for k in h.keys():
            if h[k] in ['iPhone OS', 'iOS']:
                h[k] = 'iPhone'
            elif h[k] == 'Android':
                h[k] = 'Android'
        if len(list(set(h.values()))) > 1:
            logger.warning('Found multiple phone types.')
        return(h)        
    
    def export(self, directory):
        '''
        Write all identifier information to a single csv.
        '''
        temp = list(self.identifiers.values())[-1]
        filename = temp['patient_id'] + '_identifiers'
        header = ['from_file'] + list(temp.keys())
        path = setup_csv(filename, directory, header)
        for f in self.identifiers.keys():  
            line = [f] + list(self.identifiers[f].values())
            write_to_csv(path, line)
            
    def __eq__(self, other):
        return(check_same(self, other, to_check = 'all'))


class UserData():
    '''
    Class for organizing a user's raw Beiwe data.

    Args:
        user_id (str):  Beiwe user id.
        
    Attributes:
        id (str):  Beiwe user id.
        passive (OrderedDict):  Keys are passive data streams.
            Each value is a list of all available files for the corresponding streams.
        tracking (OrderedDict):  Keys are tracking survey ids.
            Each value is a dictionary with keys 'survey_answers' and 'survey_timings'.
        audio (OrderedDict):  Keys are audio survey ids.
            Each value is a list of all available files for the corresponding survey.
        first, last (str):  
            Date/time of first and last observations.
            Formatted as '%Y-%m-%d %H_%M_%S'.
        UTC_range (list or Nonetype):  
            Ordered pair of date/times in filename_time_format, [start, end].
            If not None, files before start and after end were ignored.            
        device (DeviceInfo):  Represents contents of the user's identifier files.
    '''
    def __init__(self, user_id):
        self.id = user_id
        self.passive = OrderedDict()
        self.tracking = OrderedDict()
        self.audio = OrderedDict()
        self.first = None
        self.last  = None
        self.UTC_range = None
        self.device = None

    def load(self, directory):
        '''
        Load data records from a json file.
        
        Args:
            directory (str):  Directory of json files with merged filepaths.
            
        Returns:
            None
        '''
        data = read_json(os.path.join(directory, self.id + '_merge.json'))
        self.update(data)
 
    def create(self, raw_dirs, UTC_range = None):
        '''
        Generate records from directories of raw Beiwe data.

        Args:
            raw_dirs (str or list):  Paths to raw data directories.
            UTC_range (list or Nonetype): Optional.  
                Ordered pair of date/times in filename_time_format, [start, end].
                If not None, ignore files before start and after end.
            
        Returns:
            None        
        '''
        if type(raw_dirs) is str: raw_dirs = [raw_dirs]
        self.UTC_range = UTC_range
        print('   Collecting data files for ' + self.id + '...')
        data = make_registry(self.id, raw_dirs, self.UTC_range)
        print('   Updating records...')
        self.update(data)
        print('   Done generating registry for ' + self.id + '.\n')

    def update(self, data):
        '''
        Update after getting data records.
        '''        
        self.passive = data['passive']
        self.tracking = data['tracking']
        self.audio = data['audio']
        self.first = data['first']
        self.last = data['last']
        if 'UTC_range' in data.keys(): 
            self.UTC_range = data['UTC_range']
        # get device
        self.device = DeviceInfo(self.passive['identifiers'])
               
    def export(self, directory):
        '''
        Saves record of merged file paths. 
        
        Args:
            directory (str):  Directory where json file should be saved.
        '''
        out = OrderedDict([('first', self.first),
                           ('last', self.last),
                           ('UTC_range', self.UTC_range),
                           ('passive', self.passive),
                           ('tracking', self.tracking),
                           ('audio', self.audio)])
        write_json(out, self.id + '_merge', directory)

    def __eq__(self, other):
        return(check_same(self, other, to_check = 'all'))


class BeiweProject():
    '''
    Class for organizing directories of raw Beiwe data.

    Args:
        None
                
    Attributes:
        ids (list):  List of all available user IDs.
        data (OrderedDict):  Keys are Beiwe user ids, values are UserData objects.
        first, last (str):  
            Date/time of first and last observations across all users.
            Formatted as '%Y-%m-%d %H_%M_%S'.
        iPhone_users (list): List of all users with iPhones.
        Android_users (list): List of all users with Android phones.
        passive, tracking, audio (list):  
            Lists of available passive data streams, tracking surveys, and audio recordings across all users.
        dictionaries (OrderedDict): 
            Dictionaries used for looking up user attributes.
            By default, includes keys 'default_name', 'phone_name', and 'phone'.
        
        
        summary (Summary):
        warnings (list):
            
            
    '''
    def __init__(self):
        self.ids = []
        self.data = OrderedDict()
        self.first = None
        self.last = None
        self.iPhone_users = []
        self.Android_users = []
        self.dictionaries = OrderedDict()
        self.passive = []
        self.tracking = []
        self.audio = []
        self.summary = None
        
    def create(self, raw_dirs, user_ids = 'all'):
        '''
        Generate records from directories of raw Beiwe data.

        Args:
            raw_dirs (str or list): Paths to raw data directories.
            user_ids (list): Beiwe user IDs (str) to include.
            
        Returns:
            None        
        '''
        print('\nGenerating records for each user...\n')
        if type(raw_dirs) is str:  raw_dirs = [raw_dirs]
        available_ids = []
        for d in raw_dirs:
            available_ids += os.listdir(d)
        available_ids = sorted(list(set(available_ids)))
        if user_ids == 'all':
            user_ids = available_ids
        for i in user_ids:
            try:
                temp = UserData(i)
                temp.create(raw_dirs)
                self.data[i] = temp
                self.ids.append(i)
            except:
                flag = 'Unable to create registry for %s' % i
                print('   ' + flag + '\n')
                warnings.append(flag)
                logger.warning(flag)
        # get phone types

        self.dictionaries['phone'] = phone
        # name assignments
        print('Assigning default names...\n')
        sorted_user_ids = sort_by(self.user_ids, [self.data[i].first for i in self.user_ids])
        sorted_user_phones = [self.data[i].phone for i in sorted_user_ids]        
        
        
        default_name = OrderedDict()
        phone_name = OrderedDict()
        
        
        
        n_ids = len(sorted_user_ids)
        n_digits = len(str(n_ids))
        for i in range(n_ids):
            count = str(i+1).zfill(n_digits)
            default_name[sorted_user_ids[i]] = 'Participant ' + count + ' (' + str(sorted_user_phones[i]) + ')'
        self.dictionaries['default_name'] = default_name
        self.dictionaries['phone_name'] = phone_name
        # update
        print('Updating study records...\n')
        self.update()
        self.summarize()
        print('Finished generating study records.\n')
        
    def load(self, load_dir):
        '''
        Load data records from json files.
        
        Args:
            load_dir (str):  Path to directory of study records.
            
        Returns:
            None
        '''
        merge_dir = os.path.join(load_dir, 'registries')
        self.ids = sorted([f.split('_')[0] for f in os.listdir(merge_dir)])
        for i in self.user_ids:
            temp = UserData(i)
            temp.load(merge_dir)
            self.data[i] = temp
        self.name_assignments = read_json(os.path.join(load_dir, 'dictionaries.json'))
        self.update()

    def update(self):
        '''
        Update after getting data records.
        '''
        self.iPhone_users = [i for i in self.user_ids if self.data[i].phone == 'iPhone']
        self.Android_users = [i for i in self.user_ids if self.data[i].phone == 'Android']
        fs = [self.data[i].first for i in self.user_ids]
        ls = [self.data[i].last for i in self.user_ids]
        if len(fs) > 0:
            self.first = min(fs)
            self.last = max(ls)
        for i in self.user_ids:
            self.passive += list(self.data[i].passive.keys())
            self.tracking += list(self.data[i].tracking.keys())
            self.audio += list(self.data[i].audio.keys())
        self.passive = sorted(list(set(self.passive)))
        self.tracking = sorted(list(set(self.tracking)))
        self.audio = sorted(list(set(self.audio)))

    def summarize(self):
        pass

    def export(self, name, directory):
        '''
        Save json files with study records.  
        Overwrites pre-existing records.
        
        Args:
            name (str): Save object files to a folder with this name.
            directory (str): Where to save folder of records.
            
        Returns:
            None
        '''   
        path = os.path.join(directory, name)
        merge_path = os.path.join(path, 'registries')
        identifiers_path = os.path.join(path, 'identifiers')
        setup_directories([path, merge_path, identifiers_path])
        write_json(self.dictionaries, 'dictionaries', path)
        for i in self.user_ids:
            self.data[i].to_json(merge_path)
            self.data[i].device.export(identifiers_path)
            
    def __eq__(self, other):
        return(check_same(self, other, to_check = 'all'))