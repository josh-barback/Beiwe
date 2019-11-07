'''
Classes for representing Beiwe surveys.
'''
import logging
from collections import OrderedDict
from .functions import load_settings, load_timings
from .questions import survey_settings, tracking_questions, TrackingQuestion
from beiwetools.helpers.classes import Summary
from beiwetools.helpers.functions import check_same


logger = logging.getLogger(__name__)


class BeiweSurvey():
    '''
    Class for representing a survey from a Beiwe configuration file.
    
    Args:
        survey_config (OrderedDict):  From a JSON configuration file.
        beiweconfig (BeiweConfig): The instance to which this survey belongs.
        
    Attributes:
        name (str): An additional identifier for the study, optional.
        


        documentation (OrderedDict):  How to document this object.
            Keys are 'folder' and 'header'.
            The value for 'folder' is the name of the folder in which to export documentation.
            The value for 'header' is the name of header under which to report survey counts.
            
        
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
        self.documentation = OrderedDict([('folder', 'other_surveys'),
                                          ('header', 'Other Surveys')])
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
        self.info = load_settings(survey_settings['survey_info'], self.raw)
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
        self.class_name = 'audio'
        
    def get_settings(self):
        self.settings = load_settings(survey_settings['audio_survey_settings'], 
                                      self.raw['settings'])
        
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
        self.class_name = 'tracking'

    def get_settings(self):
        self.settings = load_settings(survey_settings['tracking_survey_settings'], 
                                      self.raw['settings'])

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


# Dictionary of tracking survey types
stypes = ['audio_survey', 'tracking_survey']
sclasses = [AudioSurvey, TrackingSurvey]
survey_classes = OrderedDict(zip(stypes, sclasses))