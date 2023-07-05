#Importing Libraries
import pandas as pd
import s3fs, boto3, json, time
from datetime import datetime, timedelta, date


def lambda_handler(event, context):
    
    print("Running on Day:", str(datetime.now().strftime("%d-%m-%Y")))
    day = (datetime.now()-timedelta(days = 1)).strftime("%d-%m-%Y")
    print("Sending for Day:", str(day))

    
    boto3_session = boto3.Session(region_name = "us-east-1")
    s3 = boto3_session.resource("s3")
    lambda_client = boto3_session.client("lambda")
    
    
    #Reading the Secrets
    secretsmanager = boto3_session.client("secretsmanager")
    secretsmanager_response = json.loads( secretsmanager.get_secret_value(SecretId = "tzf_values")["SecretString"] )
    
    
    #Reading the Data - Whatsapp
    df = pd.read_excel(secretsmanager_response["internship_completion_link"], sheet_name = "Whatsapp")
    df.columns = [x.lower() for x in df.columns]
    df["date"] = df["date"].dt.strftime("%d-%m-%Y")
    df = df[df["date"] == day]
    df.reset_index(drop = True, inplace = True)
    print(df.head(2))
    print(df.tail(2))
    
    #Trigger "whatsapp_send_mail" lambda
    if(len(df) > 0):
        print("Students Found Today for Whatsapp")
        for i, row in enumerate(df.iterrows()):
            lambda_payload = {"name" : df["name"][i], "email" : df["email"][i], "whatsapp_link" : df["whatsapp_link"][i]}
            print("Calling the send mail with information:", str(lambda_payload))
            lambda_client.invoke(FunctionName = "whatsapp_send_mail", InvocationType = "Event", Payload = json.dumps(lambda_payload))
            time.sleep(0.5)
    else:
        print("No Students Found Today for Whatsapp")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
