- A range of technologies in the AWS suite was used to automate day-to-day activities like data scraping, custom mail and other processes. User-defined schedules were implemented in AWS EventBridge to trigger the jobs. The jobs are written in Python inside the AWS Lambda Environment.
- In our system, Google Sheets is used as the source of the data. The data is extracted using the first Lambda and pushed to the Second Lambda to create a Custom Mail and post it using the Google Mail API.
- In case of failure, the AWS StepFunction is used to send Alerts to the admin.

![TZF](https://github.com/jaskeerat8/tarezameenfoundation/assets/32131898/31e2b4ba-b5db-4431-9973-f260c50442ac)
