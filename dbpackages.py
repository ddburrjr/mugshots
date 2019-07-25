import os
import mysql.connector
import logging
from dotenv import load_dotenv

this_dir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(this_dir, '.env'))

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class ConfigDB:
    HOST = os.getenv('HOST')
    PORT = os.getenv('PORT')
    USER = os.getenv('DBUSER')
    PASS = os.getenv('DBPASS')
    DATABASE = os.getenv('DATABASE')

    def config_dict(self):
        return {
            'user': f'{self.USER}',
            'password': f'{self.PASS}',
            'host': f'{self.HOST}',
            'port': self.PORT,
            'database': f'{self.DATABASE}',
        }

class SqlDB:
    _errors = []
    _prefix_msg = "-exec: [ {} ] "

    def __init__(self):
        self._config = ConfigDB()
        self._db, self._cursor = self._connect()

    def _connect(self):
        cfg = ConfigDB()
        config = cfg.config_dict()
        try:
            db = mysql.connector.connect(**config)
            cursor = db.cursor()
            msg = f"connect - {config}"
            logger.debug(self._prefix_msg.format(msg))
        except mysql.connector.Error as err:
            self.error(err, method='connect')
            db, cursor = None, None
        return db, cursor

    def counter(self, table):
        try:
            query = f"SELECT COUNT(*) FROM {table}"
            self._cursor.execute(query)
            logger.debug(self._prefix_msg.format(query))
            return self._cursor.fetchone()[0]
        except mysql.connector.Error as err:
            self.error(err, method='counter')

    def truncate(self, table):
        try:
            query = f"TRUNCATE TABLE {table}"
            _result = self._cursor.execute(query)
            logger.debug(self._prefix_msg.format(query))
            return _result
        except mysql.connector.Error as err:
            self.error(err, method='truncate')

    def search(self, query):
        try:
            self._cursor.execute(query)
            logger.debug(self._prefix_msg.format(query))
            return self._cursor.fetchone() is not None
        except mysql.connector.Error as err:
            self.error(err, method='search')

    def retrieve(self, query, multi=True):
        try:
            self._cursor.execute(query)
            logger.debug(self._prefix_msg.format(query))
            if multi:
                return self._cursor.fetchall()
            else:
                return self._cursor.fetchone()
        except mysql.connector.Error as err:
            self.error(err, method='retrieve')

    def insert(self, query, args, commit=True):
        try:
            self._cursor.execute(query, args)
            if commit is True:
                self._db.commit()
            msg = f"{query.split(' VALUES ')[0]}; args - {args}; commit={commit}"
            logger.debug(self._prefix_msg.format(msg))
        except mysql.connector.Error as err:
            self.error(err, method='insert')

    def process_all(self, commit=True):
        try:
            if commit is True:
                self._db.commit()
            else:
                self._db.rollback()
            msg = f"db.{'commit' if commit is True else 'rollback'}()"
            logger.debug(self._prefix_msg.format(msg))
        except mysql.connector.Error as err:
            self.error(err, method='process_all')

    def shutdown(self):
        try:
            self._cursor.close()
            self._db.close()
            msg = "db.close"
            logger.debug(self._prefix_msg.format(msg))
        except mysql.connector.Error as err:
            self.error(err, method='shutdown')

    def error(self, err_msg, method=None):
        err_packet = (method, err_msg)
        self._errors.append(err_packet)
        msg = f"method=[{method}] msg=[{err_msg}]"
        logger.error(msg)

    def error_type(self, err_type):
        return len([err for err in self._errors if err[0] == err_type])>0

    @property
    def have_errors(self):
        return len(self._errors) is not 0
