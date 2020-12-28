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
        result = subprocess.run(['mysql -u %s -p%s --silent -e "SHOW DATABASES"' % (DB_USER, DB_PASS)], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            shell=True)
    except subprocess.CalledProcessError as e:
        LOG.debug('Failed to get database list. Error: {}'.format(e))
        return []

    return result.stdout.decode('UTF-8')
    

def backupDB(dbName):
    filePath = os.path.abspath(os.path.join(BACKUP_DIR, dbName))
    fileName = os.path.abspath(os.path.join(filePath, '{}_{}.sql'.format(getTimeStr(), dbName)))
    if not os.path.isdir(filePath):
        try:
            os.mkdir(filePath)
        except OSError as e:
            LOG.warning('Could not create directory: {} Error: {}'.format(filePath, e))
            return False

    with open(fileName,'w') as output:
        result = subprocess.run(['mysqldump', '--user='+DB_USER, '--password='+DB_PASS, dbName], stdout=output, capture_output=True, shell=True)
    
    if not result.check_returncode():
        return False
    return fileName

def deleteOld():
    oldestTime = time.time() - (KEEP_FOR_DAYS * 24 * 60 * 60)
    for root, _, files in os.walk(BACKUP_DIR):
        for file in files:
            path = os.path.abspath(os.path.join(root, file))
            if os.path.isfile(path) and os.path.splitext(path)[-1] == '.sql':
                if os.stat(path).st_mtime < oldestTime:
                    os.remove(path)

def main():
    if not os.path.isdir(BACKUP_DIR):
        LOG.critical('Backup directory not found: {}'.format(BACKUP_DIR))
        sys.exit(1)

    for db in getDatabases():
        if not db in EXCLUDED_DBS:
            result = backupDB(db)
            if result:
                LOG.info('Successfull Backup of {}'.format(result))
            else:
                LOG.warning('Failed to Backup {}'.format(db))
        else:
            LOG.debug('Skipping backup of excluded DB: {}'.format(db))

    deleteOld()


if __name__ == '__main__':
    main()