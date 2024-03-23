# Omnivore Backup Utility

## Prerequisites:

### GraphQL access library

`pip install "gql[all]"`

### API Key

You have to provide the Omnivore API access token in the TOKEN environment variable:

Windows:

`set TOKEN=a56780c3-78e6-4c29-9f34-d865834ff6b8`

Linux/Mac:

`export TOKEN='a56780c3-78e6-4c29-9f34-d865834ff6b8'`

## Usage

`python backup.py > data.csv`

Linux/Mac users might run something like this:

`./backup.py >omnivore-$(date +"%Y%m%d").csv`
