#!/usr/bin/env python2
"""
Created on Fri Aug 16 15:07:21 2019

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
import cgitb
import sys

scriptsdir = os.path.dirname(os.path.realpath(__file__))
scriptsdir = os.path.join(scriptsdir, '')
config_file = scriptsdir+"config.json"

with open(config_file) as json_data_file:
    config_data = json.load(json_data_file)


def usage():
    argp = argparse.ArgumentParser(description='Automate data upload to customer sFTP account', formatter_class=argparse.RawTextHelpFormatter)
    argp.add_argument('-quote_number', dest='quote_number', default='none', help='= Project quote number', metavar='')
    args = argp.parse_args()

    #Upload data and send out email notification on complete.
    if args.quote_number:
        get_project_folder(args.quote_number)

def get_project_folder(quote_number):
    query_string=quote_number.upper()
    try:
        query_string=re.sub('-', '', query_string)
        query_string=re.sub('_','', query_string)
    except:
        pass
    
    rootdir=config_data['project_base']+'*/'
    project_folder=config_data['project_base']+quote_number+'_/'
    for filename in glob.iglob(rootdir):
        subject=os.path.basename(os.path.dirname(filename)).upper()
        subject=re.sub('-', '', subject)
        subject=re.sub('_','', subject)
        if query_string==subject:
            project_folder=filename
            #print('Project folder ', project_folder)
    
    return project_folder


if __name__ == "__main__":
    try:
        usage()
    except IOError:
        send_email.send_email(subject="IOError on sFTP Upload", message=cgitb.html(sys.exc_info()), files=None, email_from=config_data["email_from"], email_to=config_data["email_to"])
    except ValueError:
        send_email.send_email(subject='ValueError on sFTP Upload', message=cgitb.html(sys.exc_info()), files=None, email_from=config_data["email_from"], email_to=config_data["email_to"])
