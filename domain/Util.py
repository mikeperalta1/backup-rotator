

from domain.config.ConfigFile import ConfigFile


import datetime
from pathlib import Path


class Util:
	
	def __init__(self):
		pass
	
	@staticmethod
	def get_dir_files_recursive(path: Path) -> [Path]:
		
		files_paths = []
		for dir_path, dirs_names, filenames in path.walk():
			
			for file_name in filenames:
				
				file_path = dir_path / file_name
				
				files_paths.append(file_path)
		
		return files_paths
	
	@staticmethod
	def detect_item_creation_date(config: ConfigFile, item: Path) -> datetime.datetime:
		
		stat = None
		
		if config.date_detection == "file":
			
			# Try for the most accurate stat
			# First one that raises will just break the block, obv
			try:
				stat = item.stat().st_ctime
				# print("got ctime")
				stat = item.stat().st_mtime
				# print("got mtime")
				stat = item.stat().st_birthtime
				# print("got btime")
			except FileNotFoundError as e:
				raise e
			except AttributeError:
				pass
			
		else:
			raise AssertionError(
				f"Unsupported date-detection option: {config.date_detection}"
			)
		
		stamp = datetime.datetime.fromtimestamp(
			stat
		)
		# print("Stat:", stat)
		# print("Stamp:", stamp)
		# print(item.name, "==>", stamp)
		
		return stamp
	
	@staticmethod
	def detect_item_age_seconds(config: ConfigFile, item: Path) -> float:
		
		now = datetime.datetime.now()
		
		ctime = Util.detect_item_creation_date(config=config, item=item)
		delta = now - ctime
		seconds = delta.seconds
		
		# print(item.name, "==>", seconds, f"({ctime})")
		# print(">", "Now was:", now)
		# print(">", "ctime was:", ctime)
		# print(">", "Delta was:", delta)
		# print(">", "Seconds was:", delta.total_seconds())
		
		return delta.total_seconds()
	
	@staticmethod
	def detect_item_age_days(config: ConfigFile, item: Path) -> int:
		
		age_seconds = Util.detect_item_age_seconds(
			config=config, item=item
		)
		age_days = int(age_seconds / 86400)
		
		return age_days
	
	@staticmethod
	def seconds_to_time_string(seconds: float):
		
		if isinstance(seconds, float):
			pass
		elif isinstance(seconds, int):
			seconds = float(seconds)
		else:
			raise AssertionError("Seconds must be an int or float")
		
		# Map
		dt_map = {
			"year": 31536000.0,
			"month": 2592000.0,
			"week": 604800.0,
			"day": 86400.0,
			"hour": 3600.0,
			"minute": 60.0,
			"second": 1.0
		}
		
		s_parts = []
		for unit_label in dt_map.keys():
			
			unit_seconds = dt_map[unit_label]
			
			if seconds >= unit_seconds:
				
				unit_count = int(seconds / unit_seconds)
				
				unit_plural = "" if unit_count == 1 else "s"
				s_parts.append(
					f"{unit_count} {unit_label}{unit_plural}"
				)
				
				seconds -= unit_seconds * unit_count
		
		s = ", ".join(s_parts)
		
		return s
