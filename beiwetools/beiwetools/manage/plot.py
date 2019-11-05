


def to_plot(passive = True, tracking = True, audio = True):
    '''
    Get inputs for plot_raw_survey.
    
    Args:
        None
        
    Returns:
        work_dictionary (OrderedDict):  Keys are data types.
            Values are lists of timestamps of when that data type was collected.
    '''
    work_dictionary = OrderedDict()
    if passive:
        work_dictionary.update(self.passive)
    if tracking:
        #work_dictionary.update(flatten_nested_dictionaries(self.tracking))
        pass
        
    
        # fix this
    
    
    if audio:
        a = OrderedDict(zip([k + '_audio' for k in self.audio.keys()], self.audio.values()))
        work_dictionary.update(a)
    for k in work_dictionary.keys():
        datetimes = [os.path.basename(p).split('.')[0] for p in work_dictionary[k]]
        timestamps = [to_timestamp(h, from_format = filename_time_format, from_tz = UTC) for h in datetimes]        
        work_dictionary[k] = timestamps
    # On rare occasions there may be a tracking survey folder called "None."
    # May occur for a deleted survey?
    keys_to_delete = [k for k in work_dictionary.keys() if 'None' in k]    
    for k in keys_to_delete:
        del work_dictionary[k]
    return(work_dictionary)
    
    
    

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

