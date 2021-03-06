from logging import basicConfig, getLogger, INFO
from datetime import datetime
from connect_to_ledger import create_qldb_driver
from sampledata.sample_data import get_document_ids, print_result
from constants import Constants


from sampledata.sample_data import convert_object_to_ion
from insert_document import insert_documents
from register_person import get_scentityid_from_personid, create_mcg_request, get_document_superadmin_approval_status

logger = getLogger(__name__)
basicConfig(level=INFO)


    # logger.info('Entity with id : {} is not approved by')
    ## in case of vaccine it is GTIN Containing NDC_Code

def product_exist(transaction_executor, ProductCode):


    query = 'SELECT * FROM Products as pr WHERE pr.ProductCode = ?'
    cursor1 = transaction_executor.execute_statement(query,convert_object_to_ion(ProductCode))
    try:
        next(cursor1)
        # logger.info("Product with produce_code : {} has already been registered or in process of registeration".format(ProductCode))
        return True
    except:
        return False

def check_products_per_container_and_selling_amount(transaction_executor, Product):
    products_per_container = Product["ProductsPerContainer"]
    cases_per_container = Constants.PALLETS_PER_CONTAINER * Constants.CASES_PER_PALLETE
    minimum_selling_amount = Product["MinimumSellingAmount"]
    if products_per_container%cases_per_container == 0 and minimum_selling_amount > 0:
        return True
    else:
        # logger.info("This amount indicates number of products in the container")
        return False

def register_product(transaction_executor, product,person_id):
    ## check if the vaccine with GTIN already exist 
    # scentity_id = get_scentityid_from_personid(transaction_executor,person_id)

    logger.info("Person_id: {}".format(person_id))
    actual_scentity_id = get_scentityid_from_personid(transaction_executor,person_id)
    if actual_scentity_id:
        product.update({'ManufacturerId':actual_scentity_id})
            # logger.info("Matched for authorization!")
        if get_document_superadmin_approval_status(transaction_executor,Constants.SCENTITY_TABLE_NAME,actual_scentity_id):
            logger.info("Entity is Approved to register product!")
            ProductCode = product["ProductCode"]
            if product_exist(transaction_executor, ProductCode):
                raise Exception(" Product already exists.")
            else:
                if check_products_per_container_and_selling_amount(transaction_executor,product):
                    result = insert_documents(transaction_executor, Constants.PRODUCT_TABLE_NAME, [product])
                    product_id = result[0]
                    product_request_id = create_mcg_request(transaction_executor,product_id, person_id,2)
                    # logger.info("Request was created for product Id : {} with product request id {}".format(product_id, product_request_id))
                    logger.info(" ================================== P R O D U C T =========== R E G I S T R A T I O N ========== B E G A N=====================")
                    return product_id , product_request_id
                else:
                    cases_per_container = Constants.PALLETS_PER_CONTAINER * Constants.CASES_PER_PALLETE
                    raise Exception("Invalid ProductsPerContainer! Make it multple of : {}".format(cases_per_container))
        else:
            raise Exception("Entity not approved yet. Cannot register the product")
    else:
        raise Exception("You don't belong to any entity")


if __name__ == '__main__':

    try:
        with create_qldb_driver() as driver:
            new_product = {
            'ProductCode': "00123451000015", #GTIN for Vaccine with NDC National Drug Code
            'ProductName': "Moderna Vaccine",
            'ProductPrice': 10,
            'MinimumSellingAmount':2, #minimum selling amount in container 
            'ProductsPerContainer':100, #<<---- It denotes how many vaccines will be available in a container <<-- 100 vaccines per container
            'ProductExpiry': 120, #in days
            'ProductStorage': {
                'LowThreshTemp': 0, #in degrees Centigrate
                'HighThreshTemp': 10, #in degree Centigrate
                'HighThreshHumidity': 40 # percentage   
            },
            'ProductHSTarriffNumber':'HGJSI123123',#Used for catergorizing products in export
            'ManufacturerId': "JELcNyhcpCkBe7PCXFkgjI", #change this <<<<---------------------------
            'isApprovedBySuperAdmin':False,
            'BatchTableId': ''
            }

            # must be passed down as a prop from the react state
            person_id = "2UMpePTU2NvF1hh3XKJDtd"             #change this <<<<---------------------------
            driver.execute_lambda(lambda executor: register_product(executor, new_product, person_id))
    except Exception:
        logger.exception('Error registering product.')
