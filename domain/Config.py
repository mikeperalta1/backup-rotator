

from domain.Logger import Logger

import os


class Config:
	
	__DEFAULT_VALID_EXTENSIONS = [
		"yaml",
		"yml"
	]
	
	def __init__(self):

		self.__logger = Logger(type(self).__name__)
		self.__valid_extensions = self.__DEFAULT_VALID_EXTENSIONS
	
	def info(self, s):
		self.__logger.info(s)
	def warn(self, s):
		self.__logger.warn(s)
	def error(self, s):
		self.__logger.error(s)
	
	@staticmethod
	def get_dir_files_recursive(path: str):
		
		files_paths = []
		
		for dir_path, dirnames, filenames in os.walk(path):
			
			for file_name in filenames:
				
				file_path = os.path.join(dir_path, file_name)
				files_paths.append(file_path)
				# print("Uhm yeah", dir_path, "--", dirnames, "--", file_name)
				# print("==>", file_path)

		return files_paths
	
	def gather_valid_configs(self, paths: list=None):
		
		assert paths is not None, "Config paths cannot be None"
		assert len(paths) > 0, "Must provide at least one config file path"
		
		self.__logger.info("Gathering valid configs")
		
		file_paths = []
		configs = []
		not_configs = []
		
		# First gather all files that are potential configs
		for path in paths:
			
			self.__logger.info(f"Inspecting path: {path}")
			
			if os.path.isfile(path):
				self.__logger.info(f"Path is a file; Adding directly to potential config candidates: {path}")
				file_paths.append(path)
				
			elif os.path.isdir(path):
				self.__logger.info(f"Path is a dir; Scanning recursively for potential config candidate files: {path}")
				for file_path in Config.get_dir_files_recursive(path=path):
					self.__logger.info(f"> Candidate file: {file_path}")
					file_paths.append(file_path)
			
			else:
				raise AssertionError(f"Don't know how to handle path that isn't a file or dir: {path}")
		
		# Now, filter for files with valid YAML extensions
		for file_path in file_paths:
			if self.check_file_extension(file_path=file_path, extensions=None):
				configs.append(file_path)
			else:
				not_configs.append(file_path)
		
		self.__logger.info("Filtered out non-config files:")
		if len(not_configs) > 0:
			for not_config in not_configs:
				self.__logger.info(f"> {not_config}")
		else:
			self.__logger.info("> [none]")
		
		self.__logger.info("Kept config-looking files:")
		if len(configs) > 0:
			for config in configs:
				self.__logger.info(f"> {config}")
		else:
			self.__logger.info("> [none]")
		
		return configs
	
	def check_file_extension(self, file_path, extensions: list=None):
		
		if extensions is None:
			extensions = self.__valid_extensions
		
		file_name, file_extension = os.path.splitext(file_path)
		if len(file_extension) > 0 and file_extension[0] == ".":
			file_extension = file_extension[1:]
		file_extension = file_extension.lower()

		for valid_extension in extensions:
			#print(file_name, "---", file_extension, "---", valid_extension)
			if file_extension == valid_extension:
				return True
		
		return False

