from logging import basicConfig, getLogger, INFO
from datetime import datetime
from connect_to_ledger import create_qldb_driver
# from sampledata.sample_data import get_document_ids, print_result
from constants import Constants


from sampledata.sample_data import convert_object_to_ion, get_value_from_documentid
from create_index import create_index
from insert_document import insert_documents
from register_person import get_scentityid_from_personid, get_document_superadmin_approval_status, get_index_number


logger = getLogger(__name__)
basicConfig(level=INFO)


#create_vaccine_batch(product_id,batch --> batchSno.no.,qty, expiry date, 
#product_new_batch

def get_list_of_productids(transaction_executor,ManufacturerId):
    query = 'SELECT * FROM Products as p by id WHERE p.ManufacturerId = ?'
    cursor = transaction_executor.execute_statement(query,ManufacturerId)
    try:
        next(cursor)
        product_ids = list(map(lambda x: x.get('id'), cursor))
        logger.info("product ids sold by {} are : {}".format(ManufacturerId,product_ids))
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
    ManufacturerId = get_value_from_documentid(transaction_executor, Constants.PRODUCT_TABLE_NAME,product_id,"ManufacturerId")
    logger.info("actual_id: {} and manufactuter id : {}".format(actual_scentity_id,ManufacturerId))

    if actual_scentity_id == ManufacturerId[0]:
        logger.info("Authorized!!")
        return True
    else:
        logger.info("Ids not matched!")
        return False


def create_batch_table(transaction_executor,product_id):
    table_name = "Batches" + product_id
    logger.info("table_name for {} batches is {}".format(product_id,table_name))
    statement = 'CREATE TABLE {}'.format(table_name)
    cursor = transaction_executor.execute_statement(statement)
    ret_val = list(map(lambda x: x.get('tableId'), cursor))
    ret_val = ret_val[0]
    logger.info('Tabled Id is {}'.format(ret_val))
    create_index(transaction_executor,table_name,"BatchNo") #<<----------- this could be the problem
    return ret_val
    
def update_BatchTableId(transaction_executor,product_id,batch_table_id):
    update_statement = " UPDATE Products AS p BY id SET p.BatchTableId =? WHERE id = ?"
    cursor = transaction_executor.execute_statement(update_statement, batch_table_id, product_id)
    try:
        next(cursor)
    except:
        logger.info(" Batch id couldn't be updated")


def batch_table_exist(transaction_executor, product_id):
    query = 'SELECT p.BatchTableId FROM Products as p by id WHERE id = ?'
    cursor = transaction_executor.execute_statement(query,product_id)
    ret_val = list(map(lambda x: x.get('BatchTableId'), cursor))
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



def generate_inventory( transaction_executor,product_id,batch):

    if batch_table_exist(transaction_executor,product_id):
        BatchTableId =batch_table_exist(transaction_executor,product_id)
        logger.info("Batch Table Found : {}!".format(BatchTableId)) 
    else:
        BatchTableId = create_batch_table(transaction_executor,product_id)
        logger.info("Batch Table was created with the id: {}".format(BatchTableId))
        update_BatchTableId(transaction_executor,product_id,BatchTableId)

    # get table name from table_id 
    batch_table_name = get_tableName_from_tableId(transaction_executor,BatchTableId)
    batch_num = get_index_number(transaction_executor,batch_table_name,"BatchNo")
    print("batch number is {}".format(batch_num))
    batch['BatchNo'] = batch_num
    batch['UnitsProduced'] = len(batch["ProductInstances"])
    batch['UnitsRemaining'] = int(batch['UnitsProduced'])
    # print(batch)
    statement = 'INSERT INTO {} ?'.format(batch_table_name)
    cursor =  transaction_executor.execute_statement(statement,convert_object_to_ion(batch))
    
    try:
        next(cursor)
        logger.info(" Vaccine Inventory was added.")
    except StopIteration:
        logger.info("Problem in generating Inventory.")


def create_vaccine_batch(transaction_executor, person_id,product_id,batch):
    
    ##check if the ProductCode exists
    if product_exists(transaction_executor,product_id):
        ##check if the product is approved by superadmin
        if get_value_from_documentid(transaction_executor,Constants.PRODUCT_TABLE_NAME, product_id,"isApprovedBySuperAdmin"):
            ##check if the person_id is authorized to create the product
            if person_authorized_to_create_product(transaction_executor,product_id,person_id):
                generate_inventory(transaction_executor,product_id,batch)
                logger.info(" ================================== B A T C H =========== R E G I S T E R E D  ===============================")
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
                'BatchNo' :'', #<<--- autoincremented batch numbers from 1 
                'UnitsProduced':1000, # make this automatic by counting length of product instances
                'UnitsRemaining':"",
                'MfgDate':datetime.today().strftime('%Y-%m-%d'),
                'ProductInstances': list(range(1,101)), #Create 100 vaccines with SNO from 1 to 100 ==> can be changed with actual Alphanumeric SNo
                'CaseIds':[]
            }

            person_id = "2UMpePTU2NvF1hh3XKJDtd"
            product_id = "BFJKrHD3JBH0VPR609Yvds"

            driver.execute_lambda(lambda executor: create_vaccine_batch(executor, person_id,product_id, batch))
    except Exception:
        logger.exception('Error creating inventories!')
