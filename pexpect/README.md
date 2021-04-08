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