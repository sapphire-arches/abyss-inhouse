import logging
import logging.config
from configparser import ConfigParser

#===============================================================================
# Config loading
#===============================================================================
logging.basicConfig(level=logging.DEBUG)

config = ConfigParser()
config.read([
    '/config/bot.config',
    '/config/override.config',
])


#===============================================================================
# Logger setup
#===============================================================================
LOG_LEVELS = {
    "CRITICAL": 50,
    "ERROR": 40,
    "WARNING": 30,
    "INFO": 20,
    "DEBUG": 10,
    "NOTSET": 0,
}

def setup_logging(cfg):
    LOGMOD = 'logging.mod.'
    base_level = LOG_LEVELS[cfg.get('logging', 'root_level')]
    fmt = cfg.get('logging', 'format', raw=True)

    # Initialize loggers with the root configuration
    loggers = {
        '': {
            'handlers': ['default'],
            'level': base_level,
            'propagate': False
        }
    }

    for section in cfg.sections():
        if not section.startswith(LOGMOD):
            continue
        module = section[len(LOGMOD):]
        logging.info(f'Load level for module {module}')
        loggers[module] = {
            'level': LOG_LEVELS[cfg[section]['level']],
            'handlers': ['default'],
            'propagate': False
        }

    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': True,
        'loggers': loggers,
        'handlers': {
            'default': {
                'level': 'DEBUG',
                'formatter': 'default',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
            }
        },
        'formatters': {
            'default': {
                'format': fmt
            }
        }
    })

setup_logging(config)

