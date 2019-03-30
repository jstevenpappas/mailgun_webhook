from __future__ import with_statement
from contextlib import contextmanager
from psycopg2 import pool
import properties
import logging
import logging.handlers
import logging.config



logging.basicConfig(filename='/opt/python/log/webhook.log', level=logging.DEBUG, format='%(asctime)s %(message)s')
logger = logging.getLogger()

DBNAME = properties.RDS_LUIGI_DB_NAME
DBUSER = properties.RDS_LUIGI_USERNAME
DBPASS = properties.RDS_LUIGI_PASSWORD
DBHOST = properties.RDS_LUIGI_HOSTNAME
DBPORT = properties.RDS_LUIGI_PORT
CONNMN = 10
CONNMX = 30

"""
    To be imported only once by main thread
    from ConnectionPoolFactory import threaded_connection_pool

    1) pass threaded_connection_pool to threads created
    2) in finally block of main(), call threaded_connection_pool.closeall()

"""


class ConnectionPoolFactory:

    threadedpool = pool.ThreadedConnectionPool(CONNMN,
                                                        CONNMX,
                                                        database=DBNAME,
                                                        user=DBUSER,
                                                        password=DBPASS,
                                                        host=DBHOST,
                                                        port=DBPORT)

    def __init__(self):
        self.name = "ConnectionPoolFactory"
        logger.info('ConnectionPoolFactory  INSTANTIATED!!!')

    @contextmanager
    def getCursor(self):
        ret_pool_conn = ConnectionPoolFactory.threadedpool.getconn()
        try:
            yield ret_pool_conn.cursor()
            ret_pool_conn.commit()
        except Exception as detail:
            logger.error('ConnectionPoolFactory: Exception during getCursor() method: Exception: TYPE=%s   MSG=%s', type(detail).__name__, detail.message)
        finally:
            ConnectionPoolFactory.threadedpool.putconn(ret_pool_conn)


def close_and_cleanup():
    logger.info('<Before ConnectionPool.closeall()>:  Closed state of Connections of threadedpool: {con}'.format(con=ConnectionPoolFactory.threadedpool.closed))
    ConnectionPoolFactory.threadedpool.closeall()
    logger.info('<After ConnectionPool.closeall()>:  Closed state of Connections of threadedpool: {con}'.format(con=ConnectionPoolFactory.threadedpool.closed))


threaded_connection_pool = ConnectionPoolFactory()
