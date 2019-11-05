'''
Functions for generating visual summaries of Beiwe data.
'''
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from .time import to_timestamp, filename_time_format, UTC
from .colors import *
#from .classes import ProjectData

                    
def plot_timestamps(ax, timestamp_dictionary, labels = [],
                    zero_at = 0, palette = paired_palette(12),
                    hide_spines = ['top', 'bottom', 'left', 'right']):
    '''
    Helper function for plot_raw_survey().
    Data coverage plot for raw Beiwe data from one user.
    Each vertical line represents one csv file (one hour of data) from the corresponding data stream. 
    
    Args:
        ax (subplots.AxesSubplot):  Where to plot the timestamps.
        timestamp_dictionary (OrderedDict):  Each value should be a list of timestamps.
        labels (list): Keys of timestamp_dictionary to plot, in order from top to bottom.
        zero_at (int):  Number to subtract from all timestamps before plotting. 
        palette (seaborn.palettes._ColorPalette):  Palette to use.
        hide_spines (list): Which axis spines to hide.

    Returns:
        t_min, t_max (int):  First and last timestamps in timestamp_dictionary.
    '''
    if len(labels) == 0:
        labels = list(timestamp_dictionary.keys())
    y_cutoffs = np.linspace(1, 0, len(labels)+1)
    t_min = None
    t_max = None
    for i in range(len(labels)):
        s = labels[i]
        try:
            timestamps = [t - zero_at for t in timestamp_dictionary[s]]
        except:
            timestamps = []
        if len(timestamps) > 0:
            ax.vlines(timestamps, ymin = y_cutoffs[i], ymax = y_cutoffs[i+1], color = palette[i]) 
            if t_min is None:
                t_min = min(timestamps)
                t_max = max(timestamps)
            else:
                t_min = min(t_min, min(timestamps))
                t_max = max(t_max, max(timestamps))    
        ax.set_ylim([0, 1])
        ax.set_yticks([])
        for loc in hide_spines:
            ax.spines[loc].set_color('none')
    return(t_min, t_max)


def make_legend(ax, labels, palette, loc = 'best', lw = 10):
    '''
    Make a basic legend.
    '''
    dummy_lines = []
    for i in range(len(labels)):
        dummy_lines.append(Line2D([0], [0], color=palette[i], lw=lw))
    ax.legend(dummy_lines, labels, loc = loc, framealpha = 1, frameon = False)


def date_time_axis(t_start, t_end):
    '''
    Define axis ticks and labels for various followup periods.
    Labels are date or date/time strings.    
    
    Args:
        t_start, t_end (int):  Range in millisecond timestamps.
        
    Returns:
        
    '''
    # duration, 
    # tick condition, tick condition met
    # label condition, label condition met, time format
    date_axis_settings = [
            [2*year_ms, '%b', ['January', 'June'], '%b Y']
            ]
    #    x_min = x_min - x_min % day_ms
    #    x_max = x_max - x_max % day_ms
    #    x_range = range(x_min, x_max, day_ms)
    #    x_locs = []
    #    x_sublocs = []
    #    x_labs = []
    #    for t in x_range:
    #        d = to_readable(t, to_format = '%m/%d/%Y', to_tz = UTC)
    #        if d.split('/')[1] == '01':
    #            x_locs.append(t)
    #            if d.split('/')[0] in ['01', '07']:
    #                x_labs.append(to_readable(t, to_format = '%b %Y', to_tz = UTC))
    #                x_sublocs.append(t)
    #            else:
    #                x_labs.append('')

    pass


def elapsed_time_axis(t_start, t_end):
    '''
    Define axis ticks and labels for various followup periods.
    Return tick labels in units of days, weeks, etc. from start time.
    Especially for the case when t_start = 0, but works if not.
    Args:
        t_start, t_end (int):  Range in millisecond timestamps.
        
    Returns:
        
    '''
    # duration, tick unit, tick unit spacing, tick spacing, label spacing
    zero_axis_settings = [
            [  year_ms, 'Weeks', week_ms,   week_ms,  5*week_ms],
            [2*year_ms, 'Weeks', week_ms, 5*week_ms, 25*week_ms]
            ]

    # figure out closest time period
    t = t_end - t_start    
    durations = [s[0] for s in axis_settings]
    differences = [abs(t - i) for i in durations] 
    index = differences.index(min(differences))
    d, tu, tus, ts, ls = zero_axis_settings[0]
    # add buffers of +/- one tick space
    start = t_start - t_start % ts
    end = (t_end + ts) - (t_end + ts)% ts
    # get ticks and labels
    tick_locs = np.arange(start, end+ts, ts)
    tick_sublocs = np.arange(start, end+ls, ls)
    tick_labels = [''] * len(tick_locs)       
    label_locs = np.arange(0, len(tick_labels), int(ls / ts))
    for i in label_locs:
        tick_labels[i] = str(int( (tick_locs[i] - tick_locs[0]) / tus))
    return(start, end, tick_locs, tick_sublocs, tick_labels, tu)    



def plot_raw_survey(srd, 
                    
                    adjust,
                    
                    data_types = [], user_ids = [],
                    
                    time_range = [None, None],
                    time_followup = None,
                    
                    name_assignment = 'default',
                    align_start = False,
                    palette = paired_palette, 
                    users_per_fig = 5,
                    x_label = '',
                    title = '', 
                    save_path = None):
    '''
    Data coverage plot for raw Beiwe data from one user.
    Each vertical line represents one csv file (one hour of data) from the corresponding data stream. 


    '''
    time_range = [to_timestamp(i, filename_time_format, UTC) for i in [srd.first, srd.last]]
    
    start, end, tick_locs, tick_sublocs, tick_labels, unit = elapsed_time_axis(time_range[0], time_range[1])
    size_inches = (16.8, 8.6)
    
    
    # get user ids
    if len(user_ids) == 0:
        try:
            user_ids = list(srd.name_assignments[name_assignment].keys())
        except:
            user_ids = srd.user_ids
    else:
        user_ids = [i for i in user_ids if i in srd.user_ids]
    n_users = len(user_ids)
    # get user names
    if name_assignment is None:
        names = user_ids
    else:
        names = [srd.name_assignments[name_assignment][i] for i in user_ids]
    # get data types
    if len(data_types) == 0:
        data_types = srd.to_plot()
    else:
        data_types = [t for t in srd.to_plot() if t in data_types]
    n_data_types = len(data_types)
    # get zeros
    if align_start:
        zero_at = [to_timestamp(srd.data[i].first, filename_time_format, UTC) for i in user_ids]
    else:
        zero_at = [0] * n_users
    # get palette
    palette = palette(n_data_types)    
    # set up output
    n_figs = int(np.ceil(n_users/users_per_fig))
    fig_list = []
    for i in range(n_figs):
        fig = plt.figure()
        gs = fig.add_gridspec(nrows = users_per_fig, ncols = 2, 
                              width_ratios = [3, 1],
                              height_ratios = users_per_fig*[1])
        fig_list.append(fig)
    plot_ax_list = []
    for i in range(n_users): # user data plots
        fig_index = int(np.floor(i / users_per_fig))
        ax_index = i % users_per_fig
        ax = fig_list[fig_index].add_subplot(gs[ax_index, 0])
        plot_ax_list.append(ax)
    # plot user data: 
    for i in range(n_users):
        plot_index = i % users_per_fig + 1
        ax = plot_ax_list[i]
        ax.vlines(tick_sublocs, ymin = -5, ymax = 5, color = 'k', alpha = 0.25)
        plot_timestamps(ax, srd.data[user_ids[i]].to_plot(), 
                        data_types, zero_at[i], palette, [])
        # format axes
        ax.set_ylabel(names[i], rotation = 0, 
                      horizontalalignment = 'right',
                      verticalalignment = 'center')
        ax.set_xlim(start, end)       
        if plot_index == users_per_fig or i == n_users-1:
            ax.set_xlabel(x_label + '(' + unit + ')')        
            ax.set_xticks(tick_locs)
            ax.set_xticklabels(tick_labels) 
        else:
            ax.set_xticks([])
    # make legends and titles, format figures
    legend_ax_list = []
    for i in range(n_figs): # legends
        ax = fig_list[i].add_subplot(gs[0, 1])
        legend_ax_list.append(ax)
    for i in range(n_figs):
        fig = fig_list[i]
        fig.suptitle(title + ', Figure ' + str(i+1) + ' of ' + str(n_figs), fontsize = 16)
        ax = legend_ax_list[i]
        make_legend(ax, data_types, palette, loc = 'best', lw = 10)
        ax.set_axis_off()    
        fig.set_size_inches(size_inches, forward = True)
        fig.subplots_adjust(top = adjust[0], bottom = adjust[1], 
                            left = adjust[2], right = adjust[3], 
                            wspace = adjust[4], hspace = adjust[5])
    # save figures
    if not save_path == None:
        for i in range(n_figs):
            fig_list[i].savefig(os.path.join(save_path, title.replace(' ', '_') + '_figure_' + str(i+1) + '_of_' + str(n_figs) + '.pdf'))






#plt.close('all')


#adjust = [0.06, 0.99, 0.95, 0.05, 0.1]

#top=0.925,
#bottom=0.05,
#left=0.1,
#right=0.99,
#hspace=0.07,
#wspace=0.05


#
#ids =['dbe3zm1w',
# 'sfjtqkth',
# '74douw36',
# '613jlw2m',
# '9kbkipu2',
# '3bylengo',
# 'u4adb3nn',
# 'l1s9aayw']


#fig, ax = plt.subplots()
#plot_raw_id(ax, pd)
#user_id
#pd = OrderedDict([('gps', os.listdir(temp_dir + user_id + '/gps')),
#                  ('accelerometer', os.listdir(temp_dir + user_id + '/accelerometer')),
#                  ('power_state', os.listdir(temp_dir + user_id + '/power_state'))])
#make_legend(ax, labels, palette, loc = 'best', lw = 10)







 


            


#
#all_ids #= os.listdir(raw_dirs[0])
#apple = []
#android = []
#for i in all_ids:
#    info = get_device_info(i, raw_dirs)
#    phone_os = info[0]['device_os']
#    if phone_os == 'iOS' or phone_os == 'iPhone OS':
#        apple.append(i)
#    elif phone_os == 'Android':
#        android.append(i)
#    else:
#        print(phone_os)
#
#len(all_ids)
#len(apple)
#len(android)
#
#viz_raw(apple[:11], raw_dirs, data_streams, id_dictionary = {}, 
#            palette_system = 'hls', save_path = None, title = 'Hourly data coverage for iPhone users (entry before July 2017)',
#            size_inches = (16.8, 8.6), adjust = [0.06, 0.99, 0.95, 0.05, 0.1])
#
#viz_raw(apple[11:], raw_dirs, data_streams, id_dictionary = {}, 
#            palette_system = 'hls', save_path = None, title = 'Hourly data coverage for iPhone users (entry after July 2017)',
#            size_inches = (16.8, 8.6), adjust = [0.06, 0.99, 0.95, 0.05, 0.1])
#
#viz_raw(android, raw_dirs, data_streams + ['calls', 'texts'], id_dictionary = {}, 
#            palette_system = 'hls', save_path = None, title = 'Hourly data coverage for Android users',
#            size_inches = (16.8, 8.6), adjust = [0.06, 0.99, 0.95, 0.05, 0.1])
#
#
#import pandas as pd
#log = pd.read_csv('/mnt/veracrypt1/downloads/2018-03-17/logs/download_log.csv', index_col = None)
#log.sort_values(by = 'size_MB', inplace = True)
#log = log[log.participant_id > 0]
#all_ids = list(log.index)
#
#dates = dict()
#f = open('/mnt/veracrypt1/downloads/2018-03-17/logs/download_log.csv', 'r')
#for row in f:
#    print(row.split(',')[2])
#    if not row.split(',')[0] == 'participant_id':
#        if not row.split(',')[2] == '':        
#            dates[row.split(',')[2]] = row.split(',')[0]         
#f.close()
#len(dates.keys())
#
#sorted_dates = sorted(dates.keys())
#all_ids = 
#
#
#user_ids = ['sfjtqkth', '3bylengo', '2pb59c', 'dzve2i',  'j4zug8us']
#        
#{}.keys()
#
#ax = axes[]
#
#
#
#from beiwehelpers.time import *
#
#                for f in filenames:
#                    hours.append(f.split('.'))
#                    
#                 os.listdir(d)   
#                d = data_dirs[0]
#                 
#                 for d in raw_dirs:
#    
#path, dirs, filenames = list(os.walk(d))[0][2]
#list(filenames)
#            
#    user_id = 'sfjtqkth'
#    
#    data_streams = ['accelerometer', 'gps', 'audio_recordings', 'survey_answers']
#    
#    raw_dirs = ['/mnt/veracrypt1/downloads/2018-03-17/raw', '/mnt/veracrypt1/downloads/2018-03-17/raw']
#    
#    
#    
#    
#    
#idds = os.listdir('/mnt/veracrypt1/downloads/2018-03-17/raw')
#all_streams = []
#for idd in idds:
#    streams = os.listdir('/mnt/veracrypt1/downloads/2018-03-17/raw/' + idd)
#    for s in streams:
#        if not s in all_streams:
#            all_streams.append(s)
#    
