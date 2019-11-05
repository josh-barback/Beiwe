'''
Classes for working with Beiwe study configurations.
'''
import os
import logging
from collections import OrderedDict
from beiwetools.helpers import (check_same, Summary, 
                                local_now, setup_directories, 
                                read_json, write_json, write_string)
from .functions import *
    

logger = logging.getLogger(__name__)


class BeiweConfig():
    """
    Class for representing a Beiwe study configuration as encoded in the corresponding JSON file.

    Args:
        path (str): Path to the JSON configuration file.
            Or a path to a directory containing a previously exported configuration.
        names_path (str):  Path to a JSON file with name assignments for study objects.
            Optional. If None: 
            - study_name will be taken from the name of the configuration file,
            - survey and question names will be assigned in the order they appear in the JSON file.

    Attributes:
        warnings (list): Records of unknown settings or object types, if any.
        name (str): An additional identifier for the study, such as the name of the configuration file.
        paths (str): Paths to the files used to create the BeiweConfig object.
        name_assignments (OrderedDict): 
            Keys are object identifiers, values are readable names.
            Default assignments are:
                "Survey_1", "Survey_2", etc.
                "Survey_1_Question_1", "Survey_1_Question_2", etc.
        name_lookup (dict): 
            If assigned names are all unique, keys are names and values are identifiers.
        default_names (bool): 
            Whether or not surveys & questions are assigned default names.
            True if configuration is loaded with names_path = None.
            False if:
                update_names() method is called,
                configuration is loaded from an export,
                or configuration is loaded with a name assignment dictionary.
        raw (OrderedDict): The deserialized configuration file.
        extended_format (bool): True if the JSON file uses MongoDB Extended JSON format, False otherwise.
        identifier (int or str): 
            If the JSON file uses MongoDB Extended JSON format, then the id is a 24-character identifier for the study.
            Otherwise, the id is an integer.
            Note that this id may not be the same as the backend's identifier for this study.
        summary (Summary):  Some features of the BeiweConfig object for printing.
        device_settings (OrderedDict): Keys are setting names, values are the settings.    
        surveys (OrderedDict): Keys are survey IDs, values are BeiweSurvey objects.
        audio_surveys (list): Survey IDs for audio surveys.
        tracking_surveys (list): Survey IDs for tracking surveys.
        other_surveys (list): Other survey IDs.
        ignore (list): Attributes to ignore when checking equality.
    """    

    def __init__(self, path, names_path = None):
        self.warnings = []
        self.paths = OrderedDict()
        # check if path is a directory:
        if os.path.isdir(path):
            records = os.path.join(path, 'records')
            path = os.path.join(records, 'raw.json')
            names_path = os.path.join(records, 'names.json')
        self.paths['path'] = path
        self.paths['names_path'] = names_path
        self.default_names = self.paths['names_path'] is None
        # load configuration file
        self.raw = read_json(path)
        # get names
        self.name_assignments = OrderedDict()
        if not self.default_names:
            self.name_assignments = read_json(names_path)
        # does the configuration file use MongoDB Extended JSON? 
        self.extended_format = '$oid' in str(self.raw)
        # get identifier and deleted status
        if self.extended_format:
            self.identifier = self.raw['device_settings']['_id']['$oid']
        else:
            self.identifier = self.raw['device_settings']['id']
        # get study name
        if self.identifier in self.name_assignments:
            self.name = self.name_assignments[self.identifier]
        else:
            self.name = os.path.basename(path).replace('_surveys_and_settings', '').replace('.json', '').replace('_', ' ')
            self.name_assignments[self.identifier] = self.name
        # read settings
        self.settings = DeviceSettings(self.raw['device_settings'], self)
        # read surveys
        self.surveys = OrderedDict()
        self.audio_surveys = []
        self.tracking_surveys = []
        self.other_surveys = []
        n_surveys = len(self.raw['surveys'])
        n_digits = len(str(n_surveys)) 
        for i in range(n_surveys):
            s = self.raw['surveys'][i]
            # get/assign name                
            if self.extended_format:
                survey_id = s['_id']['$oid']
            else:
                survey_id = s['object_id']                       
            if survey_id in self.name_assignments.keys():
                name = self.name_assignments[survey_id]
            else:
                name = 'Survey_' + str(i+1).zfill(n_digits)            
                self.name_assignments[survey_id] = name
            # read survey
            if s['survey_type'] == 'audio_survey':
                survey = AudioSurvey(s, self, name)
                self.audio_surveys.append(survey.identifier)
            elif s['survey_type'] == 'tracking_survey':
                survey = TrackingSurvey(s, self, name)
                self.tracking_surveys.append(survey.identifier)
            else:
                survey = BeiweSurvey(s, self, name)
                self.other_surveys.append(survey.identifier)
                flag = 'Found unknown survey type: %s' % survey.type
                self.warnings.append(flag)
                logger.warning(flag)
            self.surveys[survey.identifier] = survey
        # get summary
        self.summarize()
        # name lookup dictionary            
        self.get_lookup()
        # when checking equality
        self.to_check = ['settings', 'surveys']

    def get_lookup(self):
        if len(list(set(self.name_assignments.values()))) == len(self.name_assignments):
            self.name_lookup = {v:k for k, v in self.name_assignments.items()}
        else: 
            self.name_lookup = {}
            logger.warning('Name assignments are not unique.')

    def summarize(self):
        details = Summary(['Identifier', 'MongDB Extended JSON format', 'Default names'],
                          [self.identifier, self.extended_format, self.default_names])
        survey_counts = Summary(['Audio Surveys', 'Tracking Surveys', 'Other Surveys'],
                                [len(s) for s in [self.audio_surveys, self.tracking_surveys, self.other_surveys]])
        self.summary = Summary([self.name, 'Number of Surveys'],
                               [details, survey_counts])
    
    def update_names(self, new_names):
        '''
        Update all name assignments.

        Args:
            new_names (dict or OrderedDict): 
                Keys are old names, values are new names.
            
        Returns:
            None
        '''
        for k in self.name_assignments:
            if self.name_assignments[k] in new_names.keys():
                self.name_assignments[k] = new_names[self.name_assignments[k]]
        self.default_names = False
        self.name = self.name_assignments[self.identifier]
        for s in self.surveys.values(): s.update_names(self.name_assignments)
        self.summarize()
        self.get_lookup()

    def __eq__(self, other):
        return(check_same(self, other, self.to_check))
                           
    def export(self, directory, track_time = True, indent = 4, max_width = 70):
        '''
        Write study documentation to text files.

        Args:
            directory (str):  Path to a directory.
            track_time (bool):  If True, nests output in a folder with current local time.
            indent (int):  Indentation for pretty printing.
            max_width (int):  Maximum line width for text file.
        
        Returns:
            out_dir (str): Path to study documentation directory.
        '''       
        if track_time:
            temp_name = 'configuration documentation from ' + local_now()
            temp = os.path.join(directory, temp_name.replace(' ', '_'))
        else:
            temp = directory
        out_dir = os.path.join(temp, self.name.replace(' ', '_'))
        # export settings
        settings_dir = os.path.join(out_dir, 'settings')
        config_dir = os.path.join(out_dir, 'records')
        setup_directories([out_dir, settings_dir, config_dir])
        # export configuration records
        write_json(self.raw, 'raw', config_dir)
        write_json(self.paths, 'paths', config_dir)        
        write_json(self.name_assignments, 'names', config_dir)
        # export summary
        self.summary.to_file('overview', out_dir, indent = indent, max_width = max_width)
        # export warnings        
        write_string('', 'warnings', out_dir, title = 'Warnings:', mode = 'w')
        if len(self.warnings) == 0: write_string('None', 'warnings', out_dir, mode = 'a')
        else:
            for w in self.warnings: write_string(w, 'warnings', out_dir, mode = 'a')
        # export device settings
        self.settings.general_summary.to_file('general_settings', settings_dir, 
                                              indent = indent, max_width = max_width)
        self.settings.passive_summary.to_file('passive_data_settings', settings_dir, 
                                              indent = indent, max_width = max_width)        
        self.settings.display_summary.to_file('display_settings', settings_dir, 
                                              indent = indent, max_width = max_width,
                                              extra_breaks = [1, 2])        
        # export surveys        
        dir_names = ['audio_surveys', 'tracking_surveys', 'other_surveys']
        surveys = [self.audio_surveys, self.tracking_surveys, self.other_surveys]
        for i in range(len(surveys)): 
            survey_list = surveys[i]
            if len(survey_list) > 0:
                survey_dir = os.path.join(out_dir, dir_names[i])
                setup_directories(survey_dir)
                for k in survey_list:
                    s = self.surveys[k]
                    name = s.name.replace(' ', '_')
                    if not s.deleted is None and s.deleted:
                        name = 'deleted_' + name
                    s.summary.to_file(name, survey_dir, indent = indent, max_width = max_width)
        return(out_dir)


class BeiweSurvey():
    '''
    Class for representing a survey from a Beiwe configuration file.
    
    Args:
        survey_config (OrderedDict):  From a JSON configuration file.
        beiweconfig (BeiweConfig): The instance to which this survey belongs.
        
    Attributes:
        name (str): An additional identifier for the study, optional.
        raw (OrderedDict): The deserialized survey configuration.
        extended_format (bool): True if the JSON file uses MongoDB Extended JSON format, False otherwise.
        deleted (bool):  True if the survey was deleted.
        type (str):  Examples are 'audio_survey', 'dummy', or 'tracking_survey'.        
        identifier (str):  The 24-character identifier for the survey.
        info (OrderedDict):  Includes identifiers, survey type, and whether the survey was deleted.
        settings (OrderedDict):  Survey settings from the JSON configuration file.
        timings (OrderedDict): Human-readable timings.  Keys are days of the week, values are lists of scheduled times. 
        content (list):  Content from the JSON configuration file.       
        content_dict (OrderedDict): Content organized for printing export.
        summary (Summary): Summary of survey attributes for printing.
        to_check (list): Attributes to consider when checking equality.
    '''
    def __init__(self, survey_config, beiweconfig, name = None):
        self.name = name
        self.raw = survey_config
        # get identifier and deleted status
        if beiweconfig.extended_format:
            self.identifier = self.raw['_id']['$oid']
            self.deleted = None
        else:
            self.identifier = self.raw['object_id']
            self.deleted = self.raw['deleted']
        # get survey type
        self.type = self.raw['survey_type']
        # get info
        self.info = load_settings(survey_info, self.raw)
        # get settings
        self.get_settings()
        # get timings
        self.timings = load_timings(self.raw['timings'])
        # get content
        self.get_content(beiweconfig)
        # summary
        self.summarize()

    def get_settings(self):
        self.settings = self.raw['settings']
        
    def get_content(self, beiweconfig):
        self.content = self.raw['content']
        self.content_dict = OrderedDict([('Content', self.content)])
        # when checking equality
        self.to_check = ['type', 'settings', 'timings', 'content']

    def summarize(self):
        labels = ['Info', 'Settings', 'Timings'] + list(self.content_dict.keys())
        items = [self.info, self.settings, self.timings] + list(self.content_dict.values())
        self.summary = Summary(labels, items, header = self.name)

    def update_names(self, name_assignments):
        self.name = name_assignments[self.identifier]
        self.summarize()

    def __eq__(self, other):
        return(check_same(self, other, self.to_check))

        
class AudioSurvey(BeiweSurvey):
    '''
    Class for representing an audio survey from a Beiwe configuration file.
    Inherits from BeiweSurvey.
        
    Attributes:
        settings (OrderedDict):  Audio survey settings from the JSON configuration file.
        prompt (str):  Audio survey prompt.
    '''    
    def __init__(self, survey_config, beiweconfig, name = None):
        super().__init__(survey_config, beiweconfig, name)

    def get_settings(self):
        self.settings = load_settings(audio_survey_settings, self.raw['settings'])
        
    def get_content(self, beiweconfig):
        try:
            self.prompt = self.raw['content'][0]['prompt']
        except:
            self.prompt = None
        self.content_dict = OrderedDict([('Prompt', self.prompt)])        
        # when checking equality
        self.to_check = ['type', 'settings', 'timings', 'prompt']     

class TrackingSurvey(BeiweSurvey):        
    '''
    Class for representing a tracking survey from a Beiwe configuration file.
    Inherits from BeiweSurvey.
        
    Attributes:
        settings (OrderedDict):  Tracking survey settings from the JSON configuration file.
        questions (OrderedDict):  Keys are question IDs, values are Tracking Question objects.
    '''    
    def __init__(self, survey_config, beiweconfig, name = None):
        super().__init__(survey_config, beiweconfig, name)

    def get_settings(self):
        self.settings = load_settings(tracking_survey_settings, self.raw['settings'])

    def get_content(self, beiweconfig):
        self.questions = OrderedDict()
        n_questions = len(self.raw['content'])
        n_digits = len(str(n_questions))
        for i in range(n_questions):
            question_config = self.raw['content'][i]
            qid = question_config['question_id']
            # get/assign name
            if qid in beiweconfig.name_assignments:
                qname = beiweconfig.name_assignments[qid]
            else:
                qname = self.name + '_Question_' + str(i+1).zfill(n_digits)
                beiweconfig.name_assignments[qid] = qname
            # identify question type            
            qtype = question_config['question_type']
            if qtype in tracking_questions.keys():
                self.questions[qid] = tracking_questions[qtype](question_config, qname)         
            else: 
                self.questions[qid] = TrackingQuestion(question_config, qname)
                flag = 'Found unknown question type: %s' %qtype
                beiweconfig.warnings.append(flag)
                logger.warning(flag)        
        self.get_content_dict()
        # when checking equality
        self.to_check = ['type', 'settings', 'timings', 'questions']     

    def get_content_dict(self):
        question_summary = Summary(['\n' + q.name for q in self.questions.values()], 
                                       [q.summary for q in self.questions.values()])        
        self.content_dict = OrderedDict([('Questions', question_summary)]) 

    def update_names(self, name_assignments):
        self.name = name_assignments[self.identifier]
        for q in self.questions.values():
            q.name = name_assignments[q.identifier]
            q.summarize()
        self.get_content_dict()
        self.summarize()


class TrackingQuestion():
    '''
    Class for representing a tracking survey question from a Beiwe configuration file.
    
    Args:
        question_config (OrderedDict):  From a JSON configuration file.
        
    Attributes:
        name (str): Assigned in order of creation, e.g. Q_01, Q_02, etc.
        raw (OrderedDict): The deserialized question configuration.        
        extended_format (bool): True if the JSON file uses MongoDB Extended JSON format, False otherwise.
        identifier (str):  The 36-character question_id. 
        type (str):  Question type, e.g 'info_text_box'
        info (OrderedDict):  Keys are 'question_id', 'question_type', 'display_if', 'question_text'
        other (OrderedDict):  Content that is specific to the question type.
        logic (OrderedDict):  The branching logic configuration from the JSON file.
        summary (Summary): Summary of question attributes for printing.
        to_check (list): Attributes to consider when checking equality.
    '''    
    def __init__(self, question_config, name = None):
        self.raw = question_config
        self.name = name
        # does the configuration file use MongoDB Extended JSON? 
        self.extended_format = '$oid' in str(self.raw)
        # get identifier
        self.identifier = self.raw['question_id']
        # get question type
        self.type = self.raw['question_type']
        # get info
        self.info = load_settings(question_info, self.raw)
        # get other content
        self.get_other_content()        
        # get logic
        if not self.info['display_if'] == 'Not found':
            self.logic = self.info['display_if']
            self.info['display_if'] = 'Uses branching logic, see configuration file for details.'
        else:
            self.logic = None
            self.info['display_if'] = 'Does not use branching logic.'            
        # summary
        self.summarize()    
        # when checking equality
        self.to_check = ['info', 'other', 'logic']
        
    def get_other_content(self):
        self.other = OrderedDict()        
        for k in self.raw.keys():
            if k not in question_info:
                self.other[k] = self.raw[k]

    def update_names(self, name_assignments):
        self.name = name_assignments[self.identifier]
        self.summarize()
        
    def summarize(self):
        labels = list(self.info.keys()) + list(self.other.keys())
        items =  list(self.info.values()) + list(self.other.values())
        self.summary = Summary(labels, items, header = self.name)

    def __eq__(self, other):
        return(check_same(self, other, self.to_check))

    
class InfoTextBox(TrackingQuestion):
    '''
    Class for representing an info text box from a Beiwe tracking survey.
    Inherits from TrackingQuestion.
    '''
    def __init__(self, question_config, name = None):
        super().__init__(question_config, name)


class CheckBox(TrackingQuestion):
    '''
    Class for representing a check box question from a Beiwe tracking survey.
    Inherits from TrackingQuestion.

    Args:
        answers (list): List of question answers in the order they appear in the configuration file.
    '''
    def __init__(self, question_config, name = None):
        super().__init__(question_config, name)
        
    def get_other_content(self):
        self.answers = [list(a.values())[0] for a in self.raw['answers']]
        #numbered_answers = [str(i) + ': ' + self.answers[i] for i in range(len(self.answers))]
        numbered_answers = OrderedDict([(str(i), self.answers[i]) for i in range(len(self.answers))])    
        self.other = OrderedDict([('answers', numbered_answers)])


class RadioButton(TrackingQuestion):
    '''
    Class for representing a radio button question from a Beiwe tracking survey.
    Inherits from TrackingQuestion.

    Args:
        answers (list): List of question answers in the order they appear in the configuration file.
    '''
    def __init__(self, question_config, name = None):
        super().__init__(question_config, name)
        self.answers = [list(a.values())[0] for a in self.raw['answers']]

    def get_other_content(self):
        self.answers = [list(a.values())[0] for a in self.raw['answers']]
        numbered_answers = OrderedDict([(str(i), self.answers[i]) for i in range(len(self.answers))])
        self.other = OrderedDict([('answers', numbered_answers)])


class Slider(TrackingQuestion):
    '''
    Class for representing a slider question from a Beiwe tracking survey.
    Inherits from TrackingQuestion.
    
    Args:
        min, max (int): Slider endpoints.
    '''
    def __init__(self, question_config, name = None):
        super().__init__(question_config, name)
        
    def get_other_content(self):
        self.min = self.raw['min']
        self.max = self.raw['max']
        self.other = OrderedDict([('min', self.min), ('max', self.max)])       
        

class FreeResponse(TrackingQuestion):
    '''
    Class for representing a free response question from a Beiwe tracking survey.
    Inherits from TrackingQuestion.
    
    Args:
        text_field_type ():
    '''
    def __init__(self, question_config, name = None):
        super().__init__(question_config, name)

    def get_other_content(self):
        self.text_field_type = self.raw['text_field_type']
        self.other = OrderedDict([('text_field_type', self.text_field_type)])         


# Dictionary of tracking question types
qtypes = ['info_text_box', 'checkbox', 'radio_button', 'slider', 'free_response']
qclasses = [InfoTextBox, CheckBox, RadioButton, Slider, FreeResponse]
tracking_questions = OrderedDict(zip(qtypes, qclasses))


class DeviceSettings():
    '''
    Class for representing device settings from a Beiwe configuration file.
    
    Args:
        device_settings (OrderedDict):  From a JSON configuration file.
        beiweconfig (BeiweConfig): The instance to which these settings belong.
        
    Attributes:
        raw (OrderedDict): Deserialized settings.
        identifiers (OrderedDict): Study identifiers.
        deleted (OrderedDict): Whether or not the study was deleted.
        survey (OrderedDict): Global survey settings.
        app (OrderedDict): Settings for app behavior.
        display (OrderedDict): Text displayed by the app.
        passive (OrderedDict): Passive data settings.
        other (OrderedDict): Settings that haven't been documented.   
        general_summary, passive_summary, display_summary (Summary):
            Organized settings for printing or export.
        to_check (list): Attributes to consider when checking equality.
    '''
    def __init__(self, device_settings, beiweconfig):
        self.raw = device_settings
        # get settings        
        self.identifiers =  load_settings(study_settings['Identifiers'], self.raw)
        if beiweconfig.extended_format: 
            self.identifiers['_id'] = self.identifiers['_id']['$oid'] 
        self.deleted =      load_settings(study_settings['Deleted Status'], self.raw)
        self.survey =       load_settings(study_settings['Survey Settings'], self.raw)
        self.app =          load_settings(study_settings['App Settings'], self.raw)
        self.display =      load_settings(study_settings['Display Settings'], self.raw)
        self.passive =      load_settings(study_settings['Passive Data Settings'], self.raw)
        known_settings = [k for s in list(study_settings.values()) for k in s]
        unknown_settings = [k for k in self.raw.keys() if k not in known_settings]
        if len(unknown_settings) > 0:
            self.other = load_settings(unknown_settings, self.raw)
            for u in unknown_settings:
                flag = 'Found unknown device setting: %s' % u
                beiweconfig.warnings.append(flag)
                logger.warning(flag)
        else:
            self.other = None
        # summaries
        self.general_summary = Summary(list(study_settings.keys())[:4] + ['Other/Unknown Settings'],
                                       [self.identifiers, self.deleted, self.survey, self.app, self.other])
        self.passive_summary = Summary(['Passive Data Settings'], [self.passive])
        self.display_summary = Summary(['Display Settings'], [self.display], sep = ':\n ')
        # when checking equality
        self.to_check = ['survey', 'app', 'display', 'passive', 'other']

    def __eq__(self, other):
        return(check_same(self, other, self.to_check))

        