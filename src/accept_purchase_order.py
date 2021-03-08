from logging import basicConfig, getLogger, INFO
import datetime
from connect_to_ledger import create_qldb_driver
from sampledata.sample_data import convert_object_to_ion, get_value_from_documentid,document_exist,update_document,get_document_ids
from constants import Constants
from create_product_batches import product_exists

from insert_document import insert_documents
from register_person import get_scentityid_from_personid,get_index_number
from approve_delivery import inventory_table_already_exist

logger = getLogger(__name__)
basicConfig(level=INFO)


def order_already_accepted(transaction_executor,purchase_order_id):
    statement= 'SELECT t.Acceptor.isOrderAccepted FROM PurchaseOrders as t BY d_id WHERE d_id = ?' 
    cursor = transaction_executor.execute_statement(statement,purchase_order_id)
    value = list(map(lambda x: x.get('isOrderAccepted'), cursor))
    if value == [1]:
        return True
    else:
        return False


def create_purchase_order_input(transaction_executor,purchase_order_id,actual_sc_entity_id):
    product_id = get_value_from_documentid(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,purchase_order_id,"ProductId")
    # number of container if order type is 1 and number of dosage if order type is 2
    order_quantity = get_value_from_documentid(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,purchase_order_id,"OrderQuantity")

    order_type = get_value_from_documentid(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,purchase_order_id,"OrderType")
    products_per_container = get_value_from_documentid(transaction_executor,Constants.PRODUCT_TABLE_NAME,product_id[0],"ProductsPerContainer")

    if order_type[0] == "1":
        product_price = get_value_from_documentid(transaction_executor,Constants.PRODUCT_TABLE_NAME,product_id[0],"ProductPrice")
    elif order_type[0] == "2":
        inventory_table = inventory_table_already_exist(transaction_executor,actual_sc_entity_id)
        product_id = get_value_from_documentid(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,purchase_order_id,"ProductId")
        inventory_id =  next(get_document_ids(transaction_executor,inventory_table[0],"ProductId",product_id[0]))
        product_price = get_value_from_documentid(transaction_executor,inventory_table[0],inventory_id,"ProductPrice")


    purchase_order_input = {
        "ProductId": product_id[0],
        "OrderQuantity": order_quantity[0],
        "OrderValue": order_quantity[0]*product_price[0]*products_per_container[0]
    }
    # logger.info(purchase_order_input)
    return purchase_order_input

def create_invoice(transaction_executor, purchase_order_input):
    invoice_number = get_index_number(transaction_executor,Constants.INVOICE_TABLE_NAME,"InvoiceNumber")
    invoice =  {
        "InvoiceNumber":"{}".format(invoice_number),
        "ProductId": purchase_order_input["ProductId"],
        "OrderQuantity": purchase_order_input["OrderQuantity"],
        "OrderValue": purchase_order_input["OrderValue"],
        "Approval":{
            "ApproverId":"",
            "isInvoiceApprovedForPayment":False
        },
        "isInvoicePayed":False,
        "TimeOfInvoiceGeneration":datetime.datetime.now().timestamp()
    }

    invoice_id = insert_documents(transaction_executor,Constants.INVOICE_TABLE_NAME,convert_object_to_ion(invoice))
    # logger.info("Invoice was created with invoice id {}".format(invoice_id[0]))
    return invoice_id[0]

def update_approving_person_id(transaction_executor,person_id, purchase_order_id):
    statement = "UPDATE PurchaseOrders AS j BY id SET j.Acceptor.ApprovingPersonId = '{}' WHERE id = '{}'".format(person_id,purchase_order_id)
    cursor  = transaction_executor.execute_statement(statement)
    try:
        next(cursor)
        logger.info("Updated!")
    except StopIteration:
        raise Exception("Problem in updating")

def get_sub_details(transaction_executor,table, sub, document_id,field):
    statement = "SELECT t.{} FROM {} as t BY d_id WHERE d_id = ?".format(sub+ "."+field,table)
    # print(statement)
    cursor = transaction_executor.execute_statement(statement,document_id)   
    value = list(map(lambda x: x.get('{}'.format(field)), cursor))

    print(value)
    return value

def accept_order(transaction_executor,purchase_order_id,person_id):
    if document_exist(transaction_executor, Constants.PURCHASE_ORDER_TABLE_NAME,purchase_order_id):
        if order_already_accepted(transaction_executor,purchase_order_id):
            raise Exception("Order Already Accepted!")
        else:
            required_scentity_id = get_sub_details(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,"Acceptor",purchase_order_id,"AcceptorScEntityId")
            actual_scentity_id = get_scentityid_from_personid(transaction_executor,person_id)
            if required_scentity_id[0] == actual_scentity_id:
                # logger.info("Matched!")
                purchase_order_input = create_purchase_order_input(transaction_executor,purchase_order_id,actual_scentity_id)
                invoice_id = create_invoice(transaction_executor,purchase_order_input)

                update_statement = "UPDATE {} AS po BY id SET po.InvoiceId = '{}' WHERE id = ?".format(Constants.PURCHASE_ORDER_TABLE_NAME,invoice_id)
                cursor = transaction_executor.execute_statement(update_statement,purchase_order_id)

                update_document(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,"Acceptor.isOrderAccepted",purchase_order_id,True)
                update_document(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,"Acceptor.ApprovingPersonId",purchase_order_id,person_id)
                try:
                    next(cursor)
                    logger.info(" ================================== O R D E R =========== A C C E P T E D ===============================")
                    # logger.info("Invoice is updated!")
                    return invoice_id
                except StopIteration:
                    raise Exception("Problem updating invoice")
            else:
                raise Exception("You are not authorized to accept this order.")
    else:
        raise Exception("Trouble finding Purchase Order!")

if __name__ == '__main__': 
    try:
        with create_qldb_driver() as driver:
            
            purchaseorderid = "HFv3NtoURu42E8H0MzNfag"        
            person_id = "2UMpePTU2NvF1hh3XKJDtd"
            driver.execute_lambda(lambda executor: accept_order(executor, purchaseorderid, person_id))
    except Exception:
        logger.exception('Error accepting the order.')  
        