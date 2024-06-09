

from domain.Logger import Logger
from domain.Util import Util


# import os
from pathlib import Path


class Config:
	
	__DEFAULT_VALID_EXTENSIONS = [
		"yaml",
		"yml"
	]
	
	def __init__(self, logger: Logger):

		self.__logger = logger
		self.__valid_extensions = self.__DEFAULT_VALID_EXTENSIONS
	
	def debug(self, s):
		self.__logger.debug(f"[{type(self).__name__}] {s}")
	
	def info(self, s):
		self.__logger.info(f"[{type(self).__name__}] {s}")
	
	def warn(self, s):
		self.__logger.warning(f"[{type(self).__name__}] {s}")
		
	def error(self, s):
		self.__logger.error(f"[{type(self).__name__}] {s}")
	
	def gather_valid_configs(self, paths: list = None) -> [Path]:
		
		assert paths is not None, "Config paths cannot be None"
		assert len(paths) > 0, "Must provide at least one config file path"
		
		self.info("Gathering valid configs")
		
		file_paths = []
		configs = []
		not_configs = []
		
		# First gather all files that are potential configs
		for path_str in paths:
			
			path = Path(path_str)
			
			self.info(f"Inspecting path: {path}")
			
			if not path.exists():
			
				self.error(f"Path doesn't exist: {path}")
			
			if path.is_file():
				
				self.debug(
					f"Path is a file; Adding directly to potential config candidates: {path}"
				)
				file_paths.append(path)
			
			elif path.is_dir():
				
				self.debug(
					f"Path is a dir;"
					" Scanning recursively for potential config candidate files: {path}"
				)
				
				for file_path in Util.get_dir_files_recursive(path=path):
					self.info(f"> Candidate file: {file_path}")
					file_paths.append(file_path)
			
			else:
				raise AssertionError(
					f"Don't know how to handle path that isn't a file or dir: {path}"
				)
		
		# Now, filter for files with valid YAML extensions
		for file_path in file_paths:
			
			if self.check_file_extension(file_path=file_path, extensions=None):
				configs.append(file_path)
			else:
				not_configs.append(file_path)
		
		self.info("Filtered out non-config files:")
		if len(not_configs) > 0:
			for not_config in not_configs:
				self.info(f"> {not_config}")
		else:
			self.info("> [none]")
		
		self.info("Kept config-looking files:")
		if len(configs) > 0:
			for config in configs:
				self.info(f"> {config}")
		else:
			self.info("> [none]")
		
		return configs
	
	def check_file_extension(self, file_path: Path, extensions: list = None) -> bool:
		
		if extensions is None:
			extensions = self.__valid_extensions
		
		file_extension = file_path.suffix
		
		# Strip preceding dot from extension
		if len(file_extension) > 0 and file_extension[0] == ".":
			file_extension = file_extension[1:]
		file_extension = file_extension.lower()
		
		for valid_extension in extensions:
			if file_extension == valid_extension:
				return True
		
		return False
