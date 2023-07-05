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
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image


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
    name = event["name"].title()
    email = event["email"]
    id = event["id"] 
    duration = event["duration"].title()
    print(f"Sending the Internship Mail to {name} with intern id {id} on mail: {email} for a duration of {duration}")
    
    
    #Getting Input
    tzf_header = "https://tarezameenservices.s3.amazonaws.com/offer_letter/raw/header.png"
    tzf_sign = "https://tarezameenservices.s3.amazonaws.com/offer_letter/raw/sign.jpg"
    html_file = "s3://tarezameenservices/offer_letter/raw/offerhtml.html"
    
    new_pdf_path = "s3://tarezameenservices/offer_letter/processed/"
    bucket = new_pdf_path.split("/")[2]
    pdf_key = "/".join(new_pdf_path.split("/")[3:]) + email.replace("@", ".") + ".pdf"
    print(f"Putting the file in bucket '{bucket}' here '{pdf_key}'")
    
    
    #Getting Date with superscript
    if(date.today().day % 10 == 1):
        superscript = "st"
    elif(date.today().day % 10 == 2):
        superscript = "nd"
    elif(date.today().day % 10 == 3):
        superscript = "rd"
    else:
        superscript = "th"
    todays_date = date.today().strftime(f'%d<sup>{superscript}</sup> %B %Y')
    
    
    
    #Making PDF
    style = getSampleStyleSheet()
    justify = ParagraphStyle(name='justify', alignment=TA_JUSTIFY, fontName="Helvetica", fontSize=11, leading=16)
    center_bold = ParagraphStyle(name='center_bold', alignment=TA_CENTER, fontName="Helvetica-Bold", fontSize=14)
    right_bold = ParagraphStyle(name='right_bold', alignment=TA_RIGHT, fontName="Helvetica-Bold", fontSize=12)
    left_bold = ParagraphStyle(name='left_bold', alignment=TA_LEFT, fontName="Helvetica-Bold", fontSize=13)
    
    
    stream = io.BytesIO()
    doc = SimpleDocTemplate(stream, pagesize = A4, bottomMargin=0, topMargin = -7, rightMargin=40, leftMargin=40)
    a4_width, a4_height = A4
    Story=[]
    
    letter_head = Image(tzf_header, a4_width, 180)
    Story.append(letter_head)
    Story.append(Spacer(a4_width, 10))
    
    Story.append(Paragraph("<u>Internship Offer Letter</u>", center_bold))
    Story.append(Spacer(a4_width, 20))
    
    Story.append(Paragraph(f"Intern ID- {id}", right_bold))
    Story.append(Spacer(a4_width, 10))
    
    Story.append(Paragraph(todays_date, right_bold))
    Story.append(Spacer(a4_width, 20))
    
    Story.append(Paragraph(name, left_bold))
    Story.append(Spacer(a4_width, 20))
    
    Story.append(Paragraph(f"SUB: Offer of Internship {str(date.today().year)} position - Reg", ParagraphStyle(name='left_bold', alignment=TA_LEFT, fontName="Helvetica-Bold", fontSize=12)))
    Story.append(Spacer(a4_width, 20))
    
    first_para = f"""We are pleased to offer intern a position of Fundraising for a fixed tenure period of <b>{duration}</b> 
    for a minimum of 7 hours Internship service per week. Intern Internship period starts from <b>{todays_date}</b>. This is an 
    Academic Virtual Internship Position, however Intern will be reimbursed any pre-approved expenses, incurred by intern on
    behalf of the organization."""
    Story.append(Paragraph(first_para, justify))
    Story.append(Spacer(a4_width, 10))
    
    second_para = """As Intern are aware, we seek to make a positive change in the lives of underprivileged children, women and
    Divyangs, as also encourage like-minded people to contribute to it. After reviewing intern qualifications, we feel
    intern would be an appropriate person to assist our organization with this endeavor. Intern will be reporting to the
    Team Leader and will seek his / her approval/advise in critical matters as and when required."""
    Story.append(Paragraph(second_para, justify))
    Story.append(Spacer(a4_width, 10))
    
    third_para = """As part of this internship, every intern is expected to actively participate in our virtual fund-raising 
    initiatives and help our Organization raise funds for the various planned social causes as a fundraising intern."""
    Story.append(Paragraph(third_para, justify))
    Story.append(Spacer(a4_width, 10))
    
    fourth_para = """<b>Fix Stipend of Rs 1000</b> shall be awarded by <b>cheque/Amazon gift voucher</b> to intern only if 
    intern achieve the assigned target successfully, additionally <b>10% of incentives</b> shall be given based upon the 
    performance. We welcome intern to Tare Zameen Foundation and our whole team is looking forward to working with intern as
    intern share intern skills diligently to meet the needs of the organization."""
    Story.append(Paragraph(fourth_para, justify))
    Story.append(Spacer(a4_width, 10))
    
    fifth_para = """Please reply on the mail or share a signed duplicate copy of this letter as a token of acceptance to this offer."""
    Story.append(Paragraph(fifth_para, justify))
    Story.append(Spacer(a4_width, 10))
    
    sixth_para = """<b>Note:</b> This is a letter of intent for association which does not constitute as the completion 
    certificate"""
    Story.append(Paragraph(sixth_para, justify))
    Story.append(Spacer(a4_width, 10))
    
    signing_out = """Yours Sincerely,<br />
    For Tare Zameen Foundation,"""
    Story.append(Paragraph(signing_out, ParagraphStyle(name='justify', alignment=TA_JUSTIFY, fontName="Helvetica", fontSize=12, leading=16)))
    
    sign = Image(tzf_sign, 200, 100, hAlign="LEFT")
    Story.append(sign)
    
    doc.build(Story)
    s3.Object(bucket, pdf_key).put(Body=stream.getvalue())
    
    
    time.sleep(3)
    ##Reading Mail body
    html = s3.Bucket(html_file.split("/")[2]).Object( "/".join(html_file.split("/")[3:]) ).get()
    html_data = html['Body'].read().decode()
    
    
    #sending mail
    try:
        message = MIMEMultipart()
        message["From"] = sender
        message["Subject"] = "Offer Letter"
        message["To"] = email
        message.attach(MIMEText(html_data.format(name), "html"))
        
        try:
            pdf_object = s3.Bucket(bucket).Object( pdf_key ).get()
            pdf_body = pdf_object['Body'].read()
            
            attach = MIMEApplication(pdf_body, _subtype="pdf")
            attach.add_header("Content-Disposition", "attachment", filename = "Offer Letter.pdf")
            message.attach(attach)
        except Exception as e:
            print("Failed to attach offer letter pdf with error: " + str(e))
        
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
