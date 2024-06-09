#!/usr/bin/env python3


from domain.BackupRotator import BackupRotator


import argparse


def main():
	
	parser = argparse.ArgumentParser(
		description="Mike's Backup Rotator. Helps automatically remove old backup files or folders."
	)
	
	parser.add_argument(
		"--debug", "--verbose",
		dest="debug",
		default=False,
		action="store_true",
		help="Verbose/Debug logging mode"
	)
	
	parser.add_argument(
		"--systemd",
		default=False,
		dest="systemd",
		action="store_true",
		help=(
			"Pass if this program will be spawned inside systemd"
			" or another system that already adds timestamps to log messages."
		)
	)
	
	parser.add_argument(
		"--syslog", "--write-to-syslog",
		default=False,
		dest="write_to_syslog",
		action="store_true",
		help=(
			"Pass if you'd like this program to write to syslog."
		)
	)
	
	parser.add_argument(
		"--config", "-c",
		dest="config_files",
		default=[],
		action="append",
		type=str,
		help="Specify a configuration file. Can be called multiple times."
	)
	parser.add_argument(
		"--dry-run", "-d",
		dest="dry_run",
		default=False,
		action="store_true",
		help="Only perform an analysis; Don't delete anything."
	)
	
	args = parser.parse_args()
	
	rotator = BackupRotator(
		debug=args.debug,
		systemd=args.systemd,
		write_to_syslog=args.write_to_syslog,
	)
	rotator.run(
		configs=args.config_files,
		dry_run=args.dry_run
	)
	

if __name__ == "__main__":
	main()

