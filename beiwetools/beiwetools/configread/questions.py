'''
Classes for representing Beiwe tracking survey questions.
'''
import os
import logging
from collections import OrderedDict
from .functions import load_settings
from beiwetools.helpers import check_same, Summary, read_json
    

logger = logging.getLogger(__name__)


# get formatted settings for study and survey parameters
this_dir = os.path.dirname(__file__)
try:
    survey_settings = read_json(os.path.join(this_dir, 'survey_settings.json'))
except:
    logging.warning('There\'s a problem with the survey attribute records.')


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
        self.info = load_settings(survey_settings['question_info'], self.raw)
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
            if k not in survey_settings['question_info']:
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
