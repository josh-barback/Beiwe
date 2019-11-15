'''
Classes for working with directories of raw Beiwe data.
'''
import os
import logging
from collections import OrderedDict

from beiwetools.configread import BeiweConfig
from beiwetools.helpers.time import (to_timestamp, reformat_datetime, day_ms,
                                     date_time_format, filename_time_format)
from beiwetools.helpers.classes import Summary
from beiwetools.helpers.functions import (read_json, write_json, setup_directories, 
                                          setup_csv, write_to_csv,
                                          check_same, sort_by, join_lists)

from .headers import identifiers_header, user_summary_header
from .functions import (passive_data, passive_available, survey_data,
                        check_dirs, merge_contents, get_survey_ids)


logger = logging.getLogger(__name__)


class BeiweProject():
    '''
    Class for organizing directories of raw Beiwe data.

    Args:
        None
                
    Attributes:
        ids (list):  List of all available user IDs, sorted by first observation.
        data (OrderedDict):  Keys are Beiwe user ids, values are UserData objects.
        first, last (str):  
            Date/time of first and last observations across all users.
            Formatted as '%Y-%m-%d %H_%M_%S'.
        lists (OrderedDict):
            Useful lists.  
            May be saved to JSON format, therefore should only contain primitive types.
            By default, includes:            
                iOS_users (list): List of all users with iPhones.
                Android_users (list): List of all users with Android phones.
        passive (list):        
            List of available passive data streams across all users.
        surveys (OrderedDict):
            Keys are raw survey data types (e.g. 'audio_recordings', 'survey_answers').
            Values are lists of corresponding survey identifiers.
        dictionaries (OrderedDict): 
            Dictionaries used for looking up user attributes.
            May be saved to JSON format, therefore should only contain primitive types. 
            By default, includes keys 'default_name', 'os', 'configuration', UTC_range.
        flags (OrderedDict): Values are lists of flagged user IDs.  Keys are:
            'ignored_users': User IDs in raw_dirs who are not included.
            'without_data': User IDs with no data streams other than identifiers.
            'irregular_directories': See UserData attributes.
            'multiple_devices': See DeviceInfo attributes.
            'multiple_os': See DeviceInfo attributes.
        use_name (str): A key in dictionaries.
            This is the dictionary that will be used to generate a summary.
        summary (Summary):  Project overview for printing.
    '''
    def __init__(self):
        self.configuration = None
        self.ids = []
        self.data = OrderedDict()
        self.first = None
        self.last = None
        self.lists = OrderedDict([('iOS_users', []), ('Android_Users', [])])
        self.passive = []
        self.surveys = OrderedDict()
        self.dictionaries = OrderedDict([('os', OrderedDict()), 
                                         ('default_name', OrderedDict())])
        flag_keys = ['ignored_users', 'without_data', 'irregular_directories',
                     'multiple_device', 'multiple_os']
        self.flags = OrderedDict(zip(flag_keys,
                                     [[], [], [], [], []]))
        self.use_name = 'default_name'
        self.summary = None
       
    def create(self, raw_dirs, user_ids = 'all', 
               configuration = None, UTC_range = None,
               include_passive = passive_data, include_surveys = survey_data):
        '''
        Generate records from directories of raw Beiwe data.

        Args:
            raw_dirs (str or list): Paths to raw data directories.
            user_ids (list): Beiwe user IDs (str) to include.
            configuration (str or OrderedDict or NoneType): 
                Optional assignment of configuration file to user IDs.
                Can be a path to a study configuration (str) for all users.
                Or a dictionary; keys are user IDs and values are paths to configurations.
            UTC_range (list or OrderedDict or NoneType):
                Optional assignment of follow-up periods to user IDs.
                Can be a pair of date/times in filename_time_format, [start, end] for all users.
                Or a dictionary; keys are user IDs and values are ranges for each user.                                
            include_passive (list): Which passive data directories to read.               
            include_survey (list): Which survey data directories to read.
            
        Returns:
            None        
        '''
        if type(raw_dirs) is str:  raw_dirs = [raw_dirs]
        available_ids = []
        for d in raw_dirs:
            available_ids += os.listdir(d)
        available_ids = sorted(list(set(available_ids)))
        if user_ids == 'all':
            user_ids = available_ids
        else:
            self.flags['ignored_users'] = [i for i in available_ids if not i in user_ids]
        self.dictionaries['configuration'] = configuration
        self.dictionaries['UTC_range'] = UTC_range
        # get user data registries
        for i in user_ids:
            try:
                CR = [configuration, UTC_range]
                cr = [None, None]
                for j in range(2):
                    if   isinstance(CR[j], str): cr[j] = CR[j]
                    elif isinstance(CR[j], (dict, OrderedDict)): cr[j] = CR[j][i]                
                temp = UserData()
                temp.create(raw_dirs, i, 
                            UTC_range = cr[1], 
                            configuration = cr[0],
                            include_passive = include_passive, 
                            include_surveys = include_surveys)
                self.data[i] = temp
            except:
                logger.warning('Unable to create registry for %s.' % i)
                self.flags['ignored_users'].append(i)
        # update lists and dictionaries
        have_ids = list(self.data.keys())
        self.ids = sort_by(have_ids, [self.data[i].first for i in have_ids])
        data_range = []
        n_ids = len(self.ids)
        n_digits = len(str(n_ids))
        for i in range(n_ids):
            d = self.data[self.ids[i]]
            if not d.first is None:
                data_range += [d.first, d.last]
            # os dictionary
            self.dictionaries['os'][d.id] = d.device.os
            # default names
            count = str(i+1).zfill(n_digits)
            self.dictionaries['default_name'][d.id] = 'Participant ' + count
            # os lists
            self.lists[d.device.os + '_users'].append(d.id)
            # data streams
            self.passive += list(d.passive.keys())
            for k in d.surveys():
                if k in self.surveys.keys():
                    self.surveys[k] += list(d.surveys[k].keys())
                else:
                    self.surveys[k] = list(d.surveys[k].keys())        
        # drop duplicate data streams
        self.passive = sorted(list(set(self.passive)))
        for k in self.surveys.keys():
            self.surveys[k] = sorted(list(set(self.surveys[k])))
        # get first and last observations
        data_range.sort()
        if len(data_range) > 0:
            self.first, self.last = data_range[0], data_range[-1]
        # get summary for printing
        self.summarize()
        logging.info('Finished generating study records for %d of %d users.' % (len(self.data), len(user_ids)))
        
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


        folders = []
        path = os.path.join(directory, name)
        merge_path = os.path.join(path, 'registries')
        identifiers_path = os.path.join(path, 'identifiers')
        setup_directories([path, merge_path, identifiers_path])


        self.ids
        self.data
        self.first
        self.last
        self.lists
        self.passive
        self.surveys
        self.dictionaries
        self.flags
        self.use_name



        write_json(self.dictionaries, 'dictionaries', path)
        for i in self.user_ids:
            self.data[i].to_json(merge_path)
            self.data[i].device.export(identifiers_path)
            
    def __eq__(self, other):
        return(check_same(self, other, to_check = 'all'))


class UserData():
    '''
    Class for organizing a user's raw Beiwe data.
        
    Attributes:
        id (str):  Beiwe user id.
        configuration (str): Optional path to a configuration file.
        passive (OrderedDict):  Keys are passive data streams.
            Each value is either:
                A list of all available files for the corresponding streams.
                Or a string describing missing data condition.
        surveys (OrderedDict):  
            Keys are names of survey directories (e.g. 'audio_recordings', 'survey_timings'.
            Values are ordered dictionaries: 
                Keys are survey identifiers.
                Values are lists of all available files for the corresponding survey.
        first, last (str):  
            Date/time of first and last observations.
            Formatted as '%Y-%m-%d %H_%M_%S'.
        UTC_range (list or Nonetype):  
            Ordered pair of date/times in filename_time_format, [start, end].
            If not None, files before start and after end were ignored.            
        not_registered (list): 
            Paths to unregistered files in irregular directories.
            Irregular directories are survey directories that contain raw data files.
        device (DeviceInfo): Represents contents of the user's identifier files.
        summary (Summary): Overview of user data for printing.
        info (
    '''
    def __init__(self):
        self.id = None
        self.configuration = None
        self.passive = None
        self.surveys = None
        self.first = None
        self.last  = None
        self.UTC_range = None
        self.not_registered = []
        self.device = None
        self.summary = None
        self.info = None

    def create(self, user_id, raw_dirs, 
               UTC_range = None, configuration = None,
               passive_include = passive_available['both'],
               surveys_include = survey_data):
        '''
        Generate records from directories of raw Beiwe data.

        Args:
            user_id (str):  Beiwe user id.
            raw_dirs (str or list):  
                Paths to directories that may contain raw data from this user.
            UTC_range (list or Nonetype): Optional.  
                Ordered pair of date/times in filename_time_format, [start, end].
                If not None, ignore files before start and after end.
            configuration (str): Optional path to a configuration file.
            passive_include (list): Which passive data directories to read.               
            survey_include (list): Which survey data directories to read.
            
        Returns:
            None        
        '''
        self.id = user_id
        self.UTC_range = UTC_range
        self.configuration = configuration
        if isinstance(raw_dirs, str): raw_dirs = [raw_dirs]
        user_dirs = [os.path.join(d, self.id) for d in raw_dirs]
        data_range = []
        # get identifiers and device
        to_check = [os.path.join(d, 'identifiers') for d in user_dirs]
        not_exist, not_dir, empty, not_empty = check_dirs(to_check)        
        if len(not_empty) > 0: merge = merge_contents(not_empty, self.UTC_range)
        else:
            logger.warning('No identifiers found for %s in this range.' % self.id)        
            try:
                merge = [merge_contents(not_empty, ['1970-01-01 00_00_00', self.UTC_range[1]])[-1]]
                logger.warning('Using last observed identifiers file for %s.' % self.id)
            except:
                merge = 'not_found'
                logger.warning('No identifiers found for %s.' % self.id)        
        self.passive['identifiers'] = merge
        try:
            self.device = DeviceInfo(self.passive['identifiers'])
            os = self.device.os
        except:
            logger.warning('Unable to get device info for ' + self.id + '.')
            os = 'both'
        # get passive data registry
        for s in passive_available['both']:
            if not s in passive_available[os]:
                self.passive[s] = 'not available for OS'
            elif not s in passive_include:
                self.passive[s] = 'ignored'
            else:
                to_check = [os.path.join(d, s) for d in user_dirs]
                not_exist, not_dir, empty, not_empty = check_dirs(to_check)          
                if len(not_empty) > 0: merge = merge_contents(not_empty, self.UTC_range)        
                else: merge = 'not_found'
                data_range += [os.path.basename(merge[0]), 
                               os.path.basename(merge[-1])]
                self.passive[s] = merge
        # get survey data registry
        for sd in survey_data:
            if sd in surveys_include:
                survey_dirs = [os.path.join(d, sd) for d in user_dirs]
                sids, files = get_survey_ids(survey_dirs)
                self.not_registered += files
                if len(sids) == 0:
                    self.surveys[sd] = 'not_found'
                else:
                    self.surveys[sd] = OrderedDict.fromkeys(sids)
                    for s in sids:
                        to_check = [os.path.join(d, s) for d in survey_dirs]                        
                        not_exist, not_dir, empty, not_empty = check_dirs(to_check)          
                        if len(not_empty) > 0: 
                            merge = merge_contents(not_empty, self.UTC_range)        
                            data_range += [os.path.basename(merge[0]), 
                                           os.path.basename(merge[-1])]
                        else: merge = 'not_found'
                    self.surveys[sd][s] = merge
        # get first & last observation datetimes
        data_range.sort()        
        if len(data_range) > 0:
            self.first = data_range[0].split('.')[0]
            self.last = data_range[-1].split('.')[0]
        # get summary
        self.summarize()
        logger.info('Created raw data registry for Beiwe user ID %s.' % self.id)

    def to_list(self, user_names = {}, object_names = {}):
        '''
        Collect some information and summary stats.
        '''
        if self.id in user_names.keys():
            user_name = user_names[self.id]
        else: user_name = None
        study_name = None
        if len(object_names) == 0:
            try:
                config = BeiweConfig(self.configuration)
                study_name = config.name.replace('_', ' ')
                object_names = config.name_assignments
            except:
                logger.warning('Configuration file not found for Beiwe user ID %s.' % self.id)
        # followup
        if not self.UTC_range is None:
            begin, end = [reformat_datetime(t, filename_time_format, date_time_format) + ' UTC' for t in self.UTC_range]
            followup_ms = to_timestamp(self.UTC_range[1], filename_time_format) - to_timestamp(self.UTC_range[1], filename_time_format)
            followup_days = round(followup_ms/day_ms, ndigits = 1)
        # observations
        if self.first is None:
            first, last, n_days = None, None, 0
        else:
            first = reformat_datetime(self.first, filename_time_format, date_time_format) + ' UTC'
            last =  reformat_datetime(self.last,  filename_time_format, date_time_format) + ' UTC'
            observation_ms = to_timestamp(self.last, filename_time_format) - to_timestamp(self.first, filename_time_format)
            observation_days = round(observation_ms/day_ms, ndigits = 1)
        # 


info = [self.id, user_name, 
        begin, end, followup_days, 
        first, last, observation_days,
        raw_count, size_MB, self.device.unique, self.device.os,
        irregular_directories, len(self.not_registered),
        study_name, self.configuration_file]
        
        
        project_labels = ['Study Name', 'Configuration File Path']
        project_items = [study_name, self.configuration]
        if not self.UTC_range is None:
            project_labels += ['Begin', 'End']
            project_items += [fd[0], fd[1]]
        project  = Summary(project_labels, project_items)
        if self.first is None:
            first, last, n_days = None, None, 0
        else:
            first = reformat_datetime(self.first, filename_time_format, date_time_format) + ' UTC'
            last =  reformat_datetime(self.last,  filename_time_format, date_time_format) + ' UTC'
            n_ms = to_timestamp(self.last, filename_time_format) - to_timestamp(self.first, filename_time_format)
            n_days = round(n_ms/day_ms, ndigits = 1)
        followup = Summary(['First Observation', 'Last  Observation', 'Total Days', 'Raw Files', 'Storage'],
                           [first, last, n_days, None, None])
        device = Summary(['Number of Devices', 'Current Phone OS', 'Found Multiple Operating Systems'],
                         [self.device.unique, self.device.os, self.device.os_flag])
        registry = Summary(['Irregular Directories', 'Unregistered Files'],
                           [len(self.flags['irregular_directories']), len(self.not_registered)])
        labels = ['Project', 'Follow-Up Summary', 'Device Records', 'Registry Issues']
        items = [project, followup, device, registry]
        self.summary = Summary(labels, items, header = user_name)


    def summarize(self, user_names = {}, object_names = {}):
        '''
        Summarize user data for documentation.

        Args:
            user_names (dict): Optional name assignments for Beiwe user IDs.
            object_names (dict): Optional name assignments for Beiwe surveys.
        '''

    def load(self, directory):
        '''
        Load data records from a json file.
        
        Args:
            directory (str):  
                Directory containing an exported UserData object.
            
        Returns:
            None
        '''
        temp = read_json(os.path.join(directory, self.id + '_registry.json'))
        self.passive   = temp['passive']
        self.surveys   = temp['surveys']
        self.first     = temp['first']
        self.last      = temp['last']  
        self.UTC_range = temp['UTC_range']
        self.device    = DeviceInfo(self.passive['identifiers'])
        self.not_registered = temp['not_registered']
        self.configuration  = temp['configuration']
        self.summarize()
 
    def export(self, directory):
        '''
        Saves record of merged file paths. 
        
        Args:
            directory (str):  Directory where json file should be saved.
        '''
        out = OrderedDict([
                ('id', self.id),
                ('passive', self.passive),
                ('surveys', self.surveys),
                ('first', self.first),
                ('last', self.last),
                ('UTC_range', self.UTC_range),
                ('flags', self.flags),
                ('configuration', self.configuration)])
        write_json(out, self.id + '_registry', directory)

    def __eq__(self, other):
        return(check_same(self, other, to_check = 'all'))


class DeviceInfo():
    '''
    Class for reading identifier files from raw Beiwe data.

    Args:  
        paths (str or list):  One or more paths to the user's identifier files.
    
    Attributes:
        identifiers (OrderedDict):  
            Keys are paths to identifier files.  
            Values are OrderedDicts that contain information from the corresponding identifier file.
        os (str): 
            'iOS' or 'Android' if history includes only one OS.
            Otherwise 'both'.
        unique (int): Number of unique devices that were used during followup.
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
            # Check header


            print(values[2])



            if keys != identifiers_header:
                logger.warning('Unknown identifiers header for user ID %s' % values[2])
            self.identifiers[p] = OrderedDict(zip(keys, values))  
        if len(list(set(self.history('device_os').values()))) == 1:
            self.os = list(self.history('device_os').values())[0]
        else:
            self.os = 'both'
            logger.warning('Found multiple operating systems for user ID %s.' % values[2])
        self.unique =  len(list(set(self.history('device_id').values())))
        if self.unique > 1:
            logger.warning('Found multiple devices for user ID %s.' % values[2])

    def history(self, header):
        '''
        Return a dictionary with history of a particular device attribute.
        For older files, replaces 'iPhone OS' with 'iOS' under header 'device_os'.
        
        Args:
            header (str): Column header from identifiers CSV.
                e.g. 'device_os', 'beiwe_version'

        Returns:
            history (OrderedDict):
                Keys are sorted timestamps.
                Values are device attributes observed at those times.        
        '''
        if not header in identifiers_header:
            logger.warning('%s isn\'t a device attribute.' % header)
        history = OrderedDict()
        for d in self.identifiers.values():
            history[d['timestamp']] = d[header]
        # operating system history
        if header == 'device_os':
            for k in history.keys():
                if history[k] == 'iPhone OS': history[k] = 'iOS'
        return(history)
        
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