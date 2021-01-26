from logging import basicConfig, getLogger, INFO
from datetime import datetime
from connect_to_ledger import create_qldb_driver
from sampledata.sample_data import get_document_ids, print_result
from constants import Constants


from sampledata.sample_data import convert_object_to_ion
from insert_document import insert_documents
from register_person import get_scentityid_from_personid, create_mcg_request, get_document_approval_status

logger = getLogger(__name__)
basicConfig(level=INFO)


    # logger.info('Entity with id : {} is not approved by')
    ## in case of vaccine it is GTIN Containing NDC_Code

def product_exist(transaction_executor, ProductCode):


    query = 'SELECT * FROM Products as pr WHERE pr.ProductCode = ?'
    cursor1 = transaction_executor.execute_statement(query,convert_object_to_ion(ProductCode))
    try:
        next(cursor1)
        logger.info("Product with produce_code : {} has already been registered or in process of registeration".format(ProductCode))
        return True
    except:
        return False

def check_minimum_selling_amount(transaction_executor, Product):
    min_selling_amount = Product["MinimumSellingAmount"]
    cases_per_container = Constants.PALLETS_PER_CONTAINER * Constants.CASES_PER_PALLETE
    if min_selling_amount%cases_per_container == 0:
        return True
    else:
        logger.info("Invalind Minimum Selling Amount! Make it multple of : {}".format(cases_per_container))
        return False

def register_product(transaction_executor, product,person_id):
    ## check if the vaccine with GTIN already exist 
    # scentity_id = get_scentityid_from_personid(transaction_executor,person_id)

    logger.info("Person_id: {}".format(person_id))
    if get_scentityid_from_personid(transaction_executor,person_id):
        scentity_id = product['ManufacturerId']
        actual_scentity_id = get_scentityid_from_personid(transaction_executor,person_id)
        if actual_scentity_id == scentity_id:
            logger.info("Matched for authorization!")
            if get_document_approval_status(transaction_executor,Constants.SCENTITY_TABLE_NAME,scentity_id):
                logger.info("Entity is Approved to register product!")
                ProductCode = product["ProductCode"]
                if product_exist(transaction_executor, ProductCode):
                    logger.info(" Product already exists.")
                else:
                    if check_minimum_selling_amount(transaction_executor,product):
                        result = insert_documents(transaction_executor, Constants.PRODUCT_TABLE_NAME, [product])
                        product_id = result[0]
                        product_request_id = create_mcg_request(transaction_executor,product_id, person_id,2)
                        logger.info("Request was created for product Id : {} with product request id {}".format(product_id, product_request_id))
                        return product_id , product_request_id
                    else:
                        logger.info("This amount indicates number of products in the container.")
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
            'ProductCode': "00123451000015", #GTIN for Vaccine with NDC National Drug Code
            'ProductNamee': "Moderna Vaccine",
            'ProductPrice': 10,
            'MinimumSellingAmount':100, #minimum selling amount must be one container <<---- this denoted how many vaccines will be available in a container
            'ProductExpiry': 120, #in days
            'ProductStorage': {
                'LowThreshTemp': 0, #in degrees Centigrate
                'HighThreshTemp': 10, #in degree Centigrate
                'HighThreshHumidity': 40 # percentage   
            },
            'ManufacturerId': "A8714Mqp6tg73ZXHvdfiYL", #change this <<<<---------------------------
            'isApprovedBySuperAdmin':False,
            'BatchTableId': ''
            }

            # must be passed down as a prop from the react state
            person_id = "9RWotYRRT3l6WTbCAXdlZj"             #change this <<<<---------------------------
            driver.execute_lambda(lambda executor: register_product(executor, new_product, person_id))
    except Exception:
        logger.exception('Error registering product.')
