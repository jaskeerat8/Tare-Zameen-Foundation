#Importing Libraries
import pandas as pd
import smtplib
import io, os
import base64
import requests
import time
import s3fs
import boto3, json
from datetime import datetime, timedelta, date
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def lambda_handler(event, context):
    
    print("Running on Day:", str(datetime.now().strftime("%d-%m-%Y")))
    day = (datetime.now()-timedelta(days = 4)).strftime("%d-%m-%Y")
    print("Sending for Day:", str(day))

    
    boto3_session = boto3.Session(region_name = "us-east-1")
    s3 = boto3_session.resource('s3')
    lambda_client = boto3_session.client('lambda')
    
    #Reading the Secrets
    secretsmanager = boto3_session.client("secretsmanager")
    secretsmanager_response = json.loads( secretsmanager.get_secret_value(SecretId = "email_2023")['SecretString'] )
    print(secretsmanager_response)
    
    
    #Reading the Data
    df = pd.read_excel(secretsmanager_response["drive_link"])
    df = df[df["date"] == day]
    df.reset_index(drop = True, inplace = True)
    
    print(df.head(2))
    print(df.tail(2))
    
    
    #Trigger "reapply_send_mail" lambda
    if(len(df) > 0):
        print("Students Found Today")
        for i, row in enumerate(df.iterrows()):
            lambda_payload = {"name" : df["name"][i], "email" : df["email"][i]}
            print("Calling the send mail with information:", str(lambda_payload))
            lambda_client.invoke(FunctionName = 'reapply_send_mail', InvocationType = 'Event', Payload = json.dumps(lambda_payload))
            time.sleep(0.5)
    else:
        print("No students Today")
    
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
