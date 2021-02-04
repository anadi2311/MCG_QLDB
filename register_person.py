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
from sampledata.sample_data import convert_object_to_ion, get_document_ids, get_document_ids_from_dml_results
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
        return True
    except StopIteration:
        logger.info("Person not found.")
        return False

def get_person_ids(transaction_executor):
    
    statement = 'SELECT PersonIds FROM SCEntities'
    cursor2 = transaction_executor.execute_statement(statement)
    person_ids = list(map(lambda x: x.get('PersonIds'), cursor2))
    return person_ids

def get_scentity_ids(transaction_executor):
    
    statement = 'SELECT id FROM SCEntities by id'
    cursor2 = transaction_executor.execute_statement(statement)
    scentity_ids = list(map(lambda x: x.get('id'), cursor2))

    return scentity_ids


def get_scentityid_from_personid(transaction_executor, person_id):

    val = get_person_ids(transaction_executor)
    k = get_scentity_ids(transaction_executor)
    id_dict = dict(zip(k,val))
    
    for key, values in id_dict.items():

        if person_id in values:
            print("person belongs to : {}".format(key))
            return key
        else:
            logger.info("Searching..")
            continue


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
        person.update({"isSuperAdmin":False}) #<<-----------uncomment after onboarding admin
        person.update({"isAdmin":False}) #<<----------- un comment after onboarding admin
        result = insert_documents(transaction_executor, Constants.PERSON_TABLE_NAME, [person])
        result = result[0]
        logger.info("New Person registered with person id : {}".format(result))
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
    request_number = get_index_number(transaction_executor,Constants.JOINING_REQUEST_TABLE_NAME,Constants.JOINING_REQUESTID_INDEX_NAME)
    sc_entity_identification_code = sc_entity['ScEntityIdentificationCode']
    sc_entity_id = next(get_document_ids(transaction_executor,Constants.SCENTITY_TABLE_NAME,"ScEntityIdentificationCode",sc_entity_identification_code))
    request = {
        "JoiningRequestNumber":request_number,
        "SenderEmployeeId": employee_id,
        "SenderPersonId" : person_id,
        "ScEntityId": sc_entity_id,
        "isAccepted":False
    }
    print(request)
    
    result = insert_documents( transaction_executor, Constants.JOINING_REQUEST_TABLE_NAME, [request])
    return result[0]
    
    
def get_index_number(transaction_executor, table_name,request_index_name):
    statement = "SELECT COUNT(t.{}) as ret_val FROM {} as t".format(request_index_name,table_name)
    print("Table: {} and Index: {}".format(table_name,request_index_name))
    cursor = transaction_executor.execute_statement(statement)

    ret_val = list(map(lambda x: x.get('ret_val'), cursor))
    # print(str(type(ret_val[0])))
    # logger.info("ret_val is {}".format(type(ret_val[0])))
    if str(type(ret_val[0])) == "<class 'amazon.ion.simple_types.IonPyNull'>":
        ret_val = 1
        logger.info("ret_val is Null")
    else:
        ret_val = int(dumps(ret_val[0],binary=False, indent='  ', omit_version_marker=True))
        ret_val = ret_val+1

    return ret_val
    
def send_request_to_company(transaction_executor, request_Id, sc_entity):
    
    
    sc_entity_id_code = sc_entity['ScEntityIdentificationCode']
    
    logger.info('Sending request to the company Admin.')
    
    statement = 'FROM SCEntities AS s WHERE s.ScEntityIdentificationCode = ? INSERT INTO s.JoiningRequests VALUE ?'
    cursor_two = transaction_executor.execute_statement(statement, sc_entity_id_code, request_Id)
    
    try:
        next(cursor_two)
        list_of_document_ids = get_document_ids_from_dml_results(cursor_two)
        logger.info('Joining Request sent with id {}'.format(request_Id))
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


def mcg_request_already_sent(transaction_executor, document_id):
    query = 'SELECT * FROM {} as m WHERE m.Document_id = ? '.format(Constants.SUPERADMIN_REQUEST_TABLE_NAME)
    cursor = transaction_executor.execute_statement(query, document_id)

    try:
        next(cursor)
        logger.info('Request to Super Admin already sent for document id : {}. Please wait for approval'.format(document_id))
        return True
    except StopIteration:
        logger.info('request for new document id!')
        return False

def create_mcg_request(transaction_executor,document_id,person_id, request_type):
    request_number = get_index_number(transaction_executor,Constants.SUPERADMIN_REQUEST_TABLE_NAME,Constants.SUPERADMIN_REQUEST_INDEX_NAME)
    request = {
        "McgRequestNumber": request_number,
        "Document_id": document_id,
        "Request_type": request_type,
        "SenderPersonId" : person_id,
        "isAccepted":False
    }

    # request type is 1 for company 2 for product
    if mcg_request_already_sent(transaction_executor, document_id):
        logger.info("Request already sent for document id : {}".format(document_id))
    else:
        result = insert_documents(transaction_executor, Constants.SUPERADMIN_REQUEST_TABLE_NAME, [request])
        request_id = result[0]
        return request_id

def get_document_superadmin_approval_status(transaction_executor, table_name, document_id):
    
    statement = 'SELECT s.isApprovedBySuperAdmin FROM {} as s by id where id = ?'.format(table_name)
    cursor = transaction_executor.execute_statement(statement, document_id)
    approval_status = list(map(lambda x: x.get('isApprovedBySuperAdmin'), cursor))
    
    logger.info("approval status : {}".format(approval_status))

    if approval_status == [1]:
        logger.info(" MCG approved")
        return True
    else:
        logger.info("Not approved")
        return False

def get_scentity_contact(transaction_executor,scentity_id,contact_field):
    statement = "SELECT t.{} FROM {} as t BY d_id WHERE d_id = ?".format("ScEntityContact."+contact_field,Constants.SCENTITY_TABLE_NAME)
    cursor = transaction_executor.execute_statement(statement,scentity_id)   
    value = list(map(lambda x: x.get('{}'.format(contact_field)), cursor))

    return value

## check if request is sent to super admin for approval of product code for that GTIN
## send request for vaccineApproval


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
    person_id = register_new_Person(transaction_executor, person)
    if get_scentityid_from_personid(transaction_executor, person_id):
        logger.info("Person with personId '{}' already belongs to a SC Entity".format(person_id))
    else:
        logger.info("Registering new Person's entity...")
        if lookup_scentity(transaction_executor, new_sc_entity):
            # send request to join a new entity
            logger.info(' Entity already exist. Sending request to join it.')
            employee_id = person['EmployeeId']
            scentity_id_code = new_sc_entity['ScEntityIdentificationCode']
            scentity_id = next(get_document_ids(transaction_executor,Constants.SCENTITY_TABLE_NAME,'ScEntityIdentificationCode',scentity_id_code))

            if get_document_superadmin_approval_status(transaction_executor,Constants.SCENTITY_TABLE_NAME, scentity_id):
                if req_already_sent(transaction_executor, person_id) == True :
                    logger.info("Please wait for your company admin to approve the request.")
                else:
                    request_Id = create_req_to_join_scentity(transaction_executor,new_sc_entity,employee_id,person_id)
                    send_request_to_company(transaction_executor,request_Id, new_sc_entity)
            else:
                logger.info('Wait for MCG to approve this entity ... ')
        else:
            #create a new entity
            if req_already_sent(transaction_executor, person_id) == True :
                logger.info("Please wait for your company admin to approve the request.")
            else:
                update_person_to_admin(transaction_executor,person_id)
                new_sc_entity.update({'PersonIds': [str(person_id)]})
                new_sc_entity.update({'isApprovedBySuperAdmin': False})
                try:
                    result = insert_documents( transaction_executor, Constants.SCENTITY_TABLE_NAME, [new_sc_entity])
                    sc_entity_id = result[0]

                    mcg_request_id = create_mcg_request(transaction_executor,sc_entity_id,person_id, 1)

                    sc_entity_id_code = new_sc_entity["ScEntityIdentificationCode"]
                    logger.info('Registration process began for new SCEntity with ScEntityIdentificationCode : {} and ScEntityId: {}. A new request was create for super admin : {}'.format(sc_entity_id_code,sc_entity_id, mcg_request_id))
                    logger.info(" ================================== P E R S O N =========== R E G I S T R A T I O N ============== I N I T I A T E D=================")
                    return mcg_request_id,sc_entity_id
                except StopIteration:
                    logger.info('Problem occurred while inserting Scentity, please review the results.')
                

if __name__ == '__main__':
    """
    Register a new driver's license.
    """
    try:
        with create_qldb_driver() as driver:
            
            # new_person_1 = {
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

            # new_sc_entity_1 = {
            # "ScEntityName" : " BuyerCompanyC",
            # "ScEntityContact":{
            #     "Email":"moderna@moderna.com",
            #     "Address":"345 DEF St, ON, CAN",
            #     "Phone": "1234567890"
            # },
            # "isApprovedBySuperAdmin": True,
            # "ScEntityTypeCode": "2",
            # "PersonIds": [],
            # "JoiningRequests" : [],
            # "ScEntityIdentificationCode" : "AS231rrrrr",    
            # "ScEntityIdentificationCodeType" : "BusinessNumber"               
            # }
            

            # new_person_2 = {
            # 'EmployeeId': 'MAN123',
            # 'FirstName': 'MAN',
            # 'LastName': 'DOE',
            # 'isSuperAdmin' : False,
            # 'isAdmin' : False,
            #  'PersonContact': {
            #         "Email": "JAN.Doe@ubc.ca",
            #         'Phone' : "8888888888",
            #         'Address': 'FirstNewUser'
            #  }}
    
            # new_sc_entity_2 = {
            # "ScEntityName" : " Moderna",
            # "ScEntityContact":{
            #     "Email":"moderna@moderna.com",
            #     "Address":"345 DEF St, ON, CAN",
            #     "Phone": "1234567890"
            # },
            # "isApprovedBySuperAdmin": False,
            # "ScEntityTypeCode": "2",
            # "PersonIds": [],
            # "JoiningRequests" : [],
            # "ScEntityIdentificationCode" : "MODERNA1234",    
            # "ScEntityIdentificationCodeType" : "BusinessNumber"               
            # }

            # new_person_3 = {
            # 'EmployeeId': 'FAN123',
            # 'FirstName': 'FAN',
            # 'LastName': 'DOE',
            # 'isSuperAdmin' : False,
            # 'isAdmin' : False,
            #  'PersonContact': {
            #         "Email": "JAN.Doe@ubc.ca",
            #         'Phone' : "8888888888",
            #         'Address': 'FirstNewUser'
            #  }}
            


            # new_sc_entity_3 = {
            # "ScEntityName" : " FEDX",
            # "ScEntityContact":{
            #     "Email":"FEDx@FEDx.com",
            #     "Address":"345 DEF St, ON, CAN",
            #     "Phone": "1234567890"
            # },
            # "isApprovedBySuperAdmin": True,
            # "ScEntityTypeCode": "2",
            # "PersonIds": [],
            # "JoiningRequests" : [],
            # "ScEntityIdentificationCode" : "COOODDO1234",    #<<--------must be checked from a govt. available data source
            # "ScEntityIdentificationCodeType" : "BusinessNumber"               
            # }            
      
            # new_person_4 = {
            # 'EmployeeId': 'CustomAgent123',
            # 'FirstName': 'ExportCustom',
            # 'LastName': 'DOE',
            # 'isSuperAdmin' : False,
            # 'isAdmin' : False,
            #  'PersonContact': {
            #         "Email": "Custom.Doe@ubc.ca",
            #         'Phone' : "8888888888",
            #         'Address': 'FirstNewUser'
            #  }}

            # new_sc_entity_4 = {
            # "ScEntityName" : "TexasAirport",
            # "ScEntityContact":{
            #     "Email":"Tsairport@airport.com",
            #     "Address":"345 DEF St, ON, CAN",
            #     "Phone": "1234567890"
            # },
            # "isApprovedBySuperAdmin": True,
            # "ScEntityTypeCode": "3",
            # "PersonIds": [],
            # "JoiningRequests" : [],
            # "ScEntityIdentificationCode" : "Tx123",    #<<--------must be checked from a govt. available data source
            # "ScEntityIdentificationCodeType" : "IATACode"               
            # }   

            # new_person_5 = {
            # 'EmployeeId': 'ImpotCustomAgent123',
            # 'FirstName': 'ImportCustom',
            # 'LastName': 'DOE',
            # 'isSuperAdmin' : False,
            # 'isAdmin' : False,
            #  'PersonContact': {
            #         "Email": "Custom.Doe@ubc.ca",
            #         'Phone' : "8888888888",
            #         'Address': 'FirstNewUser'
            #  }}

            # new_sc_entity_5 = {
            # "ScEntityName" : "VancouverAirport",
            # "ScEntityContact":{
            #     "Email":"yvrairport@airport.com",
            #     "Address":"345 DEF St, ON, CAN",
            #     "Phone": "1234567890"
            # },
            # "isApprovedBySuperAdmin": True,
            # "ScEntityTypeCode": "3",
            # "PersonIds": [],
            # "JoiningRequests" : [],
            # "ScEntityIdentificationCode" : "YVR123",    #<<--------must be checked from a govt. available data source
            # "ScEntityIdentificationCodeType" : "IATACode"               
            # }   


            # new_person_6 = {
            # 'EmployeeId': 'Hospitalemployee123',
            # 'FirstName': 'Doctor',
            # 'LastName': 'DOE',
            # 'isSuperAdmin' : False,
            # 'isAdmin' : False,
            #  'PersonContact': {
            #         "Email": "Custom.Doe@ubc.ca",
            #         'Phone' : "8888888888",
            #         'Address': 'FirstNewUser'
            #  }}

            # new_sc_entity_6 = {
            # "ScEntityName" : "YVR Hospital",
            # "ScEntityContact":{
            #     "Email":"yvrairport@airport.com",
            #     "Address":"345 DEF St, ON, CAN",
            #     "Phone": "1234567890"
            # },
            # "isApprovedBySuperAdmin": True,
            # "ScEntityTypeCode": "5",
            # "PersonIds": [],
            # "JoiningRequests" : [],
            # "ScEntityIdentificationCode" : "YVRHOSP123",    #<<--------must be checked from a govt. available data source
            # "ScEntityIdentificationCodeType" : "HospitalCode"               
            # }   

            new_person_7 = {
            'EmployeeId': 'NEWIMPORTPDRIVER',
            'FirstName': 'DRRRRW',
            'LastName': 'DOE',
            'isSuperAdmin' : False,
            'isAdmin' : False,
             'PersonContact': {
                    "Email": "JAN.Doe@ubc.ca",
                    'Phone' : "8888888888",
                    'Address': 'FirstNewUser'
             }}

            new_sc_entity_7 = {
            "ScEntityName" : " FEDX",
            "ScEntityContact":{
                "Email":"FEDx@FEDx.com",
                "Address":"345 DEF St, ON, CAN",
                "Phone": "1234567890"
            },
            "isApprovedBySuperAdmin": True,
            "ScEntityTypeCode": "2",
            "PersonIds": [],
            "JoiningRequests" : [],
            "ScEntityIdentificationCode" : "COOODDO1234",    #<<--------must be checked from a govt. available data source
            "ScEntityIdentificationCodeType" : "BusinessNumber"               
            }      

            driver.execute_lambda(lambda executor: 
                                                #register_new_user_with_scentity(executor, new_person_1, new_sc_entity_1) and
                                                #   register_new_user_with_scentity(executor, new_person_2, new_sc_entity_2) and
                                                #   register_new_user_with_scentity(executor, new_person_3, new_sc_entity_3) and
                                                #   register_new_user_with_scentity(executor, new_person_4, new_sc_entity_4) and
                                                #   register_new_user_with_scentity(executor, new_person_5, new_sc_entity_5) and
                                                #   register_new_user_with_scentity(executor, new_person_6, new_sc_entity_6) 
                                                #   and
                                                  register_new_user_with_scentity(executor, new_person_7, new_sc_entity_7)
                                                  )
    except Exception:
        logger.exception('Error registering new Person and Entities.')
    

