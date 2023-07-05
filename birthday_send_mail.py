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
    s3_client = boto3_session.client("s3")
    
    secretsmanager = boto3_session.client("secretsmanager")
    secretsmanager_response = json.loads( secretsmanager.get_secret_value(SecretId = "tzf_values")['SecretString'] )
    sender = secretsmanager_response["sender"]
    password = secretsmanager_response["password"]
    
    
    #Reading the Event
    name = event["name"]
    email = event["email"]
    print(f"Sending the Birthday mail to {name} on mail id: {email}")
    
    
    #Reading Input from s3 Locations
    raw_folder = "s3://tarezameenservices/birthday/raw/"
    modified_image_path = "s3://tarezameenservices/birthday/processed/"
    
    html_file = "html2022.html"
    base_image = "body.jpg"
    text_font = "ArialCEBold.ttf"
    
    bucket_name = raw_folder.split("/")[2]
    bucket = s3.Bucket(bucket_name)
    file_path = "/".join(raw_folder.split("/")[3:])
    processed_image_key = "/".join(modified_image_path.split("/")[3:]) + email.replace('@', '.') + ".jpg"
    print(f"Stroring the processed card to bucket '{bucket_name}' with key {processed_image_key}")
    
    
    #Reading Mail body
    html = bucket.Object(file_path + html_file).get()
    html_data = html['Body'].read().decode()
    
    
    #Reading Font file
    font_file = bucket.Object(file_path + text_font).get()
    font_stream = font_file['Body']
    
    
    #Reading base card
    image = bucket.Object(file_path + base_image).get()
    image_stream = image['Body']
    
    
    #Putting New card in s3
    img = Image.open(image_stream)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_stream, size=75)
    
    card_name = name.split(" ")
    if(len(card_name) > 1):
        card_name = " ".join([card_name[0], card_name[-1]]).title()
    else:
        card_name = card_name[0].title()
    
    color = "rgb(255,255,255)"
    w, h = draw.textsize(card_name, font=font)
    draw.text(((1100-w)/2, 560), card_name, fill=color, font=font)
    
    in_mem_file = io.BytesIO()
    img.save(in_mem_file, format=img.format)
    in_mem_file.seek(0)
    s3_client.upload_fileobj(in_mem_file, bucket_name, processed_image_key, ExtraArgs = {'ACL': 'bucket-owner-full-control'})
    
    
    #sending mail
    s3_url = f"https://{bucket_name}.s3.amazonaws.com/{processed_image_key}"
    print(s3_url)
    
    try:
        message = MIMEMultipart()
        message["From"] = sender
        message["Subject"] = f"Hey {name.title()}, It's your birthday!! ..."
        message["To"] = email
        message.attach(MIMEText(html_data.format(s3_url), "html"))

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
        'body': json.dumps('Hello from Lambda!')
    }
