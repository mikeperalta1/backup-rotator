#!/usr/bin/env python3

"""

Mike's Backup Rotator

A simple script to help automatically rotate backup files

Copyright 2024 Mike Peralta; All rights reserved

Releasing to the public under the GNU GENERAL PUBLIC LICENSE v3 (See LICENSE file for more)

"""


from domain.Logger import Logger
from domain.config.Config import Config
from domain.Util import Util


import datetime
from pathlib import Path
import shutil
import yaml


class BackupRotator:
	
	def __init__(
			self,
			debug: bool = False,
			systemd: bool = False,
			write_to_syslog: bool = False
	):
		
		self.__logger = Logger(
			name=type(self).__name__,
			debug=debug,
			systemd=systemd,
			write_to_syslog=write_to_syslog,
		)
		self.__config_helper = Config(
			logger=self.__logger
		)
		
		self.__dry_run = False
		self.__configs = []
		self.__config_paths = []
		self.__calculated_actions = []
	
	def run(self, configs, dry_run: bool = False):
		
		self.info("Begin")
		
		self.__dry_run = dry_run
		self.__config_paths = configs
		
		self._consume_configs(self.__config_paths)
		
		# Rotate once per config
		for config_index in range(len(self.__configs)):
			
			#
			config = self.__configs[config_index]
			
			#
			self.info(f"Rotating for config {config_index + 1} of {len(self.__configs)} : {config['__path']}")
			self._do_rotate(config)
	
	@staticmethod
	def current_time():
		
		now = datetime.datetime.now()
		now_s = now.strftime("%b-%d-%Y %I:%M%p")
		return str(now_s)
	
	def debug(self, s):
		self.__logger.debug(s)
	
	def info(self, s):
		self.__logger.info(s)
	
	def warn(self, s):
		self.__logger.warning(s)
	
	def error(self, s):
		self.__logger.error(s)
	
	def _consume_configs(self, paths: [Path] = None):
		
		configs = self.__config_helper.gather_valid_configs(paths=paths)
		
		for config in configs:
			
			self._consume_config(path=config)
		
	def _consume_config(self, path: Path):
		
		self.debug(f"Consuming config: {path}")
		assert path.is_file(), (
			f"Cannot consume config file because it isn't a file: {path}"
		)
		
		# Open the file
		self.debug(f"Opening config file for consumption: {path}")
		f = open(str(path))
		if not f:
			raise Exception(f"Unable to open config file: {path}")
		
		# Parse
		config_raw = yaml.safe_load(f)
		assert config_raw is not None, (
			f"Config file seems to be null or empty: {path}"
		)
		
		# Add its own path
		config_raw["__path"] = path
		
		# Consume to internal
		self.__configs.append(config_raw)
		self.info(f"Consumed config from path: {path}")
	
	def _do_rotate(self, config):
		
		self._rotate_paths(config)
	
	def _rotate_paths(self, config):
		
		self.info("Begin rotating " + str(len(config["paths"])) + " paths")
		for path in config["paths"]:
			self._rotate_path(config, path)
	
	def _rotate_path(self, config, path: Path):
		
		assert path.is_dir(), (
			f"Path should be a directory: {path}"
		)
		
		self.info(
			f"Rotating path: {path}"
		)
		
		found_any_rotation_keys = False
		if "maximum-items" in config.keys():
			
			found_any_rotation_keys = True
			
			self._rotate_path_for_maximum_items(
				config=config,
				path=path,
				max_items=config["maximum-items"]
			)
		
		if "maximum-age" in config.keys():
			
			found_any_rotation_keys = True
			
			self._rotate_path_for_maximum_age(
				config=config,
				path=path,
				max_age_days=config["maximum-age"]
			)
		
		assert found_any_rotation_keys is True, (
			"Config needs one of the following keys: \"maximum-items\""
		)
	
	def _rotate_path_for_maximum_items(self, config, path: Path, max_items: int):
		
		assert path.is_dir(), f"Path should be a directory: {path}"
		
		self.info(f"Rotating path for a maximum of {max_items} items: {path}")
		
		children = self._gather_rotation_candidates(config, path)
		
		minimum_items = self._determine_minimum_items(config)
		
		# Do we need to rotate anything out?
		if len(children) < minimum_items:
			self.info(
				f"Path only has {len(children)} items"
				f", which does not meet the minimum threshold of {minimum_items} items."
				" Won't rotate this path."
			)
			return
		elif len(children) <= max_items:
			self.info(
				f"Path only has {len(children)} items"
				f", but needs more than {max_items} for rotation"
				"; Won't rotate this path."
			)
			return
		
		self.info(f"Found {len(children)} items to examine")
		
		#
		maximum_purge_count = len(children) - minimum_items
		purge_count = len(children) - max_items
		self.info(f"Want to purge {purge_count} items")
		
		if purge_count > maximum_purge_count:
			self.info(
				f"Reducing purge count from"
				f" {purge_count} to {maximum_purge_count} items"
				f" to respect minimum items setting ({minimum_items})"
			)
			purge_count = maximum_purge_count
		
		children_to_purge = []
		for purge_index in range(purge_count):
			
			#
			item_to_purge, item_ctime, item_age_seconds, item_age = self._pick_oldest_item(
				config, children
			)
			item_to_purge: Path
			
			children.remove(item_to_purge)
			
			self.info(
				f"Found next item to purge: ({purge_index + 1})"
				f" {item_to_purge.name}"
				f" ({item_age})"
			)
			
			#
			children_to_purge.append(item_to_purge)

		#
		self.info("Removing items")
		for child_to_purge in children_to_purge:
			
			child_to_purge: Path
			
			self.debug(f"Purging item: {child_to_purge.name}")
			
			self._remove_item(config, child_to_purge)
	
	def _rotate_path_for_maximum_age(self, config, path: Path, max_age_days: int):
		
		assert path.is_dir(), f"Path should be a directory: {path}"
		
		self.info(
			f"Rotating path for max age of {max_age_days} days: {path}"
		)
		
		children = self._gather_rotation_candidates(config, path)
		minimum_items = self._determine_minimum_items(config)
		
		# Do we need to rotate anything out?
		if len(children) < minimum_items:
			self.info(
				f"Path only has {len(children)} items"
				f", which does not meet the minimum threshold of {minimum_items} items."
				f" Won't rotate this path."
			)
			return
		
		self.info(
			f"Examining {len(children)} items for deletion"
		)
		children_to_delete = []
		for child in children:
			
			age_seconds = self._detect_item_age_seconds(config, child)
			age_days = self._detect_item_age_days(config, child)
			age_formatted = Util.seconds_to_time_string(age_seconds)
			
			if age_days > max_age_days:
				self.info(
					f"[Old enough    ] {child.name} ({age_formatted})"
				)
				children_to_delete.append(child)
			else:
				self.info(
					f"[Not Old enough] {child.name} ({age_formatted})"
				)
		
		if len(children_to_delete) > 0:
			
			self.info("Removing old items ...")
			
			for child_to_delete in children_to_delete:
				self._remove_item(config, child_to_delete)
			
		else:
			self.info("No old items to remove")
	
	def _gather_rotation_candidates(self, config, path: Path):
		
		self.debug(f"Begin gathering rotation candidates for: {path}")
		
		candidates: [Path] = []
		
		if "target-type" not in config.keys():
			raise Exception("Please provide the configuration key: target-type")
		
		for item_name in path.iterdir():
			
			item_path = path / item_name
			self.debug(f"Found an item: {item_name} ==> {item_path}")
			
			if config["target-type"] == "file":
				
				if not item_path.is_file():
					self.debug(f"Not a file; Skipping: {item_name}")
					continue
			
			elif config["target-type"] == "directory":
				
				if not item_path.is_dir():
					self.debug(f"Not a directory; Skipping: {item_name}")
					continue
				
			else:
				raise Exception(
					"Configuration key \"target-type\" must be \"file\" or \"directory\""
				)
			
			candidates.append(item_path)
		
		return candidates
	
	def _pick_oldest_item(self, config, items) -> (Path, float, float, str):
		
		best_item = None
		best_ctime = None
		for item in items:
			
			ctime = self._detect_item_date(config, item)
			if best_ctime is None or ctime < best_ctime:
				best_ctime = ctime
				best_item = item
		
		age_seconds = self._detect_item_age_seconds(config, best_item)
		age_string = Util.seconds_to_time_string(age_seconds)

		return best_item, best_ctime, age_seconds, age_string
	
	@staticmethod
	def _detect_item_date(config, item: Path) -> datetime.datetime:
		
		assert "date-detection" in config.keys(), (
			"Please provide config key: \"date-detection\""
		)
		detection = config["date-detection"]
		
		if detection == "file":
			ctime = datetime.datetime.fromtimestamp(
				item.stat().st_ctime, tz=datetime.timezone.utc
			)
		
		else:
			raise AssertionError(
				f"Invalid value for \"date-detection\""
				"; Should be one of [file]: {detection}"
			)
		
		return ctime
	
	def _detect_item_age_seconds(self, config, item: Path) -> float:
		
		now = datetime.datetime.now()
		
		ctime = self._detect_item_date(config, item)
		delta = now - ctime.now()
		
		return delta.seconds
	
	def _detect_item_age_days(self, config, item: Path) -> int:
		
		age_seconds = self._detect_item_age_seconds(config, item)
		age_days = int(age_seconds / 86400)

		return age_days
	
	def _remove_item(self, config, path: Path):
		
		if path.is_file():
			
			self._remove_file(config, path)
			
		elif path.is_dir():
			
			self._remove_directory(config, path)
			
		else:
			raise AssertionError(
				f"Don't know how to remove this item: {path}"
			)
	
	def _remove_file(self, config, file_path: Path):
		
		if not file_path.is_file():
			raise Exception(
				f"Tried to remove a file, but this path isn't a file: {file_path}"
			)
		
		if self.__dry_run:
			
			self.info(f"Won't purge file during global-level dry run: {file_path}")
			
		elif "dry-run" in config.keys() and config["dry-run"] is True:
			
			self.info(f"Won't purge file during config-level dry run: {file_path}")
			
		else:
			self.info(f"Purging file: {file_path}")
			file_path.unlink()
	
	def _remove_directory(self, config, dir_path: Path):
		
		if not dir_path.is_dir():
			raise Exception(
				f"Tried to remove a directory"
				f", but this path isn't a directory: {dir_path}"
			)
		
		if self.__dry_run:
			
			self.info(f"Won't purge directory during global-level dry run: {dir_path}")
			
		elif "dry-run" in config.keys() and config["dry-run"] is True:
			
			self.info(f"Won't purge directory during config-level dry run: {dir_path}")
			
		else:
			
			self.info(f"Purging directory: {dir_path}")
			shutil.rmtree(dir_path)
	
	def _determine_minimum_items(self, config) -> int:
		
		minimum_items = 0
		
		if "minimum-items" in config.keys():
			
			minimum_items = config["minimum-items"]
			
			self.info(
				f"Won't delete anything unless a minimum of {minimum_items} items were found"
			)
		
		else:
			self.info(
				"No value found for \"minimum-items\""
				"; Will not enforce minimum item constraint."
			)
		
		return minimum_items
