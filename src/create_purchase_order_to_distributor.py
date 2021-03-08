from logging import basicConfig, getLogger, INFO
from connect_to_ledger import create_qldb_driver
from amazon.ion.simpleion import dumps, loads
logger = getLogger(__name__)
basicConfig(level=INFO)

from sampledata.sample_data import document_exist,get_value_from_documentid,get_document_ids,convert_object_to_ion
from insert_document import insert_documents
from constants import Constants
from register_person import get_scentityid_from_personid, get_index_number
from approve_delivery import inventory_table_already_exist,product_exist_in_inventory

## minimum selling amount is set by distributor in inventory table in the multiple of Cases for example 10 cases
## can only be ordered in multiple of cases ex 11


## create purchase order for hospital 
def create_purchase_order_to_distributor(transaction_executor,purchase_order_details,distributor_id,hospital_person_id):

    product_id = purchase_order_details["ProductId"]
    number_of_containers_ordered = purchase_order_details["OrderQuantity"]

    if document_exist(transaction_executor,Constants.SCENTITY_TABLE_NAME,distributor_id):
        # check person belong to ScEntity
        actual_sc_entity_id = get_scentityid_from_personid(transaction_executor, hospital_person_id)
        if actual_sc_entity_id:
            manufacturer_id = get_value_from_documentid(transaction_executor,Constants.PRODUCT_TABLE_NAME,product_id,"ManufacturerId")
            # print(manufacturer_id)
            if manufacturer_id[0] != distributor_id:
                # scentity_type_code = get_value_from_documentid(transaction_executor,Constants.SCENTITY_TABLE_NAME,distributor_id,"ScEntityTypeCode")
                # logger.info("Distributor confirmed")            
                inventory_table = inventory_table_already_exist(transaction_executor,distributor_id)
                if inventory_table:
                    #check product exist with distributor
                    if product_exist_in_inventory(transaction_executor,inventory_table[0],product_id):
                        # check number of dosage are in muliple of cases and more than minumum amount
                        inventory_id = next(get_document_ids(transaction_executor,inventory_table[0],"ProductId",product_id))
                        minimum_containers_order = get_value_from_documentid(transaction_executor,inventory_table[0],inventory_id,"MinimumSellingAmount")
            
                        if number_of_containers_ordered >= minimum_containers_order[0] and isinstance(number_of_containers_ordered,int):
                            
                            purchase_order_number = get_index_number(transaction_executor, Constants.PURCHASE_ORDER_TABLE_NAME,"PurchaseOrderNumber")
                            purchase_order_details.update({"OrderType": "2"})
                            purchase_order_details.update({"PurchaseOrderNumber": purchase_order_number})
                            purchase_order_details['Orderer'].update({'OrdererScEntityId': actual_sc_entity_id})
                            purchase_order_details['Orderer'].update({'OrdererPersonId': hospital_person_id})
                            purchase_order = {**purchase_order_details,"Acceptor":{"isOrderAccepted":False,"AcceptorScEntityId":distributor_id,"ApprovingPersonId":""},"InvoiceId":"","HighestPackagingLevelIds":[],"HighestPackagingLevelType": "Containers"}
                            purchase_order_id = insert_documents(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,convert_object_to_ion(purchase_order))
                            # logger.info("Order was placed sucessfully with id: {}".format(purchase_order_id))
                            logger.info(" ================================== O R D E R =========== P L A C E D ===============================")
                            return purchase_order_id[0]

                        else:
                            raise Exception("Number of dosage must be an integer and greater than {} ".format(minimum_containers_order))
                    else:
                        raise Exception("Distributor doesn't have this product.")
                else:
                    raise Exception("Distributor does not have any inventory")
            else:
                raise Exception("Order is being placed to wrong entity. Check Distributor_id")
        else:
            raise Exception("Check the person id!")
    else:
        raise Exception(" Check Distributor id!")



if __name__ == '__main__':
    
    try:
        with create_qldb_driver() as driver:
            purchaseorderdetails = {
                "PurchaseOrderNumber":"",
                "ProductId":"BFJKrHD3JBH0VPR609Yvds",
                "OrderQuantity" : 1, ## <<------- denotes number of conatienrs
                "Orderer":{
                    "OrdererScEntityId":"",
                    "OrdererPersonId" :""
                },
                "isOrderShipped":False,
                "OrderType":""
            }
            # must be passed down as a prop from the react state
            distributorid = "G8ijbJrPmL5BnoovlZVW73"
            hospitalpersonid = "6xA6lh8SJGl4vEEaQS3uAd"             #change this <<<<---------------------------
            driver.execute_lambda(lambda executor: create_purchase_order_to_distributor(executor,purchaseorderdetails,distributorid,hospitalpersonid))
    except Exception:
        logger.exception('Error creating order.')
