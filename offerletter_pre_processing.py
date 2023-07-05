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
    sns_client = boto3_session.client("sns")
    
    secretsmanager = boto3_session.client("secretsmanager")
    secretsmanager_response = json.loads( secretsmanager.get_secret_value(SecretId = "tzf_values")['SecretString'] )
    
    
    #Get Dates
    todays_date = datetime.now(pytz.timezone("Asia/Calcutta")).date()
    #todays_date = (datetime.now(pytz.timezone("Asia/Calcutta")) - timedelta(days = 1)).date()
    print(todays_date)
    todays_month = todays_date.month
    todays_year = todays_date.year
    
    
    #Read Data from Google Drive - internshala internship excel file
    link = secretsmanager_response["offerletter_link"]
    df = pd.read_excel(link, sheet_name = "college Interns")
    
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], format= '%Y-%m-%d %H:%M:%S')
    
    if(todays_month != 1):
        print("Not in January")
        #df = df[(( df["Timestamp"].dt.month == todays_month ) | (df["Timestamp"].dt.month == todays_month-1 )) & ( df["Timestamp"].dt.year == todays_year )]
        df = df[df["Timestamp"].dt.year == todays_year]
    else:
        print("In January")
        #df = df[(( df["Timestamp"].dt.month == todays_month ) & ( df["Timestamp"].dt.year == todays_year )) | ((df["Timestamp"].dt.month == 12 ) & ( df["Timestamp"].dt.year == todays_year-1 ))]
        df = df[(( df["Timestamp"].dt.month == todays_month ) & ( df["Timestamp"].dt.year == todays_year )) | ( df["Timestamp"].dt.year == todays_year-1 )]
    
    df.sort_values(['Timestamp'], ascending= True, kind = 'quicksort', inplace=True)
    df["ID"] = df["ID"].astype(str)
    df = df.reset_index(drop=True)
    for i in df[(df["Timestamp"].dt.hour == 23) & (df["Timestamp"].dt.minute >= 50)].index:
        df.iloc[i, df.columns.get_loc("Timestamp")] = df["Timestamp"][i] + timedelta(minutes = 10)
    
    
    #Send Data to get updated in sheet
    emptydf = df[df["ID"] == "nan"]
    
    for i in emptydf.index:
        
        string_month = emptydf["Timestamp"][i].strftime('%B').upper()
        string_year = str(emptydf["Timestamp"][i].strftime('%y'))
        
        if(emptydf["Timestamp"][i].month == df["Timestamp"][i-1].month):
            previous_rank = df["ID"][i-1].split(string_month)[-1]
            substitute_id = "TZF" + string_year + string_month + str( int(previous_rank) + 1 )
            df.iloc[i, df.columns.get_loc("ID")] = substitute_id
        else:
            previous_rank = 0
            substitute_id = "TZF" + string_year + string_month + str( int(previous_rank) + 1 )
            df.iloc[i, df.columns.get_loc("ID")] = substitute_id
    
    emptydf = df.iloc[list(emptydf.index), ][['ID', 'Timestamp', 'Name', 'Email id', 'Date of Birth']]
    email_message_df = emptydf.to_string(col_space = 35, index = False)
    
    try:
        send_mail = sns_client.publish( TopicArn = "arn:aws:sns:us-east-1:215101936245:Update_drive_sheet", Message = email_message_df,
        Subject = "Please update these Intern ID's in the sheet for fundraising interns")
    except Exception as e:
        print("send_mail to update values error: " + str(e))
        pass
    print(email_message_df)
    
    
    #Trigger "offerletter_send_mail" lambda
    df = df[( df["Timestamp"].dt.date == todays_date )]
    df = df.reset_index(drop=True)
    print("\nSending Offer Letter to: ")
    print(df[["Name", "ID", "Email id", "internship duration in month"]].to_string(col_space = 35, index = False))
    
    if(len(df) > 0):
        print("New Student Responses Found")
        for i in range(len(df)):
            try:
                lambda_payload = {"name" : df["Name"][i], "email" : df["Email id"][i], "id" : df["ID"][i], "duration" : str(int(df["internship duration in month"][i])) + " month"}
            except Exception as e:
                print("lambda_payload error: " + str(e))
                lambda_payload = {}
            lambda_client.invoke(FunctionName = 'offerletter_send_mail', InvocationType = 'Event', Payload = json.dumps(lambda_payload))
            time.sleep(4)
    else:
        print("No New Student Responses Found")
    
    
    return {
        'statusCode': 200,
        'body': json.dumps('Process Complete')
    }
