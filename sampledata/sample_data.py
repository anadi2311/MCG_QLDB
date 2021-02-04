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
            'isAdmin' : True,
             'PersonContact': {
                "Email": "UBC.CIC@ubc.ca",
                'Phone' : "9999999999",
                'Address': 'UBC CIC'
        }}
        
    ]
    
    SCENTITY = [
            {
            "ScEntityName" : " Pfizer",
            "ScEntityContact":{
                "Email":"pfizer@pfizer.com",
                "Address":"123 ABC St, Texas, USA",
                "Phone": "1234567890"
            },    
            "ScEntityIdentificationCode" : "JXkY1234",    
            "ScEntityIdentificationCodeType" : "BusinessNumber",
            "isApprovedBySuperAdmin": False,
            "ScEntityTypeCode": "2",
            "PersonIds": [],
            "JoiningRequests" : [],
            },
            {
            "ScEntityName" : "MCG",
            "ScEntityContact":{
                "Email":"MCG@mcg.com",
                "Address":"123 ABC St, Texas, USA",
                "Phone": "1234567890"
            },    
            "ScEntityIdentificationCode" : "admin1234",    
            "ScEntityIdentificationCodeType" : "BusinessNumber",
            "isApprovedBySuperAdmin": True,
            "ScEntityTypeCode": "1",
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
    print(query)
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

def get_value_from_documentid(transaction_executor, table_name, document_id, field):
    # print("SELECT t.{} FROM {} as t BY d_id WHERE d_id = {}".format(field, table_name,document_id))
    if document_exist(transaction_executor,table_name,document_id):
        query = "SELECT t.{} FROM {} as t BY d_id WHERE d_id = ?".format(field, table_name)
        cursor_three = transaction_executor.execute_statement(query, document_id)
        value = list(map(lambda x: x.get(field), cursor_three))
        logger.info("value of {} in {} is : {} ".format(field, document_id, value))
        return value
    else:
        return [False]

def delete_document(transaction_executor, table_name, document_id):
    query = 'DELETE FROM {} as t BY id  WHERE id IN ?'.format(table_name)
    cursor = transaction_executor.execute_statement(query, document_id)
    try:
        next(cursor)
        logger.info( 'Successfully deleted')
    except:
        logger.info('Problem in deletion!')

def document_exist(transaction_executor, table_name, document_id):
    query = 'SELECT * FROM {} as t by id WHERE id = ?'.format(table_name)
    cursor = transaction_executor.execute_statement(query,document_id)
    try:
        next(cursor)
        return True
    except:
        logger.info("Document doesn't exist. Check document id!")
        return False

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

def update_document( transaction_executor, table_name,field_name,document_id,new_value):
    if isinstance(new_value,str) :
        update_statement = " UPDATE {} AS j BY id SET j.{} = '{}' WHERE id = ?".format(table_name,field_name,str(new_value))
    else:
        update_statement = " UPDATE {} AS j BY id SET j.{} = {} WHERE id = ?".format(table_name,field_name,str(new_value))
    
    # print(update_statement)
    cursor = transaction_executor.execute_statement(update_statement,document_id)

    try:
        next(cursor)
        logger.info("{} in {} of id {} Updated Successfully!".format(field_name, table_name,document_id))
    except StopIteration:
        logger.info("Error updating the document in {}".format(table_name))
 