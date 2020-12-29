import os
import sys
import time
import subprocess

from core import (
    LOG,
    DB_USER,
    DB_PASS,
    BACKUP_DIR,
    KEEP_FOR_DAYS,
    EXCLUDED_DBS,
)

def getTimeStr():
    return time.strftime('%d-%b-%Y_%H:%M:%S')

def getDatabases():
    try:
        result = subprocess.run(['mysql', '-u'+DB_USER, '-p'+DB_PASS, '--silent', '-e', 'SHOW DATABASES;'], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        LOG.debug('Failed to get database list. Error: {}'.format(e))
        return []

    if not result.returncode == 0:
        LOG.debug('Failed to get database list. Error: {}'.format(result))
        return []

    dbs = result.stdout.decode('UTF-8').splitlines()
    LOG.debug('Databases found: {}'.format(dbs))

    return dbs

def backupDB(dbName):
    filePath = os.path.abspath(os.path.join(BACKUP_DIR, dbName))
    fileName = os.path.abspath(os.path.join(filePath, '{}_{}.sql'.format(getTimeStr(), dbName)))
    if not os.path.isdir(filePath):
        try:
            os.mkdir(filePath)
        except OSError as e:
            LOG.warning('Could not create directory: {} Error: {}'.format(filePath, e))
            return False

    LOG.debug('Attempting to dump {} to {}'.format(dbName, fileName))
    with open(fileName,'w') as output:
        try:
            result = subprocess.run(['mysqldump', '--force', '--opt', '--skip-lock-tables', '--user='+DB_USER, '--password='+DB_PASS, dbName],
                stdin=subprocess.PIPE,
                stdout=output)
        except subprocess.CalledProcessError as e:
            LOG.debug('Failed to backup {} ERROR: {}'.format(dbName, e))
            return False
    if not result.returncode == 0:
        LOG.debug('Failed to backup {} Error: {}'.format(dbName, result))
        return False

    return fileName

def deleteOld():
    oldestTime = time.time() - ((KEEP_FOR_DAYS * 24 * 60 * 60) + 10)
    for root, _, files in os.walk(BACKUP_DIR):
        for file in files:
            path = os.path.abspath(os.path.join(root, file))
            if os.path.isfile(path) and os.path.splitext(path)[-1] == '.sql':
                if os.stat(path).st_mtime < oldestTime or os.stat(path).st_size == 0:
                    LOG.debug('Deleting old backup {}'.format(os.path.basename(path)))
                    os.remove(path)

def main():
    if not os.path.isdir(BACKUP_DIR):
        LOG.critical('Backup directory not found: {}'.format(BACKUP_DIR))
        sys.exit(1)

    for db in getDatabases():
        if not db in EXCLUDED_DBS:
            result = backupDB(db)
            if result:
                LOG.info('Backed up {}'.format(db))
            else:
                LOG.warning('Failed to Backup {}'.format(db))
        else:
            LOG.debug('Skipping backup of excluded DB: {}'.format(db))

    deleteOld()


if __name__ == '__main__':
    main()
