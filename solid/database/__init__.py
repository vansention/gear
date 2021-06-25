

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


import settings


class SessionContext(object):

    def __init__(self,Session):
        self.Session = Session

    def __enter__(self):
        
        self.session = self.Session()
        return self.session

    def __exit__(self,exc_type, exc_value, trace):
        #logging.debug(f'{exc_type}, {exc_value}, {trace}')
        #self.session.commit()
        self.session.close()


class SqlalchemyConfig(object):

    def __init__(self,db_url,
        encoding='utf-8',
        echo=False,
        convert_unicode=True,
        pool_size=16,
        max_overflow=0,
        pool_recycle=3600):
    
        self.engine = create_engine(settings.DB_URL,
            encoding='utf-8',
            echo=False,
            convert_unicode=True,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=0,
            pool_recycle=3600)
        self.Model = declarative_base(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self):
        return SessionContext(self.Session)





