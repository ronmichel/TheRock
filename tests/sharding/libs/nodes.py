#!/usr/bin/python3
import os
import re
import sys
import time
import glob
import json
import dill
import lzma
import base64
import select
import socket
import pickle
import textwrap
import subprocess
import kubernetes

from . import utils
from libs.utils import log

TIMEOUT = 1200


class Gpu(object):
	def __init__(self, node, index=0, env={}):
		self.node = node
		self.index = index
		self.env = env

	def runCmd(self, *cmd, env={}, **kwargs):
		env.update(self.env)
		return self.node.runCmd(*cmd, env=env, **kwargs)


class Node(object):
	def __init__(self, rockDir=None, env={}):
		self.rockDir = rockDir
		self.env = env
		self.errors = []
		self.host = socket.gethostname()

	def _format(self, content):
		if not isinstance(content, str):
			return content
		for fmt in re.findall(r'\{(.*?)\}', content):
			try:
				content = re.sub('{'+re.escape(fmt)+'}', str(eval(fmt)), content)
			except:
				pass
		return content

	def runCmd(self, *cmd, cwd=None, env=None, stdin=None, timeout=TIMEOUT, verbose=True,
		out=False, err=False, **kwargs,
	):
		cmd = [self._format(c) for c in cmd]
		if verbose != None:
			cwdStr = f'cd {cwd}; ' if cwd else ''
			envStr = ''
			if env:
				for key, value in env.items():
					envStr += f"{key}='{self._format(value)}' "
			log(f'RunCmd: {cwdStr}{envStr}{" ".join(cmd)}')
		if env:
			env = {k:self._format(str(v)) for k,v in env.items()}
			env.update(os.environ)
		# launch process
		process = subprocess.Popen(cmd,
			stdin=subprocess.PIPE if stdin else None,
			stdout=subprocess.PIPE, stderr=subprocess.PIPE,
			cwd=cwd, env=env, close_fds=True, **kwargs
		)
		# handling stdin
		if stdin:
			process.stdin.write(stdin if isinstance(stdin, bytes) else stdin.encode())
			process.stdin.close()
		# following process stdout / stderr
		os.set_blocking(process.stdout.fileno(), False)
		os.set_blocking(process.stderr.fileno(), False)
		verbose and log('out:')
		rets, stdout, stderr = None, b'', b''
		def _readStream(fd):
			chunk = fd.read(8196)
			verbose and log(chunk, newline=False)
			return chunk
		chunk = None
		while chunk != b'':
			rfds = select.select([process.stdout, process.stderr], [], [], timeout)[0]
			if not rfds:
				msg = f'Reached Timeout of {timeout} sec, Exiting...'
				log(msg)
				stdout += msg.encode()
				process.kill()
				break
			if process.stdout in rfds:
				stdout += (chunk := _readStream(process.stdout))
			if process.stderr in rfds:
				stderr += (chunk := _readStream(process.stderr))
		# handling return value
		ret = process.wait()
		if ret != 0 and verbose != None:
			log(f'cmd failed: {" ".join(cmd)}')
		verbose and log(f'ret: {ret}')
		# returns
		if not out:
			return ret
		if not err:
			return ret, (stdout+stderr).decode()
		return ret, stdout.decode(), stderr.decode()

	def writeFile(self, filepath, content, cwd=None, verbose=False):
		return self.runCmd('tee', filepath, stdin=content, cwd=cwd, verbose=verbose) == 0

	def readFile(self, filepath, cwd=None, verbose=None):
		ret, out = self.runCmd('cat', filepath, cwd=cwd, out=True, verbose=verbose)
		return out

	@utils._callOnce
	def getCpuCount(self):
		ret, out = self.runCmd('nproc', out=True, verbose=None)
		return int(out)

	@utils._callOnce
	def getOsDetails(self):
		content = self.readFile('/etc/os-release', verbose=None)
		return dict(re.findall(r'(\w+)="?([^"\n]+)', content))

	@utils._callOnce
	def getGpuCount(self):
		return len(glob.glob('/dev/dri/render*'))

	@utils._callOnce
	def getGpus(self):
		if (ngpus := self.getGpuCount()) > 1:
			return [Gpu(self, i, env={
				#'ROCR_VISIBLE_DEVICES': i,
				'HIP_VISIBLE_DEVICES': i,
				'HSA_VISIBLE_DEVICES': i,
			}) for i in range(ngpus)]
		return [Gpu(self)]

	def checkRock(self, verbose=None):
		return bool(self.runCmd('ls', self.rockDir, verbose=verbose) == 0)

	def verifyRock(self, verbose=True):
		if not self.checkRock():
			return False
		if self.runCmd(f'./bin/rocm-smi', cwd=self.rockDir, verbose=None) != 0:
			verbose and log('Error: Failed to get rocm-smi')
			return False
		log('Rocm Driver is healthy')
		return True
