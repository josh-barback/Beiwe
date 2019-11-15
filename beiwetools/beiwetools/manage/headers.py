'''Headers for CSVs handled by accrep.

'''

identifiers_header = [ # column names for raw Beiwe identifiers files.
  'timestamp',    # Millisecond timestamp when these device parameters were observed.
  'UTC time',     # Human-readable UTC date-time formatted as '%Y-%m-%dT%H:%M:%S.%f'.
  'patient_id',   # Beiwe user ID.
  'MAC',
  'phone_number',
  'device_id',
  'device_os',    # 'iOS' or 'Android'. Older files may say 'iPhone OS' instead of 'iOS'.
  'os_version',
  'product',
  'brand',
  'hardware_id',
  'manufacturer',
  'model',
  'beiwe_version' # Note that iPhone identifiers have an extra unlabeled column.  
  ]               # The extra entry is appended to the 'beiwe_version' entry, separated by underscore.

user_summary_header = [
  'user_id',            # Beiwe user ID.
  'user_name',          # Other identifier for user, if any.
  'followup_begin',     # Datetime range (UTC) used when registry was created.
  'followup_end', 
  'followup_days',      # Number of days of followup.
  'first_observation',  # Datetimes (UTC) of first/last observation. 
  'last_observation', 
  'total_days',         # Number of days between first and last observations.
  'raw_file_count',     # Number of unique raw files.
  'size_MB',            # Size of all raw files on disk (megabytes).
  'n_devices',          # Number of unique devices (phones).
  'os',                 # 'iOS' or 'Android'. May be 'both' if user switched phones.
  'irregular_directories', # Number of top survey directories that contain raw data files.
  'unregistered_files',    # Number of raw data files in top survey directories.
  'study_name',         # Study name, if a configuration file is attached.
  'configuration_file', # Path to configuration file, if one is attached.
  ]

passive_summary_header = [
        
  ]

survey_summary_header = [

  ]