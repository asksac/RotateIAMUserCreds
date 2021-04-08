## Overview

This directory contains scripts to invoke the Lamba function deployed via Terraform root module, fetch 
the new IAM User access credentials (access key id and secret key) and then run an external command 
called `tpconfig` (offered by NetBackup's CloudCatalyst service). 

The `invoke_lambda.py` and `test_tpconfig.py` scripts require `pexpect` Python package to be installed. 

If you wish to have `pexpect` package installed in a local sub-directory, you can install as follows: 

Using Python 2.7: 
```bash
pip2.7 install pexpect -t ./lib
```

Using Python 3: 
```bash
pip install pexpect -t ./lib
```

For local testing purposes, `tpconfig` is a shell script provided to simulate the actual tpconfig command. 

## Usage

Running `python invoke_lambda.py -h` produces the following usage instructions: 

```
usage: invoke_lambda.py [-h] [--debug] [--endpoint ENDPOINT] [--region REGION] [--auth-profile AUTH_PROFILE] [--save-profile SAVE_PROFILE]
                        [--storage-server STORAGE_SERVER] [--stype STYPE] --function-name FUNCTION_NAME
                        payload

invoke a lambda function synchronously

positional arguments:
  payload               JSON string as input to lambda function

optional arguments:
  -h, --help            show this help message and exit
  --debug               enables debug logging mode
  --endpoint ENDPOINT   lambda endpoint DNS name (eg. lambda.us-east-1.amazonaws.com)
  --region REGION       AWS region name (eg. us-east-1)
  --auth-profile AUTH_PROFILE
                        aws credentials file profile name for lambda service authentication
  --save-profile SAVE_PROFILE
                        aws credentials file profile name for saving new access key id and secret key
  --storage-server STORAGE_SERVER
                        netbackup storage server name
  --stype STYPE         netbackup stype parameter value
  --function-name FUNCTION_NAME
                        lambda function's name (eg. HelloWorld)

note: this program requires python 2.7 or above
```

A sample command line to run `invoke_lambda.py` is shown below (make sure to change parameter values
before running the command): 

```shell
python invoke_lambda.py --debug \
  --endpoint vpce-xxxxxxxxxxxxxxxx-xxxxxxxx.lambda.us-east-1.vpce.amazonaws.com \
  --region us-east-1 \
  --auth-profile default \
  --save-profile default \
  --storage-server my-server \
  --stype PureDisk_amazon_rawd \
  --function-name RotateIAMUserCreds \
  '{"AccessKeyMinAgeInDays":"30"}' 
```

*Note: `--debug` flag must never is used in Production environment, it will output secret key value in logs.*