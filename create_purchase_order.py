from logging import basicConfig, getLogger, INFO
from datetime import datetime
from connect_to_ledger import create_qldb_driver
from sampledata.sample_data import convert_object_to_ion, get_value_from_documentid
from constants import Constants
from create_product_batches import product_exists

from insert_document import insert_documents
from register_person import get_scentityid_from_personid,get_document_superadmin_approval_status,get_index_number

logger = getLogger(__name__)
basicConfig(level=INFO)



#createPurchaseOrder(transaction_executor,person_id,PurchaseOrderDetails) <<--------- insert Accepted,invoiceId,ContainerId from outside as variables
def create_purchase_order (transaction_executor, person_id, purchase_order_details):
    

    product_id = purchase_order_details["ProductId"]
    #check if the product exist and approved
    if product_exists(transaction_executor,product_id):
        # logger.info("Product Found!")
        order_quantity = purchase_order_details["OrderQuantity"]
        ##check if the product is approved
        if get_document_superadmin_approval_status(transaction_executor,Constants.PRODUCT_TABLE_NAME, product_id):
            #check if the orderQuantity is less than greater than
            if (isinstance(order_quantity,int)): #<<--------------- have to convery orderquantity to float  
                if order_quantity >= 1:
                    scentity_id = get_scentityid_from_personid(transaction_executor,person_id)
                    if scentity_id: 
                        #check if the orderer company is approved
                        if get_document_superadmin_approval_status(transaction_executor,Constants.SCENTITY_TABLE_NAME,scentity_id):
                            purchase_order_number = get_index_number(transaction_executor, Constants.PURCHASE_ORDER_TABLE_NAME,"PurchaseOrderNumber")
                            purchase_order_details.update({"PurchaseOrderNumber": purchase_order_number})
                            purchase_order_details['Orderer'].update({'OrdererScEntityId': scentity_id})
                            purchase_order_details['Orderer'].update({'OrdererPersonId': person_id})
                            sc_entity_type_code = get_value_from_documentid(transaction_executor,Constants.SCENTITY_TABLE_NAME,scentity_id,"ScEntityTypeCode")
                            if sc_entity_type_code[0] == "2" :## normal company
                                highest_packaging_level = "Container"
                            logger.info(purchase_order_details)
                            ## highest packagin level Id in this case is container since that is the minimum amount that distributor has to order
                            purchase_order = {**purchase_order_details,"Acceptor":{"isOrderAccepted":False,"AcceptorScEntityId":scentity_id,"ApprovingPersonId":""},"InvoiceId":"","HighestPackagingLevelIds":[],"HighestPackagingLevelType": highest_packaging_level}
                            purchase_order_id = insert_documents(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,convert_object_to_ion(purchase_order))

                            logger.info("Order was placed sucessfully with id: {}".format(purchase_order_id))
                            logger.info(" ================================== O R D E R =========== P L A C E D ===============================")
                            return purchase_order_id[0]
                        else:
                            logger.info("OrdererComany is not approved by the Admin.")
                    else:
                        logger.info("check if person id is associated with an entity.")
                else:
                    logger.info("Order quantity cannot be zero.")
            else:
                logger.info("Order Quantity can only be in the form of integers.")
        else:
            logger.info("Product is not approved yet. Wait for the product to get approved first.")
    else:
        logger.info(" Product Id is wrong!")
    

def get_orderer_id(transaction_executor, purchase_order_id):
    query = "SELECT t.Orderer.OrdererScEntityId FROM PurchaseOrders as t BY d_id WHERE d_id = ?"
    cursor_three = transaction_executor.execute_statement(query, purchase_order_id)
    
    value = list(map(lambda x: x.get("OrdererScEntityId"), cursor_three))
    logger.info("Orderer's Id is {}".format(value))
    return value[0]

if __name__ == '__main__':

    try:
        with create_qldb_driver() as driver:
            purchaseorderdetails = {
                "PurchaseOrderNumber":"",
                "ProductId":"60bq1j1hcbq2nAZWKyWAbX",
                "OrderQuantity" : 2, ## <<------- must be in integer and refers to number of containers ordered (In this case total vaccines ordered are 100)
                "Orderer":{
                    "OrdererScEntityId":"",
                    "OrdererPersonId" :""
                },
                "isOrderShipped":False,
            }
            # must be passed down as a prop from the react state
            person_id = "8qGdFJhMN4h9M8KnQSI2ku"             #change this <<<<---------------------------
            driver.execute_lambda(lambda executor: create_purchase_order(executor, person_id,purchaseorderdetails))
    except Exception:
        logger.exception('Error creating order.')

