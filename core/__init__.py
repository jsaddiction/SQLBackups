import os
import sys
import logging
import shutil
from configparser import ConfigParser


APP_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
LOG_DIR = os.path.join(APP_ROOT, 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'SQLBackups.log')
EXAMPLE_CFG_FILE = os.path.join(APP_ROOT, 'settings.ini.example')
CFG_FILE = os.path.join(APP_ROOT, 'settings.ini')


def setup_config():
    if os.path.isfile(CFG_FILE):
        parser = ConfigParser()
        try:
            parser.read(CFG_FILE)
        except Exception as e:
            print('Could not read settings.ini Aborting ERROR: {}'.format(e))
            sys.exit(1)
        return parser
    else:
        print('Could not find the settings.ini file. Creating one for you.')
        try:
            shutil.copyfile(EXAMPLE_CFG_FILE, LOG_FILE)
        except Exception:
            print('Could not create your settings file. Create it manually.')
            sys.exit(1)
    
    print('Please configure settings.ini and rerun this script.')
    sys.exit(1)

def setup_log():
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    level = logging.getLevelName(CFG.get('LOGGING', 'level').upper())
    log = logging.getLogger('SQLBackups')
    log.setLevel(level)
    
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    log.addHandler(sh)

    if CFG.getboolean('LOGGING', 'to_file'):
        fh = logging.handlers.RotatingFileHandler(LOG_FILE, mode='a', maxBytes=1000000, backupCount=3)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        log.addHandler(fh)

    return log
    

CFG = setup_config()
LOG = setup_log()

DB_USER = CFG.get('SERVER', 'root_user')
DB_PASS = CFG.get('SERVER', 'root_password')
BACKUP_DIR = CFG.get('BACKUPS', 'backup_dir')
EXCLUDED_DBS = [x.strip() for x in CFG.get('DATABASE','excluded_databases').split(',')]
KEEP_FOR_DAYS = CFG.getint('BACKUPS','keep_days')