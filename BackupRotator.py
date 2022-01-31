#!/usr/bin/env python3

"""

Mike's Backup Rotator

A simple script to help automatically rotate backup files

Copyright 2019 Mike Peralta; All rights reserved

Released under the GNU GENERAL PUBLIC LICENSE v3 (See LICENSE file for more)

"""

import datetime
import os
import shutil
import sys
import syslog
import yaml


class BackupRotator:
	
	def __init__(self):
		
		self.__dry_run = False
		self.__configs = []
		self.__config_paths = []
		self.__calculated_actions = []
	
	def run(self, configs, dry_run: bool = False):
		
		self.log("Begin")
		
		self.__dry_run = dry_run
		self.__config_paths = configs
		
		self.consume_configs(self.__config_paths)
		
		# Rotate once per config
		for config_index in range(len(self.__configs)):
			
			#
			config = self.__configs[config_index]
			
			#
			self.log("Rotating for config " + str(config_index + 1) + " of " + str(len(self.__configs)), config["__path"])
			self.do_rotate(config)
	
	@staticmethod
	def current_time():
		
		now = datetime.datetime.now()
		now_s = now.strftime("%b-%d-%Y %I:%M%p")
		return str(now_s)
	
	def log(self, s, o=None):
		
		now = self.current_time()
		
		to_log = "[" + now + "][Backup Rotator] " + str(s)
		if o is not None:
			to_log += " " + str(o)
		
		syslog.syslog(to_log)
		
		print(to_log)
	
	def consume_configs(self, paths: list=None):
		
		assert paths is not None, "Config paths cannot be None"
		assert len(paths) > 0, "Must provide at least one config file path"
		
		# Use each config path
		for path in paths:
			
			# If this is a single path
			if os.path.isfile(path):
				self.consume_config(path)
			
			# If this is a directory
			elif os.path.isdir(path):
				
				# Iterate over each file inside
				for file_name in os.listdir(path):
					self.consume_config(os.path.join(path, file_name))
				
	def consume_config(self, path: str):
		
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
		self.log("Consumed config from path:", path)
	
	def do_rotate(self, config):
	
		self.rotate_paths(config)
	
	def rotate_paths(self, config):
		
		self.log("Begin rotating " + str(len(config["paths"])) + " paths")
		for path in config["paths"]:
			self.rotate_path(config, path)
	
	def rotate_path(self, config, path):
		
		self.log("Rotating path", path)
		
		if "maximum-items" not in config:
			raise Exception("Please provide config key: \"maximum-items\"")
		max_items = config["maximum-items"]
		
		if not os.path.isdir(path):
			raise Exception("Path should be a directory:" + str(path))
		
		children = self.gather_rotation_candidates(config, path)
		
		# Do we need to rotate anything out?
		if len(children) <= max_items:
			self.log(
				"Path only has " + str(len(children)) + " items,"
				+ " but needs more than " + str(max_items) + " for rotation"
				+ "; Won't rotate this path."
			)
			return
		
		#
		purge_count = len(children) - max_items
		self.log(
			"Need to purge " + str(purge_count) + " items"
		)
		
		for purge_index in range(purge_count):
			
			#
			item_to_purge = self.pick_item_to_purge(config, children)
			children.remove(item_to_purge)
			
			#
			if os.path.isfile(item_to_purge):
				self.remove_file(config, item_to_purge)
			elif os.path.isdir(item_to_purge):
				self.remove_directory(config, item_to_purge)
			else:
				raise Exception("Don't know how to remove this item: " + str(item_to_purge))
	
	@staticmethod
	def gather_rotation_candidates(config, path):
		
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
	
	@staticmethod
	def pick_item_to_purge(config, items):
		
		if "date-detection" not in config.keys():
			raise Exception("Please provide config key: \"date-detection\"")
		
		detection = config["date-detection"]
		best_item = None
		best_ctime = None
		for item in items:
			
			if detection == "file":
				ctime = os.path.getctime(item)
				if best_ctime is None or ctime < best_ctime:
					best_ctime = ctime
					best_item = item
			else:
				raise Exception("Invalid value for \"date-detection\": " + str(detection))
		
		return best_item
	
	def remove_file(self, config, file_path):
		
		if not os.path.isfile(file_path):
			raise Exception("Tried to remove a file, but this path isn't a file: " + str(file_path))
		
		if self.__dry_run:
			self.log("Won't purge file during global-level dry run: ", file_path)
		elif "dry-run" in config.keys() and config["dry-run"] is True:
			self.log("Won't purge file during config-level dry run: ", file_path)
		else:
			self.log("Purging file:", file_path)
			os.remove(file_path)
	
	def remove_directory(self, config, dir_path):
		
		if not os.path.isdir(dir_path):
			raise Exception("Tried to remove a directory, but this path isn't a directory: " + str(dir_path))
		
		if self.__dry_run:
			self.log("Won't purge directory during global-level dry run: ", dir_path)
		elif "dry-run" in config.keys() and config["dry-run"] is True:
			self.log("Won't purge directory during config-level dry run: ", dir_path)
		else:
			self.log("Purging directory:", dir_path)
			shutil.rmtree(dir_path)
