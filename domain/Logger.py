
import logging

class Logger:

	def __init__(self, name: str):
		
		self.__name = name

	def debug(self, s):
		print(self.__name, s)
	def info(self, s):
		print(self.__name, s)
	def warn(self, s):
		print(self.__name, s)
	def error(self, s):
		print(self.__name, s)

