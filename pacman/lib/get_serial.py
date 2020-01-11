import os
import subprocess
import hashlib
import sys
from uuid import getnode


def check_root():

	if os.geteuid() > 0:
		print ("ERROR: must be root to use.")
		sys.exit(1)


def check_hardware():

	out = subprocess.check_output(['uname', '-a'])
	out = out.decode('utf-8').split(' ')[11]
	return out


def get_mb_serial():
	check_root()
	out = subprocess.check_output(['dmidecode'])
	out = out.decode('utf-8')
	seriales = [ line for line in out.split('\n') if line.find('Serial Number') >= 0 ]
	serial = seriales[1].split(' ')[2]
	return serial


def hash(serial):

	crypted = hashlib.md5(serial.encode()).hexdigest()
	return crypted


def get_hashed_mbserial():

	if check_hardware() == 'x86_64':
		serialHash = hash(get_mb_serial())
	else:
		serialHash = hash(str(getnode()))
	return serialHash	


if __name__ == "__main__":
    print(get_hashed_mbserial())