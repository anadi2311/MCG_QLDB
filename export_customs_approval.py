from logging import basicConfig, getLogger, INFO
from connect_to_ledger import create_qldb_driver
from amazon.ion.simpleion import dumps, loads
logger = getLogger(__name__)
basicConfig(level=INFO)

import datetime
from constants import Constants
from sampledata.sample_data import convert_object_to_ion, get_value_from_documentid,document_exist,update_document
from register_person import get_scentityid_from_personid,get_index_number,get_document_superadmin_approval_status,get_scentity_contact
from check_container_safety import isContainerSafe


def document_already_approved_by_customs(transaction_executor, approval_type,document_table_name, document_id):
    statement = 'SELECT s.{}.isApprovedByCustoms FROM {} as s by id where id = ?'.format(approval_type,document_table_name)
    cursor = transaction_executor.execute_statement(statement, document_id)
    approval_status = list(map(lambda x: x.get("isApprovedByCustoms"), cursor))
    # print("isApprovedBy"+"{}".format(approval_type[:6])+"Customs")
    logger.info("{} of {} approval status : {}".format(approval_type, document_table_name, approval_status))
    

    if approval_status == [1]:
        logger.info(" approved")
        return True
    else:
        logger.info("not approved")
        return False


def custom_approval(transaction_executor,container_id,approval_type,customs_person_id):
    if document_exist(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_id):
        scentity_id = get_scentityid_from_personid(transaction_executor,customs_person_id)
        ## we will just check if person is a custom agent. and then airway bill/bill of lading will be made from the point where custom agen works
        print(scentity_id)
        scentity_type_code = get_value_from_documentid(transaction_executor,Constants.SCENTITY_TABLE_NAME,scentity_id,"ScEntityTypeCode")
        if scentity_type_code[0] == '3':
            logger.info("Customs Agent confirmed")
            airway_bills = get_value_from_documentid(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_id,"AirwayBillIds")
            destination_id = get_value_from_documentid(transaction_executor,Constants.AIRWAY_BILL_TABLE_NAME,airway_bills[0][-1],"{}".format(approval_type[:6])+"AirportId")

            if scentity_id == destination_id[0]:
                logger.info("Custom Agent belongs to {} airport.".format(approval_type[:6]))
                
                if get_document_superadmin_approval_status(transaction_executor,Constants.SCENTITY_TABLE_NAME,scentity_id):
                    if isContainerSafe(transaction_executor,container_id):
                    ##check if container is safe:
                        certificateofOrigin = get_value_from_documentid(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_id,"CertificateOfOriginId")
                        packinglist = get_value_from_documentid(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_id,"PackingListId")
                        already_approved = (document_already_approved_by_customs(transaction_executor,approval_type,Constants.CERTIFICATE_OF_ORIGIN_TABLE_NAME,certificateofOrigin[0]) and
                        document_already_approved_by_customs(transaction_executor,approval_type, Constants.PACKING_LIST_TABLE_NAME,packinglist[0]))

                        if already_approved:
                            logger.info("Documents were already approved!")
                        else:
                            if approval_type == "ExportApproval":                                
                                lorry_reciepts = get_value_from_documentid(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_id,"LorryRecieptIds")
                                update_document(transaction_executor,Constants.LORRY_RECEIPT_TABLE_NAME,"isDeliveryDone",lorry_reciepts[0][-1],True)
                                update_document(transaction_executor,Constants.LORRY_RECEIPT_TABLE_NAME,"DeliveryTime",lorry_reciepts[0][-1],datetime.datetime.now().timestamp())
                            
                            update_document(transaction_executor,Constants.CERTIFICATE_OF_ORIGIN_TABLE_NAME,"{}.isApprovedByCustoms".format(approval_type),certificateofOrigin[0],True)
                            update_document(transaction_executor,Constants.CERTIFICATE_OF_ORIGIN_TABLE_NAME,"{}.ApproverId".format(approval_type),certificateofOrigin[0],customs_person_id)
                            update_document(transaction_executor,Constants.PACKING_LIST_TABLE_NAME,"{}.isApprovedByCustoms".format(approval_type),packinglist[0],True)
                            update_document(transaction_executor,Constants.PACKING_LIST_TABLE_NAME,"{}.ApproverId".format(approval_type),packinglist[0],customs_person_id)
                    else:
                        logger.info("====A L A R M ==== CANNOT APPROVE=== CONTAINER DANGEROUS====") 
                else:
                    logger.info("Airport not confirmed yet.")
            else:
                raise Exception("Custom Agent doesn't belong to this airport")

        elif scentity_type_code[0] == '4':
            logger.info("Customs Agent confirmed")
            bill_of_ladings = get_value_from_documentid(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_id,"BillOfLadingIds")
            destination_id = get_value_from_documentid(transaction_executor,Constants.BILL_OF_LADING_TABLE_NAME,bill_of_ladings[0][-1],"{}".format(approval_type[:6])+"portId")
            
            if scentity_id == destination_id[0]:
                logger.info("Custom Agent belongs to {} airport.".format(approval_type[:6]))
                
                if get_document_superadmin_approval_status(transaction_executor,Constants.SCENTITY_TABLE_NAME,scentity_id):
                    if isContainerSafe(transaction_executor,container_id):
                    ##check if container is safe:

                        certificateofOrigin = get_value_from_documentid(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_id,"CertificateOfOriginId")
                        packinglist = get_value_from_documentid(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_id,"PackingListId")
                        already_approved = (document_already_approved_by_customs(transaction_executor,approval_type,Constants.CERTIFICATE_OF_ORIGIN_TABLE_NAME,certificateofOrigin[0]) and
                        document_already_approved_by_customs(transaction_executor,approval_type, Constants.PACKING_LIST_TABLE_NAME,packinglist[0]))

                        if already_approved:
                            logger.info("Documents were already approved!")
                        else:
                            logger.info("approving CoO and PL")
                            lorry_reciepts = get_value_from_documentid(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_id,"LorryRecieptIds")
                            update_document(transaction_executor,Constants.LORRY_RECEIPT_TABLE_NAME,"isDeliveryDone",lorry_reciepts[0][-1],True)
                            update_document(transaction_executor,Constants.CERTIFICATE_OF_ORIGIN_TABLE_NAME,"{}.isApprovedByCustoms".format(approval_type),certificateofOrigin[0],True)
                            update_document(transaction_executor,Constants.CERTIFICATE_OF_ORIGIN_TABLE_NAME,"{}.ApproverId".format(approval_type),certificateofOrigin[0],customs_person_id)
                
                            update_document(transaction_executor,Constants.PACKING_LIST_TABLE_NAME,"{}.isApprovedByCustoms".format(approval_type),packinglist[0],True)
                            update_document(transaction_executor,Constants.PACKING_LIST_TABLE_NAME,"{}.ApproverId".format(approval_type),packinglist[0],customs_person_id)
                    else:
                        raise Exception("====A L A R M ==== CANNOT APPROVE=== CONTAINER DANGEROUS====") 
                else:
                    raise Exception("Airport not confirmed yet.")
            else:
                raise Exception("Agent not Authorized.")
        else:
            raise Exception("Person not Custom Agent")
    else:
       raise Exception("Container not found!")


if __name__ == '__main__': 
    try:
        with create_qldb_driver() as driver:

            containerid =   '9xSy20PlmQhF3GzgSLscGw' #'FHUUNgAj4bIHf92sVKzxI3'
            custompersonid = '2Zgr9lH9nouHafYYP5e5z5'
            approvaltype = 'ExportApproval'
            driver.execute_lambda(lambda executor: custom_approval(executor, containerid,approvaltype, custompersonid))
    except Exception:
        logger.exception('Error.')  
    
