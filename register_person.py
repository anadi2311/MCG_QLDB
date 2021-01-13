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
from datetime import datetime

from amazon.ion.simpleion import dumps, loads
from sampledata.sample_data import convert_object_to_ion, get_document_ids, get_document_ids_from_dml_results, print_result
from constants import Constants
from insert_document import insert_documents
from connect_to_ledger import create_qldb_driver

logger = getLogger(__name__)
basicConfig(level=INFO)


def person_already_exists(transaction_executor, employee_id):
    """
    Verify whether a driver already exists in the database.
    :type transaction_executor: :py:class:`pyqldb.execution.executor.Executor`
    :param transaction_executor: An Executor object allowing for execution of statements within a transaction.
    :type gov_id: str
    :param gov_id: The government ID to search `Person` table against.
    :rtype: bool
    :return: If the Person has been registered.
    """
    query = 'SELECT * FROM Persons AS p WHERE p.EmployeeId = ?'
    cursor = transaction_executor.execute_statement(query, convert_object_to_ion(employee_id))
    try:
        next(cursor)
        logger.info("Person already exists.")
        return True
    except StopIteration:
        logger.info("Person not found.")
        return False

def get_person_ids(transaction_executor):
    
    statement = 'SELECT PersonIds FROM SCEntities'
    cursor2 = transaction_executor.execute_statement(statement)
    person_ids = list(map(lambda x: x.get('PersonIds'), cursor2))
    logger.info("Existing Person Ids are: {} ".format(person_ids))
    return person_ids

def get_scentity_ids(transaction_executor):
    
    statement = 'SELECT id FROM SCEntities by id'
    cursor2 = transaction_executor.execute_statement(statement)
    scentity_ids = list(map(lambda x: x.get('id'), cursor2))
    logger.info("Existing scentity ids are {}".format(scentity_ids))
    return scentity_ids

def lookup_scentity_for_person(transaction_executor, person_id):
    """
    Query drivers license table by person ID.
    :type transaction_executor: :py:class:`pyqldb.execution.executor.Executor`
    :param transaction_executor: An Executor object allowing for execution of statements within a transaction.
    :type person_id: str
    :param person_id: The person ID to check.
    :rtype: :py:class:`pyqldb.cursor.stream_cursor.StreamCursor`
    :return: Cursor on the result set of a statement query.
    """
    
    person_ids = get_person_ids(transaction_executor)
    query = 'SELECT * FROM SCEntities AS d WHERE ? IN ? '
    cursor = transaction_executor.execute_statement(query, person_id, person_ids)
    return cursor

def get_scentityid_from_personid(transaction_executor, person_id):

    values = get_person_ids(transaction_executor)
    keys = get_scentity_ids(transaction_executor)
    id_dict = dict(zip(keys,values))
    
    for key, values in id_dict.items():
        if person_id in values:
            return key
        else:
            logger.info("Person does not belong to any entity")
            return False


def person_belong_to_scentity(transaction_executor, person_id):
    """
    Check if the driver already has a driver's license using their unique document ID.
    :type transaction_executor: :py:class:`pyqldb.execution.executor.Executor`
    :param transaction_executor: An Executor object allowing for execution of statements within a transaction.
    :type document_id: str
    :param document_id: The document ID to check.
    :rtype: bool
    :return: If the Person has a drivers license.
    """
    cursor = lookup_scentity_for_person(transaction_executor, person_id)
    try:
        next(cursor)
        print_result(cursor)
        return True
    except StopIteration:
        return False

def register_new_Person(transaction_executor, person):
    """
    Register a new driver in QLDB if not already registered.
    :type transaction_executor: :py:class:`pyqldb.execution.executor.Executor`
    :param transaction_executor: An Executor object allowing for execution of statements within a transaction.
    :type driver: dict
    :param driver: The driver's license to register.
    """
    employee_id = person['EmployeeId']
    if person_already_exists(transaction_executor, employee_id):
        result = next(get_document_ids(transaction_executor, Constants.PERSON_TABLE_NAME, 'EmployeeId', employee_id))
        logger.info('Person with  employee_Id {} already exists with PersonId: {} .'.format(employee_id, result))
    else:
        result = insert_documents(transaction_executor, Constants.PERSON_TABLE_NAME, [person])
        result = result[0]
    return result
        

def lookup_scentity(transaction_executor, new_sc_entity):
    scentity_id = new_sc_entity['ScEntityIdentificationCode']
    query = 'SELECT * FROM SCEntities AS d WHERE d.ScEntityIdentificationCode = ?'
    cursor = transaction_executor.execute_statement(query, scentity_id)
    try:
        next(cursor)
        logger.info("Entity already exists")
        return True
    except StopIteration:
        logger.info("Entity not found. Registering new Entity")
        return False
    
def create_req_to_join_scentity(transaction_executor, sc_entity, employee_id, person_id):

    # insert the request document in request table
    request = {
        "SenderEmployeeId": employee_id,
        "SenderPersonId" : person_id,
        "ScEntityIdentificationCode": sc_entity['ScEntityIdentificationCode'],
        "isAccepted":False
    }
    
    result = insert_documents( transaction_executor, Constants.JOINING_REQUEST_TABLE_NAME, [request])
    return result[0];
    
    
def calculateTotalRequests(transaction_executor, sc_entity):
    
    sc_entity_id_code = sc_entity['ScEntityIdentificationCode']
        
    logger.info("Calculating total requests")
    
    query_one = 'SELECT SIZE(JoiningRequests) as RequestNumbers FROM SCEntities AS s WHERE s.ScEntityIdentificationCode = ?'
    cursor_one= transaction_executor.execute_statement(query_one,sc_entity_id_code)
    
    
    for row in cursor_one:
        request_number = int(dumps(row["RequestNumbers"], binary = False,indent='  ', omit_version_marker=True))
        logger.info("Total requests for this company are {}".format(request_number))

    return request_number

    
def send_request_to_company(transaction_executor, request_Id, sc_entity):
    
    
    sc_entity_id_code = sc_entity['ScEntityIdentificationCode']
    
    logger.info('Sending request to the company Admin.')
    
    statement = 'FROM SCEntities AS s WHERE s.ScEntityIdentificationCode = ? INSERT INTO s.JoiningRequests VALUE ?'
    cursor_two = transaction_executor.execute_statement(statement, sc_entity_id_code, request_Id)
    
    try:
        list_of_document_ids = get_document_ids_from_dml_results(cursor_two)
        logger.info('Request sent with id {}'.format(request_Id))
    except:
        logger.exception("Couldn't send the request.")

def req_already_sent(transaction_executor, person_id):
    
    # statement = "SELECT * FROM {} as j where j.SenderPersonId = ?".format(Constants.JOINING_REQUEST_TABLE_NAME)
    # cursor_four = transaction_executor.execute_statement(statement, person_id)
    # print_result(cursor_four)
    
    results = get_document_ids(transaction_executor, Constants.JOINING_REQUEST_TABLE_NAME, 'SenderPersonId',person_id)    
    try: 
        request_id = next(results)
        logger.info("Request already sent with id : {}".format(request_id))
        return True
    except StopIteration:
        logger.info(" Request not found")
        return False

def update_person_to_admin(transaction_executor,person_id):
    
    update_statement = " UPDATE Persons AS p BY id SET p.isAdmin = true WHERE id = ?"
    cursor = transaction_executor.execute_statement(update_statement, person_id)
    try:
        next(cursor)
        logger.info("Person with person id :{} was made an admin.".format(person_id))
    except:
        logger.info("Problem arised while making person with person id :{} as admin.".format(person_id))

def register_new_user_with_scentity(transaction_executor, person, new_sc_entity):
    """
    Register a new driver and a new driver's license in a single transaction.
    :type transaction_executor: :py:class:`pyqldb.execution.executor.Executor`
    :param transaction_executor: An Executor object allowing for execution of statements within a transaction.
    :type driver: dict
    :param driver: The driver's license to register.
    :type new_license: dict
    :param new_license: The driver's license to register.
    """
    person_id = register_new_Person(transaction_executor, person);
    if person_belong_to_scentity(transaction_executor, person_id):
        logger.info("Person with personId '{}' already belongs to a SC Entity".format(person_id))
    else:
        logger.info("Registering new driver's entity...")
        if lookup_scentity(transaction_executor, new_sc_entity):
            # send request to join a new entity
            logger.info(' Entity already exist. Sending request to join it.')
            employee_id = person['EmployeeId']
            
            if req_already_sent(transaction_executor, person_id) == True :
                logger.info("Please wait for your company admin to approve the request.")
            else:
                request_Id = create_req_to_join_scentity(transaction_executor,new_sc_entity,employee_id,person_id)
                send_request_to_company(transaction_executor,request_Id, new_sc_entity)
            
        else:
            #create a new entity
            if req_already_sent(transaction_executor, person_id) == True :
                logger.info("Please wait for your company admin to approve the request.")
            else:
                update_person_to_admin(transaction_executor,person_id)
                new_sc_entity.update({'PersonIds': str(person_id)})
                try:
                    result = insert_documents( transaction_executor, Constants.SCENTITY_TABLE_NAME, [new_sc_entity])
                    sc_entity_id = result[0];
                    sc_entity_id_code = new_sc_entity["ScEntityIdentificationCode"]
                    logger.info('Successfully registered new SCEntity with ScEntityIdentificationCode : {} and ScEntityId: {}.'.format(sc_entity_id_code,sc_entity_id))
                    return
                except StopIteration:
                    logger.info('Problem occurred while inserting Scentity, please review the results.')
                    return
                

if __name__ == '__main__':
    """
    Register a new driver's license.
    """
    try:
        with create_qldb_driver() as driver:
            
            # new_person = {
            # 'EmployeeId': 'BOB123',
            # 'FirstName': 'Bob',
            # 'LastName': 'Doe',
            # 'isSuperAdmin' : False,
            # 'isAdmin' : False,
            #  'PersonContact': {
            #     "Email": "Bob.Doe@ubc.ca",
            #     'Phone' : "8888888888",
            #     'Address': 'FirstNewUser'
            #  }}

            new_person = {
            'EmployeeId': 'JAN123',
            'FirstName': 'JANE',
            'LastName': 'DOE',
            'isSuperAdmin' : False,
            'isAdmin' : False,
             'PersonContact': {
                "Email": "JAN.Doe@ubc.ca",
                'Phone' : "8888888888",
                'Address': 'FirstNewUser'
             }}
    
  
            new_sc_entity = {
            "ScEntityName" : " Moderna",
            "ScEntityLocation" : "345 DEF St, ON, CAN",
            "ScEntityContact": "1234567890",
            "isApprovedBySuperAdmin": False,
            "ScentityTypeCode": 2,
            "PersonIds": [],
            "JoiningRequests" : [],
            "ScEntityIdentificationCode" : "ABCD1234",    
            "ScEntityIdentificationCodeType" : "BusinessNumber"               
            }

            # new_sc_entity = {
            # "ScEntityName" : " CompanyB",
            # "ScEntityLocation" : "abad,asdasd,asdad",
            # "ScEntityContact": "1234567890",
            # "isApprovedBySuperAdmin": False,
            # "ScentityTypeCode": 2,
            # "PersonIds": [],
            # "JoiningRequests" : [],
            # "ScEntityIdentificationCode" : "ASDSD1234",    
            # "ScEntityIdentificationCodeType" : "BusinessNumber"               
            # }

            driver.execute_lambda(lambda executor: register_new_user_with_scentity(executor, new_person, new_sc_entity))
    except Exception:
        logger.exception('Error registering new Person and Entities.')
    

