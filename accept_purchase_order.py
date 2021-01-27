from logging import basicConfig, getLogger, INFO
from datetime import datetime
from connect_to_ledger import create_qldb_driver
from sampledata.sample_data import convert_object_to_ion, get_value_from_documentid,document_exist,update_document
from constants import Constants
from create_product_batches import product_exists

from insert_document import insert_documents
from register_person import get_scentityid_from_personid,get_index_number

logger = getLogger(__name__)
basicConfig(level=INFO)


#check if PO exist


#check if person_id belongs to SCEntity for which order is accepted

#check if order already accepted
# def order_already_accepted(transaction_executor,purchase_order_id):
#     value = get_value_from_documentid(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,purchase_order_id,"Acceptor.isOrderAccepted")
#     logger.info("Orderer accepted is {}".format(value))
#     if value == [0]:
#         return False
#     else:
#         return True
def order_already_accepted(transaction_executor,purchase_order_id):
    statement= 'SELECT t.Acceptor.isOrderAccepted FROM PurchaseOrders as t BY d_id WHERE d_id = ?' 
    cursor = transaction_executor.execute_statement(statement,purchase_order_id)
    value = list(map(lambda x: x.get('isOrderAccepted'), cursor))
    if value == [1]:
        return True
    else:
        return False


def create_purchase_order_input(transaction_executor,purchase_order_id):
    product_id = get_value_from_documentid(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,purchase_order_id,"ProductId")
    order_quantity = get_value_from_documentid(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,purchase_order_id,"OrderQuantity")
  
    product_price = get_value_from_documentid(transaction_executor,Constants.PRODUCT_TABLE_NAME,product_id[0],"ProductPrice")

    purchase_order_input = {
        "ProductId": product_id[0],
        "OrderQuantity": order_quantity[0],
        "OrderValue": order_quantity[0]*product_price[0]
    }
    logger.info(purchase_order_input)
    return purchase_order_input

def create_invoice(transaction_executor, purchase_order_input):
    invoice_number = get_index_number(transaction_executor,Constants.INVOICE_TABLE_NAME,"InvoiceNumber")
    invoice =  {
        "InvoiceNumber":"{}".format(invoice_number),
        "ProductId": purchase_order_input["ProductId"],
        "OrderQuantity": purchase_order_input["OrderQuantity"],
        "OrderValue": purchase_order_input["OrderValue"],
        "Approval":{
            "approverId":"",
            "isInvoiceApprovedForPayment":False
        },
        "isInvoicePayed":False,
        "TimeOfInvoiceGeneration":datetime.today().strftime('%Y-%m-%d')
    }

    invoice_id = insert_documents(transaction_executor,Constants.INVOICE_TABLE_NAME,convert_object_to_ion(invoice))
    logger.info("Invoice was created with invoice id {}".format(invoice_id[0]))
    return invoice_id[0]

def update_approving_person_id(transaction_executor,person_id, purchase_order_id):
    statement = "UPDATE PurchaseOrders AS j BY id SET j.Acceptor.ApprovingPersonId = '{}' WHERE id = '{}'".format(person_id,purchase_order_id)
    cursor  = transaction_executor.execute_statement(statement)
    try:
        next(cursor)
        logger.info("Updated!")
    except StopIteration:
        logger.info("Problem in updating")
## Assign container --> 
#       create cases table -->take out batch which has vaccines left and assign in the array --> put 10 cases in container 
## update containerId and Invoice Id

def accept_order(transaction_executor,purchase_order_id,person_id):
    if document_exist(transaction_executor, Constants.PURCHASE_ORDER_TABLE_NAME,purchase_order_id):
        if order_already_accepted(transaction_executor,purchase_order_id):
            logger.info("Order Already Accepted!")
        else:
            product_id = get_value_from_documentid(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,purchase_order_id,"ProductId")
            manufacturer_id = get_value_from_documentid(transaction_executor,Constants.PRODUCT_TABLE_NAME,product_id[0],"ManufacturerId")
            actual_scentity_id = get_scentityid_from_personid(transaction_executor,person_id)
            if manufacturer_id[0] == actual_scentity_id:
                logger.info("Matched!")
                purchase_order_input = create_purchase_order_input(transaction_executor,purchase_order_id)
                invoice_id = create_invoice(transaction_executor,purchase_order_input)

                update_statement = "UPDATE {} AS po BY id SET po.InvoiceId = '{}' WHERE id = ?".format(Constants.PURCHASE_ORDER_TABLE_NAME,invoice_id)
                cursor = transaction_executor.execute_statement(update_statement,purchase_order_id)

                update_document(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,"Acceptor.isOrderAccepted",purchase_order_id,True)
                try:
                    next(cursor)
                    logger.info("Invoice is updated!")
                except StopIteration:
                    logger.info("Problem updating invoice")

            else:
                logger.info("You are not authorized to accept this order.")

    else:
        logger.info("Trouble finding Purchase Order!")

if __name__ == '__main__': 
    try:
        with create_qldb_driver() as driver:
            
            purchaseorderid = "C1DYY8qp9N8Fx5M1VVNkLl"        
            person_id = "ChnkiwR6B4325uiSVdJlyQ"
            driver.execute_lambda(lambda executor: accept_order(executor, purchaseorderid, person_id))
    except Exception:
        logger.exception('Error accepting the order.')  
        