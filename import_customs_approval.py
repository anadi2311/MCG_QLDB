

from logging import basicConfig, getLogger, INFO
from connect_to_ledger import create_qldb_driver
from amazon.ion.simpleion import dumps, loads
logger = getLogger(__name__)
basicConfig(level=INFO)

import datetime
from constants import Constants
from sampledata.sample_data import convert_object_to_ion, get_value_from_documentid,document_exist,update_document
from register_person import get_scentityid_from_personid,get_index_number,get_document_superadmin_approval_status,get_scentity_contact
from export_customs_approval import document_already_approved_by_customs,custom_approval
from approve_airwaybill_bol import lading_bill_already_approved



def approve_import_customs(transaction_executor,conatiner_id,customs_person_id,warehouse_id):
    certificate_of_origin_id = get_value_from_documentid(transaction_executor,Constants.CONTAINER_TABLE_NAME,conatiner_id,"CertificateOfOriginId")
    packing_list_id = get_value_from_documentid(transaction_executor, Constants.CONTAINER_TABLE_NAME,conatiner_id,"PackingListId")
    export_custom_approved = (document_already_approved_by_customs(transaction_executor,"ExportApproval",Constants.CERTIFICATE_OF_ORIGIN_TABLE_NAME,certificate_of_origin_id[0]) and
    document_already_approved_by_customs(transaction_executor,"ExportApproval", Constants.PACKING_LIST_TABLE_NAME,packing_list_id[0]))  

    if export_custom_approved:
        import_custom_approved = (document_already_approved_by_customs(transaction_executor,"ImportApproval",Constants.CERTIFICATE_OF_ORIGIN_TABLE_NAME,certificate_of_origin_id[0]) and
        document_already_approved_by_customs(transaction_executor,"ImportApproval", Constants.PACKING_LIST_TABLE_NAME,packing_list_id[0]))

        logger.info(import_custom_approved)
        if import_custom_approved:
            logger.info("Already approved by import customs")
        else:
            print("=============")
            custom_approval(transaction_executor,conatiner_id,"ImportApproval",customs_person_id)
            airway_bill_ids = get_value_from_documentid(transaction_executor,Constants.CONTAINER_TABLE_NAME,conatiner_id,"AirwayBillIds")
            update_document(transaction_executor,Constants.AIRWAY_BILL_TABLE_NAME,"isDelivered",airway_bill_ids[0][-1],True)
            update_document(transaction_executor,Constants.AIRWAY_BILL_TABLE_NAME,"WarehouseId",airway_bill_ids[0][-1],warehouse_id)
    else:
        logger.info(" ======Not===Approved=======By==========Export=========")

if __name__ == '__main__': 
    try:
        with create_qldb_driver() as driver:

            containerid = 'JZeiTO95m9cHzpzYbvTgQn'
            custompersonid = 'BlFTzO07Kz44HVQtYKLHnl'
            warehouseid = 'XYTTH'
            driver.execute_lambda(lambda executor: approve_import_customs(executor, containerid,custompersonid,warehouseid))
    except Exception:
        logger.exception('Error.')  

    
