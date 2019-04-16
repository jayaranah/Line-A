# -*- coding: utf-8 -*-
from linepy import LINE
from threading import Thread
from functools import wraps
import traceback
import logging

log = logging.getLogger(__name__)

class OEPoll(object):
	def __init__(self, client):
		if not isinstance(client, LINE):
			raise Exception('You need to set LINE instance to initialize OEPoll')

		self.client: LINE = client
		self.func_handler : list = []
		self.Opinterrupts: dict = []

	def fetchOps(self, revision: int, count: int = 1):
		return self.client.poll.fetchOperations(revision, count)

	def is_message(self, types, *arg, **kwg):
		def decorator(func):
			@wraps(func)
			def wraper(self, *args, **kwgs):
				func(*args, **kwgs)
				return True

			data = {
				func:arg,
				"data":kwg
			}
			self.func_handler.append(data)
			return wraper, self.Opinterrupts.append({types:func}), True
		return decorator

	def setRevision(self, revision):
		self.client.revision = max(revision, self.client.revision)

	def _exec(self, ops, func):
		msg = ops.message
		for i in range(len(self.func_handler)):
			if func in self.func_handler[i]:
				if len(self.func_handler[i][func]) < 1:
					self.do_job(c=i, ops=ops)
				else:
					if self.func_handler[i][func][0] != None:
						if self.func_handler[i][func][0](msg):
							self.do_job( c=i, ops=ops)

	def do_job(self, ops, c):
		try:
			Thread(target=self.Opinterrupts[c][ops.type],args=(ops,)).start()
		except Exception:
			log.error(traceback.format_exc())

	def start(self):
		while True:
			self.trace()

	def trace(self):
		try:
			ops = self.fetchOps(self.client.revision)
			for op in ops:
				if self.func_handler:
					for i in range(len(self.Opinterrupts)):
						if list(self.Opinterrupts[i].values())[0] in self.func_handler[i]:
							if op.type in self.Opinterrupts[i].keys():
								self._exec(op, self.Opinterrupts[i][op.type])
							self.setRevision(op.revision)
		except EOFError:
			pass
		except Exception:
			log.error(traceback.format_exc())
