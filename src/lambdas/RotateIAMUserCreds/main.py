import os
import logging
import boto3
from botocore.exceptions import ClientError
import datetime
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create IAM client
iam_client = boto3.client('iam')

def time_diff(key_created_date):
  now = datetime.datetime.now(datetime.timezone.utc)
  diff = now - key_created_date
  return diff.days
  
def list_access_key(user, days_filter, status_filter):
  access_keys = iam_client.list_access_keys(UserName = user)
  user_keys = []
  
  # user may have 2 access keys 
  for keys in access_keys['AccessKeyMetadata']: 
    key_details = {}
    days = time_diff(keys['CreateDate'])
    if days >= days_filter and keys['Status'] == status_filter:
      key_details['UserName'] = keys['UserName']
      key_details['AccessKeyId'] = keys['AccessKeyId']
      key_details['KeyAgeInDays'] = days
      key_details['Status'] = keys['Status']
      user_keys.append(key_details)
  
  return user_keys
  
def create_key(user):
  access_key_metadata = iam_client.create_access_key(UserName = user)
  access_key = access_key_metadata['AccessKey']['AccessKeyId']
  secret_key = access_key_metadata['AccessKey']['SecretAccessKey']
  return (access_key, secret_key)
  
def disable_key(user, access_key):
  try:
    iam_client.update_access_key(UserName = user, AccessKeyId = access_key, Status = 'Inactive')
    logger.info(access_key + ' has been disabled')
  except ClientError as err:
    logger.error('Exception received from iam_client.update_access_key(): ' + err)
    logger.info('The access key with id %s cannot be found' % access_key)
      
def delete_key(user, access_key):
  try:
    iam_client.delete_access_key(UserName = user, AccessKeyId = access_key)
    logger.info(access_key + ' has been deleted')
  except ClientError as err:
    logger.error('Exception received from iam_client.delete_access_key: ' + err)
    logger.info('The access key with id %s cannot be found' % access_key)
      

def lambda_handler(event, context):
  # to limit exposure via this Lambda, we want to restrict IAM user via an environment variable
  user = os.environ.get('IAM_USER_NAME')
  if (not user): 
    err_msg = 'A valid username not specified via IAM_USER_NAME environment variable'
    logger.error(err_msg)
    return {
      'statusCode': 500,
      'body': err_msg
    }

  #days_filter = os.environ.get('IAM_ACCESS_KEY_MIN_AGE')
  days_filter = event.get('AccessKeyMinAgeInDays')
  if (not days_filter or not days_filter.isnumeric()): 
    err_msg = 'A valid value of AccessKeyMinAgeInDays not specified in function payload, e.g. {"AccessKeyMinAgeInDays": "30"}'
    logger.error(err_msg)
    return {
      'statusCode': 500,
      'body': err_msg
    }

  logger.info('Requested IAM_USER_NAME and AccessKeyMinAgeInDays: {}, {}'.format(user, days_filter))

  user_keys = list_access_key(user = user, days_filter = int(days_filter), status_filter = 'Active')
  new_keys = []
  for access_key in user_keys:
      logger.info('Rotating access key id {} for user {}'.format(access_key['AccessKeyId'], access_key['UserName']))
      disable_key(user = access_key['UserName'], access_key = access_key['AccessKeyId'])
      delete_key(user = access_key['UserName'], access_key = access_key['AccessKeyId'])
      nk = create_key(user = access_key['UserName'])
      logger.info('New access key id {} generated for user {}'.format(nk[0], access_key['UserName']))
      new_keys.append(nk)
  
  return {
    'statusCode': 200,
    'body': {
      'newKeys': new_keys, 
      'activeKeys': list_access_key(user = user, days_filter = 0, status_filter = 'Active')
    }
  }

# if called from terminal 
if __name__ == '__main__':
  print(lambda_handler(None, None))