from logging import basicConfig, getLogger, INFO
from datetime import datetime
from connect_to_ledger import create_qldb_driver
from sampledata.sample_data import get_document_ids, print_result, get_value_from_documentid, delete_document
from amazon.ion.simpleion import dumps, loads
from constants import Constants

from register_person import get_scentityid_from_personid


logger = getLogger(__name__)
basicConfig(level=INFO)



def approve_joining_request(transaction_executor, request_id,person_id):
    
    # check if request agrees with the id
    if request_exists(transaction_executor, request_id):
        # approve the request'
        logger.info(" Request exists.")
        sc_entity_id = get_value_from_documentid(transaction_executor,Constants.JOINING_REQUEST_TABLE_NAME,request_id,"ScEntityId")
        actual_scentity_id = get_scentityid_from_personid(transaction_executor,person_id)
        if sc_entity_id[0] == actual_scentity_id:
            logger.info("Authorized!")
            if get_value_from_documentid(transaction_executor, Constants.JOINING_REQUEST_TABLE_NAME, request_id, 'isAccepted') == [1]: 
                logger.info("Request Already accepted")
                
            else:   
                update_statement = " UPDATE JoiningRequest AS j BY id SET j.isAccepted = true WHERE id = ?"
                transaction_executor.execute_statement(update_statement, request_id)
                
                person_id = get_value_from_documentid(transaction_executor, Constants.JOINING_REQUEST_TABLE_NAME, request_id, 'SenderPersonId')
                person_id = person_id[0]
                scentity_id = get_value_from_documentid(transaction_executor, Constants.JOINING_REQUEST_TABLE_NAME, request_id, 'ScEntityId')
                join_person_to_company(transaction_executor, scentity_id[0], person_id)
                logger.info("Request : {} Accepted".format(request_id))
                logger.info(" ================================== P E R S O N =========== A D D E D ===============================")
        else:
            logger.info("Person not authorized")    
    else:
        logger.info("Request doesn't exist.")
   
    
     
def join_person_to_company(transaction_executor, scentity_id, person_id):
        
    statement = 'FROM SCEntities AS s By id WHERE id = ? INSERT INTO s.PersonIds VALUE ?'
    cursor_two = transaction_executor.execute_statement(statement, scentity_id, person_id)
    
    try:
        next(cursor_two)
        logger.info("Person Joined to the SCentity")
    except StopIteration:
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



if __name__ == '__main__':
    try:
        with create_qldb_driver() as driver:
            
            requestid = "GjyuFfPptqRGdcvpkB0e5G" 
            personid = "ElYLFZylZJnBNGPia4VoDv"       
  
            driver.execute_lambda(lambda executor: approve_joining_request(executor,requestid,personid))
    except Exception:
        logger.exception('Error accepting the request.')


