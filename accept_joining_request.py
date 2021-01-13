from logging import basicConfig, getLogger, INFO
from datetime import datetime
from connect_to_ledger import create_qldb_driver
from sampledata.sample_data import get_document_ids, print_result, get_value_from_documentid
from amazon.ion.simpleion import dumps, loads
from constants import Constants


logger = getLogger(__name__)
basicConfig(level=INFO)



def approve_joining_request(transaction_executor, request_id):
    
    # check if request agrees with the id
    if request_exists(transaction_executor, request_id):
        # approve the request'
        logger.info(" Request exists.")
        
        if get_value_from_documentid(transaction_executor, Constants.JOINING_REQUEST_TABLE_NAME, request_id, 'isAccepted') == [1]: 
            logger.info("Request Already accepted")
            
        else:            
            update_statement = " UPDATE JoiningRequest AS j BY id SET j.isAccepted = true WHERE id = ?"
            transaction_executor.execute_statement(update_statement, request_id)
            
            person_id = get_value_from_documentid(transaction_executor, Constants.JOINING_REQUEST_TABLE_NAME, request_id, 'SenderPersonId')
            scentity_id_code = get_value_from_documentid(transaction_executor, Constants.JOINING_REQUEST_TABLE_NAME, request_id, 'ScEntityIdentificationCode')
            
            join_person_to_company(transaction_executor, scentity_id_code, person_id)
            logger.info("Request : {} Accepted".format(request_id))
        
    else:
        logger.info("Request doesn't exist.")
   
    
     
def join_person_to_company(transaction_executor, scentity_id_code, person_id):
        
    statement = 'FROM SCEntities AS s WHERE s.ScEntityIdentificationCode = ? INSERT INTO s.PersonIds VALUE ?'
    cursor_two = transaction_executor.execute_statement(statement, scentity_id_code, person_id)
    
    try:
        cursor_two
        logger.info("Person Joined to the SCentity")
    except:
        logger.info("Person can't join.")
    
def request_exists(transaction_executor, request_id):
    
    statement = " SELECT * FROM JoiningRequest as j BY j_id WHERE j_id = ?"
    cursor_one = transaction_executor.execute_statement(statement, request_id)
    
    try:
        next(cursor_one)
        return True
    except:
        logger.info(" Request with request id: {} does not exist.".format(request_id))
        return False    
        

# def request_accepted(transaction_executor, request_id):
    
#     statement = " SELECT j.isAccepted FROM JoiningRequest as j BY j_id WHERE j_id = ?"
#     cursor_five = transaction_executor.execute_statement(statement, request_id)
    
    
#     for row in cursor_five:
#         isAccepted = dumps(row, binary=False, indent='  ', omit_version_marker=True)
    
#     logger.info(isAccepted)


if __name__ == '__main__':
    """
    Register a new driver's license.
    """
    try:
        with create_qldb_driver() as driver:
            
            request_id = "65vrXPWIXMqClbnei3PV8D"        
  
            driver.execute_lambda(lambda executor: approve_joining_request(executor,request_id))
    except Exception:
        logger.exception('Error accepting the request.')