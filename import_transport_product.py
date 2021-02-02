from logging import basicConfig, getLogger, INFO
from connect_to_ledger import create_qldb_driver
from amazon.ion.simpleion import dumps, loads
logger = getLogger(__name__)
basicConfig(level=INFO)

from constants import Constants
from register_person import get_scentityid_from_personid,get_scentity_contact
from sampledata.sample_data import get_value_from_documentid,document_exist,update_document
from check_container_safety import isContainerSafe
from export_transport_product import create_lorry_reciept, update_document_in_container

def deliver_product(transaction_executor,container_id,pick_up_person_id):
    if document_exist(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_id):
    #check if container_exist
        if isContainerSafe(transaction_executor,container_id):
            actual_sc_entity_id = get_scentityid_from_personid(transaction_executor,pick_up_person_id)
            transport_type = get_value_from_documentid(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_id,"TransportType")
            #check if container is safe
            if transport_type == 1:
                airway_bills = get_value_from_documentid(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_id,"AirwayBillIds")
                pick_up_scentity_id = get_value_from_documentid(transaction_executor,Constants.AIRWAY_BILL_TABLE_NAME,airway_bills[-1][0], "RecieverScEntityId")
            elif transport_type == 2:
                bill_of_lading = get_value_from_documentid(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_id,"BillOfLadingIds")
                pick_up_scentity_id = get_value_from_documentid(transaction_executor,Constants.BILL_OF_LADING_TABLE_NAME,bill_of_lading[-1][0],"RecieverScEntityId")

            if actual_sc_entity_id == pick_up_scentity_id[0]:
                logger.info("Authorized!")
                if transport_type == 1:
                    update_document(transaction_executor,Constants.AIRWAY_BILL_TABLE_NAME,"RecieverApproval.isApproved",airway_bills[-1][0],True)
                    update_document(transaction_executor,Constants.AIRWAY_BILL_TABLE_NAME,"RecieverApproval.ApproverId",airway_bills[-1][0], pick_up_person_id)
                    pick_up_location = get_value_from_documentid(transaction_executor,Constants.AIRWAY_BILL_TABLE_NAME,airway_bills[-1][0],"ImportAirportName")
                    consignee_id = get_value_from_documentid(transaction_executor,Constants.AIRWAY_BILL_TABLE_NAME,airway_bills[-1][0],"SenderScEntityId")

                elif transport_type == 2:
                    update_document(transaction_executor,Constants.BILL_OF_LADING_TABLE_NAME,"RecieverApproval.isApproved",bill_of_lading[-1][0],True)
                    update_document(transaction_executor,Constants.BILL_OF_LADING_TABLE_NAME,"RecieverApproval.ApproverId",bill_of_lading[-1][0], pick_up_person_id)
                    pick_up_location = get_value_from_documentid(transaction_executor,Constants.BILL_OF_LADING_TABLE_NAME,bill_of_lading[-1][0],"ImportPortName")
                    consignee_id = get_value_from_documentid(transaction_executor,Constants.BILL_OF_LADING_TABLE_NAME,bill_of_lading[-1][0],"SenderScEntityId")


                consignee_name = get_value_from_documentid(transaction_executor,Constants.SCENTITY_TABLE_NAME,consignee_id[0],"ScEntityName")
                delivery_location = get_scentity_contact(transaction_executor,actual_sc_entity_id[0],"Address")
                lorry_reciepts = get_value_from_documentid(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_id,"LorryRecieptIds")
                carrier_id = get_value_from_documentid(transaction_executor,Constants.LORRY_RECEIPT_TABLE_NAME,lorry_reciepts[-1][0],"CarrierId")
                if carrier_id[0] == pick_up_scentity_id:
                    logger.info("No request was made by buyer to pickup. Creating a new L/R to initiate import delivery.")
                    lorry_reciept_id = create_lorry_reciept(transaction_executor,actual_sc_entity_id,pick_up_person_id,pick_up_location[0],delivery_location,consignee_id,consignee_name,True)
                    update_document_in_container(transaction_executor,container_id,"LorryRecieptIds",lorry_reciept_id[0])
                else:
                    logger.info("Pick up request was made by new carrier assigned by buyer.")
                    update_document(transaction_executor,Constants.LORRY_RECEIPT_TABLE_NAME,"isPickedUp",lorry_reciepts[-1][0],True)
            else:
                logger.info("Not Authorized!")
        else:
            logger.info("Container Not Safe!")
    else:
        logger.info("Not Authorized!")
            #check if pick up person is authorized


if __name__ == '__main__': 
    try:
        with create_qldb_driver() as driver:

            containerid = ""
            pickuppersonid = ""
            driver.execute_lambda(lambda executor: deliver_product(executor, containerid, pickuppersonid))
    except Exception:
        logger.exception('Error.')  