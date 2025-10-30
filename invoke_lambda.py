import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='myFunction',
    InvocationType='RequestResponse',
    Payload=json.dumps({"message": "Hello AWS!"})
)

result = json.loads(response['Payload'].read())
print(json.dumps(result, indent=2))
