

from domain.config.ConfigFile import ConfigFile
from domain.config.Scanner import Scanner
from domain.Logger import Logger


from pathlib import Path


class Config:
	
	def __init__(self, logger: Logger, config_files_paths: [Path]):
		
		self.__logger = logger
		
		self.__config_files_paths: [Path] = config_files_paths
		self.__configs: {} = None
		
		self.__scanner = Scanner(
			logger=self.__logger
		)
		
		self._consume_configs()
	
	def _consume_configs(self, paths: [Path] = None):
		
		config_paths = self.__scanner.gather_valid_config_paths(paths=paths)
		
		for config_path in config_paths:
			
			config = ConfigFile(
				logger=self.__logger,
				path=config_path
			)
			
			self.__configs[config.key] = config
	
	@property
	def config_files(self) -> [ConfigFile]:
		return self.__configs.values()
