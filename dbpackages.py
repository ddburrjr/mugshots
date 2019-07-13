import mysql.connector
from configure import ConfigDB
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class SqlDB:
    _errors = []

    def __init__(self):
        self._config = ConfigDB()
        self._db, self._cursor = self.connect()

    def connect(self):
        cfg = self._config
        config = {
            'user': f'{cfg.USER}',
            'password': f'{cfg.PASS}',
            'host': f'{cfg.HOST}',
            'port': cfg.PORT,
            'database': f'{cfg.DATABASE}',
        }
        try:
            db = mysql.connector.connect(**config)
            cursor = db.cursor()
            logger.debug(f"connection established - {config}")
        except mysql.connector.Error as err:
            self.error(err, method='connect')
            db, cursor = None, None
        return db, cursor

    def search(self, query):
        try:
            self._cursor.execute(query)
            logger.debug(f"executing - {query}")
            return self._cursor.fetchone() is not None
        except mysql.connector.Error as err:
            self.error(err, method='search')

    def retrieve(self, query):
        try:
            self._cursor.execute(query)
            logger.debug(f"executing - {query}")
            return self._cursor.fetchall()
        except mysql.connector.Error as err:
            self.error(err, method='retrieve')

    def insert(self, query, args, commit=True):
        try:
            self._cursor.execute(query, args)
            if commit is True:
                self._db.commit()
            logger.debug(f"executing - {query.split(' VALUES ')[0]}; args - {args}; commit={commit}")
        except mysql.connector.Error as err:
            self.error(err, method='insert')

    def process_all(self, commit=True):
        try:
            if commit is True:
                self._db.commit()
            else:
                self._db.rollback()
            logger.debug(f"executing - db.{'commit' if commit is True else 'rollback'}()")
        except mysql.connector.Error as err:
            self.error(err, method='process_all')

    def shutdown(self):
        try:
            self._cursor.close()
            self._db.close()
            logger.debug("db closed")
        except mysql.connector.Error as err:
            self.error(err, method='shutdown')

    def error(self, err_msg, method=None):
        err_packet = (method, err_msg)
        self._errors.append(err_packet)
        logger.error(f"method=[{method}] msg=[{err_msg}]")

    def error_type(self, err_type):
        return len([err for err in self._errors if err[0] == err_type])>0

    @property
    def have_errors(self):
        return len(self._errors) is not 0
