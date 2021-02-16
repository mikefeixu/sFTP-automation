#!/usr/bin/env python3

import boto3
import sys
import os
import hashlib
import binascii
from boto3.dynamodb.conditions import Key

sftpusername=sys.argv[1]
sftppassword=sys.argv[2]
dynamodb=boto3.resource('dynamodb')
table=dynamodb.Table('SFTPUsers')

def hash_password(sftppassword):
#    """Hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', sftppassword.encode('utf-8'), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')

#Qury the user name from database
response=table.query(
    KeyConditionExpression=Key('username').eq(sftpusername)
)
items=response['Items']

# If the user exist, update the user with password that is provided
if (sftpusername in str(items)) == True:
    table.update_item(
        Key={
            'username': sftpusername
        },
        UpdateExpression='SET password = :val1',
        ExpressionAttributeValues={
            ':val1': hash_password(sftppassword)
        }
    )
# If the user doesn't exist, create the new user account
else:
    table.put_item(
        Item={
        'username': sftpusername,
        'password': hash_password(sftppassword)
    }
)