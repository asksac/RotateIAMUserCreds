import sys, os, datetime
import base64, hashlib, hmac
import logging
import json
import argparse
import xml.dom.minidom
import subprocess
import copy

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

CREDENTIALS_FILE = '~/.aws/credentials'

# read aws access key id and secret from os.environment or ~/.aws/credentials file
def getAccessKeys(profile = None): 
  access_key = os.getenv('AWS_ACCESS_KEY_ID')
  secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')

  if not access_key or not secret_key:       
    if not profile: profile = os.getenv('AWS_PROFILE', 'default')
    config = configparser.RawConfigParser()
    config.read(os.path.expanduser(CREDENTIALS_FILE))
    access_key = config.get(profile, 'aws_access_key_id') 
    secret_key = config.get(profile, 'aws_secret_access_key') 

  return (access_key, secret_key)

# save aws access key id and secret to ~/.aws/credentials file
def saveAccessKeys(profile, access_key, secret_key): 
  config = configparser.RawConfigParser()
  config.read(os.path.expanduser(CREDENTIALS_FILE))
  if not config.has_section(profile): 
    config.add_section(profile)
  config.set(profile, 'aws_access_key_id', access_key) 
  config.set(profile, 'aws_secret_access_key', secret_key) 
  with open(os.path.expanduser(CREDENTIALS_FILE), 'w') as configfile:
    config.write(configfile)

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
  logging.debug('Request string: ' + method + ' ' + url)
  logging.debug('Request headers: ' + str(headers))

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
    logging.error('Response error code and reason: ' + res_code + '/' + err_reason)

  if logging.DEBUG >= logging.root.level:    
    if res_body.startswith('<?xml'):
      res_body_print = prettyXml(res_body)
    else:
      try: 
        res_body_json = json.loads(res_body)
        res_body_print = json.dumps(res_body_json, indent=4, separators=(',', ': '))
      except: 
        res_body_print = res_body

    logging.debug('Response code: ' + str(res_code))
    logging.debug('Response data: ' + res_body_print)

  return (res_code, res_body)

def prettyXml(txt):
  dom = xml.dom.minidom.parseString(txt)
  xml_pretty_str = dom.toprettyxml()
  return xml_pretty_str

def tpConfig(storage_server, stype, access_key_id, secret_key): 
  command = ['tpconfig', '-update', '-storage_server', storage_server, '-stype', stype, '-sts_user_id', access_key_id, '-password', secret_key]
  logging.info('Calling tpconfig with following parameters: ' + str(command))
  output = subprocess.call(command)
  logging.info('Output from tpconfig: ' + output)

  #p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  #print(p.stdout.readline())
  #p.stdin.write(secret_key.encode()+b'\n')
  #print(p.stdout.readline())
  #p.stdin.write(secret_key.encode()+b'\n')
  #print(p.stdout.readline())
  #os.write(p.stdin.fileno(), secret_key.encode()+b'\n')
  #os.write(p.stdin.fileno(), secret_key.encode()+b'\n')
  #output = p.communicate(input=secret_key.encode())[0]

# -----

def main():
  # edit these settings to change region, scheme or endpoint
  lambda_service = dict(
    name = 'lambda', 
    scheme = 'https',
  )

  # parse cli options
  cliparser = argparse.ArgumentParser(
    description = 'invoke a lambda function synchronously', 
    epilog = 'note: this program requires python 2.7 or above'
  )
  cliparser.add_argument('--debug', 
    required=False, 
    action='store_true', 
    help='enables debug logging mode'
  )
  cliparser.add_argument('--endpoint', 
    required=False, 
    default='lambda.us-east-1.amazonaws.com', 
    help='lambda endpoint DNS name (eg. lambda.us-east-1.amazonaws.com)'
  )
  cliparser.add_argument('--region', 
    required=False, 
    default='us-east-1', 
    help='AWS region name (eg. us-east-1)'
  )
  cliparser.add_argument('--auth-profile',  
    required=False, 
    help='aws credentials file profile name for lambda service authentication'
  )
  cliparser.add_argument('--save-profile',  
    required=False, 
    help='aws credentials file profile name for saving new access key id and secret key'
  )
  cliparser.add_argument('--storage-server',  
    required=False, 
    help='netbackup storage server name'
  )
  cliparser.add_argument('--stype',  
    required=False, 
    help='netbackup stype parameter value'
  )
  cliparser.add_argument('--function-name', 
    required=True, 
    dest='function_name', 
    help='lambda function\'s name (eg. HelloWorld)'
  )
  cliparser.add_argument('payload', 
    help='JSON string as input to lambda function'
  )

  # extract cli option values and set program behavior
  args = cliparser.parse_args()

  # sets logging level
  level = logging.INFO # default
  if args.debug: level = logging.DEBUG
  logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=level)

  lambda_service['region'] = args.region
  lambda_service['endpoint'] = args.endpoint
 
  (access_key, secret_key) = getAccessKeys(args.auth_profile)
  if access_key is None or secret_key is None:
    logging.error('AWS access credentials not found in os.environment or ~/.aws/credentials file')
    sys.exit(-1)
  else: 
    logging.info('Using access key id {} for lambda service authentication'.format(access_key))

  lambda_service['access_key'] = access_key
  lambda_service['secret_key'] = secret_key

  # sets logging level for urllib
  if lambda_service.get('scheme') == 'https': 
    https_logger = urllibx.HTTPSHandler(debuglevel = 1 if args.debug else 0)
    opener = urllibx.build_opener(https_logger) # put your other handlers here too!
    urllibx.install_opener(opener)
  else: 
    http_logger = urllibx.HTTPHandler(debuglevel = 1 if args.debug else 0)
    opener = urllibx.build_opener(http_logger) # put your other handlers here too!
    urllibx.install_opener(opener)

  # Invoke Lambda function 
  logging.info('Invoking lambda function {} using access key id {}'.format(args.function_name, access_key))
  post_uri = '/2015-03-31/functions/' + args.function_name + '/invocations'
  req_body = args.payload
  (req_url, req_headers) = build_request(service=lambda_service, method='POST', uri_path=post_uri, body=req_body, 
                        headers={'x-amz-invocation-type': 'RequestResponse', 'x-amz-log-type': 'Tail'})
  (res_code, res_body) = submit_request('POST', req_url, req_headers, req_body)

  if (int(res_code) != 200): 
    logging.error('Received response code {} from lambda. Exiting as it is a non 200 code.'.format(res_code))
    sys.exit(-2)

  try: 
    res_body_json = json.loads(res_body)
    newKeys = res_body_json.get('body').get('newKeys')
    activeKeys = res_body_json.get('body').get('activeKeys')

    newKeys_masked = copy.deepcopy(newKeys)
    for k in newKeys_masked: k[1] = len(k[1])*'*'
    logging.info('Lambda returned newKeys: {}'.format(newKeys_masked))
    logging.info('Lambda returned activeKeys: {}'.format(activeKeys))
  except: 
    logging.exception('Lambda response is an invalid JSON string')
    logging.debug('Lambda response: ' + res_body)
    sys.exit(-3)

  new_access_key_id = new_secret_key = None
  try: 
    if type(newKeys) is list and len(newKeys) > 0: 
      new_access_key_id = newKeys[0][0]
      new_secret_key = newKeys[0][1]
      if args.save_profile: 
        saveAccessKeys(args.save_profile, new_access_key_id, new_secret_key)
        logging.info('New access key id {} and secret key saved to file {} under {} profile.'.format(new_access_key_id, CREDENTIALS_FILE, args.save_profile))
      else:
        logging.warning('New access key id and secret key not saved to credentials file as --save-profile option was not provided')
    else: 
      logging.error('Lambda response did not return any valid new keys')
  except: 
    logging.exception('New access key could not be processed')
    sys.exit(-4)

  if args.storage_server and args.stype: 
    tpConfig(args.storage_server, args.stype, new_access_key_id, new_secret_key)

# -----

if __name__ == '__main__':
    main()
