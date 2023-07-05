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
from PIL import Image, ImageDraw, ImageFont, ImageOps

def lambda_handler(event, context):
    
    #Making s3 Resource
    boto3_session = boto3.Session(region_name = "us-east-1")
    s3 = boto3_session.resource('s3')
    lambda_client = boto3_session.client('lambda')
    
    secretsmanager = boto3_session.client("secretsmanager")
    secretsmanager_response = json.loads( secretsmanager.get_secret_value(SecretId = "tzf_values")['SecretString'] )
    
    #Getting Todays Birthday Data
    birthday_email_list = "s3://tarezameenservices/birthday/raw/Birthday_Email_List.xlsx"
    today = (datetime.now()-timedelta(days = 0)).strftime("%d-%m")
    
    df = pd.read_excel(birthday_email_list)
    df['Name'] = df['Name'].str.strip()
    df['Name'] = df['Name'].str.lower()
    df['Email'] = df['Email'].str.strip()
    df['Email'] = df['Email'].str.lower()
    df.dropna(subset=["date of Birth"], inplace=True)
    df["date of Birth"]= pd.to_datetime(df["date of Birth"], format='%Y-%m-%d')
    df = df[df["date of Birth"].dt.strftime("%d-%m") == today]
    df = df.drop_duplicates(subset = ["Email"])
    df = df.reset_index(drop=True)
    print(df)
    
    #Trigger "birthday_send_mail" lambda
    if(len(df) > 0):
        print("Birthdays Found Today")
        for i in range(len(df)):
            lambda_payload = {"name" : df["Name"][i], "email" : df["Email"][i]}
            lambda_client.invoke(FunctionName = 'birthday_send_mail', InvocationType = 'Event', Payload = json.dumps(lambda_payload))
            time.sleep(5)
    else:
        print("No Birthdays Today")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Process Compl')
    }
