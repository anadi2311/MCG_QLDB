from logging import basicConfig, getLogger, INFO
from connect_to_ledger import create_qldb_driver
from amazon.ion.simpleion import dumps, loads
logger = getLogger(__name__)
basicConfig(level=INFO)

from functools import reduce
import itertools
import datetime
from constants import Constants
from create_index import create_index
from create_purchase_order_to_manufacturer import get_orderer_id
from register_person import get_scentityid_from_personid
from insert_document import insert_documents
from sampledata.sample_data import get_value_from_documentid,document_exist,update_document,convert_object_to_ion,get_document_ids
from check_container_safety import isContainerSafe
from export_customs_approval import document_already_approved_by_customs
from create_table import create_table


def inventory_table_already_exist(transaction_executor,scentity_id):
    inventory_table_name = "INVENTORY"+scentity_id
    statement = "SELECT * FROM information_schema.user_tables WHERE name = '{}'".format(inventory_table_name) 
    cursor = transaction_executor.execute_statement(statement)
    
    try:
        logger.info("Inventory table exist!")
        ret_val = list(map(lambda x: x.get('name'), cursor))    
        print(ret_val)     
        return ret_val
    except StopIteration:
        logger.info("Table does bot exist")
        return False


    
def product_exist_in_inventory(transaction_executor,inventory_table_name,product_id):
    statement = "SELECT * FROM {} AS i by id WHERE i.ProductId = ?".format(inventory_table_name)
    # print(statement)
    cursor = transaction_executor.execute_statement(statement,product_id)

    try:
        next(cursor)
        logger.info("Product exist")
        return True
    except StopIteration:
        logger.info("Product not found")
        return False

def generate_new_product_inventory(transaction_executor,inventory_table_name,product_id,product_instances,case_ids,pallete_ids,container_ids,delivered_product_quantity):
    inventory = {
        "ProductId":product_id,
        "ProductInstances": product_instances,
        "CaseIds":case_ids,
        "PalleteIds":pallete_ids,
        "ContainerIds":container_ids,
        "CurrentInventory": delivered_product_quantity,
        "MinimumSellingAmount":"",
        "ProductPrice":""
    }

    inventory_id = insert_documents(transaction_executor,inventory_table_name,convert_object_to_ion(inventory))
    return inventory_id


def insert_value_in_inventory_table(transaction_executor,inventory_table,field,inventory_id,value):
    statement = "FROM {} AS s by id WHERE id = '{}' INSERT INTO s.{} VALUE ?".format(inventory_table,inventory_id,field)
    cursor = transaction_executor.execute_statement(statement,value)

    try:
        next(cursor)
        logger.info("value inserted!")
    except StopIteration:
        logger.info("Problem inserting value in inventory table")

def update_current_product_inventory(transaction_executor,inventory_table_name,product_id,product_instances,case_ids,pallete_ids,container_ids,delivered_product_quantity):
    inventory_id = next(get_document_ids(transaction_executor,inventory_table_name,"ProductId",product_id))
    insert_value_in_inventory_table(transaction_executor,inventory_table_name,"CaseIds",inventory_id,case_ids)
    insert_value_in_inventory_table(transaction_executor,inventory_table_name,"PalleteIds",inventory_id,pallete_ids)
    insert_value_in_inventory_table(transaction_executor,inventory_table_name,"ContainerIds",inventory_id,container_ids)
    current_inventory = get_value_from_documentid(transaction_executor,inventory_table_name,inventory_id,"CurrentInventory")

    updated_inventory = int(current_inventory[0]) + delivered_product_quantity
    update_document(transaction_executor,inventory_table_name,"CurrentInventory",inventory_id,updated_inventory)


def update_product_inventory(transaction_executor,scentity_id,product_id,product_instances,case_ids,pallete_ids,container_ids,delivered_product_quantity):
    
    inventory_table_name = inventory_table_already_exist(transaction_executor,scentity_id)
    if inventory_table_name:
        pass
    else:
        inventory_table_name = "INVENTORY"+scentity_id
        create_table(transaction_executor,inventory_table_name)
        create_index(transaction_executor,inventory_table_name,"ProductId") 

    if product_exist_in_inventory(transaction_executor,inventory_table_name,product_id):
        update_current_product_inventory(transaction_executor,inventory_table_name,product_id,product_instances,case_ids,pallete_ids,container_ids,delivered_product_quantity)
        logger.info("inventory was updated")
        ## update the inventory by amount and insert the container_id, pallete,cases
    else:
        inventory_id = generate_new_product_inventory(transaction_executor,inventory_table_name,product_id,product_instances,case_ids,pallete_ids,container_ids,delivered_product_quantity)
        logger.info("New inventory was added for product. Reference Id:{}".format(inventory_id))
        ## insert document


def oneDArray(x):
    return list(itertools.chain(*x))

def approve_order_delivery(transaction_executor,purchase_order_id,person_id):
    if document_exist(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,purchase_order_id):
        orderer_id = get_orderer_id(transaction_executor,purchase_order_id)
        actual_sc_entity_id = get_scentityid_from_personid (transaction_executor,person_id)
        order_quantity = get_value_from_documentid(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,purchase_order_id,"OrderQuantity")        
        product_id = get_value_from_documentid(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,purchase_order_id,"ProductId")
        if actual_sc_entity_id == orderer_id:
            delivered_container_ids = []
            delivered_pallete_ids = []
            delivered_cases_ids = []
            delivered_product_instances = []
            delivered_product_quantity = 0
            container_ids = get_value_from_documentid(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,purchase_order_id,"HighestPackagingLevelIds")
            invoice_id = get_value_from_documentid(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,purchase_order_id,"InvoiceId")
            update_document(transaction_executor, Constants.INVOICE_TABLE_NAME, "Approval.isInvoiceApprovedForPayment", invoice_id[0],True)
            update_document(transaction_executor, Constants.INVOICE_TABLE_NAME, "Approval.ApproverId", invoice_id[0],True)

            for container_id in container_ids[0]:
                
                certificate_of_origin_id = get_value_from_documentid(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_id,"CertificateOfOriginId")
                packing_list_id = get_value_from_documentid(transaction_executor, Constants.CONTAINER_TABLE_NAME,container_id,"PackingListId")
                if isContainerSafe:

                    is_container_delivered = get_value_from_documentid(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_id,"isDelivered")
                    if is_container_delivered == [0]:
              
                        import_custom_approved = (document_already_approved_by_customs(transaction_executor,"ImportApproval",Constants.CERTIFICATE_OF_ORIGIN_TABLE_NAME,certificate_of_origin_id[0]) and
                        document_already_approved_by_customs(transaction_executor,"ImportApproval", Constants.PACKING_LIST_TABLE_NAME,packing_list_id[0]))

                        if import_custom_approved:
                            update_document(transaction_executor,Constants.CONTAINER_TABLE_NAME,"isDelivered",container_id,True)
                            lorry_reciepts = get_value_from_documentid(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_id,"LorryRecieptIds")
                            update_document(transaction_executor,Constants.LORRY_RECEIPT_TABLE_NAME,"isDeliveryDone",lorry_reciepts[0][-1],True)
                            update_document(transaction_executor,Constants.LORRY_RECEIPT_TABLE_NAME,"DeliveryTime",lorry_reciepts[0][-1],datetime.datetime.now().timestamp())
                            delivered_container_ids.append(container_id)
                            
                            packing_list_id= get_value_from_documentid(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_id,"PackingListId")
                            pallete_ids = get_value_from_documentid(transaction_executor,Constants.PACKING_LIST_TABLE_NAME,packing_list_id[0],"PalleteIds")
                            # pallete_ids = oneDArray(pallete_ids)
                            delivered_pallete_ids.append(pallete_ids[0])
                            case_ids = get_value_from_documentid(transaction_executor,Constants.PACKING_LIST_TABLE_NAME,packing_list_id[0],"CasesIds")
                            case_ids = oneDArray(case_ids[0])
                            
                            delivered_cases_ids.append(case_ids)
                            product_quantity = get_value_from_documentid(transaction_executor,Constants.PACKING_LIST_TABLE_NAME,packing_list_id[0],"ProductQuantity")
                            # print(product_quantity[0])
                            delivered_product_quantity = delivered_product_quantity + int(product_quantity[0][0])

                            
                            for case_id in case_ids:

                                product_instances = get_value_from_documentid(transaction_executor,Constants.CASES_TABLE_NAME,case_id,"ProductInstances")
                                delivered_product_instances.append(product_instances[0])
                        else:
                            raise ValueError("Container Not Approved by Import Customs")
                    else:
                        raise Exception("Container Already Delivered")
                else:
                    logger.info("A L A R M================C O N T A I N E R=======N O T=======S A F E ==========")
            delivered_pallete_ids = reduce(lambda x,y: x+y, delivered_pallete_ids)
            delivered_cases_ids = reduce(lambda x,y: x+y, delivered_cases_ids)
            delivered_product_instances =  oneDArray(delivered_product_instances)
            containers_delivered = len(delivered_container_ids)
            
          
            invoice_id = get_value_from_documentid(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,purchase_order_id,"InvoiceId")
            if order_quantity[0] == containers_delivered:
            
                update_document(transaction_executor,Constants.INVOICE_TABLE_NAME,"OrderQuantity",invoice_id[0],containers_delivered)
                logger.info("all containers delivered without damage ")
            elif order_quantity[0] > containers_delivered:
                logger.info("{} containers were damaged in the tranport. Updating new order quantity and order value.".format(order_quantity[0]-containers_delivered))
                update_document(transaction_executor,Constants.INVOICE_TABLE_NAME,"OrderQuantity",invoice_id[0],containers_delivered)
                product_id = get_value_from_documentid(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,purchase_order_id,"ProductId")
                product_price = get_value_from_documentid(transaction_executor,Constants.PRODUCT_TABLE_NAME,product_id[0],"ProductPrice")
                new_order_value = containers_delivered*product_price[0]
                update_document(transaction_executor,Constants.INVOICE_TABLE_NAME,"OrderValue",invoice_id[0],new_order_value)
            
            ###### update inventory #####################
            update_product_inventory(transaction_executor,actual_sc_entity_id,product_id[0],delivered_product_instances,delivered_cases_ids,delivered_pallete_ids,delivered_container_ids,delivered_product_quantity)

            
        else:
            logger.info("Access Denied")
    else:
        logger.info("Purchase Order does not exist.")
    
    #check if person is authorized
    #check if container is safe
    #approve_delivery of that container
    #approve_deliver in L/R
    #create an inventory table for Distributor


if __name__ == '__main__': 
    try:
        with create_qldb_driver() as driver:

            purchaseorderid = '96EioUftVpm38ZeropGKef'
            buyerpersonsid = "6xA6lh8SJGl4vEEaQS3uAd"
            driver.execute_lambda(lambda executor: approve_order_delivery(executor, purchaseorderid,buyerpersonsid))
    except Exception:
        logger.exception('Error.')  


