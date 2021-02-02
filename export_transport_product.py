from logging import basicConfig, getLogger, INFO
from connect_to_ledger import create_qldb_driver
from amazon.ion.simpleion import dumps, loads
logger = getLogger(__name__)
basicConfig(level=INFO)

import datetime
from constants import Constants
from register_person import get_index_number,get_scentityid_from_personid,get_scentity_contact
from insert_document import insert_documents
from sampledata.sample_data import convert_object_to_ion, get_value_from_documentid,document_exist,update_document

'''
suggestion - make another few funcitons for every company to delegate tasks to their employee's using their person id
for example --> a here carrier company can use assigntrucker(person_id) to acknowledge pick up. Truck driver of that person_id 
can use this pick_up_order. This function will have a check for trucker's person_id with original assigned person_id.
Right now scentityid will be checked.


We assume that any person of the carrier company can pickup the order
'''

def create_lorry_reciept(transaction_executor,carrier_id,truck_carrier_person_id,pick_up_location,delivery_location,consignee_id,consignee_name, is_Picked_Up):
    lrno = get_index_number(transaction_executor,Constants.LORRY_RECEIPT_TABLE_NAME,Constants.LORRY_RECEIPT_INDEX_NAME)
    lorry_reciept = {
        "LorryRecieptNumber": lrno ,
        "CarrierId":carrier_id,
        "TruckerId":truck_carrier_person_id,
        "ConsigneeId":consignee_id,
        "ConsigneeName": consignee_name,
        "PickUpLocation":pick_up_location,
        "DeliveryLocation":delivery_location,
        "PickUpTime": datetime.datetime.now().timestamp(),
        "DeliveryTime": "",
        "isPickedUp":is_Picked_Up,
        "isDeliveryDone":False
    }   

    lorry_reciept_id = insert_documents(transaction_executor, Constants.LORRY_RECEIPT_TABLE_NAME,convert_object_to_ion(lorry_reciept))
    logger.info("LR created: {}!".format(lorry_reciept_id))
    return lorry_reciept_id

def create_airway_bill(transaction_executor,sender_id, reciever_id,container_id, air_carrier_id,export_airport_id,import_airport_id):
    awbillno = get_index_number(transaction_executor,Constants.AIRWAY_BILL_TABLE_NAME,Constants.AIRWAY_BILL_INDEX_NAME)
    export_airport_name = get_value_from_documentid(transaction_executor,Constants.SCENTITY_TABLE_NAME,export_airport_id,"ScEntityName")
    import_airport_name = get_value_from_documentid(transaction_executor,Constants.SCENTITY_TABLE_NAME,import_airport_id,"ScEntityName")



    airway_bill = {
        "AirwayBillNumber" : awbillno,
        "CarrierId":air_carrier_id,
        "ContainerId":container_id,
        "AirCarrierApproval":{
            "isApproved":False,
            "ApproverId":""
        },
        "RecieverApproval":{
            "isApproved": False,
            "ApproverId":""
        },
        "SenderScEntityId":sender_id,
        "RecieverScEntityId":reciever_id,
        "isDelivered":False,
        "WarehouseId":"",
        "ExportAirportId":export_airport_id,
        "ExportAirportName":export_airport_name[0],
        "ImportAirportId":import_airport_id,
        "ImportAirportName":import_airport_name[0]
    }
    
    airway_bill_id = insert_documents(transaction_executor,Constants.AIRWAY_BILL_TABLE_NAME,convert_object_to_ion(airway_bill))
    return airway_bill_id

def create_bill_of_lading(transaction_executor,sender_id, reciever_id,container_id, sea_carrier_id,export_port_id,import_port_id):
    bolno =  get_index_number(transaction_executor,Constants.BILL_OF_LADING_TABLE_NAME,Constants.BILL_OF_LADING_INDEX_NAME)
    export_port_name = get_value_from_documentid(transaction_executor,Constants.SCENTITY_TABLE_NAME,export_port_id,"ScEntityName")
    import_port_name = get_value_from_documentid(transaction_executor,Constants.SCENTITY_TABLE_NAME,import_port_id,"ScEntityName")


    bill_of_lading = {
        "BillOfLadingNumber" : bolno,
        "CarrierId":sea_carrier_id,
        "Container_id":container_id,
        "SeaCarrierApproval":{
            "isApproved":False,
            "ApproverId":""
        },
        "RecieverApproval":{
            "isApproved": False,
            "ApproverId":""
        },
        "SenderScEntityId":sender_id,
        "RecieverScEntityId":reciever_id, # If the same carrier is transporting the container then reciever Id will be carrier id
        "isDelivered":False,
        "WarehouseId":"",
        "ExportPortId":export_port_id,
        "ExportPortName":export_port_name[0],
        "ImportPortId":import_port_id,
        "ImportPortName":import_port_name[0]
    }
    
    bill_of_lading_id = insert_documents(transaction_executor,Constants.BILL_OF_LADING_TABLE_NAME,convert_object_to_ion(bill_of_lading))
    return bill_of_lading_id


def update_document_in_container(transaction_executor,container_id,document_type,document_id):
    statement = "FROM {} AS s by id WHERE id = '{}' INSERT INTO s.{} VALUE ?".format(Constants.CONTAINER_TABLE_NAME,container_id,document_type)
    # print(statement)
    cursor = transaction_executor.execute_statement(statement, document_id)
    try:
        next(cursor)
        logger.info("Document inserted")
    except StopIteration:
        logger.info("Document cannot be inserted!")


# pick_up container requested by carrier ---> for every container that order entails
def pick_up_order(transaction_executor,purchase_order_id,truck_carrier_person_id, freight_carrier_id, export_location_id,import_location_id):
    container_ids = get_value_from_documentid(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,purchase_order_id,"ContainerIds")
    carrier_company_id = get_value_from_documentid(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_ids[0][0],"CarrierCompanyId")

    actual_sc_entity_id = get_scentityid_from_personid(transaction_executor,truck_carrier_person_id)

    if carrier_company_id[0]== actual_sc_entity_id:
        logger.info("Authorized!")
        product_id = get_value_from_documentid(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,purchase_order_id,"ProductId")
        product_id = product_id[0]
        manufacturer_id = get_value_from_documentid(transaction_executor,Constants.PRODUCT_TABLE_NAME,product_id,"ManufacturerId")
        manufacturer_name = get_value_from_documentid(transaction_executor,Constants.SCENTITY_TABLE_NAME,manufacturer_id[0],"ScEntityName")
        pick_up_location = get_scentity_contact(transaction_executor,manufacturer_id[0],"Address")
        delivery_location = get_scentity_contact(transaction_executor,export_location_id,"Address")
        logger.info("Pickup location is : {}".format(pick_up_location))
        for container_id in container_ids[0]:
            lorry_reciept_id = create_lorry_reciept(transaction_executor,actual_sc_entity_id,truck_carrier_person_id,pick_up_location[0],delivery_location[0],manufacturer_id,manufacturer_name,True)
            update_document_in_container(transaction_executor,container_id,"LorryRecieptIds",lorry_reciept_id[0])
            export_location_type = get_value_from_documentid(transaction_executor,Constants.SCENTITY_TABLE_NAME,export_location_id,"ScEntityTypeCode")##
            if export_location_type == ['3']:
                airway_bill_id = create_airway_bill(transaction_executor,manufacturer_id,actual_sc_entity_id, container_id, freight_carrier_id,export_location_id,import_location_id)
                update_document_in_container(transaction_executor,container_id,"AirwayBillIds",airway_bill_id[0])
            elif export_location_type == ['4']:
                bill_of_lading_id = create_bill_of_lading(transaction_executor,manufacturer_id,actual_sc_entity_id, container_id,freight_carrier_id,export_location_id,import_location_id)
                update_document_in_container(transaction_executor,container_id,"BillOfLadingIds",bill_of_lading_id[0])

        logger.info("=====================  O R D E R ====== P I C K E D ===================")
    else:
        logger.info("Person not authorized for the pickup")

# makes LR and give 
# custom clerance ( show CoO and PL) --> mark not cleared if IoT anamoly

# delivery is made... check it by sensor data as well
#

if __name__ == '__main__': 
    try:
        with create_qldb_driver() as driver:

            purchaseorderid = 'InjUlzwdM0iFFLICMJzj3o'
            truckcarrierpersonid = 'C6Xa4ZRJFzgARB3HkHqCeF'
            freightcarrierid = '' # id of the carrier that will take container to destination country --> can be same as truck carrier or different
            exportairportid = '543ZHjkBjfD4tKAuqa8mAV'
            importairportid =  '5EhcKRLYmsn9Ax7ITlhBs5'
            driver.execute_lambda(lambda executor: pick_up_order(executor, purchaseorderid,truckcarrierpersonid,freightcarrierid,exportairportid,importairportid))
    except Exception:
        logger.exception('Error.')  