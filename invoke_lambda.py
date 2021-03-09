import sys, os, datetime
import base64, hashlib, hmac
import logging
import json
import argparse
import xml.dom.minidom

if (sys.version_info > (3, 0)):
  # Python 3
  import urllib
  import urllib.request as urllibx
  import urllib.parse as urlparse
  from urllib.parse import quote_plus
  from urllib.error import HTTPError
  import configparser as configparser
else:
  # Python 2
  import urllib
  import urllib2 as urllibx
  import urlparse
  from urllib import quote_plus
  from urllib2 import HTTPError
  import ConfigParser as configparser

# read aws access key id and secret from os.environment or ~/.aws/credentials file
def getAccessKeys(): 
  access_key = os.getenv('AWS_ACCESS_KEY_ID')
  secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')

  if not access_key or not secret_key:       
    profile = os.getenv('AWS_PROFILE', 'default')
    config = configparser.RawConfigParser()
    config.read(os.path.expanduser('~/.aws/credentials'))
    access_key = config.get(profile, 'aws_access_key_id') 
    secret_key = config.get(profile, 'aws_secret_access_key') 

  return (access_key, secret_key)

# create an hmac signature of msg using specified key
def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

# create a signing key using AWS4 format
def getSignatureKey(key, dateStamp, regionName, serviceName):
    kDate = sign(('AWS4' + key).encode('utf-8'), dateStamp)
    kRegion = sign(kDate, regionName)
    kService = sign(kRegion, serviceName)
    kSigning = sign(kService, 'aws4_request')
    return kSigning

# create an http request based on AWS4 format and specified parameters
def build_request(service, method='GET', host=None, uri_path='/', query_params={}, headers={}, body=None): 
  t = datetime.datetime.utcnow()
  amzdate = t.strftime('%Y%m%dT%H%M%SZ')
  datestamp = t.strftime('%Y%m%d') # Date in YYYYMMDD format, used in credential scope

  if (method in ['GET', 'DELETE', 'HEAD']): 
    body = ''
  elif not body: 
    body = ''
  payload_hash = hashlib.sha256(body.encode('utf-8')).hexdigest()

  if not host: host = service.get('endpoint')

  headers['host'] = host
  headers['x-amz-content-sha256'] = payload_hash
  headers['x-amz-date'] = amzdate

  canonical_uri = uri_path
  canonical_querystring = "&".join([ k + '=' + quote_plus(query_params[k]) for k in sorted(query_params.keys()) ])

  canonical_headers = ''
  signed_headers = ''
  for k in sorted(headers.keys()): 
    canonical_headers += k.lower() + ':' + headers[k] +'\n'
    if not signed_headers:
      signed_headers += k
    else:
      signed_headers += ';' + k

  # create a signed authorization header using AWS Signature Version 4
  canonical_request = method + '\n' + canonical_uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash
  algorithm = 'AWS4-HMAC-SHA256'
  credential_scope = datestamp + '/' + service.get('region') + '/' + service.get('name') + '/' + 'aws4_request'
  string_to_sign = algorithm + '\n' +  amzdate + '\n' +  credential_scope + '\n' +  hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
  signing_key = getSignatureKey(service.get('secret_key'), datestamp, service.get('region'), service.get('name'))
  signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()
  authorization_header = algorithm + ' ' + 'Credential=' + service.get('access_key') + '/' + credential_scope + ', ' +  'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature

  # add our new authorization header
  headers['authorization'] = authorization_header

  request_url = urlparse.urlunparse((service.get('scheme'), service.get('endpoint'), uri_path, None, canonical_querystring, None))
  return (request_url, headers)

# call http endpoint with specified parameters and AWS4 signature
def submit_request(method, url, headers, body=None):
  logging.debug('>> Request URL: [' + method + ' ' + url + ']')
  logging.debug('>> Request Headers: ' + str(headers))

  if not body: 
    request = urllibx.Request(url, headers=headers)
  else: 
    body_bytes = body.encode() # required in Python 3, default is utf-8
    request = urllibx.Request(url, data=body_bytes, headers=headers)

  request.get_method = lambda: method 
  try: 
    response = urllibx.urlopen(request)
    res_code = response.getcode()
    res_body = response.read().decode()
  except HTTPError as ex:
    err_reason = ex.reason
    res_code = ex.code
    res_body = ex.read().decode()
    logging.error('!! Response Error: ' + err_reason)

  if res_body.startswith('<?xml'):
    res_body_print = prettyXml(res_body)
  else:
    try: 
      res_body_json = json.loads(res_body)
      res_body_print = json.dumps(res_body_json, indent=4, separators=(',', ': '))
    except: 
      res_body_print = res_body

  logging.info('<< Response Code: ' + str(res_code))
  logging.info('<< Response Data: \n' + res_body_print)
  return (res_code, res_body)

def prettyXml(txt):
  dom = xml.dom.minidom.parseString(txt)
  xml_pretty_str = dom.toprettyxml()
  return xml_pretty_str

# -----

def main():
  # edit these settings to change region, scheme or endpoint
  lambda_service = dict(
    name = 'lambda', 
    scheme = 'https',
  )

  cliparser = argparse.ArgumentParser(description = 'invoke a lambda function synchronously', epilog = 'note: this program requires python 2.7 or above')
  cliparser.add_argument('function_name', help='lambda function\'s ARN or name (eg. HelloWorld)')
  cliparser.add_argument('--endpoint', required=False, default='lambda.us-east-1.amazonaws.com', help='lambda endpoint DNS name (eg. lambda.us-east-1.amazonaws.com)')
  cliparser.add_argument('--region', required=False, default='us-east-1', help='AWS region name (eg. us-east-1)')

  args = cliparser.parse_args()
  lambda_service['region'] = args.region
  lambda_service['endpoint'] = args.endpoint
 
  (access_key, secret_key) = getAccessKeys()
  if access_key is None or secret_key is None:
      print('AWS access credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) not found in os.environment or ~/.aws/credentials file')
      sys.exit(-1)

  lambda_service['access_key'] = access_key
  lambda_service['secret_key'] = secret_key

  logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

  # sets logging level for urllib
  if lambda_service.get('scheme') == 'https': 
    https_logger = urllibx.HTTPSHandler(debuglevel = 1)
    opener = urllibx.build_opener(https_logger) # put your other handlers here too!
    urllibx.install_opener(opener)
  else: 
    http_logger = urllibx.HTTPHandler(debuglevel = 1)
    opener = urllibx.build_opener(http_logger) # put your other handlers here too!
    urllibx.install_opener(opener)

  # Invoke API call 
  print('----- Lambda:Invoke -----')
  post_uri = '/2015-03-31/functions/' + args.function_name + '/invocations'
  data = ''
  (u, h) = build_request(service=lambda_service, method='POST', uri_path=post_uri, body=data, 
                        headers={'x-amz-invocation-type': 'RequestResponse', 'x-amz-log-type': 'Tail'})
  res = submit_request('POST', u, h, data)
  print('----- Lambda:Invoke -----\n\n')

# -----

if __name__ == '__main__':
    main()
