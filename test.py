
owais: Owais@1234
achal: Achal@1234
abhay: Abhay@1234
import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('receipt_data')

response = table.scan()
for item in response['Items']:
    print(len(item))
