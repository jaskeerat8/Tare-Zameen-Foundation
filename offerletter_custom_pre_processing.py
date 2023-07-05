#Importing Libraries
import pandas as pd
import smtplib
import io, os
import base64
import requests
import time, pytz
import s3fs, boto3, json
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
    lambda_client = boto3_session.client('lambda')
    secretsmanager = boto3_session.client("secretsmanager")
    secretsmanager_response = json.loads( secretsmanager.get_secret_value(SecretId = "tzf_values")['SecretString'] )
    
    
    #Get Dates
    todays_date = str((datetime.now(pytz.timezone("Asia/Calcutta")) - timedelta(days = 1)).date())
    print("Sending offer letters for Date: " + todays_date)
    
    
    #Read Data from Google Drive
    link = secretsmanager_response["offerletter_custom_link"]
    df = pd.read_excel(link, sheet_name = "offer letter")
    
    df.columns = [x.lower() for x in df.columns]
    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.date
    df["timestamp"] = df["timestamp"].astype("str")
    
    df = df[df["timestamp"] ==  todays_date]
    df = df.reset_index(drop=True)
    
    
    #Trigger "offerletter_send_mail" lambda
    print("\nSending Offer Letter to: ")
    print(df[["name", "id", "email id", "internship duration in month"]].to_string(col_space = 35, index = False))
    
    
    if(len(df) > 0):
        print("New Student Responses Found")
        for i in range(len(df)):
            lambda_payload = {"name" : df["name"][i], "email" : df["email id"][i], "id" : df["id"][i], "duration" : str(int(df["internship duration in month"][i])) + " month"}
            print(lambda_payload)
            lambda_client.invoke(FunctionName = 'offerletter_send_mail', InvocationType = 'Event', Payload = json.dumps(lambda_payload))
            time.sleep(4)
    else:
        print("No New Student Responses Found")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Process Complete')
    }
