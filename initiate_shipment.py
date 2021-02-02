from logging import basicConfig, getLogger, INFO
from connect_to_ledger import create_qldb_driver
from amazon.ion.simpleion import dumps, loads
import datetime
from sampledata.sample_data import convert_object_to_ion, get_value_from_documentid,document_exist,update_document
from constants import Constants
from insert_document import insert_documents
from register_person import get_scentityid_from_personid,get_index_number,get_document_approval_status,get_scentity_contact
from create_product_batches import get_tableName_from_tableId,batch_table_exist
from accept_purchase_order import order_already_accepted
import ast
import json

logger = getLogger(__name__)
basicConfig(level=INFO)


def create_case(transaction_executor, product_code, purchase_order_id,product_instances):
    s_no = get_index_number(transaction_executor,Constants.CASES_TABLE_NAME,"CaseNumber")
    case_number = "1"+str(product_code)+ str(s_no) #<<-----------level 1 denotes case level of product
    logger.info(case_number)
    case = {
        "CaseNumber":case_number,
        "PalleteId" : "",
        "PurchaseOrderId" : purchase_order_id,
        "ProductInstances":product_instances # this value should come from scanning the GTIN barcode of the products
    }
    case_id = insert_documents(transaction_executor,Constants.CASES_TABLE_NAME,[case])
    return case_id

def insert_caseIds (transaction_executor,batch_table_name,batch_id,case_id_values):
    statement = "FROM {} AS s by id WHERE id = '{}' INSERT INTO s.CaseIds VALUE ?".format(batch_table_name,batch_id)
    cursor = transaction_executor.execute_statement(statement, case_id_values)
    try:
        next(cursor)
        logger.info("Cases added!")
    except StopIteration:
        logger.info("Problem inserting case Ids")


def assign_products_into_case(transaction_executor,product_id,batch_table_name,product_units_ordered,products_per_case,purchase_order_id,product_code):

    statement = 'SELECT * FROM {} as b By id where b.UnitsRemaining > 0'.format(batch_table_name) 
    cursor = transaction_executor.execute_statement(statement)
    total_number_of_cases_required = int(product_units_ordered/products_per_case)
    current_number_of_cases_required = int(product_units_ordered/products_per_case)
    cases = []
    for batch in cursor:
        if current_number_of_cases_required > 0:
            current_batch = dumps(batch,binary=False)
            current_batch = current_batch[9:]
            current_batch = current_batch.replace('"','').replace('{','{"').replace('}','"}').replace(':','":"').replace(',','","').replace('[','["').replace(']','"]').replace('"[','[').replace(']"',']')
            current_batch_dict = ast.literal_eval(current_batch)
            # print(current_batch_dict)

            batch_inventory_left= current_batch_dict['UnitsRemaining']
            batch_inventory_left = int(batch_inventory_left)
            
            logger.info("current batch_inventory: {} ".format(batch_inventory_left))
            logger.info("{} cases will be filled for this order!".format(current_number_of_cases_required))

            product_instances = current_batch_dict['ProductInstances'] # change with 'ProductInstances'
            batch_id = current_batch_dict['id']
            logger.info("Filling a case from batch {}".format(batch_id))
            units_produced = int(current_batch_dict['UnitsProduced'])
            starting_case_number = len(cases)
            ending_case_number = len(cases)
            for case in range(len(cases)+1,int(total_number_of_cases_required)+1):
                if batch_inventory_left > 0:
                    case_product_instances = product_instances[(units_produced - batch_inventory_left) : (units_produced +int(products_per_case) - batch_inventory_left)]
                    logger.info(case_product_instances)
                    case_id = create_case(transaction_executor,product_code[0],purchase_order_id,case_product_instances)
                    logger.info("--------------------------------Case {} added----------------------------------".format(case))
                    cases.append(case_id[0])
                    batch_inventory_left = batch_inventory_left - products_per_case
                    current_number_of_cases_required = current_number_of_cases_required - 1
                    ending_case_number = ending_case_number + 1
                    if current_number_of_cases_required == 0:
                        update_document(transaction_executor,batch_table_name,"UnitsRemaining",batch_id,int(batch_inventory_left))
                        insert_caseIds(transaction_executor,batch_table_name,batch_id,cases[starting_case_number:ending_case_number])
                        # update_document(transaction_executor,batch_table_name,"CaseIds",batch_id,cases[starting_case_number:ending_case_number])
                else:
                    update_document(transaction_executor,batch_table_name,"UnitsRemaining",batch_id,int(batch_inventory_left))
                    insert_caseIds(transaction_executor,batch_table_name,batch_id,cases[starting_case_number:ending_case_number])                    
                    #update_document(transaction_executor,batch_table_name,"CaseIds",batch_id,cases[starting_case_number:ending_case_number])
                    logger.info("No inventory left! Moving to next batch to fill {} more cases".format(current_number_of_cases_required))
                    break
        else:     
            break

    logger.info("All the cases packed :{}".format(cases))
    return cases


def assign_cases_into_pallete(transaction_executor,case_ids,product_code):
    number_of_palletes_required = int(len(case_ids)/Constants.CASES_PER_PALLETE)
    starting_case_number = 0
    ending_case_number = int(Constants.CASES_PER_PALLETE)
    palletes = []
    for pallete in range(1,number_of_palletes_required+1):
        s_no = get_index_number(transaction_executor,Constants.PALLETE_TABLE_NAME,"PalleteNumber")
        pallete_number = "2"+str(product_code)+ str(s_no) #<<-----------level 2 denotes pallete level of product
        current_case_ids = case_ids[starting_case_number:ending_case_number]
        pallete = {
            "PalleteNumber":pallete_number,
            "CaseIds": current_case_ids,
            "ContainerId":""
        }
        pallete_id = insert_documents(transaction_executor,Constants.PALLETE_TABLE_NAME,convert_object_to_ion(pallete))
        palletes.append(pallete_id[0])
        starting_case_number = starting_case_number+Constants.CASES_PER_PALLETE
        ending_case_number = starting_case_number+ Constants.CASES_PER_PALLETE
        update_pallete_ids_in_cases(transaction_executor,current_case_ids,pallete_id)
    
    return palletes



def update_pallete_ids_in_cases(transaction_executor,case_ids,pallete_id):
    for case_id in case_ids:
        update_document(transaction_executor,Constants.CASES_TABLE_NAME,"PalleteId",case_id,pallete_id)

    logger.info("Successfully updated pallete ids in cases")




def create_certificate_of_origin(transaction_executor,product_id):
    product_name = get_value_from_documentid(transaction_executor,Constants.PRODUCT_TABLE_NAME,product_id,"ProductName")
    product_hs_tarriff = get_value_from_documentid(transaction_executor,Constants.PRODUCT_TABLE_NAME,product_id,"ProductHSTarriffNumber")
    manufacturer_id = get_value_from_documentid(transaction_executor,Constants.PRODUCT_TABLE_NAME,product_id,"ManufacturerId")
    manufacturer_name = get_value_from_documentid(transaction_executor,Constants.SCENTITY_TABLE_NAME,manufacturer_id[0],"ScEntityName")


    certificate_of_origin = {
        'CertificateOfOriginNumber':get_index_number(transaction_executor,Constants.CERTIFICATE_OF_ORIGIN_TABLE_NAME,"CertificateOfOriginNumber"),
        'ProductName':product_name,
        'Productid':product_id,
        'ProductHSTarriffNumber':product_hs_tarriff[0],
        'ManufacturerId':manufacturer_id,
        'ManufacturerName':manufacturer_name,
        'ManufacturerLocation':get_scentity_contact(transaction_executor,manufacturer_id,"Address"),
        'ExportApproval':{
            "ApproverId":"",
            "isApprovedByCustoms":False},
        'ImportApproval':{
            "ApproverId":"",
            "isApprovedByCustoms":False
        }}
    
    certificate_of_origin_id = insert_documents(transaction_executor,Constants.CERTIFICATE_OF_ORIGIN_TABLE_NAME,convert_object_to_ion(certificate_of_origin))
    logger.info("Certificate of Origin Created successfully!")
    return certificate_of_origin_id


def create_packing_list(transaction_executor, product_quantity,product_code,palleteIds):
        container_case_ids = []
        for palleteId in palleteIds:
            pallete_case_ids = get_value_from_documentid(transaction_executor,Constants.PALLETE_TABLE_NAME,palleteId,"CaseIds")
            container_case_ids.append(pallete_case_ids[0])
            
        packing_list = {
            "PackingListNumber":get_index_number(transaction_executor,Constants.PACKING_LIST_TABLE_NAME,"PackingListNumber"),
            "NumberOfPalletes":Constants.PALLETS_PER_CONTAINER,
            "PalleteIds":palleteIds,
            "NumberofCases":Constants.PALLETS_PER_CONTAINER*Constants.CASES_PER_PALLETE,
            "CasesIds": container_case_ids[0],
            "ProductCode": product_code[0],
            "ProductQuantity" : product_quantity[0],
            "ExportApproval":{
                        "ApproverId":"",
                        "isApprovedByCustoms":False},
            'ImportApproval':{
                        "ApproverId":"",
                        "isApprovedByCustoms":False

        }}

        packing_list_id = insert_documents(transaction_executor,Constants.PACKING_LIST_TABLE_NAME,packing_list)
        return packing_list_id[0]

def assign_palletes_into_container(transaction_executor,pallete_ids,product_code,purchase_order_id,carrier_company_id,certificate_of_origin_id,product_quantity,transport_type):
    number_of_containers_required = int(len(pallete_ids)/Constants.PALLETS_PER_CONTAINER)
    starting_pallete_number = 0
    ending_pallete_number = int(Constants.PALLETS_PER_CONTAINER) 
    '''
    here we are creating containers
    in actual scneario container will already be created with iot mapped on them by the SUPERADMIN
    '''

    containers = []
    for container in range(1,number_of_containers_required+1):
        s_no = get_index_number(transaction_executor,Constants.CONTAINER_TABLE_NAME,"ContainerNumber")
        container_number = "3"+str(product_code)+ str(s_no) #<<-----------level 3 denotes container level of product
        current_pallete_ids = pallete_ids[starting_pallete_number:ending_pallete_number]
        packing_list_id = create_packing_list(transaction_executor,product_quantity,product_code,current_pallete_ids)

        '''
        Here we are marking container safe when it is generated. In production we will need another file "mark_contaier_safe"
        Manufacturer person will fire this function --> it will fire check_container_safe to check from data of every iot if container is safe.
        '''

        container = {
            "ContainerNumber":container_number,
            "PurchaseOrderId" : purchase_order_id,
            "PalleteIds": current_pallete_ids,
            "ContainerSafety" : {"isContainerSafeForDelivery" : True,
                                 "LastCheckedAt": datetime.datetime.now().timestamp()},
            "CarrierCompanyId":carrier_company_id, ## this carrier is the company which takes in charge of complete frieght of the container that manufacturer chooses
            "TransportType":transport_type, #<<-------- 1 denotes air and 2 denotes ocean
            "PackingListId" : packing_list_id,
            "LorryRecieptIds" : [],
            "IotIds" : [],
            "AirwayBillIds": [],
            "BillOfLadingIds" : [],
            "CertificateOfOriginId":certificate_of_origin_id,
            "isDelivered":False
        }
        container_id = insert_documents(transaction_executor,Constants.CONTAINER_TABLE_NAME,convert_object_to_ion(container))
        containers.append(container_id[0])
        starting_pallete_number = starting_pallete_number+Constants.PALLETS_PER_CONTAINER
        ending_pallete_number = starting_pallete_number+ Constants.PALLETS_PER_CONTAINER
        update_container_ids_in_palletes(transaction_executor,current_pallete_ids,container_id)
    
    return containers

def update_container_ids_in_palletes(transaction_executor,pallete_ids,container_id):
    for pallete_id in pallete_ids:
        update_document(transaction_executor,Constants.PALLETE_TABLE_NAME,"ContainerId",pallete_id,container_id)

    logger.info("Successfully updated container ids in pallete")


def update_container_ids_in_purchase_order(transaction_executor,container_ids,purchase_order_id):
    update_document(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,"ContainerIds",purchase_order_id,container_ids)
    logger.info("Successfully updated conatiner ids in purchase order")

def enough_inventory_registered_for_order(transaction_executor, products_per_case,purchase_order_id, batch_table_name):
    container_order_quantity = get_value_from_documentid(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,purchase_order_id,"OrderQuantity")
    container_order_quantity = int(container_order_quantity[0])
    product_units_ordered = container_order_quantity*Constants.PALLETS_PER_CONTAINER*Constants.CASES_PER_PALLETE*int(products_per_case)

    statement = 'SELECT SUM(b.UnitsRemaining) as invrem FROM {} as b WHERE b.UnitsRemaining > 0'.format(batch_table_name)

    cursor = transaction_executor.execute_statement(statement)
    inventory_remaining = list(map(lambda x: x.get('invrem'), cursor))
    inventory_remaining = int(dumps(inventory_remaining[0],binary=False, indent='  ', omit_version_marker=True))

    if inventory_remaining >= product_units_ordered:
        logger.info(" Enough inventory to pack the order: {}!".format(inventory_remaining))
        return product_units_ordered
    else:
        logger.info("Not enough inventory!")
        return False

def shipment_already_started(transaction_executor,purchase_order_id):
    container_ids = get_value_from_documentid(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,purchase_order_id,"ContainerIds")

    if len(container_ids[0])>0:
        logger.info("Shipment already began. Following container ids were : {}".format(container_ids))
        return True
    else:
        return False


def initiate_shipment(transaction_executor, carrier_company_id, transport_type,purchase_order_id,person_id):
    if document_exist(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,purchase_order_id):
        logger.info("Purchase Order Found!")
        if get_document_approval_status(transaction_executor,Constants.SCENTITY_TABLE_NAME,carrier_company_id):
            product_id = get_value_from_documentid(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,purchase_order_id,"ProductId")
            product_id = product_id[0]
            manufacturer_id = get_value_from_documentid(transaction_executor,Constants.PRODUCT_TABLE_NAME,product_id,"ManufacturerId")
            actual_scentity_id = get_scentityid_from_personid(transaction_executor,person_id)
            if manufacturer_id[0] == actual_scentity_id:
                logger.info("Authorized!")
                batch_table_id = batch_table_exist(transaction_executor,product_id)
                if order_already_accepted(transaction_executor,purchase_order_id):
                    if shipment_already_started(transaction_executor,purchase_order_id):                    
                        logger.info('Shipment already started.')
                    else:
                        if batch_table_id:
                            batch_table_name = get_tableName_from_tableId(transaction_executor,batch_table_id)
                            min_selling_amount = get_value_from_documentid(transaction_executor,Constants.PRODUCT_TABLE_NAME,product_id,"MinimumSellingAmount")
                            products_per_case = round((min_selling_amount[0])/(Constants.CASES_PER_PALLETE*Constants.PALLETS_PER_CONTAINER))
                            logger.info("products_per_case is : {}".format(products_per_case))
                            product_units_ordered = enough_inventory_registered_for_order(transaction_executor,products_per_case,purchase_order_id,batch_table_name)
                            if product_units_ordered:
                                logger.info("Units Ordered are: {}".format(product_units_ordered))
                                update_document(transaction_executor,Constants.PURCHASE_ORDER_TABLE_NAME,"isOrderShipped",purchase_order_id,True)
                                product_code = get_value_from_documentid(transaction_executor,Constants.PRODUCT_TABLE_NAME,product_id,"ProductCode")
                                case_ids = assign_products_into_case(transaction_executor,product_id,batch_table_name,product_units_ordered,products_per_case,purchase_order_id,product_code)
                                pallete_ids = assign_cases_into_pallete(transaction_executor,case_ids,product_code)
                                certificate_of_origin_id = create_certificate_of_origin(transaction_executor,product_id)
                                product_quantity = get_value_from_documentid(transaction_executor,Constants.PRODUCT_TABLE_NAME,product_id,"MinimumSellingAmount")
                                container_ids = assign_palletes_into_container(transaction_executor,pallete_ids,product_code,purchase_order_id,carrier_company_id,certificate_of_origin_id[0],product_quantity,transport_type)
                                update_container_ids_in_purchase_order(transaction_executor,container_ids,purchase_order_id)

                                logger.info("===================== S H I P M E N T ======= I N I T I A T E D =======================")
                            else:
                                logger.info(" First produce and register the vaccines into the sytem before shipping them")
                        else: 
                            logger.info('Register the Batch table first by inputting inventory!')
                else:
                    logger.info("Accept the order first!")
            else:
                logger.info("Not authorized!")
        else:
            logger.info("Carrier company is not approved by MCG.")
    else:
        logger.info("order doesn't exist")

 
if __name__ == '__main__': 
    try:
        with create_qldb_driver() as driver:
            
            purchaseorderid = "Au1ElhG7Y8oK8VBXMjg1Eo"        
            personid = "FS8XQHgWCoY16Tgv8TD3Aa"
            carriercompanyid = "Jpbn2DXq18I6ggNj8AjbMB"
            transporttype = 1,
            driver.execute_lambda(lambda executor: initiate_shipment(executor, carriercompanyid,transporttype,purchaseorderid, personid))
    except Exception:
        logger.exception('Error accepting the order.')  


