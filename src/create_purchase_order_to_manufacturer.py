from logging import basicConfig, getLogger, INFO
from datetime import datetime
from connect_to_ledger import create_qldb_driver
from sampledata.sample_data import convert_object_to_ion, get_value_from_documentid,document_exist
from constants import Constants
from create_product_batches import product_exists

from insert_document import insert_documents
from register_person import get_scentityid_from_personid,get_document_superadmin_approval_status,get_index_number

logger = getLogger(__name__)
basicConfig(level=INFO)



#createPurchaseOrder(transaction_executor,person_id,PurchaseOrderDetails) <<--------- insert Accepted,invoiceId,ContainerId from outside as variables
def create_purchase_order_to_manufacturer (transaction_executor, person_id, purchase_order_details):
    

    product_id = purchase_order_details["ProductId"]
    #check if the product exist and approved
    if product_exists(transaction_executor,product_id):
        # logger.info("Product Found!")
        order_quantity = purchase_order_details["OrderQuantity"]
        ##check if the product is approved
        if get_document_superadmin_approval_status(transaction_executor,Constants.PRODUCT_TABLE_NAME, product_id):
            #check if the orderQuantity is less than greater than
            if (isinstance(order_quantity,int)): #<<--------------- have to convery orderquantity to float  
                min_selling_amount_containers = get_value_from_documentid(transaction_executor,Constants.PRODUCT_TABLE_NAME,product_id,"MinimumSellingAmount")
                if order_quantity >= min_selling_amount_containers[0]:
                    scentity_id = get_scentityid_from_personid(transaction_executor,person_id)
                    if scentity_id: 
                        #check if the orderer company is approved
                        if get_document_superadmin_approval_status(transaction_executor,Constants.SCENTITY_TABLE_NAME,scentity_id):
                            purchase_order_number = get_index_number(transaction_executor, Constants.PURCHASE_ORDER_TABLE_NAME,"PurchaseOrderNumber")
                            purchase_order_details.update({"PurchaseOrderNumber": purchase_order_number})
                            purchase_order_details.update({"OrderType": "1"}) ## order type 1 is by distributor to manufacturer
                                                                                ## order type 2 is to distributor by downstream entities
                            purchase_order_details['Orderer'].update({'OrdererScEntityId': scentity_id})
                            purchase_order_details['Orderer'].update({'OrdererPersonId': person_id})
                            sc_entity_type_code = get_value_from_documentid(transaction_executor,Constants.SCENTITY_TABLE_NAME,scentity_id,"ScEntityTypeCode")
                            if sc_entity_type_code[0] == "2" :## normal company
                                highest_packaging_level = "Container"
                            # logger.info(purchase_order_details)
                            
                            product_id = purchase_order_details["ProductId"]
                            manufacturer_id = get_value_from_documentid(transaction_executor,Constants.PRODUCT_TABLE_NAME,product_id,"ManufacturerId")
        
                            ## highest packagin level Id in this case is container since that is the minimum amount that distributor has to order

                            purchase_order = {**purchase_order_details,"Acceptor":{"isOrderAccepted":False,"AcceptorScEntityId":manufacturer_id[0],"ApprovingPersonId":""},"InvoiceId":"","HighestPackagingLevelIds":[],"HighestPackagingLevelType": highest_packaging_level}
                            purchase_order_id = insert_documents(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,convert_object_to_ion(purchase_order))

                            # logger.info("Order was placed sucessfully with id: {}".format(purchase_order_id))
                            logger.info(" ================================== O R D E R =========== P L A C E D ===============================")
                            return purchase_order_id[0]
                        else:
                            raise Exception("OrdererComany is not approved by the Admin.")
                    else:
                        raise Exception("check if person id is associated with an entity.")
                else:
                    raise Exception("Order quantity cannot be less than minimum quantity.")
            else:
                raise Exception("Order Quantity can only be in the form of integers.")
        else:
            raise Exception("Product is not approved yet. Wait for the product to get approved first.")
    else:
        raise Exception(" Product Id is wrong!")
    

def get_orderer_id(transaction_executor, purchase_order_id):
    query = "SELECT t.Orderer.OrdererScEntityId FROM PurchaseOrders as t BY d_id WHERE d_id = ?"
    cursor_three = transaction_executor.execute_statement(query, purchase_order_id)
    
    value = list(map(lambda x: x.get("OrdererScEntityId"), cursor_three))
    # logger.info("Orderer's Id is {}".format(value))
    return value[0]

def get_sub_details(transaction_executor,table, sub, document_id,field):
    if document_exist(transaction_executor, table,document_id):
        statement = "SELECT t.{} FROM {} as t BY d_id WHERE d_id = ?".format(sub+ "."+field,table)
        cursor = transaction_executor.execute_statement(statement,document_id)   
        value = list(map(lambda x: x.get('{}'.format(field)), cursor))
        return value
    else:
        raise Exception('Document not found!')
        
    

if __name__ == '__main__':
    
    try:
        with create_qldb_driver() as driver:
            purchaseorderdetails = {
                "PurchaseOrderNumber":"",
                "ProductId":"BFJKrHD3JBH0VPR609Yvds",
                "OrderQuantity" : 2, ## <<------- number of containers orered ## keep this 2 because max transaction limit is 2
                "Orderer":{
                    "OrdererScEntityId":"",
                    "OrdererPersonId" :""
                },
                "isOrderShipped":False,
                "OrderType":""
            }
            # must be passed down as a prop from the react state
            person_id = "6rq5FLKmPdVJi7fpGk5BEp"             #change this <<<<---------------------------
            driver.execute_lambda(lambda executor: create_purchase_order_to_manufacturer(executor, person_id,purchaseorderdetails))
    except Exception:
        logger.exception('Error creating order.')

        

