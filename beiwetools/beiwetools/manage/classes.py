'''
Classes for working with directories of raw Beiwe data.
'''
import os
import logging
from collections import OrderedDict
from beiwetools.helpers.time import to_timestamp, UTC, filename_time_format
from beiwetools.helpers.process import make_registry
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
        current (OrderedDict):  
            The most recent information about the device.
            Keys are column headers from an identifier file, 
            e.g. 'device_os', 'os_version'.        
    '''
    def __init__(self, paths):
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
        self.current = self.identifiers[paths[-1]]
        
    def to_csv(self, directory):
        '''
        Write all identifier information to a single csv.
        '''
        filename = self.current['patient_id'] + '_identifiers'
        header = ['from_file'] + list(self.current.keys())
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
        device (DeviceInfo):  Represents contents of the user's identifier files.
        phone (str): 'iPhone' or 'Android'.
    '''

    def __init__(self, user_id):
        self.id = user_id
        self.passive = OrderedDict()
        self.tracking = OrderedDict()
        self.audio = OrderedDict()
        self.first = None
        self.last  = None
        self.device = None
        self.phone = None

    def load(self, directory):
        '''
        Load data records from a json file.
        
        Args:
            directory (str):  Directory of json files with merged filepaths.
            
        Returns:
            None
        '''
        self.data = read_json(os.path.join(directory, self.id + '_merge.json'))
        self.update()
 
    def create(self, raw_dirs):
        '''
        Generate records from directories of raw Beiwe data.

        Args:
            raw_dirs (str or list):  Paths to raw data directories.
            
        Returns:
            None        
        '''
        print('   Collecting data files for ' + self.id + '...')
        self.data = make_registry(self.id, raw_dirs)
        print('   Updating records...')
        self.update()
        print('   Done generating records for ' + self.id + '.\n')

    def update(self):
        '''
        Update after getting data records.
        '''        
        self.passive = self.data['passive']
        self.tracking = self.data['tracking']
        self.audio = self.data['audio']
        self.first = self.data['first']
        self.last = self.data['last']
        # get device
        self.device = DeviceInfo(self.passive['identifiers'])
        # get phone type
        if self.device.current['device_os'] in ['iPhone OS', 'iOS']:
            self.phone = 'iPhone'
        elif self.device.current['device_os'] == 'Android':
            self.phone = 'Android'
               
    def to_json(self, directory):
        '''
        Saves record of merged file paths. 
        
        Args:
            directory (str):  Directory where json file should be saved.
        '''
        out = OrderedDict([('first', self.first),
                           ('last', self.last),
                           ('passive', self.passive),
                           ('tracking', self.tracking),
                           ('audio', self.audio)])
        write_json(out, self.id + '_merge', directory)
    
    
class BeiweProject():
    '''
    Class for organizing directories of raw Beiwe data.

    Args:
        None
                
    Attributes:
        user_ids (list):  List of all available user ids.
        data (OrderedDict):  Keys are Beiwe user ids, values are UserData objects.
        first, last (str):  
            Date/time of first and last observations across all users.
            Formatted as '%Y-%m-%d %H_%M_%S'.
        iPhone_users (list):
        Android_users (list):
        name_assignments (orderedDict): Keys are descriptions of the name assignment.
            Each value is a name assignment.
            A name assignment is a dictionary in which keys are Beiwe user ids and values are assigned names.
            When loaded or created, a default assignment is created in which users are sorted by order of first available observation.
        passive, tracking, audio (list):  Lists of available passive data streams, tracking surveys, and audio recordsings across all users.

    '''
    def __init__(self):
        self.user_ids = []
        self.data = OrderedDict()
        self.first = None
        self.last = None
        self.iPhone_users = []
        self.Android_users = []
        self.name_assignments = OrderedDict()
        self.passive = []
        self.tracking = []
        self.audio = []
        
    def create(self, raw_dirs, ignore_users = []):
        '''
        Generate records from directories of raw Beiwe data.

        Args:
            raw_dirs (str or list): Paths to raw data directories.
            ignore_users (list): Beiwe user IDs (str) to omit.
            
        Returns:
            None        
        '''
        print('\nGenerating records for each user...\n')
        user_ids = []
        if type(raw_dirs) is str:  raw_dirs = [raw_dirs]
        for d in raw_dirs:
            user_ids += os.listdir(d)
        user_ids = sorted(list(set(user_ids)))
        self.user_ids = [i for i in user_ids if i not in ignore_users]
        for i in self.user_ids:
            temp = UserData(i)
            temp.create(raw_dirs)
            self.data[i] = temp
        # name assignments
        print('Assigning default names...\n')
        sorted_user_ids = sort_by(self.user_ids, [self.data[i].first for i in self.user_ids])
        sorted_user_phones = [self.data[i].phone for i in sorted_user_ids]        
        default_names = OrderedDict()
        n_ids = len(sorted_user_ids)
        n_digits = len(str(n_ids))
        for i in range(n_ids):
            count = str(i+1).zfill(n_digits)
            default_names[sorted_user_ids[i]] = 'Participant ' + count + ' (' + str(sorted_user_phones[i]) + ')'
        self.name_assignments['default'] = default_names
        # update
        print('Updating study records...\n')
        self.update()
        print('Finished generating study records.\n')
        
    def load(self, load_dir):
        '''
        Load data records from json files.
        
        Args:
            load_dir (str):  Path to directory of study records.
            
        Returns:
            None
        '''
        merge_dir = os.path.join(load_dir, 'merge_records')
        self.user_ids = sorted([f.split('_')[0] for f in os.listdir(merge_dir)])
        for i in self.user_ids:
            temp = UserData(i)
            temp.load(merge_dir)
            self.data[i] = temp
        self.name_assignments = read_json(os.path.join(load_dir, 'name_assignments.json'))
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
        else:
            self.first = None
            self.last = None        
        for i in self.user_ids:
            self.passive += list(self.data[i].passive.keys())
            self.tracking += list(self.data[i].tracking.keys())
            self.audio += list(self.data[i].audio.keys())
        self.passive = sorted(list(set(self.passive)))
        self.tracking = sorted(list(set(self.tracking)))
        self.audio = sorted(list(set(self.audio)))

    def to_plot(self, passive = True, tracking = True, audio = True):
        '''
        Get inputs for plot_raw_survey.
        
        Args:
            None
            
        Returns:
            all_types (list):  All available data types across all users.
        '''
        all_types = []
        if passive:
            all_types += self.passive
        if tracking:
            sa = [i + '_survey_answers' for i in self.tracking]
            st = [i + '_survey_timings' for i in self.tracking]
            all_types += sorted(sa + st)
        if audio:
            all_types += [i + '_audio' for i in self.audio]
        # On rare occasions there may be a tracking survey folder called "None."
        # May occur for a deleted survey?
        all_types = [t for t in all_types if not 'None' in t]      
        return(all_types)

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
        merge_path = os.path.join(path, 'merge_records')
        identifiers_path = os.path.join(path, 'identifiers')
        setup_directories([path, merge_path, identifiers_path])
        write_json(self.name_assignments, 'name_assignments', path)
        for i in self.user_ids:
            self.data[i].to_json(merge_path)
            self.data[i].device.to_csv(identifiers_path)