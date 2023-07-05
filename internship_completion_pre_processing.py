#Importing Libraries
import pandas as pd
import smtplib
import io, os
import base64, re
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

def digit_month(x):
    return re.findall(r'\d+[.]*\d*', x)[0]
    

def lambda_handler(event, context):
    
    #Making s3 Resource
    boto3_session = boto3.Session(region_name = "us-east-1")
    lambda_client = boto3_session.client('lambda')
    
    secretsmanager = boto3_session.client("secretsmanager")
    secretsmanager_response = json.loads( secretsmanager.get_secret_value(SecretId = "tzf_values")['SecretString'] )
    
    
    #Get Dates
    yesterdays_date = ( datetime.now(pytz.timezone("Asia/Calcutta")) - timedelta(days = 1) ).date().strftime("%Y-%m-%d")
    print("Sending Data for Date: " + str(yesterdays_date))
    
    
    #Read Data from Google Drive
    link = secretsmanager_response["internship_completion_link"]
    df = pd.read_excel(link, sheet_name = "certificate")
    
    df = df.apply(lambda x: x.astype(str).str.lower())
    df.columns = [x.lower() for x in df.columns]
    df = df.reset_index(drop=True)
    
    df["duration in  month"] = df["duration in  month"].apply(digit_month)
    df["duration in  month"] = df["duration in  month"].astype("float")
    df["date"] = pd.to_datetime(df["date"], format = "%Y-%m-%d")
    
    df = df[df["date"] == yesterdays_date]
    
    
    #Trigger "internship_completion_send_mail" lambda
    if(len(df) > 0):
        print("Sending student their certificates")
        for i in df.index:
            attachments = {}
            
            if(df["certificate"][i] == "yes"):
                attachments["certificate"] = 1
            else:
                attachments["certificate"] = 0
            
            if(df["lor"][i] == "yes"):
                attachments["lor"] = 1
            else:
                attachments["lor"] = 0
            
            if(df["award"][i] == "yes"):
                attachments["award"] = 1
            else:
                attachments["award"] = 0
            
            if(df["duration in  month"][i]%1 == 0.0):
                lambda_payload = {"name":df["name"][i], "duration": int(df["duration in  month"][i]), "profile":df["position"][i], "email":df["email id"][i], "id":df["interns id"][i], "attachments":attachments}
            else:
                lambda_payload = {"name":df["name"][i], "duration": float(df["duration in  month"][i]), "profile":df["position"][i], "email":df["email id"][i], "id":df["interns id"][i], "attachments":attachments}
            
            print(lambda_payload)
            lambda_client.invoke(FunctionName = 'internship_completion_send_mail', InvocationType = 'Event', Payload = json.dumps(lambda_payload))
            time.sleep(5)

    else:
        print("No student found")
    
    
    return {
        'statusCode': 200,
        'body': json.dumps('Certificates Sent')
    }
