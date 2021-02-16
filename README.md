# sFTP-automation
A tool that automates the sFTP account generation and data delivery


# sFTP automation User Guide


## Table of Contents


- [sFTP automation User Guide](#sftp-automation-user-guide)
  - [Table of Contents](#table-of-contents)
    - [Running the Pipeline](#running-the-pipeline)
    - [Running sFTP script without pipeline:](#running-sftp-script-without-pipeline)
  - [Report issues or feature requests](#report-issues-or-feature-requests)


### Running the Pipeline
- Pipeline use cases:
  - Case one: Run with a quote number. Quote is required, other arguments are optional. If pe is used, the job will be submitted to the grid. And the job logs can be found in the project root folder.
```
python3 sFTP_automation.py -quote_number [quote number] -customer_email <customer email> -folder_to_upload <folder to be uploaded> -pe <nodetypes>
```
  - Case two: Run without a quote number. Customer_email and folder_to_upload are both required. Other arguments are optional. If pe is used, the job will be submitted to the grid. And the job logs can be found in the current working folder.
```
python3 sFTP_automation.py -customer_email [customer email] -folder_to_upload [folder to be uploaded] -pe <vip, fat, or ddn>
```

### Running sFTP script without pipeline
- This script allows you to either create a new user and password or reset an existing user password in our new SFTP endpoint (server). The new SFTP URL is “sftp.xxxxxx.com”. After the sftp user is created, you can upload the data either using SFTP client or aws s3 cli to their folder.
  - To create a new SFTP user or reset an existing user password run the script:
```
python3 s3-sftp-user.py username password
# username = SFTP user name
# password = SFTP user password
```
  - To upload data to user’s folder via aws cli.
```
aws sync source_data_path s3://<your s3 bucket>/username/
# or
aws cp source_data_path s3://<your s3 bucket>/username/
# Add --recursive for copying a folder
```

### Report issues or feature requests
- Open git repository link: https://github.com/mikefeixu/sFTP-automation/issues
- Click "New Issue"
- Enter the details and submit.
