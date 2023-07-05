#Importing Libraries
import pandas as pd
import smtplib
import io, os
import base64
import requests
import pytz, time
import s3fs
import boto3, json
from datetime import datetime, timedelta, date
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from PIL import Image, ImageDraw, ImageFont, ImageOps
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
import reportlab.platypus as RP
import PIL as pil


def make_lor(s3, output, tzf_header, tzf_sign, todays_date, name, email, duration, profile, ID):
    
    #Making LOR
    input_stream = io.BytesIO()
    doc = SimpleDocTemplate(input_stream, pagesize = A4, bottomMargin=0, topMargin = -7, rightMargin=60, leftMargin=60)
    a4_width, a4_height = A4
    
    #Setting Styles
    style = getSampleStyleSheet()
    center_bold = ParagraphStyle(name='center_bold', alignment=TA_CENTER, fontName="Helvetica-Bold", fontSize=20)
    justify = ParagraphStyle(name='justify', alignment=TA_JUSTIFY, fontName="Helvetica", fontSize=12, leading=14)
    right_bold = ParagraphStyle(name='right_bold', alignment=TA_RIGHT, fontName="Helvetica-Bold", fontSize=13)
    left_bold = ParagraphStyle(name='left_bold', alignment=TA_LEFT, fontName="Helvetica-Bold", fontSize=13)
    
    #Writing the flow in LOR page
    Story=[]
    
    letter_head = RP.Image(tzf_header, a4_width, 180)
    Story.append(letter_head)
    Story.append(Spacer(a4_width, 30))
    
    Story.append(Paragraph("<u>Letter of Recommendation</u>", center_bold))
    Story.append(Spacer(a4_width,60))
    
    Story.append(Paragraph(f"Date: {todays_date}", right_bold))
    Story.append(Spacer(a4_width, 40))
    
    first_para = f"""This is to certify that <b>{name}</b> has successfully completed his/her internship with 
    Tare Zameen Foundation during the period of {duration}."""
    Story.append(Paragraph(first_para, justify))
    Story.append(Spacer(a4_width, 15))
    
    second_para = f"""During the period, he/she handled <b>{profile}</b> profile, <b>assigned responsibilities he/she
    had worked on.</b>"""
    Story.append(Paragraph(second_para, justify))
    Story.append(Spacer(a4_width, 15))
    
    third_para = f"""During the course of internship, <b>{name}</b> has shown great amount of responsibility, 
    sincerity and a genuine willingness to learn and zeal to take on new assignments & 
    challenges. In particular, his/her coordination skills and communication skills are par 
    excellence and his/her attention to details is impressive."""
    Story.append(Paragraph(third_para, justify))
    Story.append(Spacer(a4_width, 40))
    
    fourth_para = """We wish him/her all the very best for his/her future."""
    Story.append(Paragraph(fourth_para, justify))
    Story.append(Spacer(a4_width, 25))
    
    signing_out = """Yours Sincerely,<br />
    For Tare Zameen Foundation,"""
    Story.append(Paragraph(signing_out, ParagraphStyle(name='justify', alignment=TA_JUSTIFY, fontName="Helvetica", fontSize=12, leading=16)))
    Story.append(Spacer(a4_width, 10))
    
    sign = RP.Image(tzf_sign, 200, 100, hAlign="LEFT")
    Story.append(sign)
    
    doc.build(Story)
    
    bucket = output.split("/")[2]
    lor_key = "/".join(output.split("/")[3:]) + f"lor/{ email.replace('@', '.lor.') }.pdf"
    print(f"Putting LOR in bucket '{bucket}' here '{lor_key}'")
    s3.Object(bucket, lor_key).put(Body = input_stream.getvalue())
    return lor_key


def make_award(s3, output, award_image, name, email, font_file):
    
    #Reading award card
    award_file = s3.Bucket( award_image.split("/")[2] ).Object( "/".join(award_image.split("/")[3:]) ).get()
    award_stream = award_file['Body']
    
    #Making Award
    img = pil.Image.open(award_stream)
    img_w, img_h = img.size
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_file.get()['Body'], size = 100)
    
    award_name = name.split(" ")
    if(len(award_name) > 1):
        award_name = " ".join([award_name[0], award_name[-1]]).upper()
    else:
        award_name = award_name[0].upper()
    
    add = 0
    for an in award_name.split(" "):
        draw_w, draw_h = draw.textsize(an, font = font)
        draw.text( ((img_w - draw_w)/2 - 10, 1555 + add), an, fill = "rgb(247, 237, 188)", font = font)
        add = add + draw_h
    
    in_mem_award = io.BytesIO()
    img.save(in_mem_award, format=img.format)
    in_mem_award.seek(0)
    
    bucket = output.split("/")[2]
    award_key = "/".join(output.split("/")[3:]) + f"award/{ email.replace('@', '.award.') }.png"
    print(f"Putting AWARD in bucket '{bucket}' here '{award_key}'")
    s3.Object(bucket, award_key).put(Body = in_mem_award.getvalue())
    return award_key


def make_certificate(s3, output, certificate_image, todays_date, name, email, duration, profile, ID, font_file):
    
    #Reading certificate image
    certificate_file = s3.Bucket( certificate_image.split("/")[2] ).Object( "/".join(certificate_image.split("/")[3:]) ).get()
    certificate_stream = certificate_file['Body']
    
    #Making Certificate Of Completion
    img = pil.Image.open(certificate_stream)
    img_w, img_h = img.size
    draw = ImageDraw.Draw(img)
    
    font = ImageFont.truetype(font_file.get()['Body'], size = 70)
    draw_w, draw_h = draw.textsize(name, font=font)
    draw.text( ( (img_w-draw_w)/2, 550 ), name, fill = "rgb(0, 0, 0)", font = font)
    
    internship_line = f"{profile} intern for a duration of {duration}."
    font = ImageFont.truetype(font_file.get()['Body'], size = 30)
    draw_w, draw_h = draw.textsize(internship_line, font=font)
    draw.text( ( (img_w-draw_w)/2, 690 ), internship_line, fill = "rgb(0, 0, 0)", font = font)
    
    certificate_date = f"Certificate Issue Date: {todays_date}"
    font = ImageFont.truetype(font_file.get()['Body'], size = 27)
    draw_w, draw_h = draw.textsize( certificate_date, font=font)
    draw.text( ( 140, 1115 ), certificate_date, fill = "rgb(0, 0, 0)", font = font)
    
    certificate_id = f"Certificate ID: {ID}"
    font = ImageFont.truetype(font_file.get()['Body'], size = 27)
    draw_w, draw_h = draw.textsize( certificate_id, font=font)
    draw.text( ( img_w-169-draw_w, 1110 ), certificate_id, fill = "rgb(0, 0, 0)", font = font)
    
    in_mem_certificate = io.BytesIO()
    img.save(in_mem_certificate, format="pdf")
    in_mem_certificate.seek(0)
    
    bucket = output.split("/")[2]
    certificate_key = "/".join(output.split("/")[3:]) + f"certificate/{ email.replace('@', '.certificate.') }.pdf"
    print(f"Putting Certificate in bucket '{bucket}' here '{certificate_key}'")
    s3.Object(bucket, certificate_key).put(Body = in_mem_certificate.getvalue())
    return certificate_key


def lambda_handler(event, context):
    
    #Making s3 Resource
    boto3_session = boto3.Session(region_name = "us-east-1")
    s3 = boto3_session.resource('s3')
    
    secretsmanager = boto3_session.client("secretsmanager")
    secretsmanager_response = json.loads( secretsmanager.get_secret_value(SecretId = "tzf_values")['SecretString'] )
    sender = secretsmanager_response["sender"]
    password = secretsmanager_response["password"]
    
    #Reading the Event
    
    todays_date = datetime.now(pytz.timezone("Asia/Calcutta")).date().strftime('%d %B %Y')
    
    name = event["name"].strip().title()
    email = event["email"]
    
    duration = event["duration"] 
    if(duration == 1):
        duration = str(duration) + " month"
    else:
        duration = str(duration) + " months"
    print("Duration is: " + duration)
    duration = duration.strip()
    
    profile = event["profile"].strip().title()
    ID = event["id"].strip().upper()
    
    attachments = event["attachments"]
    print(f"Sending the Internship Mail to {name} for profile {profile} on mail: {email} for a duration of {duration}")
    
    
    #Getting Input
    tzf_header = "https://tarezameenservices.s3.amazonaws.com/internship_completion/raw/header.png"
    tzf_sign = "https://tarezameenservices.s3.amazonaws.com/internship_completion/raw/sign.jpg"
    font_ttf = "s3://tarezameenservices/internship_completion/raw/ArialCEBold.ttf"
    award_image = "s3://tarezameenservices/internship_completion/raw/award.png"
    certificate_image = "s3://tarezameenservices/internship_completion/raw/certificate.jpg"
    html_file = "s3://tarezameenservices/internship_completion/raw/completionhtml.html"
    
    output = "s3://tarezameenservices/internship_completion/processed/"
    
    
    #Reading Font file
    font_file = s3.Bucket( font_ttf.split("/")[2] ).Object( "/".join(font_ttf.split("/")[3:]) )
    
    
    
    ##Making Attachments##
    send_attachments = []
    
    #Making LOR
    if(attachments["lor"] == 1):
        print("Making LOR")
        lor_s3_key = make_lor(s3, output, tzf_header, tzf_sign, todays_date, name, email, duration, profile, ID)
        send_attachments.append("Lor")
    
    #Making AWARD
    if(attachments["award"] == 1):
        print("Making AWARD")
        award_s3_key = make_award(s3, output, award_image, name, email, font_file)
        send_attachments.append("Award")
    
    #Making Certificate
    if(attachments["certificate"] == 1):
        print("Making Certificate")
        certificate_s3_key = make_certificate(s3, output, certificate_image, todays_date, name, email, duration, profile, ID, font_file)
        send_attachments.append("Certificate")
    
    length = len(send_attachments)
    send_attachments = " & ".join(send_attachments)
    if(length == 3):
        send_attachments = send_attachments.replace(" &", ",", 1)
    print("Sending: " + send_attachments)
    
    
    
    #Making Mail Body
    html = s3.Bucket(html_file.split("/")[2]).Object( "/".join(html_file.split("/")[3:]) ).get()
    html_data = html['Body'].read().decode().format(name, str(send_attachments))
    
    #sending mail
    if((attachments["lor"] == 1) or (attachments["award"] == 1) or (attachments["certificate"] == 1)):
        try:
            message = MIMEMultipart()
            message["From"] = sender
            message["Subject"] = f"{name}, congratulations on completing your Internship Period!!"
            message["To"] = email
            message.attach(MIMEText(html_data, "html"))
            
            if(attachments["lor"] == 1):
                try:
                    lor_attachment = s3.Bucket( output.split("/")[2] ).Object( lor_s3_key ).get()['Body'].read()
                    attach = MIMEApplication(lor_attachment, _subtype="pdf")
                    attach.add_header("Content-Disposition", "attachment", filename = "LOR.pdf")
                    message.attach(attach)
                except Exception as e:
                    print("Failed to attach LOR pdf with error: " + str(e))
            
            
            if(attachments["award"] == 1):
                try:
                    award_attachment = s3.Bucket( output.split("/")[2] ).Object( award_s3_key ).get()['Body'].read()
                    attach = MIMEApplication(award_attachment, _subtype="png")
                    attach.add_header("Content-Disposition", "attachment", filename = "Award.png")
                    message.attach(attach)
                except Exception as e:
                    print("Failed to attach Award png with error: " + str(e))
            
            
            if(attachments["certificate"] == 1):
                try:
                    certificate_attachment = s3.Bucket( output.split("/")[2] ).Object( certificate_s3_key ).get()['Body'].read()
                    attach = MIMEApplication(certificate_attachment, _subtype="pdf")
                    attach.add_header("Content-Disposition", "attachment", filename = "Certificate.pdf")
                    message.attach(attach)
                except Exception as e:
                    print("Failed to attach Certificate pdf with error: " + str(e))
            
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
    else:
        print("Nothing To Send")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Mail Sent using AWS Lambda')
    }
