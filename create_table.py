from logging import basicConfig, getLogger, INFO

from constants import Constants
from connect_to_ledger import create_qldb_driver

logger = getLogger(__name__)
basicConfig(level=INFO)


def create_table(transaction_executor, table_name):
    """
    Create a table with the specified name using an Executor object.
    :type transaction_executor: :py:class:`pyqldb.execution.executor.Executor`
    :param transaction_executor: An Executor object allowing for execution of statements within a transaction.
    :type table_name: str
    :param table_name: Name of the table to create.
    :rtype: int
    :return: The number of changes to the database.
    """
    logger.info("Creating the '{}' table...".format(table_name))
    statement = 'CREATE TABLE {}'.format(table_name)
    cursor = transaction_executor.execute_statement(statement)
    logger.info('{} table created successfully.'.format(table_name))
    return len(list(cursor))


if __name__ == '__main__':
    """
    Create registrations, vehicles, owners, and licenses tables in a single transaction.
    """
    try:
        with create_qldb_driver() as qldb_driver:
            qldb_driver.execute_lambda(lambda x: create_table(x, Constants.SCENTITY_TABLE_NAME) and
                                   create_table(x, Constants.PERSON_TABLE_NAME) and
                                   create_table(x, Constants.JOINING_REQUEST_TABLE_NAME),
                                   lambda retry_attempt: logger.info('Retrying due to OCC conflict...'))
            logger.info('Tables created successfully.')
    except Exception:
        logger.exception('Errors creating tables.')
