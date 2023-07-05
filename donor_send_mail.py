#Importing Libraries
import pandas as pd
import smtplib
import io, os
import base64
import requests
import s3fs
import time, random
import boto3, json
from datetime import datetime, timedelta, date
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from PIL import Image, ImageDraw, ImageFont, ImageOps

def lambda_handler(event, context):
    
    boto3_session = boto3.Session(region_name = "us-east-1")
    s3 = boto3_session.resource("s3")
    s3_client = boto3_session.client("s3")
    
    
    print(random.randint(1, 100))
    time.sleep(random.randint(1, 100))
    
    
    #Reading the Secrets
    secretsmanager = boto3_session.client("secretsmanager")
    secretsmanager_response = json.loads( secretsmanager.get_secret_value(SecretId = "tzf_values")["SecretString"] )
    
    sender = secretsmanager_response["hr_sender"]
    password = secretsmanager_response["hr_password"]
    s3_path = "s3://tarezameenservices/donor/"
    html_file = "donor.html"
    
    
    #Reading the Event
    name = event["name"].title()
    email = event["email"]
    print(f"Sending the Donor mail to: {name} on mail id: {email}")
    
    
    #Reading Mail body
    bucket = s3.Bucket(s3_path.split("/")[2])
    file_path = "/".join(s3_path.split("/")[3:])
    
    html = bucket.Object(file_path + html_file).get()
    html_data = html['Body'].read().decode()
    
    
    #Sending Mail
    try:
        message = MIMEMultipart()
        message["From"] = "Tare Zameen Foundation"

        message["Subject"] = f"Hey {name.title()}, Thank you for your support!!"
        message["To"] = email
        message.attach(MIMEText(html_data.format(name.title()), "html"))

        session = smtplib.SMTP("smtp.gmail.com", 587)
        session.starttls()
        session.login(sender, password)
        text = message.as_string()
        
        status = 0
        while(status == 0):
            response = session.sendmail(sender, email, text)
            if( not bool(response)):
                print("Mail Sent")
                status = 1
            else:
                time.sleep(10)
            
        session.quit()
    except Exception as e:
        print("Failed to send message with error: " + str(e))
        
    return {
        'statusCode': 200,
        'body': json.dumps("Message Sent")
    }
