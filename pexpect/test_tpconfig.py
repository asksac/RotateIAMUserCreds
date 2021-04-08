#!/usr/bin/env python

import sys, os, datetime
import logging
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
import pexpect 

# sets logging level
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# TODO - update these values during testing
access_key_id = 'XXXXXXXXXXXX'
secret_key = 'XXXXXXXXXXXX'
storage_server = 'XXXXXXXXXXXX'
stype = 'XXXXXXXXXXXX'

# run tpconfig command
tpcargs = ['-update', '-storage_server', storage_server, '-stype', stype, '-sts_user_id', access_key_id] # '-password', secret_key
child = pexpect.spawn('tpconfig', tpcargs)
child.logfile = sys.stdout
child.expect(['(.*)password for User Id(.*):', pexpect.EOF, pexpect.TIMEOUT])
child.sendline(secret_key)
child.expect(['(.*)password to confirm it:', pexpect.EOF, pexpect.TIMEOUT])
child.sendline(secret_key)
child.wait()
logging.info('tpconfig returned output: %s' % child.after)
logging.info('Done executing tpconfig with exit code %s and signal status %s' % (child.exitstatus, child.signalstatus))

'''
# alternate method of calling external command using Python built-in `subprocess`

command = ['tpconfig', 'sac']
logging.info('Calling subprocess with following parameters: ' + ' '.join(command))
#env = dict(os.environ)
secret_key = 'hello'

# method 1
#proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#outdata, errdata = proc.communicate(os.linesep.join([secret_key, secret_key]).encode())
#rc = proc.returncode
#logging.info('tpconfig returned code: %s' % rc)
#logging.info('tpconfig output: %s (stderr: %s)' % (outdata, errdata))

# method 2
#proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#output = proc.communicate(os.linesep.join(['hello', 'hello']).encode())[0]
#rc = proc.returncode
#print(rc, output)

# method 3
#proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#print(proc.stdout.readline())
#proc.stdin.write(b'Hello World\n')
#proc.stdin.flush()
#print(proc.stdout.readline())
#proc.stdin.write(b'Hello World\n')
#proc.stdin.flush()
#proc.stdin.close()
#print(proc.stdout.readline())
#proc.terminate()
#proc.wait(timeout=0.2)
'''