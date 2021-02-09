from logging import basicConfig, getLogger, INFO
from connect_to_ledger import create_qldb_driver
from amazon.ion.simpleion import dumps, loads
logger = getLogger(__name__)
basicConfig(level=INFO)

from constants import Constants
from register_person import get_scentityid_from_personid
from approve_delivery import inventory_table_already_exist,product_exist_in_inventory
from sampledata.sample_data import update_document,get_document_ids

def update_price_and_minimum_selling_amount(transaction_executor, product_id, minimum_selling_amount,new_product_price,distributor_person_id):
    # check if person has scentity
    actual_sc_entity_id = get_scentityid_from_personid(transaction_executor, distributor_person_id)
    if actual_sc_entity_id:
        # check if sc entity has inventory table and product_id
        inventory_table = inventory_table_already_exist(transaction_executor,actual_sc_entity_id)
        if inventory_table:
            #check product exist with distributor
            if product_exist_in_inventory(transaction_executor,inventory_table[0],product_id):    
                ## minimum selling amount is in number of cases
                inventory_id =  next(get_document_ids(transaction_executor,inventory_table[0],"ProductId",product_id))
                print(inventory_id)
                update_document(transaction_executor,inventory_table[0],"ProductPrice",inventory_id, new_product_price)
                update_document(transaction_executor,inventory_table[0],"MinimumSellingAmount",inventory_id, minimum_selling_amount)

                logger.info("=================== P R I C E === A N D ==== S E L L I N G ++++ A M O U N T ======= U P D A T E D ========")
            
            else:
                raise Exception("Product does not exist in inventory!")
        else:
            raise Exception("No inventory table exist")
    else:
        raise Exception("No SCentity for the person")



if __name__ == '__main__': 
    try:
        with create_qldb_driver() as driver:
            
            productid = "BFJKrHD3JBH0VPR609Yvds" 
            minimumsellingamount = 1       # in number of containers
            newproductprice = 20 # price per container
            distributorpersonid = "6rq5FLKmPdVJi7fpGk5BEp"
            driver.execute_lambda(lambda executor: update_price_and_minimum_selling_amount(executor,productid, minimumsellingamount,newproductprice,distributorpersonid))
    except Exception:
        logger.exception('Error accepting the order.') 