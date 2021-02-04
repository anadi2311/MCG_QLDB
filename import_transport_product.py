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
from export_customs_approval import document_already_approved_by_customs

def deliver_product(transaction_executor,container_id,pick_up_person_id):
    if document_exist(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_id):
    #check if container_exist
        certificate_of_origin_id = get_value_from_documentid(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_id,"CertificateOfOriginId")
        packing_list_id = get_value_from_documentid(transaction_executor, Constants.CONTAINER_TABLE_NAME,container_id,"PackingListId")
        import_custom_approved = (document_already_approved_by_customs(transaction_executor,"ImportApproval",Constants.CERTIFICATE_OF_ORIGIN_TABLE_NAME,certificate_of_origin_id[0]) and
        document_already_approved_by_customs(transaction_executor,"ImportApproval", Constants.PACKING_LIST_TABLE_NAME,packing_list_id[0]))

        if import_custom_approved:
            logger.info("Approved by Import!")
            if isContainerSafe(transaction_executor,container_id):
                actual_sc_entity_id = get_scentityid_from_personid(transaction_executor,pick_up_person_id)
                transport_type = get_value_from_documentid(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_id,"TransportType")
                print(transport_type)
                
                #check if container is safe
                if transport_type[0] == [1]:
                    airway_bills = get_value_from_documentid(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_id,"AirwayBillIds")

                    pick_up_scentity_id = get_value_from_documentid(transaction_executor,Constants.AIRWAY_BILL_TABLE_NAME,airway_bills[0][-1], "RecieverScEntityId")
                elif transport_type[0] == [2]:
                    bill_of_lading = get_value_from_documentid(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_id,"BillOfLadingIds")
                    pick_up_scentity_id = get_value_from_documentid(transaction_executor,Constants.BILL_OF_LADING_TABLE_NAME,bill_of_lading[0][-1],"RecieverScEntityId")

                if actual_sc_entity_id == pick_up_scentity_id[0]:
                    logger.info("Authorized!")
                    if transport_type[0] == [1]:
                        is_picked_up = get_value_from_documentid( transaction_executor,Constants.AIRWAY_BILL_TABLE_NAME,airway_bills[0][-1],"RecieverApproval.isApproved")
                        if is_picked_up[0] == 0:
                            update_document(transaction_executor,Constants.AIRWAY_BILL_TABLE_NAME,"RecieverApproval.isApproved",airway_bills[0][-1],True)
                            update_document(transaction_executor,Constants.AIRWAY_BILL_TABLE_NAME,"RecieverApproval.ApproverId",airway_bills[0][-1], pick_up_person_id)
                            pick_up_location = get_value_from_documentid(transaction_executor,Constants.AIRWAY_BILL_TABLE_NAME,airway_bills[0][-1],"ImportAirportName")
                            consignee_id = get_value_from_documentid(transaction_executor,Constants.AIRWAY_BILL_TABLE_NAME,airway_bills[0][-1],"SenderScEntityId")
                        else:
                            raise Exception("container already picked up")

                    elif transport_type[0] == [2]:
                        is_picked_up = get_value_from_documentid( transaction_executor,Constants.AIRWAY_BILL_TABLE_NAME,bill_of_lading[0][-1],"RecieverApproval.isApproved")
                        if is_picked_up[0] == 0:
                            update_document(transaction_executor,Constants.BILL_OF_LADING_TABLE_NAME,"RecieverApproval.isApproved",bill_of_lading[0][-1],True)
                            update_document(transaction_executor,Constants.BILL_OF_LADING_TABLE_NAME,"RecieverApproval.ApproverId",bill_of_lading[0][-1], pick_up_person_id)
                            pick_up_location = get_value_from_documentid(transaction_executor,Constants.BILL_OF_LADING_TABLE_NAME,bill_of_lading[0][-1],"ImportPortName")
                            consignee_id = get_value_from_documentid(transaction_executor,Constants.BILL_OF_LADING_TABLE_NAME,bill_of_lading[0][-1],"SenderScEntityId")
                        else:
                            raise Exception("Container Already picked up")

                    consignee_name = get_value_from_documentid(transaction_executor,Constants.SCENTITY_TABLE_NAME,consignee_id[0],"ScEntityName")
                    delivery_location = get_scentity_contact(transaction_executor,actual_sc_entity_id[0],"Address")
                    lorry_reciepts = get_value_from_documentid(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_id,"LorryRecieptIds")
                    carrier_id = get_value_from_documentid(transaction_executor,Constants.LORRY_RECEIPT_TABLE_NAME,lorry_reciepts[0][-1],"CarrierId")
                    if carrier_id[0] == pick_up_scentity_id[0]:
                        logger.info("No request was made by buyer to pickup. Creating a new L/R to initiate import delivery.")
                        lorry_reciept_id = create_lorry_reciept(transaction_executor,actual_sc_entity_id,pick_up_person_id,pick_up_location[0],delivery_location,consignee_id,consignee_name,True)
                        update_document_in_container(transaction_executor,container_id,"LorryRecieptIds",lorry_reciept_id[0])
                    else:
                        logger.info("Pick up request was made by new carrier assigned by buyer.")
                        update_document(transaction_executor,Constants.LORRY_RECEIPT_TABLE_NAME,"isPickedUp",lorry_reciepts[0][-1],True)
                else:
                    logger.info("Not Authorized!")
            else:
                raise Exception("Container Not Safe!")
        else:
            raise Exception("Not approved by Customs.")
    else:
        logger.info("Not Authorized!")
            #check if pick up person is authorized


if __name__ == '__main__': 
    try:
        with create_qldb_driver() as driver:

            containerid = "0AdAXocWBM4C8Xhxm9lqLa" #96EioNwSjcq8HKLBRjcvPp
            pickuppersonid = "DdM1T0ZclFM5Wo7VDKfAFn"
            driver.execute_lambda(lambda executor: deliver_product(executor, containerid, pickuppersonid))
    except Exception:
        logger.exception('Error.')  