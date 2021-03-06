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
from sampledata.input_data import SampleData
from constants import Constants
from sampledata.sample_data import convert_object_to_ion,  get_document_ids_from_dml_results
from connect_to_ledger import create_qldb_driver

logger = getLogger(__name__)
basicConfig(level=INFO)


def update_person_id(document_id):
    """
    Update the PersonId value for DriversLicense records and the PrimaryOwner value for VehicleRegistration records.
    :type document_ids: list
    :param document_ids: List of document IDs.
    :rtype: list
    :return: Lists of updated DriversLicense records and updated VehicleRegistration records.
    """
    new_sc_entity = SampleData.SCENTITY.copy()
   
    new_sc_entity[0]["PersonIds"].append(document_id)
    # logger.info(new_sc_entity)
    return new_sc_entity

def insert_documents(transaction_executor, table_name, documents):
    """
    Insert the given list of documents into a table in a single transaction.
    :type transaction_executor: :py:class:`pyqldb.execution.executor.Executor`
    :param transaction_executor: An Executor object allowing for execution of statements within a transaction.
    :type table_name: str
    :param table_name: Name of the table to insert documents into.
    :type documents: list
    :param documents: List of documents to insert.
    :rtype: list
    :return: List of documents IDs for the newly inserted documents.
    """
    # logger.info('Inserting some documents in the {} table...'.format(table_name))
    statement = 'INSERT INTO {} ?'.format(table_name)
    cursor = transaction_executor.execute_statement(statement, convert_object_to_ion(documents))
    list_of_document_ids = get_document_ids_from_dml_results(cursor)
    
    return list_of_document_ids


def update_and_insert_documents(transaction_executor):
    """
    Handle the insertion of documents and updating PersonIds all in a single transaction.
    :type transaction_executor: :py:class:`pyqldb.execution.executor.Executor`
    :param transaction_executor: An Executor object allowing for execution of statements within a transaction.
    """
    admin_id = insert_documents(transaction_executor, Constants.PERSON_TABLE_NAME, SampleData.PERSON)

    logger.info("Updating PersonIds for 'SCENTITY' ...")
    new_sc_entity = update_person_id(admin_id[0])

    mcg_id = insert_documents(transaction_executor, Constants.SCENTITY_TABLE_NAME, new_sc_entity)

    return admin_id[0], mcg_id[0]
    
    

if __name__ == '__main__':
    """
    Insert documents into a table in a QLDB ledger.
    """
    try:
        with create_qldb_driver() as driver:
            # An INSERT statement creates the initial revision of a document with a version number of zero.
            # QLDB also assigns a unique document identifier in GUID format as part of the metadata.
            driver.execute_lambda(lambda executor: update_and_insert_documents(executor),
                                  lambda retry_attempt: logger.info('Retrying due to OCC conflict...'))
            logger.info('Documents inserted successfully!')
    except Exception:
        logger.exception('Error inserting or updating documents.')
