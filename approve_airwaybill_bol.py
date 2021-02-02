from logging import basicConfig, getLogger, INFO
from connect_to_ledger import create_qldb_driver
logger = getLogger(__name__)
basicConfig(level=INFO)

import datetime
from constants import Constants
from sampledata.sample_data import get_value_from_documentid,document_exist,update_document
from register_person import get_scentityid_from_personid
from check_container_safety import isContainerSafe
from export_customs_approval import document_already_approved_by_customs

def lading_bill_already_approved(transaction_executor,approval_type,bill_id):
    if approval_type == "AirCarrierApproval":
        table = Constants.AIRWAY_BILL_TABLE_NAME
    else:
        table = Constants.BILL_OF_LADING_TABLE_NAME
    statement = 'SELECT s.{}.isApproved FROM {} as s by id where id = ?'.format(approval_type,table)
    cursor = transaction_executor.execute_statement(statement, bill_id)
    approval_status = list(map(lambda x: x.get("isApproved"), cursor))
    # print("isApprovedBy"+"{}".format(approval_type[:6])+"Customs")
    logger.info("approval status : {}".format(approval_status))

    if approval_status == [1] or approval_type == None:
        logger.info(" approved")
        return True
    else:
        logger.info("not approved")
        return False

def approve_lading_bill( transaction_executor, bill_id, carrier_person_id):
    
    ## check if bill exist 

    if document_exist(transaction_executor,Constants.AIRWAY_BILL_TABLE_NAME,bill_id):
        ## authenticate air_person
        actual_sc_entity_id = get_scentityid_from_personid(transaction_executor,carrier_person_id)
        air_carrier_id = get_value_from_documentid(transaction_executor,Constants.AIRWAY_BILL_TABLE_NAME,bill_id,"CarrierId")
        print(actual_sc_entity_id)
        print(air_carrier_id)
        if actual_sc_entity_id == air_carrier_id[0]:
            logger.info("Authorized!")
            container_id = get_value_from_documentid(transaction_executor,Constants.AIRWAY_BILL_TABLE_NAME,bill_id,"ContainerId")
            if lading_bill_already_approved(transaction_executor,"AirCarrierApproval",bill_id):
                logger.info("Already Approved!")
            else:
                if isContainerSafe(transaction_executor,container_id[0]):
                    certificate_of_origin_id = get_value_from_documentid(transaction_executor, Constants.CONTAINER_TABLE_NAME, container_id[0],"CertificateOfOriginId")
                    packing_list_id = get_value_from_documentid(transaction_executor, Constants.CONTAINER_TABLE_NAME, container_id[0],"PackingListId")
                    custom_approved = (document_already_approved_by_customs(transaction_executor,"ExportApproval",Constants.CERTIFICATE_OF_ORIGIN_TABLE_NAME,certificate_of_origin_id[0]) and
                    document_already_approved_by_customs(transaction_executor,"ExportApproval", Constants.PACKING_LIST_TABLE_NAME,packing_list_id[0]))
                    if custom_approved:

                        update_document(transaction_executor,Constants.AIRWAY_BILL_TABLE_NAME,"AirCarrierApproval.isApproved",bill_id,True)
                        update_document(transaction_executor,Constants.AIRWAY_BILL_TABLE_NAME,"AirCarrierApproval.ApproverId",bill_id, carrier_person_id)
                    else:
                        logger.info("Container not Approved By customs")
                else:
                    logger.info("====A L A R M ==== CANNOT APPROVE=== CONTAINER DANGEROUS====")
        else:
            logger.info("Not Authorized")
    
    elif document_exist(transaction_executor,Constants.BILL_OF_LADING_TABLE_NAME,bill_id):                
        ## authenticate Sea_person
        actual_sc_entity_id = get_scentityid_from_personid(transaction_executor,carrier_person_id)
        Sea_carrier_id = get_value_from_documentid(transaction_executor,Constants.BILL_OF_LADING_TABLE_NAME,bill_id,"SeaCarrierId")
        if actual_sc_entity_id == Sea_carrier_id[0]:
            logger.info("Authorized!")
            container_id = get_value_from_documentid(transaction_executor,Constants.BILL_OF_LADING_TABLE_NAME,bill_id,"ContainerId")
            if lading_bill_already_approved(transaction_executor,"SeaCarrierApproval",bill_id):
                logger.info("Already Approved!")
            else:
                if isContainerSafe(transaction_executor,container_id):
                    certificate_of_origin_id = get_value_from_documentid(transaction_executor, Constants.CONTAINER_TABLE_NAME, container_id[0],"CertificateOfOrigin")
                    packing_list_id = get_value_from_documentid(transaction_executor, Constants.CONTAINER_TABLE_NAME, container_id[0],"PackingList")
                    already_approved = (document_already_approved_by_customs(transaction_executor,"ExportApproval",Constants.CERTIFICATE_OF_ORIGIN_TABLE_NAME,certificate_of_origin_id[0]) and
                    document_already_approved_by_customs(transaction_executor,"ExportApproval", Constants.PACKING_LIST_TABLE_NAME,packing_list_id[0]))

                    if already_approved:    
                        update_document(transaction_executor,Constants.BILL_OF_LADING_TABLE_NAME,"SeaCarrierApproval.isApproved",bill_id,True)
                        update_document(transaction_executor,Constants.BILL_OF_LADING_TABLE_NAME,"SeaCarrierApproval.ApproverId",bill_id, carrier_person_id)
                    else:
                        logger.info("Container not Approved By customs")
                else:
                    logger.info("====A L A R M ==== CANNOT APPROVE=== CONTAINER DANGEROUS====")
        else:
            logger.info("Not Authorized")
    else:
        logger.info("Bill not found!")


if __name__ == '__main__': 
    try:
        with create_qldb_driver() as driver:

            airwaybillid = '3bZ9PlGBO7gItPScNwxD31'
            carrierpersonid = 'C6Xa4ZRJFzgARB3HkHqCeF'
            driver.execute_lambda(lambda executor: approve_lading_bill(executor, airwaybillid, carrierpersonid))
    except Exception:
        logger.exception('Error.')  


