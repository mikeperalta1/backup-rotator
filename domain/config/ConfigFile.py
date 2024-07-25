

from domain.Logger import Logger


from pathlib import Path
import yaml


class ConfigFile:
	
	__VALID_TARGET_TYPES = [
		"file",
		"directory"
	]
	
	__VALID_DATE_DETECTION_TYPES = [
		"file"
	]
	
	def __init__(
			self, logger: Logger,
			path: Path,
	):
		
		self.__logger = logger
		self.__path = path.absolute()
		
		# noinspection PyTypeChecker
		self.__data: dict = None
		
		self.__dry_run: bool = True
		
		# noinspection PyTypeChecker
		self.__target_type: str = None
		
		# noinspection PyTypeChecker
		self.__date_detection: str = None
		
		self.__rotatable_paths: [Path] = []
		
		self.__minimum_items: int = 0
		# noinspection PyTypeChecker
		self.__maximum_items: int = None
		# noinspection PyTypeChecker
		self.__maximum_age: int = None
		
		self._load()
		self._consume()
		
	def __str__(self):
		
		s = ""
		
		s += "*** Config File ***"
		s += f"\n> Path: {self.__path}"
		s += f"\n> Dry run: " + ("Yes" if self.__dry_run else "No")
		s += f"\n> Minimum items: {self.__minimum_items}"
		s += f"\n> Maximum items: {self.__maximum_items}"
		s += f"\n> Maximum age (in days): {self.__maximum_age}"
		s += f"\n> Target type: {self.__target_type}"
		s += f"\n> Date detection: {self.__date_detection}"
		s += f"\n> Rotatable paths: "
		if len(self.__rotatable_paths) > 0:
			for p in self.__rotatable_paths:
				s += f"\n>> {p}"
		else:
			s += "\n>> [none]"
		
		return s
	
	def _load(self):
		
		self.info(f"Loading config: {self.__path}")
		
		assert self.__path.is_file(), (
			f"Cannot load config file because it isn't a file: {self.__path}"
		)
		
		# Open the file
		self.debug(f"Opening config file for load: {self.__path}")
		f = open(str(self.__path))
		if not f:
			raise Exception(f"Unable to open config file: {self.__path}")
		
		# Load data
		self.__data = yaml.safe_load(f)
		assert self.__data is not None, (
			f"Config file seems to be null or empty: {self.__path}"
		)
		
		# Consume to internal
		self.info(f"Loaded config from path: {self.__path}")
	
	def _consume(self):
		
		try:
			
			assert isinstance(self.__data, dict), (
				f"Config file should be a dict!"
			)
			
			if "options" in self.__data.keys():
				
				self.info(f"Found options setting")
				options = self.__data["options"]
				assert isinstance(options, dict), "Options must be a dict"
				
				if "dry-run" in options.keys():
					
					dry_run = self.__data["options"]["dry-run"]
					self.info(f"Found dry run option: {dry_run}")
					assert isinstance(dry_run, bool), "dry-run setting must be boolean"
					self.__dry_run = dry_run
				else:
					self.warning(f"No dry-run option found; Will use default: {self.__dry_run}")
				
				if "minimum-items" in options.keys():
					
					minimum_items = options["minimum-items"]
					self.info(f"Found minimum-items option: {minimum_items}")
					assert isinstance(minimum_items, int), (
						f"Option minimum-items must be int, but got: {minimum_items}"
					)
					self.__minimum_items = minimum_items
				else:
					self.warning(
						f"No minimum-items option found; Will use default: {self.__minimum_items}"
					)
				
				assert (
					"maximum-items" in options.keys()
					or
					"maximum-age" in options.keys()
				), (
					"Options should include either maximum-items or maximum-age"
				)
				
				if "maximum-items" in options.keys():
					
					maximum_items = options["maximum-items"]
					self.info(f"Found maximum-items option: {maximum_items}")
					assert isinstance(maximum_items, int), (
						f"Option maximum-items must be int, but got: {maximum_items}"
					)
					assert maximum_items > 0, (
						f"Option maximum-items is zero, which doesn't make sense."
					)
					self.__maximum_items = maximum_items
				else:
					self.warning(
						f"No maximum-items option found; Will use default: {self.__maximum_items}"
					)
				
				if "maximum-age" in options.keys():
					
					maximum_age = options["maximum-age"]
					self.info(f"Found maximum-age option (max age in days): {maximum_age}")
					assert maximum_age is None or isinstance(maximum_age, int), (
						f"Option maximum-age must be None or an integer,"
						f" but got: {type(maximum_age).__name__} ({maximum_age})"
					)
					assert maximum_age is None or maximum_age > 0, (
						f"Option maximum-age is zero, which doesn't make sense."
					)
					self.__maximum_age = maximum_age
				else:
					self.warning(
						f"No maximum-age option found; Will use default: {self.__maximum_age}"
					)
				
				assert "target-type" in options.keys(), (
					f"Option target-type is required"
				)
				target_type = options["target-type"]
				self.info(f"Found target-type option: {target_type}")
				assert isinstance(target_type, str), (
					f"Option target-type must be str, but got: {target_type}"
				)
				assert target_type in self.__VALID_TARGET_TYPES, (
					f"Option target-type must be one of: {self.__VALID_TARGET_TYPES}"
				)
				self.__target_type = target_type
				
				if "date-detection" in options.keys():
					date_detection = options["date-detection"]
					self.info(f"Found date-detection option: {date_detection}")
					assert isinstance(date_detection, str), (
						f"Option date-detection must be str, but got: {date_detection}"
					)
					assert date_detection in self.__VALID_DATE_DETECTION_TYPES, (
						f"Option date-detection must be one of: {self.__VALID_DATE_DETECTION_TYPES}"
					)
					self.__date_detection = date_detection
				else:
					self.error(
						f"Option date-detection not found; Will use default: {self.__date_detection}"
					)
					raise AssertionError(
						f"Option date-detection is required."
					)
				
			else:
				self.error(f"No options key found!")
				raise AssertionError(f"No options key found!")
			
			assert "paths" in self.__data, (
				f"Could not find 'paths' key"
			)
			rotatable_paths = self.__data["paths"]
			if isinstance(rotatable_paths, str):
				rotatable_paths = [rotatable_paths]
			assert isinstance(rotatable_paths, list), (
				"Rotatable 'paths' key must be a string or list"
			)
			for i in range(len(rotatable_paths)):
				p = rotatable_paths[i]
				if isinstance(p, Path):
					continue
				elif isinstance(p, str):
					rotatable_paths[i] = Path(p)
				else:
					raise AssertionError(
						f"All rotatable paths must be strings or pathlib::Path objects"
					)
			
			self.__rotatable_paths = rotatable_paths
			self.info(f"Found {len(self.__rotatable_paths)} rotatable paths")
		
		except KeyError as e:
			
			self.error(
				f"Failed to load config due to KeyError"
				f"\nFile: {self.__path}"
				f"\nError: {str(e)}"
			)
			raise e
		
		except AssertionError as e:
			
			self.error(
				f"Failed to load config due to AssertionError"
				f"\nFile: {self.__path}"
				f"\nError: {str(e)}"
			)
			raise e
	
	def debug(self, s):
		self.__logger.debug(f"({self.__path.name}) {s}")
	
	def info(self, s):
		self.__logger.info(f"({self.__path.name}) {s}")
	
	def warning(self, s):
		self.__logger.warning(f"({self.__path.name}) {s}")
	
	def error(self, s):
		self.__logger.error(f"({self.__path.name}) {s}")
	
	@property
	def key(self) -> str:
		return str(self.__path)
		
	@property
	def path(self) -> Path:
		return self.__path
	
	@property
	def data(self) -> dict:
		return self.__data
	
	@property
	def dry_run(self) -> bool:
		return self.__dry_run
	
	@dry_run.setter
	def dry_run(self, b: bool):
		self.__dry_run = b
	
	@property
	def target_type(self) -> str:
		return self.__target_type
	
	@property
	def date_detection(self) -> str:
		return self.__date_detection
	
	@property
	def rotatable_paths(self) -> [Path]:
		return self.__rotatable_paths
	
	@property
	def minimum_items(self) -> int:
		return self.__minimum_items
	
	@property
	def maximum_items(self) -> int:
		return self.__maximum_items

	@property
	def maximum_age(self) -> int:
		return self.__maximum_age
