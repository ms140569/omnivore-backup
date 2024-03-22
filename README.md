Omnivore Backup Utility

You have to provide the Omnivore API access token in the TOKEN environment variable:

export TOKEN='a56780c3-78e6-4c29-9f34-d865834ff6b8'

than run:

./backup.py >omnivore-$(date +"%Y%m%d").csv

