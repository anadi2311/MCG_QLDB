from logging import basicConfig, getLogger, INFO
from connect_to_ledger import create_qldb_driver
from amazon.ion.simpleion import dumps, loads
logger = getLogger(__name__)
basicConfig(level=INFO)

import datetime
from constants import Constants
from create_purchase_order import get_orderer_id
from register_person import get_scentityid_from_personid
from sampledata.sample_data import get_value_from_documentid,document_exist,update_document
from check_container_safety import isContainerSafe
from create_table import create_table
# from export_transport_product import create_lorry_reciept, update_document_in_container


def approve_order_delivery(transaction_executor,purchase_order_id,person_id):
    
    if document_exist(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,purchase_order_id):
        orderer_id = get_orderer_id(transaction_executor,purchase_order_id)
        actual_sc_entity_id = get_scentityid_from_personid (transaction_executor,person_id)
        order_quantity = get_value_from_documentid(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,purchase_order_id,"OrderQuantity")        

        delivered_container_ids = []
        if actual_sc_entity_id == orderer_id:
            container_ids = get_value_from_documentid(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,purchase_order_id,"ContainerIds")
            for container_id in container_ids[0]:
                if isContainerSafe:
                    update_document(transaction_executor,Constants.CONTAINER_TABLE_NAME,"isDelivered",container_id,True)
                    lorry_reciepts = get_value_from_documentid(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_id,"LorryRecieptIds")
                    update_document(transaction_executor,Constants.LORRY_RECEIPT_TABLE_NAME,"isDeliveryDone",lorry_reciepts[-1][0],True)
                    update_document(transaction_executor,Constants.LORRY_RECEIPT_TABLE_NAME,"DeliveryTime",lorry_reciepts[-1][0],datetime.datetime.now().timestamp())
                    delivered_container_ids.append(container_id)
                else:
                    logger.info("A L A R M================C O N T A I N E R=======N O T=======S A F E ==========")
            
            containers_delivered = len(delivered_container_ids)
            
            if order_quantity[0] == containers_delivered:
                invoice_id = get_value_from_documentid(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,purchase_order_id,"InvoiceId")
                update_document(transaction_executor,Constants.INVOICE_TABLE_NAME,"OrderQuantity",invoice_id[0],containers_delivered)
                logger.info("all containers delivered without damage ")
            elif order_quantity[0] > containers_delivered:
                logger.info("{} containers were damaged in the tranport. Updating new order quantity and order value.".format(order_quantity[0]-containers_delivered))
                update_document(transaction_executor,Constants.INVOICE_TABLE_NAME,"OrderQuantity",invoice_id[0],containers_delivered)
                product_id = get_value_from_documentid(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,purchase_order_id,"ProductId")
                product_price = get_value_from_documentid(transaction_executor,Constants.PRODUCT_TABLE_NAME,product_id[0],"ProductPrice")
                new_order_value = containers_delivered*product_price[0]
                update_document(transaction_executor,Constants.INVOICE_TABLE_NAME,"OrderValue",invoice_id[0],new_order_value)

        

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

            purchaseorderid = 'InjUlzwdM0iFFLICMJzj3o'
            buyerpersonsid = ""
            driver.execute_lambda(lambda executor: approve_order_delivery(executor, purchaseorderid,buyerpersonsid))
    except Exception:
        logger.exception('Error.')  


