
import logging
import sys

class Logger:

	def __init__(self, name: str, debug: bool=False):
		
		self.__name = name
		
		self.__logger = logging.getLogger(self.__name)

		if debug:
			level = logging.DEBUG
		else:
			level = logging.INFO
		
		self.__logger.setLevel(level)
		
		formatter = logging.Formatter('[%(asctime)s][%(name)s][%(levelname)s] %(message)s')
		
		# Console output / stream handler
		handler = logging.StreamHandler()
		handler.setLevel(level)
		handler.setFormatter(formatter)
		self.__logger.addHandler(handler)
	
	def debug(self, s):
		self.__logger.debug(s)
	def info(self, s):
		self.__logger.info(s)
	def warn(self, s):
		self.__logger.warn(s)
	def error(self, s):
		self.__logger.error(s)
