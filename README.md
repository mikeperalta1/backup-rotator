
# Mike's Backup Rotator

This program functions somewhat similarly to a log rotator. It's purpose is to rotate backup files, so your disk doesn't fill up. 

Suppose you have a third party backup program regularly dropping backup files into some directory. You could use this program to limit the number of files that remain in the directory at any given time.

# Requirements

* Python 3
* PyYAML (```pip3 install pyaml```)

# How to Execute

The script is invoked with Python3, like so:

```
python3 backup-rotator
```

Alternatively, if your *env* program is setup correctly for python3, you may simply execute this script as-is:

```
/path/to/backup-rotator
```

## Command Line Arguments

This program won't do much without command line arguments. Primarily, it needs to know the location of at least one configuration file or directory.

### --dry-run

Tells the program to run without making any changes. Instead, it will merely list the changes (deletions) it would have made.

### --config < path >

Specifies a path to a configuration file or directory. If a directory is specified, all files in the directory will be used as configuration files.

## Configuration File Format

Configuration files are written in [YAML](https://yaml.org/) format. Supported keys are as follows:

### dry-run

If this is set to *true*, this particular configuration file won't cause any changes to disk (see *--dry-run* command line argument above)

### target-type <file | directory>

The target type can be set to either *file* or *directory*, and specifies what we will be rotating.

* When *file*, only files inside the specified paths are considered for rotation. This is appropriate for rotating backups that drop single files into the same destination directory. For example, a directory structure that looks like this:
    * /my/backup/path/2019-07-01-My-Backup.tar.gz
    * /my/backup/path/2019-07-02-My-Backup.tar.gz
    * /my/backup/path/2019-07-03-My-Backup.tar.gz
    * /my/backup/path/2019-07-04-My-Backup.tar.gz

* When *directory*, only directories inside the specified paths are considered for rotation. This is appropriate for rotating backups that are saved as whole directories, inside an outer destination directory. For example, a directory structure that looks like this:
    * /my/backup/path/2019-07-01-My-Backup-Directory/
    * /my/backup/path/2019-07-02-My-Backup-Directory/
    * /my/backup/path/2019-07-03-My-Backup-Directory/
    * /my/backup/path/2019-07-04-My-Backup-Directory/

*In both examples above, the main configured backup path is **/my/backup/path***

### date-detection < file >

Specifies the method used when attempting to determine how old a backup file/dir is.

* When *file*, the files creation stamp is used

Currently, only *file* is supported

### maximum-items < INTEGER >

Specifies the maximum number of backup files/dirs that are allowed in a path before rotating will happen. Should be an integer.

For example, when the *maximum-items* value is set to 5, and *target-type* is *file*, the program will not rotate any files until there are at least 5 in the target directory.

### paths < Array of Paths >

Specifies all paths that should be scanned with these settings. You may specify one or more paths

## Sample Configuration File

*sample-config.yaml*
```
dry-run: true

target-type: file

date-detection: file

maximum-items: 5

paths:
 - /path/to/backup/dir1/
 - /path/to/backup/dir2/
 - /path/to/backup/dir3/
 - /path/to/backup/dir4/
```




