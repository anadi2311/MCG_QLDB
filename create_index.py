# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# This code expects that you have AWS credentials setup per:
# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html
from logging import basicConfig, getLogger, INFO

from constants import Constants
from connect_to_ledger import create_qldb_driver

logger = getLogger(__name__)
basicConfig(level=INFO)


def create_index(transaction_executor, table_name, index_attribute):
    """
    Create an index for a particular table.
    :type transaction_executor: :py:class:`pyqldb.execution.executor.Executor`
    :param transaction_executor: An Executor object allowing for execution of statements within a transaction.
    :type table_name: str
    :param table_name: Name of the table to add indexes for.
    :type index_attribute: str
    :param index_attribute: Index to create on a single attribute.
    :rtype: int
    :return: The number of changes to the database.
    """
    logger.info("Creating index on '{}'...".format(index_attribute))
    statement = 'CREATE INDEX on {} ({})'.format(table_name, index_attribute)
    cursor = transaction_executor.execute_statement(statement)
    return len(list(cursor))


if __name__ == '__main__':
    """
    Create indexes on tables in a particular ledger.
    """
    logger.info('Creating indexes on all tables in a single transaction...')
    try:
        with create_qldb_driver() as driver:
            driver.execute_lambda(lambda x: create_index(x, Constants.PERSON_TABLE_NAME,
                                                          Constants.PERSON_ID_INDEX_NAME)
                                        and create_index(x, Constants.SCENTITY_TABLE_NAME,
                                                    Constants.SCENTITY_ID_INDEX_NAME)
                                        and create_index(x,Constants.JOINING_REQUEST_TABLE_NAME,
                                                    Constants.JOINING_REQUESTID_INDEX_NAME)
                                        and create_index(x, Constants.SUPERADMIN_REQUEST_TABLE_NAME,
                                                    Constants.SUPERADMIN_REQUEST_INDEX_NAME)
                                        and create_index(x, Constants.PRODUCT_TABLE_NAME,
                                                    Constants.PRODUCT_ID_INDEX_NAME)
                                        and create_index(x, Constants.PURCHASE_ORDER_TABLE_NAME, 
                                                    Constants.PURCHASE_ORDER_ID_INDEX_NAME),
                                  lambda retry_attempt: logger.info('Retrying due to OCC conflict...'))
            logger.info('Indexes created successfully.')
    except Exception:
        logger.exception('Unable to create indexes.')