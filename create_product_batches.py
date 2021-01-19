from logging import basicConfig, getLogger, INFO
from datetime import datetime
from connect_to_ledger import create_qldb_driver
from sampledata.sample_data import get_document_ids, print_result
from constants import Constants


from sampledata.sample_data import convert_object_to_ion, get_value_from_documentid
from insert_document import insert_documents
from register_person import get_scentityid_from_personid, create_mcg_request, get_approval_status

logger = getLogger(__name__)
basicConfig(level=INFO)


#create_vaccine_batch(product_id,batch --> batchSno.no.,qty, expiry date, 
#product_new_batch

def get_list_of_productids(transaction_executor,manufacturer_id):
    query = 'SELECT * FROM Products as p by id WHERE p.manufacturer_id = ?'
    cursor = transaction_executor.execute_statement(query,manufacturer_id)
    try:
        next(cursor)
        product_ids = list(map(lambda x: x.get('id'), cursor))
        logger.info("product ids sold by {} are : {}".format(manufacturer_id,product_ids))
        return product_ids
    except StopIteration:
        logger.info("No product ids formed!")
        return False

def product_exists(transaction_executor, product_id):
    query = 'SELECT * FROM Products as p by id WHERE id = ?'
    cursor = transaction_executor.execute_statement(query,product_id)
    try:
        next(cursor)
        logger.info("Product exists!")
        return True
    except StopIteration:
        logger.info("Product not found! Please check the id!!")
        return False

def person_authorized_to_create_product(transaction_executor,product_id,person_id):
    actual_scentity_id = get_scentityid_from_personid(transaction_executor,person_id)
    manufacturer_id = get_value_from_documentid(transaction_executor, Constants.PRODUCT_TABLE_NAME,product_id,"manufacturer_id")
    logger.info("actual_id: {} and manufactuter id : {}".format(actual_scentity_id,manufacturer_id))

    if actual_scentity_id == manufacturer_id[0]:
        logger.info("Authorized!!")
        return True
    else:
        logger.info("Ids not matched!")
        return False

def create_batch_table(transaction_executor,product_id):
    table_name = product_id + "Batches"
    logger.info("table_name for {} batches is {}".format(product_id,table_name))
    statement = 'CREATE TABLE {}'.format(table_name)
    cursor = transaction_executor.execute_statement(statement)
    ret_val = list(map(lambda x: x.get('tableId'), cursor))
    ret_val = ret_val[0]
    logger.info('ret_val is {}'.format(ret_val))
    return ret_val
    
def update_batch_table_id(transaction_executor,product_id,batch_table_id):
    update_statement = " UPDATE Products AS p BY id SET p.batch_table_name =? WHERE id = ?"
    cursor = transaction_executor.execute_statement(update_statement, batch_table_id, product_id)
    try:
        next(cursor)
    except:
        logger.info(" Batch id couldn't be updated")


def batch_table_exist(transaction_executor, product_id):
    query = 'SELECT p.batch_table_id FROM Products as p by id WHERE id = ?'
    cursor = transaction_executor.execute_statement(query,product_id)
    ret_val = list(map(lambda x: x.get('batch_table_id'), cursor))
    print(ret_val)
    ret_val = ret_val[0]
    if len(ret_val) > 0:
        return ret_val
    else:
        return False


def get_tableName_from_tableId(transaction_executor, table_id):
    statement = 'SELECT name FROM information_schema.user_tables WHERE  tableId = ?' 
    cursor = transaction_executor.execute_statement(statement, table_id)
    ret_val = list(map(lambda x: x.get('name'), cursor))
    ret_val = ret_val[0]
    return ret_val

def batch_no_exist(transaction_executor,batch_table_name,batch_no):
    statement = 'SELECT FROM {} as b WHERE b.batch_no = ?'.format(batch_table_name)
    cursor = transaction_executor.execute_statement(statement,batch_no)
    try:
        next(cursor)
        return True
    except:
        logger.info("Batch Number not matched. Adding the new batch info ..")
        return False

def generate_inventory( transaction_executor,product_id,batch):

    if batch_table_exist(transaction_executor,product_id):
        batch_table_id =batch_table_exist(transaction_executor,product_id)
        logger.info("Batch Table Found : {}!".format(batch_table_id)) 
    else:
        batch_table_id = create_batch_table(transaction_executor,product_id)
        logger.info("Batch Table was created with the id: {}".format(batch_table_id))
        update_batch_table_id(transaction_executor,product_id,batch_table_id)

    # get table name from table_id 
    batch_table_name = get_tableName_from_tableId(transaction_executor,batch_table_id)
    if batch_no_exist(transaction_executor,batch_table_name,batch.batch_no):
        logger.info("Not allowed to repeat batch number. ")
    else:
        statement = 'INSERT INTO {} ?'.format(batch_table_name)
        cursor =  transaction_executor.execute_statement(statement,convert_object_to_ion(batch))

        try:
            next(cursor)
            logger.info(" Vaccine Inventory was added.")
        except StopIteration:
            logger.info("Problem in generating Inventory.")


def create_vaccine_batch(transaction_executor, person_id,product_id,batch):
    
    ##check if the product_code exists
    if product_exists(transaction_executor,product_id):
        ##check if the product is approved by superadmin
        if get_value_from_documentid(transaction_executor,Constants.PRODUCT_TABLE_NAME, product_id,"isApprovedBySuperAdmin"):
            ##check if the person_id is authorized to create the product
            if person_authorized_to_create_product(transaction_executor,product_id,person_id):
                generate_inventory(transaction_executor,product_id,batch)
            else:
                logger.info("You don't have authority for this product!")
        else:
            logger.info("Wait for product to be approved by SuperAdmin.")
    else:
        logger.info("Trouble finding product.")
   
   
if __name__ == '__main__':

    try:
        with create_qldb_driver() as driver:
            
            batch = {
                'batch_no':'1',
                'unitsProduced':100,
                'MfgDate':'YYMMDD',
                'productInstances': list(range(1,101)) #Create 100 vaccines with SNO from 1 to 100 ==> can be changed with actual Alphanumeric SNo
            }

            person_id = "ATP79apUuTW33whnMmwsad"
            product_id = "Dp04VJIoHUgJILB0bR8YoH"

            driver.execute_lambda(lambda executor: create_vaccine_batch(executor, person_id,product_id, batch))
    except Exception:
        logger.exception('Error creating inventories!')