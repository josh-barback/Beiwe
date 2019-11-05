'''
Functions for working with Beiwe time formats.
'''
import pytz
import logging
import datetime
from timezonefinder import TimezoneFinder
from .time_constants import *


logger = logging.getLogger(__name__)


try:
    import holidays
    has_holidays = True
    US_holidays = holidays.UnitedStates()
except:
    logger.warning('Unable to import package holidays.')
    has_holidays = False


def is_US_holiday(date, date_format = date_only):
    '''
    Identify dates that are US holidays.
    There is probably a better way to do this with pandas.
    
    Args:
        date (str): Date string.
        date_format (str): Format of date.
        
    Returns:
        is_holiday (bool): True if the date us_holidays = holidays.UnitedStates()is a US holiday.
    '''    
    is_holiday = None
    if has_holidays:
        is_holiday = datetime.datetime.strptime(date, date_format) in US_holidays
        return(is_holiday)
    else:
        logger.warning('Holidays package was not imported.')
    return(is_holiday)
    

def local_now(to_format = local_time_format):
    '''
    Get the current local time.
    Mainly 
    
    Args:
        to_format (str):  Time format, expressed using directives from the datetime package.
    
    Returns:
        local (str):  Formatted local time now.
    
    '''
    now = datetime.datetime.now().astimezone()
    local = now.strftime(to_format)
    return(local)


def convert_seconds(s):
	'''
	Convert second of day to clock time.

	Args:
		s (int):  Second of the day.

	Returns:
		time (str):  Clock time formatted as '%H:%M'.
	'''
	time = to_readable(s*1000, to_format = '%H:%M', to_tz = UTC)
	return(time)


def to_timestamp(time, from_format, from_tz = UTC):
	'''
	Convert a date/time string to a timestamp.
	
	Args:
		time (str):  A human-readable date/time string.
		from_format (str):  The format of time, expressed using directives from the datetime package.
		from_tz (timezone from pytz.tzfile):  The timezone of time.

	Returns:
		ts (int): Timestamp in milliseconds.
	'''
	dt = datetime.datetime.strptime(time, from_format)
	utc_dt = from_tz.localize(dt)
	ts = round(utc_dt.timestamp() * 1000) 
	return(ts)


def to_readable(timestamp, to_format, to_tz):    
	'''
	Convert a timestamp to a human-readable string localized to a particular timezone.

	Args:
		timestamp (int):  Timestamp in milliseconds.
		to_format (str):  The format of readable, expressed using directives from the datetime package.
		to_tz (str or timezone from pytz.tzfile):  The timezone of readable.

	Returns:
		readable (str):  A human-readable date/time string.
	'''
	if type(to_tz) is str:
		to_tz = pytz.timezone(to_tz)
	dt = datetime.datetime.utcfromtimestamp(timestamp/1000)
	utc_dt = pytz.utc.localize(dt)
	local_dt = utc_dt.astimezone(to_tz)
	readable = local_dt.strftime(to_format)
	return(readable)    


def get_timezone(latitude, longitude, try_closest = True):
    '''
    Get timezone from latitude and longitude.

    Args:
        latitude, longitude (float): Coordinates.
        try_closest (bool): 
            If True and no timezone found, will try to find closest timezone within +/- 1 degree latitude & longitude.

    Returns:
        tz (str): Timezone string that can be read by pytz.timezone().       
    '''    
    tf = TimezoneFinder()
    tz = tf.timezone_at(lng = longitude, lat = latitude)
    if tz is None and try_closest:
        logger.warning('No timezone found for %s, %s.  Looking for closest timezone.' % (str(latitude), str(longitude)))
        tz = tf.closest_timezone_at(lat=latitude, lng=longitude)    
    return(tz)
    
    
def difference_days(first_date, second_date):
    '''
    Get number of days between two dates.

    Args:
        first_date, second_date (str):
            Dates in date_only format.
            
    Returns:
        difference (int): 
            Number of days between the two dates.
            Positive if first_date is before second_date.
            Negative if first_date is after second_date.    
    '''
    d0 = datetime.datetime.strptime(first_date, date_only)
    d1 = datetime.datetime.strptime(second_date, date_only)
    difference = (d1 - d0).days
    return(difference)
        
    
def between_days(start_date, end_date):
    '''    
    Get a list of dates given start and end dates.
    
    
    Args:
        start_date, end_date (str):
            Dates in date_only format.
            
    Returns:
        date_list (list): List of dates from start_date to end_date, inclusive.        
    '''    
    d0 = datetime.datetime.strptime(start_date, date_only)    
    d1 = datetime.datetime.strptime(end_date, date_only)    
    dt_list = [d0]
    while dt_list[-1] < d1:
        dt_list.append(dt_list[-1] + datetime.timedelta(days = 1))
    date_list = [dt.strftime(date_only) for dt in dt_list]
    return(date_list)
