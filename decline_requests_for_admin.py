from logging import basicConfig, getLogger, INFO
from connect_to_ledger import create_qldb_driver
from sampledata.sample_data import get_value_from_documentid, delete_document
from constants import Constants
from accept_requests_for_admin import mcg_request_exist,update_approval_status, mcg_request_already_approved


logger = getLogger(__name__)
basicConfig(level=INFO)


def decline_request_to_approve_company_or_product(transaction_executor, request_id):
    ## check if request exists
    ## check if request was approved
    if mcg_request_exist(transaction_executor, request_id):
        if mcg_request_already_approved(transaction_executor, request_id):
            logger.info("Request was already approved! Continuting to decline it now")
            update_statement = "UPDATE {} AS j BY id SET j.isAccepted = false WHERE id = ?".format(Constants.SUPERADMIN_REQUEST_TABLE_NAME)
            cursor = transaction_executor.execute_statement(update_statement, request_id)
            update_approval_status(transaction_executor,request_id,"false")
            try:
                next(cursor)
                logger.info("Request successfully Declined and deleted!")
                logger.info(" ================================== R E Q U E S T =========== D E N I E D ===============================")
            except StopIteration:
                logger.info("Request couldn't be accepted!")
        else: 
            logger.info("Declining and deleting requests!")
            update_approval_status(transaction_executor,request_id,"false")
    else:
        logger.info("Any request with request id : {} doesn't exist.".format(request_id))


if __name__ == '__main__':
    try:
        with create_qldb_driver() as driver:
            
            request_id = "0LIDa4UWi8a7aqXtwhBYPE"        
  
            driver.execute_lambda(lambda executor: decline_request_to_approve_company_or_product(executor,request_id))
    except Exception:
        logger.exception('Error accepting the request.')
