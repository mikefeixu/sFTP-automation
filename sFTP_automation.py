#!/usr/bin/env python2
"""
Created on Fri Aug  2 11:58:47 2019

@author: fei.xu
"""

#### ----
# Given quote number, get or create sFTP account and upload data. 
#### ----

import os
import glob
import argparse
import json
import re
import send_email
import pandas as pd
import cgitb
import sys
import codecs
import random
import string
import MySQLdb
import subprocess
import sjm_job_writer
import glob
import get_project_folder
import logging
import commands
import time

scriptsdir = os.path.dirname(os.path.realpath(__file__))
scriptsdir = os.path.join(scriptsdir, '')
config_file = scriptsdir+"config.json"

with open(config_file) as json_data_file:
    config_data = json.load(json_data_file)


def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def usage():
    argp = argparse.ArgumentParser(description='Automate data upload to customer sFTP account', formatter_class=argparse.RawTextHelpFormatter)
    argp.add_argument('-quote_number', dest='quote_number', default='none', help='= Project quote number', metavar='')
    argp.add_argument('-customer_email', dest='customer_email', default='none', help='= Customer email', metavar='')
    argp.add_argument('-folder_to_upload', dest='folder_to_upload', default='none', help='= Folder to be uploaded', metavar='')
    argp.add_argument('-pe', dest='pe', default='none', help='= parallel environment', metavar='')
    argp.add_argument('-send_email', dest='send_email', type=str2bool, default=False, help='= Whether to send email to customer', metavar='')
    args = argp.parse_args()

    #Upload data and send out email notification on complete.
    if args.quote_number or (args.customer_email and args.folder_to_upload):
        upload(args.quote_number, args.customer_email, args.folder_to_upload, args.pe, args.send_email)
    if args.send_email:
        print("Function is closed for now")

# Pipeline Log messages
def sFTP_upload_log(msg, log_folder):
    msg=str(msg)
    logfile=log_folder+"sFTP_auto_upload.log"
    print (msg)
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    if os.path.exists(logfile)==True:
        logging.basicConfig(filename=logfile, level=logging.INFO, filemode='a', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    else:
        logging.basicConfig(filename=logfile, level=logging.INFO, filemode='w', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    logging.info(msg)
    #change permission
    chmod_cmd="chmod 666 "+logfile
    os.system(chmod_cmd)


#Execute sql script query and return the results
def run_db(query, database=config_data['sFTP_db']):
    print ('Run query: '+query)
    host = config_data['host']
    user = config_data['user']
    passwd = config_data['password']

    # Connect to DB
    db = MySQLdb.connect(host=host,
                         user=user,
                         passwd=passwd,
                         db=database)
    cursor = db.cursor()
    cursor.execute(query)
    # Commit your changes in the database
    db.commit()
    numrows = cursor.rowcount
    output_rows = []
    # Get and display one row at a time
    for x in range(0, numrows):
        row = cursor.fetchone()
        output_rows.append(row)
    # Close the connection
    db.close()
    return output_rows


#Generate a random string of letters and digits
def randomStringDigits(stringLength=20):
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))

#Get customer email from smartsheet_info.txt
def get_email_from_smartsheet(project_folder):
    log_folder = project_folder
    smartsheet_info = os.path.join(project_folder,"reports","rawdata","smartsheet_info.txt")
    if not os.path.exists(smartsheet_info):
        print (smartsheet_info)
        log_msg = "smartsheet_info.txt not found, please provide customer email by using argument -customer_email."
        sFTP_upload_log(log_msg, log_folder)
        sys.exit(log_msg)
    df_smartsheet = pd.read_table(smartsheet_info, names=["columnID","columnName","value"], header=None)
    customer_email = df_smartsheet.loc[df_smartsheet["columnName"] == 'Client Contact E-Mail',"value"].to_string(index=False)
    if not re.match(r"^.*@.*$", customer_email):
        log_msg = "Customer email not found, please provide customer email by using argument -customer_email."
        sFTP_upload_log(log_msg, log_folder)
        sys.exit(log_msg)
    log_msg = "Retrieved customer email from smartsheet_info.txt "+customer_email
    sFTP_upload_log(log_msg, log_folder)
    return customer_email


#Get customer email from project_detail.csv
def get_email_from_project_detail(project_folder):
    log_folder = project_folder
    project_detail = os.path.join(project_folder,"reports","rawdata","project_detail.csv")
    if os.path.exists(project_detail):
        df_labUI = pd.read_csv(project_detail, header=0).fillna('')
        customer_email = df_labUI["Customer Email"][0]
        if not re.match(r"^.*@.*$", customer_email):
            customer_email = df_labUI["CustomerName"][0]
    log_msg = "Retrieved customer email from project_detail.csv "+customer_email
    sFTP_upload_log(log_msg, log_folder)
    return customer_email


#Get unique username by the email and full name provided in the metadata which was pulled from the smartsheet with quote number.
def get_username(quote_number, customer_email):
    log_folder = os.getcwd()+'/'
    if quote_number != 'none':
        project_folder = get_project_folder.get_project_folder(quote_number)
        log_folder = project_folder
        if customer_email == 'none':
            project_detail = os.path.join(project_folder,"reports","rawdata","project_detail.csv")
            if os.path.exists(project_detail):
                customer_email = get_email_from_project_detail(project_folder)
                if not re.match(r"^.*@.*$", customer_email):
                    customer_email = get_email_from_smartsheet(project_folder)
            else:
                customer_email = get_email_from_smartsheet(project_folder)

    if customer_email != 'none' and not re.match(r"^.*@.*$", customer_email):
        log_msg = "Customer email is not valid."
        sFTP_upload_log(log_msg, log_folder)
        sys.exit(log_msg)

    customer_email = customer_email.lower()
    username = "_".join(customer_email.split(".")).lower()
    username = username.replace('@', '_')

    #Remove the surfix in the username:
    username = re.sub(r"_com$|_net$|_gov$|_edu$|_de$|_uk$|_ac_uk$|_co_uk$|_ch$|_fr$_es$|_org$", "", username)
    username = username[:32]
    log_msg = "Email address transformed to username: "+username
    sFTP_upload_log(log_msg, log_folder)

    #Query db to get the record with given username
    query_select = "SELECT * FROM `SFTP_Automation` where Email = '"+customer_email+"'"
    sFTP_upload_log(query_select, log_folder)
    #print(query_select)
    output_rows=run_db(query_select, config_data['sFTP_db'])
    sFTP_upload_log(output_rows, log_folder)
    #print(output_rows)
    if len(output_rows) > 0:
        password = output_rows[0][2]
        log_msg = "Retrieved password: "+password
        sFTP_upload_log(log_msg, log_folder)
        get_sFTP_account(username, password, log_folder)
    else:
        password = randomStringDigits(20)
        log_msg = "Generated password: "+password
        sFTP_upload_log(log_msg, log_folder)
        
        get_sFTP_account(username, password, log_folder)
        query_insert = "INSERT INTO SFTP_Automation (ID, Username, Password, Email, Institute, Notes) VALUES (NULL, '"+username+"', '"+password+"', '"+customer_email+"', 'Institute', 'Notes')"
        sFTP_upload_log(query_insert, log_folder)
        #print(query_insert)
        run_db(query_insert, config_data['sFTP_db'])

    log_msg = "\nUsing this username and password: "+username+" "+password+"\n"
    sFTP_upload_log(log_msg, log_folder)
    return(username, password)

#Get or create user sFTP account if not exist
def get_sFTP_account(username, password, log_folder):
    sFTP_account_cmd = config_data['python3']+ " " + config_data['sFTP_script'] + " " + username + " " +password
    log_msg = "Create sFTP account command: "+sFTP_account_cmd
    sFTP_upload_log(log_msg, log_folder)

    exit_status = 1
    try_time = 1
    while exit_status != 0:
        exit_status = os.system(sFTP_account_cmd)
        if exit_status != 0:
            log_msg = "Attempted to create sFTP acount "+str(try_time)+" time. Will retry in 5 seconds..."
            sFTP_upload_log(log_msg, log_folder)
            time.sleep(5)
            try_time += 1
        if try_time >= 5:
            sys.exit("Failed to create sFTP account, please re-run the program at a later time or contact Fei for further assistance.")

#Uploade data to sFTP account and return the status
def upload(quote_number, customer_email, folder_to_upload, pe, send_email):
    log_folder = os.getcwd()+'/'
    (username, password) = get_username(quote_number, customer_email)
    if len(username) < 1 or len(password) < 1:
        log_msg = "Failed to retrieve or create user sFTP account info. Please contact Fei for assistance."
        sFTP_upload_log(log_msg, log_folder)
        sys.exit(log_msg)

    if quote_number != 'none':
        project_folder = get_project_folder.get_project_folder(quote_number)
        log_folder = project_folder

    #Determine which folder to upload.
    if folder_to_upload == 'none':
        sFTP_folder = quote_number
        deliverables = project_folder + "deliverables"
        if not os.path.exists(deliverables):
            deliverables = project_folder + "deliverables_temp"
    else:
        if not os.path.exists(folder_to_upload):
            log_msg = "The user-provided path: "+folder_to_upload+" does not exist."
            sFTP_upload_log(log_msg, log_folder)
            sys.exit(log_msg)
        deliverables = folder_to_upload
        sFTP_folder = os.path.basename(deliverables)
        if quote_number != 'none':
            sFTP_folder = quote_number+'/'+sFTP_folder
        print(sFTP_folder)
    log_msg = "Folder to be uploaded is: "+deliverables+"\n"
    sFTP_upload_log(log_msg, log_folder)

    #Upload with aws, if pe is provided, it will submit the upload job to the grid
    log_msg = "Start to upload data:"
    sFTP_upload_log(log_msg, log_folder)
    
    upload_cmd = config_data['aws']+" s3 sync "+deliverables+" "+config_data['aws_s3_server']+username+'/'+sFTP_folder
    log_msg = "Upload command: "+upload_cmd+"\n"
    sFTP_upload_log(log_msg, log_folder)
    
    validate_result_cmd = config_data['aws']+" s3 ls --recursive --human-readable --summarize "+config_data['aws_s3_server']+username+'/'+sFTP_folder
    log_msg = "Validate uploaded files command: "+validate_result_cmd+"\n"
    sFTP_upload_log(log_msg, log_folder)
    
    upload_cmd = upload_cmd+";\n"+validate_result_cmd

    #Handle grid environment arguement.
    if pe == 'none':
        if config_data['gridnode'] in commands.getstatusoutput("hostname")[1]:
            log_msg = "Please do not run upload command directly on "+config_data['gridnode']+". It is recommended to use "+config_data['uploadnode']+" if you are not submitting upload jobs to grid."
            sFTP_upload_log(log_msg, log_folder)
            sys.exit("Upload process was terminated.")
        os.system(upload_cmd)
    else:
        log_msg = "Submit upload job to grid: "+pe
        sFTP_upload_log(log_msg, log_folder)
        if pe not in ['ddn', 'vip', 'fat']:
            sys.exit("pe should be one of 'ddn', 'vip', or 'fat'.")
        hexID_cmd = 'date +%s |xargs printf "%x"'
        hexID = subprocess.check_output(hexID_cmd, shell=True, universal_newlines=True)
        if quote_number == 'none':
            working_folder = os.getcwd()+'/'
        else:
            working_folder = project_folder

        sjm_log_folder = log_folder+'log'
        if not os.path.exists(sjm_log_folder):
            os.makedirs(sjm_log_folder)

        sjmFile = working_folder+'upload.'+str(hexID)+'.sjm'
        with open(sjmFile, "a") as f:
            f.writelines('log_dir '+log_folder+'log\n')
        
        sjm_job_writer.sjm_job_writer(sjmFile=sjmFile, jobName='upload'+hexID, pe=pe, slots='1', cmd=upload_cmd, newFile=False, local=False)
        exit_status = os.system(config_data["sjmbin"]+"sjm "+sjmFile)
        if exit_status != 0:
            sys.exit("Please make sure you are able to submit jobs to grid. If it doesn't work, please contact your HPC administrator.")
        log_msg = "Job submitted to the grid. Please find the upload progress and result in project log folder."
        sFTP_upload_log(log_msg, log_folder)

    if quote_number != 'none':
        email_template_cmd = config_data['python3']+' '+scriptsdir+'generate_email.py -quote_number '+quote_number+' -username '+username+' -password '+password
        os.system(email_template_cmd)
        print (email_template_cmd)
        log_msg = "Generated email template in the project folder."
        sFTP_upload_log(log_msg, log_folder)
        send_delivery_email(quote_number)


#Send delivery email to customer after review the email template.html in the project folder
def send_delivery_email(quote_number):
    project_folder = get_project_folder.get_project_folder(quote_number)
    email_template = project_folder+"/email_template.html"

    subject = quote_number+' delivered'

    f = codecs.open(email_template, 'r')
    message = f.read()
    
    download_guide = scriptsdir+"Data_Download_Guide.pdf"
    rawdata_report = project_folder+config_data['reports']+quote_number+"Data_Report.html"
    if os.path.exists(download_guide) and os.path.exists(rawdata_report):
        files = download_guide+","+rawdata_report
        send_email.send_email(subject=subject, message=message, files=files, email_from=config_data["email_from"], email_to=config_data["email_to"])


if __name__ == "__main__":
    try:
        usage()
    except IOError:
        send_email.send_email(subject="IOError on sFTP Upload", message=cgitb.html(sys.exc_info()), files=None, email_from=config_data["email_from"], email_to=config_data["email_to"])
    except ValueError:
        send_email.send_email(subject='ValueError on sFTP Upload', message=cgitb.html(sys.exc_info()), files=None, email_from=config_data["email_from"], email_to=config_data["email_to"])
