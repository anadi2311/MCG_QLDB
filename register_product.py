from logging import basicConfig, getLogger, INFO
from datetime import datetime
from connect_to_ledger import create_qldb_driver
from sampledata.sample_data import get_document_ids, print_result
from constants import Constants


from sampledata.sample_data import convert_object_to_ion
from insert_document import insert_documents
from register_person import get_scentityid_from_personid, get_scentityid_from_personid, create_mcg_request, get_approval_status

logger = getLogger(__name__)
basicConfig(level=INFO)


    # logger.info('Entity with id : {} is not approved by')
    ## in case of vaccine it is GTIN Containing NDC_Code

def product_exist(transaction_executor, product_code):
  


    query = 'SELECT * FROM Products as pr WHERE pr.product_code = ?'
    cursor1 = transaction_executor.execute_statement(query,convert_object_to_ion(product_code))
    try:
        next(cursor1)
        logger.info("Product with produce_code : {} has already been registered or in process of registeration".format(product_code))
        return True
    except:
        return False


def register_product(transaction_executor, product,person_id):
    ## check if the vaccine with GTIN already exist 
    # scentity_id = get_scentityid_from_personid(transaction_executor,person_id)

    logger.info("Person_id: {}".format(person_id))
    if get_scentityid_from_personid(transaction_executor,person_id):
        scentity_id = product['manufacturer_id']
        actual_scentity_id = get_scentityid_from_personid(transaction_executor,person_id)
        if actual_scentity_id == scentity_id:
            logger.info("Matched for authorization!")
            if get_approval_status(transaction_executor,scentity_id):
                logger.info("Entity is Approved to register product!")
                product_code = product["product_code"]
                if product_exist(transaction_executor, product_code):
                    logger.info(" Product already exists.")
                else:
                    result = insert_documents(transaction_executor, Constants.PRODUCT_TABLE_NAME, [product])
                    product_id = result[0]
                    product_request_id = create_mcg_request(transaction_executor,product_id, person_id,2)
                    logger.info("Request was created for product Id : {} with product request id {}".format(product_id, product_request_id))
                    return product_id , product_request_id
            else:
                logger.info("Entity not approved yet. Cannot register the product")
        else:
            logger.info("You don't belong to this entity")
    else:
        logger.info("Person doesn't belong to any entity. First Register person with an Entity")


if __name__ == '__main__':

    try:
        with create_qldb_driver() as driver:
            new_product = {
            'product_code': "00123451000013", #GTIN for Vaccine with NDC National Drug Code
            'product_name': "Moderna Vaccine",
            'product_price': 10,
            'product_expiry': 120, #in days
            'product_storage': {
                'low_thresh_temp': 0, #in degrees Centigrate
                'high_thresh_temp': 10, #in degree Centigrate
                'high_thresh_humidity': 40 # percentage   
            },
            'manufacturer_id': "23ki18Jamhg8VyRWQsoKic", #change this <<<<---------------------------
            'isApprovedBySuperAdmin':False,
            'batch_table_id': ''
            }


            # must be passed down as a prop from the react state
            person_id = "ATP79apUuTW33whnMmwsad"             #change this <<<<---------------------------
            driver.execute_lambda(lambda executor: register_product(executor, new_product, person_id))
    except Exception:
        logger.exception('Error registering product.')
