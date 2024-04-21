#!/usr/bin/env python3

"""

Mike's Backup Rotator

A simple script to help automatically rotate backup files

Copyright 2023 Mike Peralta; All rights reserved

Releasing to the public under the GNU GENERAL PUBLIC LICENSE v3 (See LICENSE file for more)

"""


from domain.Logger import Logger
from domain.Config import Config


import datetime
import os
# import pprint
import shutil
import sys
import time
import yaml


class BackupRotator:
	
	def __init__(self, debug:bool = False):
		
		self.__logger = Logger(name=type(self).__name__, debug=debug)
		self.__config_helper = Config(logger=self.__logger)
		
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
		self.__logger.warn(s)
	def error(self, s):
		self.__logger.error(s)
	
	def _consume_configs(self, paths: list=None):
		
		configs = self.__config_helper.gather_valid_configs(paths=paths)
		for config in configs:
			self._consume_config(path=config)
		
	def _consume_config(self, path: str):
		
		# Open the file
		f = open(path)
		if not f:
			raise Exception("Unable to open config file: " + path)
		
		# Parse
		config = yaml.safe_load(f)
		
		# Add its own path
		config["__path"] = path
		
		# Consume to internal
		self.__configs.append(config)
		self.info(f"Consumed config from path: {path}")
	
	def _do_rotate(self, config):
	
		self._rotate_paths(config)
	
	def _rotate_paths(self, config):
		
		self.info("Begin rotating " + str(len(config["paths"])) + " paths")
		for path in config["paths"]:
			self._rotate_path(config, path)
	
	def _rotate_path(self, config, path):
		
		assert os.path.isdir(path), "Path should be a directory: {}".format(path)
		
		self.info("Rotating path: {}".format(path))
		
		found_any_rotation_keys = False
		if "maximum-items" in config.keys():
			found_any_rotation_keys = True
			self._rotate_path_for_maximum_items(config=config, path=path, max_items=config["maximum-items"])
		if "maximum-age" in config.keys():
			found_any_rotation_keys = True
			self._rotate_path_for_maximum_age(config=config, path=path, max_age_days=config["maximum-age"])

		assert found_any_rotation_keys is True, \
			"Config needs one of the following keys: \"maximum-items\""

	def _rotate_path_for_maximum_items(self, config, path: str, max_items: int):
		
		assert os.path.isdir(path), "Path should be a directory: {}".format(path)
		
		self.info("Rotating path for a maximum of {} items: {}".format(
			max_items, path
		))
		
		children = self._gather_rotation_candidates(config, path)
		
		minimum_items = self._determine_minimum_items(config)
		
		# Do we need to rotate anything out?
		if len(children) < minimum_items:
			self.info("Path only has {} items, which does not meet the minimum threshold of {} items. Won't rotate this path.".format(
				len(children), minimum_items
			))
			return
		elif len(children) <= max_items:
			self.info("Path only has {} items, but needs more than {} for rotation; Won't rotate this path.".format(
				len(children), max_items
			))
			return
		self.info("Found {} items to examine".format(len(children)))
		
		#
		maximum_purge_count = len(children) - minimum_items
		purge_count = len(children) - max_items
		self.info("Want to purge {} items".format(purge_count))

		if purge_count > maximum_purge_count:
			self.info("Reducing purge count from {} to {} items to respect minimum items setting ({})".format(
				purge_count, maximum_purge_count, minimum_items
			))
			purge_count = maximum_purge_count
		
		children_to_purge = []
		for purge_index in range(purge_count):
			
			#
			item_to_purge, item_ctime, item_age_seconds, item_age = self._pick_oldest_item(config, children)
			children.remove(item_to_purge)
			self.info("Found next item to purge: ({}) {} ({})".format(
				purge_index + 1,
				os.path.basename(item_to_purge),
				item_age
			))
			
			#
			children_to_purge.append(item_to_purge)

		#
		self.info("Removing items")
		for child_to_purge in children_to_purge:
			child_basename = os.path.basename(child_to_purge)
			self._remove_item(config, child_to_purge)
	
	def _rotate_path_for_maximum_age(self, config, path: str, max_age_days: int):
		
		assert os.path.isdir(path), "Path should be a directory: {}".format(path)
		
		self.info("Rotating path for max age of {} days: {}".format(max_age_days, path))
		
		children = self._gather_rotation_candidates(config, path)
		minimum_items = self._determine_minimum_items(config)
		
		# Do we need to rotate anything out?
		if len(children) < minimum_items:
			self.info("Path only has {} items, which does not meet the minimum threshold of {} items. Won't rotate this path.".format(
				len(children), minimum_items
			))
			return
		
		self.info("Examining {} items for deletion".format(len(children)))
		children_to_delete = []
		for child in children:
			
			age_seconds = self._detect_item_age_seconds(config, child)
			age_days = self._detect_item_age_days(config, child)
			age_formatted = self.seconds_to_time_string(age_seconds)
			child_basename = os.path.basename(child)
			
			if age_days > max_age_days:
				self.info("[Old enough    ] {} ({})".format(
					child_basename, age_formatted
				))
				children_to_delete.append(child)
			else:
				self.info("[Not Old enough] {} ({})".format(
					child_basename, age_formatted
				))
		
		if len(children_to_delete) > 0:
			self.info("Removing old items ...")
			for child_to_delete in children_to_delete:
				basename = os.path.basename(child_to_delete)
				self._remove_item(config, child_to_delete)
		else:
			self.info("No old items to remove")
		
		
	@staticmethod
	def _gather_rotation_candidates(config, path):
		
		candidates = []
		
		if "target-type" not in config.keys():
			raise Exception("Please provide the configuration key: target-type")
		
		for item_name in os.listdir(path):
			
			item_path = os.path.join(path, item_name)
			
			if config["target-type"] == "file":
				if not os.path.isfile(item_path):
					continue
			elif config["target-type"] == "directory":
				if not os.path.isdir(item_path):
					continue
			else:
				raise Exception("Configuration key \"target-type\" must be \"file\" or \"directory\"")
			
			candidates.append(item_path)
		
		return candidates
	
	def _pick_oldest_item(self, config, items):
		
		best_item = None
		best_ctime = None
		for item in items:
			
			ctime = self._detect_item_date(config, item)
			if best_ctime is None or ctime < best_ctime:
				best_ctime = ctime
				best_item = item
		
		age_seconds = self._detect_item_age_seconds(config, best_item)
		age_string = self.seconds_to_time_string(age_seconds)

		return best_item, best_ctime, age_seconds, age_string
	
	@staticmethod
	def _detect_item_date(config, item):
		
		assert "date-detection" in config.keys(), "Please provide config key: \"date-detection\""
		detection = config["date-detection"]

		if detection == "file":
			ctime = os.path.getctime(item)
		else:
			raise AssertionError(f"Invalid value for \"date-detection\"; Should be one of [file]: {detection}")

		return ctime

	def _detect_item_age_seconds(self, config, item):
		
		now = time.time()
		ctime = self._detect_item_date(config, item)
		delta = now - ctime
		
		return delta

	def _detect_item_age_days(self, config, item):
		
		age_seconds = self._detect_item_age_seconds(config, item)
		age_days = int(age_seconds / 86400)

		return age_days

	def seconds_to_time_string(self, seconds: float):
		
		if isinstance(seconds, float):
			pass
		elif isinstance(seconds, int):
			seconds = float * 1.0
		else:
			raise AssertionError("Seconds must be an int or float")
		
		# Map
		map = {
			"year": 31536000.0,
			"month": 2592000.0,
			"week": 604800.0,
			"day": 86400.0,
			"hour": 3600.0,
			"minute": 60.0,
			"second": 1.0
		}
		
		s_parts = []
		for unit_label in map.keys():
			unit_seconds = map[unit_label]
			if seconds >= unit_seconds:
				unit_count = int(seconds / unit_seconds)
				s_parts.append("{} {}{}".format(
					unit_count, unit_label,
					"" if unit_count == 1 else "s"
				))
				seconds -= unit_seconds * unit_count
		
		s = ", ".join(s_parts)
		
		return s

	def _remove_item(self, config, path):
		
		if os.path.isfile(path):
			self._remove_file(config, path)
		elif os.path.isdir(path):
			self._remove_directory(config, path)
		else:
			raise AssertionError("Don't know how to remove this item: {}".format(path))

	def _remove_file(self, config, file_path):
		
		if not os.path.isfile(file_path):
			raise Exception("Tried to remove a file, but this path isn't a file: " + str(file_path))
		
		if self.__dry_run:
			self.info(f"Won't purge file during global-level dry run: {file_path}")
		elif "dry-run" in config.keys() and config["dry-run"] is True:
			self.info(f"Won't purge file during config-level dry run: {file_path}")
		else:
			self.info(f"Purging file: {file_path}")
			os.remove(file_path)
	
	def _remove_directory(self, config, dir_path):
		
		if not os.path.isdir(dir_path):
			raise Exception("Tried to remove a directory, but this path isn't a directory: " + str(dir_path))
		
		if self.__dry_run:
			self.info(f"Won't purge directory during global-level dry run: {dir_path}")
		elif "dry-run" in config.keys() and config["dry-run"] is True:
			self.info(f"Won't purge directory during config-level dry run: {dir_path}")
		else:
			self.info(f"Purging directory: {dir_path}")
			shutil.rmtree(dir_path)

	
	def _determine_minimum_items(self, config):
		
		minimum_items = 0
		
		if "minimum-items" in config.keys():
			minimum_items = config["minimum-items"]
			self.info("Won't delete anything unless a minimum of {} items were found".format(minimum_items))
		else:
			self.info("No value found for \"minimum-items\"; Will not enforce minimum item constraint.")
		
		return minimum_items
