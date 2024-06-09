
import logging
from logging.handlers import SysLogHandler

import sys


class Logger:

	def __init__(self, name: str, debug: bool = False):
		
		self.__name = name
		
		self.__logger = logging.getLogger(self.__name)

		if debug:
			level = logging.DEBUG
		else:
			level = logging.INFO
		
		self.__logger.setLevel(level)
		
		formatter = logging.Formatter(
			fmt="[{name}][{levelname:<7}] {message}",
			style='{'
		)
		formatter_full = logging.Formatter(
			fmt="[{asctime}][{name}][{levelname:<7}] {message}",
			style='{'
		)
		
		# Console output / stream handler (STDOUT)
		handler = logging.StreamHandler(
			stream=sys.stdout
		)
		handler.setLevel(level)
		handler.addFilter(lambda entry: entry.levelno <= logging.INFO)
		handler.setFormatter(formatter_full)
		self.__logger.addHandler(handler)
		
		# Console output / stream handler (STDERR)
		handler = logging.StreamHandler(
			stream=sys.stderr
		)
		handler.setLevel(logging.WARNING)
		handler.setFormatter(formatter_full)
		self.__logger.addHandler(handler)
		
		# Syslog handler
		handler = SysLogHandler(
			address="/dev/log"
		)
		handler.setLevel(level)
		handler.setFormatter(formatter)
		self.__logger.addHandler(handler)
		
		# This is annoying inside cron
		self.debug("Test debug log")
		self.info("Test info log")
		self.warn("Test warn log")
		self.error("Test error log")
	
	def debug(self, s):
		self.__logger.debug(s)

	def info(self, s):
		self.__logger.info(s)

	def warn(self, s):
		self.__logger.warning(s)

	def warning(self, s):
		self.__logger.warning(s)
	
	def error(self, s):
		self.__logger.error(s)
