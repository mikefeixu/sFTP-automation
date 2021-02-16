#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 19 14:09:17 2019

@author: fei.xu
"""

#### ----
# Send email. 
#### ----

import os
import glob
import argparse
import json
import re
import time
import smtplib
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.utils import COMMASPACE, formatdate

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
    argp = argparse.ArgumentParser(description='Pacbio workflow control', formatter_class=argparse.RawTextHelpFormatter)
    argp.add_argument('-subject', dest='subject', help='= email subject', metavar='')
    argp.add_argument('-message', dest='message', help='= email message', metavar='')
    argp.add_argument('-files', dest='files', default=None, help='= email attachments', metavar='')
    argp.add_argument('-email_from', dest='email_from', default=config_data['email_from'], help='= sender', metavar='')
    argp.add_argument('-email_to', dest='email_to', default=config_data['email_to'], help='= receipent', metavar='')
    args = argp.parse_args()

    send_email(args.subject, args.message, args.files, args.email_from, args.email_to)


def send_email(subject, message, files, email_from, email_to):
    msg1 = MIMEText(message,'html')
    mail = MIMEMultipart("test")
    mail['Subject'] = subject
    mail['From'] = email_from
    mail['To'] = ", ".join(email_to.split(","))
    mail.attach(msg1)

    if re.search(r'\w', message):
        try:
            s = smtplib.SMTP(config_data['SMTP'], 25)
        except:
            time.sleep(3)
            s = smtplib.SMTP(config_data['SMTP'], 25)
        #add attachments if available
        if files!=None and re.search(r'\w+', files):
            files=files.split(",")
            for f in files or []:
                print ("Attached file: " + f)
                with open(f, "rb") as fil:
                    part = MIMEApplication(
                        fil.read(),
                        Name=os.path.basename(f)
                    )
                fil.close()
                # After the file is closed
                part['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(f)
                mail.attach(part)
        s.sendmail(email_from, email_to, mail.as_string())
        s.quit()


if __name__ == "__main__":

    usage()
