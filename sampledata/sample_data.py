from datetime import datetime
from decimal import Decimal
from logging import basicConfig, getLogger, INFO

from amazon.ion.simple_types import IonPyBool, IonPyBytes, IonPyDecimal, IonPyDict, IonPyFloat, IonPyInt, IonPyList, \
    IonPyNull, IonPySymbol, IonPyText, IonPyTimestamp
from amazon.ion.simpleion import dumps, loads

logger = getLogger(__name__)
basicConfig(level=INFO)
IonValue = (IonPyBool, IonPyBytes, IonPyDecimal, IonPyDict, IonPyFloat, IonPyInt, IonPyList, IonPyNull, IonPySymbol,
            IonPyText, IonPyTimestamp)


class SampleData:
    """
    Sample domain objects for use throughout this tutorial.
    """
    PERSON = [
        {
            'EmployeeId': 'JOHNDOE123',
            'FirstName': 'John',
            'LastName': 'Doe',
            'isSuperAdmin': False,
            'isAdmin' : False,
             'PersonContact': {
                "Email": "John.Doe@ubc.ca",
                'Phone' : "8888888888",
                'Address': 'UBC Blockchain'
        }},
        {
            'EmployeeId': 'MARRYDOE123',
            'FirstName': 'Marry',
            'LastName': 'Doe',
            'isSuperAdmin':False,
            'isAdmin' : False,
             'PersonContact': {
                "Email": "Marry.Doe@ubc.ca",
                'Phone' : "1111111111",
                'Address': 'UBC Blockchain'
        }},
        {
            'EmployeeId': 'AdminMCG123',
            'FirstName': 'UBC',
            'LastName': 'CIC',
            'isSuperAdmin' : True,
            'isAdmin' : False,
             'PersonContact': {
                "Email": "UBC.CIC@ubc.ca",
                'Phone' : "9999999999",
                'Address': 'UBC CIC'
        }}
        
    ]
    
    SCENTITY = [
            {
            "ScEntityName" : " Pfizer",
            "ScEntityLocation" : "123 ABC St, Texas, USA",
            "ScEntityContact": "1234567890",
            "ScEntityIdentificationCode" : "JXkY1234",    
            "ScEntityIdentificationCodeType" : "BusinessNumber",
            "isApprovedByAdmin": False,
            "ScentityTypeCode": 2,
            "PersonIds": [],
            "JoiningRequests" : [],
            }
        ]


def convert_object_to_ion(py_object):
    """
    Convert a Python object into an Ion object.
    :type py_object: object
    :param py_object: The object to convert.
    :rtype: :py:class:`amazon.ion.simple_types.IonPyValue`
    :return: The converted Ion object.
    """
    ion_object = loads(dumps(py_object))
    return ion_object


def to_ion_struct(key, value):
    """
    Convert the given key and value into an Ion struct.
    :type key: str
    :param key: The key which serves as an unique identifier.
    :type value: str
    :param value: The value associated with a given key.
    :rtype: :py:class:`amazon.ion.simple_types.IonPyDict`
    :return: The Ion dictionary object.
    """
    ion_struct = dict()
    ion_struct[key] = value
    return loads(str(ion_struct))


def get_document_ids(transaction_executor, table_name, field, value):
    """
    Gets the document IDs from the given table.
    :type transaction_executor: :py:class:`pyqldb.execution.executor.Executor`
    :param transaction_executor: An Executor object allowing for execution of statements within a transaction.
    :type table_name: str
    :param table_name: The table name to query.
    :type field: str
    :param field: A field to query.
    :type value: str
    :param value: The key of the given field.
    :rtype: list
    :return: A list of document IDs.
    """
    query = "SELECT id FROM {} AS t BY id WHERE t.{} = '{}'".format(table_name, field, value)
    cursor = transaction_executor.execute_statement(query)
    list_of_ids = map(lambda table: table.get('id'), cursor)
    return list_of_ids


def get_document_ids_from_dml_results(result):
    """
    Return a list of modified document IDs as strings from DML results.
    :type result: :py:class:`pyqldb.cursor.stream_cursor.StreamCursor`
    :param: result: The result set from DML operation.
    :rtype: list
    :return: List of document IDs.
    """
    ret_val = list(map(lambda x: x.get('documentId'), result))
    return ret_val


def print_result(cursor):
    """
    Pretty print the result set. Returns the number of documents in the result set.
    :type cursor: :py:class:`pyqldb.cursor.stream_cursor.StreamCursor`/
                  :py:class:`pyqldb.cursor.buffered_cursor.BufferedCursor`
    :param cursor: An instance of the StreamCursor or BufferedCursor class.
    :rtype: int
    :return: Number of documents in the result set.
    """
    result_counter = 0
    for row in cursor:
        # Each row would be in Ion format.
        logger.info(dumps(row, binary=False, indent='  ', omit_version_marker=True))
        result_counter += 1
    return result_counter
