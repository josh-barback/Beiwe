'''Functions for graphical summaries of raw Beiwe data records.

'''
import os
import logging

import numpy as np
import matplotlib.pyplot as plt

from collections import OrderedDict

from beiwetools.helpers.plot import elapsed_time_axis, plot_timestamps, make_legend
from beiwetools.helpers.colors import paired_palette
from beiwetools.helpers.time import to_timestamp, filename_time_format, UTC


logger = logging.getLogger(__name__)


# plot
# plot_setup
# plot each user
# do axes
# do title 
# do legend

# BeiweProject.plot(align, path = None, title = 'Raw Data Coverage')
path (Nonetype or str):
If str, then


plot_setup()

# coverage plot for each user
for i in range(len(user_ids)):
    ax, ud = plot_axes[i], bp.data[user_ids[i]]
    user_plot(ax, ud, align, to_plot_passive, to_plot_surveys, palette)    
# legend for each figure
labels_dict = legend_setup(to_plot_passive, to_plot_surveys)
for ax in legend_axes:
    make_fancy_legend(ax, labels_dict, palette, loc = 'best', lw = 10)
    ax.axis('off')


def legend_setup(to_plot_passive, to_plot_surveys):
    labels_dict = OrderedDict({'passive': to_plot_passive})
    labels_dict.update(to_plot_surveys)
    for k in labels_dict:
    
    
    return(labels_dict)
    

def plot_setup(
        bp,      
        user_ids = 'all', 
        user_names = 'default_nameidentifier_lookup',
        users_per_fig = 'all',
        align = 'absolute', 
        show_range = 'auto',
        palette_function = paired_palette,
        legend_size = 0.25,
        passive_data = 'all', 
        survey_data = 'all'):
    '''
    Args:
        bp (BeiweProject): A BeiweProject object.
        title (str): Title for figure(s).
        user_ids (list): List of Beiwe user ids to include.
            User data is plotted according to the order of this list.
        user_names (str or dict or OrderedDict): How to label user data.
            If 'id' then plot is labeled with Beiwe user IDs.
            Can be a key (str) from bp.lookup, e.g. 'default_name'.
            If dict, then keys are Beiwe user ids, values are names.
        users_per_fig (str or int):
            If 'all' then all data is plotted on one figure.
            If int, then 
        align (str):
            If 'absolute', plots true timestamps.
            If 'relative', zero for each user is the user's first observation.
        show_range (str or tuple):
            If 'auto' then adjusts time range to show timestamps from all users.
            Otherwise, a pair of datetimes in filename_time_format (start, end).
        palette_function (function):  
            Palette function to use (e.g. from beiwetools.helpers.colors).


        legend_size (float): Legend size, around 0.25 is probably good.


        passive_data (list): List of passive data streams to plot.
        survey_data (OrderedDict):
            Which survey data to plot.
            Keys are survey data types (e.g. 'survey_timings').
            Values are lists of survey ids or names.

    Returns:
        plot_axes ():
        legend_axes ():
        
    '''
    # which user IDs to include:
    if user_ids == 'all': user_ids = bp.ids
    else: user_ids = [i for i in user_ids if i in bp.ids]
    # which user names to use:
    if isinstance(user_names, str):
        if user_names == 'id':
            user_names = dict(zip(user_ids, user_ids))
        elif user_names in bp.lookup:
            user_names = bp.lookup[user_names]
    names = [user_names[i] for i in user_ids]
    # set up figures:
    if users_per_fig == 'all': users_per_fig = len(user_ids)
    n_figures = int(np.ceil(len(user_ids)/users_per_fig))
    figures = []
    plot_axes = []
    legend_axes = []
    for i in range(n_figures):
        fig = plt.figure()
        figures.append(fig)
        gs = fig.add_gridspec(nrows = users_per_fig, ncols = 2, 
                              width_ratios = [1, legend_size],
                              height_ratios = users_per_fig*[1])
        for j in range(users_per_fig):
            ax = fig.add_subplot(gs[j, 0]) # one plot for each user
            plot_axes.append(ax)
        ax = fig.add_subplot(gs[0, 1]) # one legend for each figure
        legend_axes.append(ax)    
    # x axis
    
    
    # which passive data to plot:
    if passive_data == 'all':
        to_plot_passive = bp.passive
    # which survey data to plot:
    if survey_data == 'all':
        to_plot_surveys = bp.surveys
    else:
        to_plot_surveys = OrderedDict()
        for k in survey_data:
            temp = []
            for s in survey_data[k]:
                if s in bp.surveys[k]:
                    temp.append(s)
                elif s in bp.lookup['reverse_object_name']:
                    temp.append(bp.lookup['reverse_object_name'][s])
            to_plot_surveys[k] = temp

    # palette
    n_streams = len(to_plot_passive) + sum([len(to_plot_surveys[k]) for k in to_plot_surveys])
    palette = palette_function(n_streams)
        
    return(user_ids, names, palette,
           figures, plot_axes, legend_axes, 
           x_range, x_ticks, x_labels,
           to_plot_passive, to_plot_surveys)
        

def project_legend(bp, to_plot_passive, to_plot_surveys):
    pass






fig = plt.figure()
ax = fig.add_axes([0,0,1,1])

idd = r.ids[0]
ud = r.data[idd]

user_plot(ax, ud, to_plot_passive, to_plot_surveys,
              zero_at = 0, palette = paired_palette)

labels = ['a', 'b', 'c']


def project_plot(bp,                  
                 user_ids,
                 user_names,
                 to_plot_passive, to_plot_surveys,
                 align, palette):
    '''
    Coverage plot for a BeiweProject object.

    Args:
        bp (BeiweProject): A BeiweProject object.
        user_ids (list): List of Beiwe user ids to include.
        user_names (OrderedDict):  Keys are Beiwe user ids, values are user names.
        to_plot_passive (list): List of passive data streams to plot.
        to_plot_surveys (OrderedDict):
            Which survey data to plot.
            Keys are survey data types (e.g. 'survey_timings').
            Values are lists of survey ids.
        align (str):
            If 'absolute', plots true timestamps.
            If 'relative', zero for each user is the user's first observation.
        palette (seaborn.palettes._ColorPalette):  Palette to use.

    Returns:
        None
    '''    
    
    
    # plot each user's coverage
    for i in range(len(user_ids)):
        ax = plot_axes[i]
        ud = bp.data[i]
        user_plot(ax, ud, align, to_plot_passive, to_plot_surveys, palette)


def user_plot(ax, ud, align, to_plot_passive, to_plot_surveys, palette):
    '''
    Coverage plot for a UserData object.

    Args:
        ax (subplots.AxesSubplot):  Where to plot the timestamps.
        ud (UserData): Registry of raw user data.
        align (str):
            If 'absolute', plots true timestamps.
            If 'relative', zero is first observation (ud.first).
        to_plot_passive (list): List of passive data streams to plot.
        to_plot_surveys (OrderedDict):
            Which survey data to plot.
            Keys are survey data types (e.g. 'survey_timings').
            Values are lists of survey ids.
        palette (seaborn.palettes._ColorPalette):  Palette to use.

    Returns:
        None
    '''    
    # make filepath dictionary
    tsd = OrderedDict()
    for p in to_plot_passive:
        try:
            tsd[p] = ud.passive[p]['files']
        except:
            tsd[p] = []
    for st in to_plot_surveys:
        for sid in to_plot_surveys[st]:
            try:
                tsd[st + '_' + sid] = ud.surveys[st]['ids'][sid]['files']
            except:
                tsd[st + '_' + sid] = []
    # convert to timestamps
    for k in tsd:
        tsd[k] = [to_timestamp(os.path.basename(p).split('.')[0], from_format = filename_time_format) for p in tsd[k]]
    # get zero
    if align == 'relative':
        zero_at = to_timestamp(ud.first, from_format = filename_time_format)
    elif align == 'absolute':
        zero_at = 0
    # plot timestamps
    plot_timestamps(ax, timestamp_dictionary = tsd,
                    zero_at = zero_at, palette = palette)













    
# On rare occasions there may be a tracking survey folder called "None."
# May occur for a deleted survey?
    
    
    


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
