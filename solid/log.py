
import logging
import logging.config
import time

from solid import mongo

def init_log():
    LOGGING = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'verbose': {
                    'format': '%(asctime)s - %(levelname)s - %(name)s - %(filename)s:%(lineno)d : %(message)s'
                    },
                },

            'handlers':
            {
                'console': {
                    'level': 'DEBUG',
                    'class': 'logging.StreamHandler',
                    'formatter': 'verbose'
                    },
                },
            'root': {
                'handlers': ['console'],
                'level': 'DEBUG',
                },
            }

    logging.config.dictConfig(LOGGING)
