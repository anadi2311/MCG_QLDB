from logging import basicConfig, getLogger, INFO
from connect_to_ledger import create_qldb_driver
from sampledata.sample_data import get_value_from_documentid, delete_document
from constants import Constants

logger = getLogger(__name__)
basicConfig(level=INFO)



def mcg_request_exist(transaction_executor, request_id):

    query = 'SELECT * FROM {} as m by id WHERE id = ? '.format(Constants.SUPERADMIN_REQUEST_TABLE_NAME)
    cursor = transaction_executor.execute_statement(query, request_id)

    try:
        next(cursor)
        logger.info('Request exists!')
        return True
    except StopIteration:
        logger.info('Request not Found')
        return False

def mcg_request_already_approved(transaction_executor, request_id):
    query  = 'SELECT m.isAccepted from {} as m by id where id = ?'.format(Constants.SUPERADMIN_REQUEST_TABLE_NAME)
    cursor = transaction_executor.execute_statement(query,request_id)
    approval_status = list(map(lambda x: x.get('isAccepted'), cursor))
    
    logger.info("approval status : {}".format(approval_status))

    if approval_status == [0]:
        logger.info(" not approved")
        return False
    else:
        logger.info("approved")
        return True


def update_approval_status(transaction_executor,request_id,status):
    request_type = get_value_from_documentid(transaction_executor,Constants.SUPERADMIN_REQUEST_TABLE_NAME,request_id,"Request_type")
    request_type = request_type[0]
    document_id = get_value_from_documentid(transaction_executor,Constants.SUPERADMIN_REQUEST_TABLE_NAME,request_id,"Document_id")
    logger.info(request_type)
    logger.info(document_id)

    if request_type == 1:
        table_name = Constants.SCENTITY_TABLE_NAME

    else:
        table_name = Constants.PRODUCT_TABLE_NAME

    if status == "false":
       
        # delete this if statement if you want to keep person even if SCEntitiy is deleted
        if request_type == 1:
            person_ids = get_value_from_documentid(transaction_executor, table_name,document_id[0],'PersonIds')
            logger.info(person_ids)
            person_ids = person_ids[0]
            logger.info('person_ids are :{}'.format(person_ids))
            delete_document(transaction_executor, Constants.PERSON_TABLE_NAME,person_ids)  
            logger.info('Following documents were deleted : person id:{}'.format(person_ids))


        # id must be in list so request_id was converted to ['request_id']
        delete_document(transaction_executor,table_name,document_id)
        delete_document(transaction_executor,Constants.SUPERADMIN_REQUEST_TABLE_NAME, [request_id]) 
        logger.info('Following documents were deleted :  product or scentity id: {} and request id:{}'.format(document_id,request_id))
        
    else:
        update_statement = " UPDATE {} AS j BY id SET j.isApprovedBySuperAdmin = true WHERE id = ?".format(table_name)
        document_id = document_id[0]
        cursor = transaction_executor.execute_statement(update_statement, document_id)
        try:
            next(cursor)
            logger.info("Approval Status Updated!")
        except StopIteration:
            logger.info("Status was not updated!")

def accept_request_to_approve_company_or_product(transaction_executor, request_id):
    if mcg_request_exist(transaction_executor, request_id):
        if mcg_request_already_approved(transaction_executor, request_id):
            logger.info("Request is already approved!")
        else:
            update_approval_status(transaction_executor,request_id,True)
            update_statement = " UPDATE {} AS j BY id SET j.isAccepted = true WHERE id = ?".format(Constants.SUPERADMIN_REQUEST_TABLE_NAME)
            cursor = transaction_executor.execute_statement(update_statement, request_id)
            try:
                next(cursor)
                logger.info("Request successfully accepted!")
            except StopIteration:
                logger.info("Request couldn't be accepted!")
    else:
        logger.info("Any request with request id : {} doesn't exist.".format(request_id))




if __name__ == '__main__':
    try:
        with create_qldb_driver() as driver:
            
            request_id = "AIl46rO96mT2ONIu32kvz3"        
  
            driver.execute_lambda(lambda executor: accept_request_to_approve_company_or_product(executor,request_id))
    except Exception:
        logger.exception('Error accepting the request.')