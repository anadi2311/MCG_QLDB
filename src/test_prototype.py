from logging import basicConfig, getLogger, INFO
from constants import Constants
from connect_to_ledger import create_qldb_driver
from insert_document import update_and_insert_documents
from create_iot import create_iot, assign_iot
from sampledata.input_data import InputData
from register_person import register_new_user_with_scentity
from accept_requests_for_admin import accept_request_to_approve_company_or_product
from accept_joining_request import approve_joining_request
from register_product import register_product
from create_product_batches import create_batch
from create_purchase_order_to_manufacturer import create_purchase_order_to_manufacturer
from accept_purchase_order import accept_order
from initiate_shipment_manufacturer import initiate_shipment
from export_transport_product import pick_up_order
from export_customs_approval import custom_approval
from approve_airwaybill_bol import approve_lading_bill
from import_customs_approval import approve_import_customs
from import_transport_product import deliver_product_to_distributor
from approve_delivery import approve_order_delivery
from update_minimum_selling_amount import update_price_and_minimum_selling_amount
from create_purchase_order_to_distributor import create_purchase_order_to_distributor
from initiate_shipment_distributor import initiate_distributor_shipment
from local_transport_product import deliver_product_to_final_entity

logger = getLogger(__name__)
basicConfig(level=INFO)

try:
    with create_qldb_driver() as driver:
        # An INSERT statement creates the initial revision of a document with a version number of zero.
        # QLDB also assigns a unique document identifier in GUID format as part of the metadata.

        # ##
        
        # admin_id = "5pxmzjFWEydDqXfJQRreFI"
        # iot_ids = ['7T6FuPTIWioC7pimcoFsPz', '7oOLzofzGkX3GunPOSwq9Y', '4o5UjVeRwpHLlVFjQeE87Q', '6mW3jb3v2gAAARutuGBuzS', 'I79Ic0ogvUxIC2xGyxrbBY', 'JOzfRHpmM0m0FRGqXrWC54']
        
        # sc_entity_ids = {'CDC': '3gtAwwDi0s92r6bC7kSMPO', 'Moderna': 'GE2l8HBtiJ9GF3bjWLorHe', 'FEDX': '2ZgrAMny2qv7YHX1iZ4aNQ', 'TexasAirport': 'IXlQDlp3XMQ3sKQKxlrNt3', 'VancouverAirport': 'AohDG7iWxZQ0mesu9c8azk', 'YVRHospital': '17CRIOBXLU2EVnAtOLJ2LI'}
        
        # person_ids = {'Buyer': '0bGIAHNUs8YG0ChtgRVdDI', 'Manufacturer': 'EgEJjwlnAGa46SOurJuLBb', 'ExportDriver': 'D8PsLcLgaspAe3Y39chCto', 'ExportCustom': '5vHoW53CCqKKjlOAA7dIIR', 'ImportCustom': '2JimbJOwyiT3EI56RH7FJA', 'HospitalPurchaser': 'Jdxk0LEnjSf00AO7yclmsA', 'ImportDriver': '6BFt58SDebZL4w6VmbZefI', 'LocalDriver': 'EFcC8BlR7pTDuaB1TLEp9s'}

        # product_id = '1NAVrRaYuK4HOZhM4R2VFI'

        # purchase_order_id = 'Kgq2GYqsknbKa4ClMubFXy'

        # invoice_id = "HFv3OUnyxeB5BvxZkX1hme"

        # pick_up_request_id = 'Au1EmTWDt9iGDj3Z6zphbS'

        # container_ids = ['ChnkjrLLQqHIrH8JDW6p3G', '2UMpd10JYkV0wcGccRli1l']

        # lorry_reciept_id = [['HlrCWbc1uGUBGr5WYoRhKc']]

        # airway_bill_id = [['3Lb4rX12tDLKD5fNBOdbi4']]


        # # ##



        logger.info(" ++++++++++++++++++++++++++++++++++++++++++  0.1 Admin and MCG successfully onboarding Begins       ++++++++++++++++++++++++++++++++++++++")
        admin_id, mcg_id = driver.execute_lambda(lambda executor: update_and_insert_documents(executor),
                                lambda retry_attempt: logger.info('Retrying due to OCC conflict...'))
      
        
##################################################################################################################
        # we will create 3 iots

        logger.info(" ++++++++++++++++++++++++++++++++++++++++++  0.2 IoTs Onboarding begins       ++++++++++++++++++++++++++++++++++++++")
        
        iot_ids = []
        for iot in InputData._iot:
            iot_id = driver.execute_lambda(lambda executor: create_iot(executor,admin_id,iot),
                                lambda retry_attempt: logger.info('Retrying due to OCC conflict...'))
            iot_ids.append(iot_id)
        
################################################################################################################### 

        # Let's onboard all the stakeholders [0:6][6:8] 
        logger.info(" ++++++++++++++++++++++++++++++++++++++++++  1.1 Onboarding company Admins  -- Mcg Request Created  ++++++++++++++++++++++++++++++++++++++")
        person_ids = {}
        sc_entity_ids = {}
        mcg_request_ids = []
        for data in InputData.register_person_data[0:6]:
            person_name = data[0]["new_person"]["FirstName"]
            sc_entity_name = data[1]["new_sc_entity"]["ScEntityName"]
            person_id, sc_entity_id, mcg_request_id =  driver.execute_lambda(lambda executor: register_new_user_with_scentity(executor, data[0]["new_person"], data[1]["new_sc_entity"]),
                                lambda retry_attempt: logger.info('Retrying due to OCC conflict...'))
            mcg_request_ids.append(mcg_request_id)
            person_ids["{}".format(person_name)] = person_id
            sc_entity_ids["{}".format(sc_entity_name)] = sc_entity_id            
        

# ###################################################################################################################   
        # Admin accepts all the requests

        logger.info("++++++++++++++++++++++++++++++++++++++++++  1.2 Admin accepts the request and onboards the admins  ++++++++++++++++++++++++++++++++++++++")        
        for req in mcg_request_ids:
            return_statement = driver.execute_lambda(lambda executor: accept_request_to_approve_company_or_product(executor,req,admin_id),
                                lambda retry_attempt: logger.info('Retrying due to OCC conflict...'))
            logger.info(return_statement)

# ###################################################################################################################   
        # Creating two joining requests for two truck drivers. Carrier company will accept them. Assume Export Driver and admin are the same
        # logger.info("++++++++++++++++++++++++++++++++++++++++++  1.3 Company Admins accept respective joining requests  ++++++++++++++++++++++++++++++++++++++")

        joining_request_ids = []
        for data in InputData.register_person_data[6:8]:
            person_name = data[0]["new_person"]["FirstName"]
            sc_entity_name = data[1]["new_sc_entity"]["ScEntityName"]
            person_id, joining_request_id =  driver.execute_lambda(lambda executor: register_new_user_with_scentity(executor, data[0]["new_person"], data[1]["new_sc_entity"]),
                                lambda retry_attempt: logger.info('Retrying due to OCC conflict...'))
            joining_request_ids.append(joining_request_id)
            person_ids["{}".format(person_name)] = person_id
            

        

        for req in joining_request_ids:
            return_statement = driver.execute_lambda(lambda executor: approve_joining_request(executor,req,person_ids["ExportDriver"]),
                                lambda retry_attempt: logger.info('Retrying due to OCC conflict...'))
            logger.info(return_statement)
            
    ################################################################################################################### 
            # buyer creates the product and admin approves it


        logger.info("++++++++++++++++++++++++++++++++++++++++++  2.2 Manufacturer creates the product and MCG approves it  ++++++++++++++++++++++++++++++++++++++")
            
        product_id, product_request_id = driver.execute_lambda(lambda executor: register_product(executor, InputData.new_product, person_ids["Manufacturer"]),
                                lambda retry_attempt: logger.info('Retrying due to OCC conflict...'))
        return_statement = driver.execute_lambda(lambda executor: accept_request_to_approve_company_or_product(executor,product_request_id,admin_id),
                                lambda retry_attempt: logger.info('Retrying due to OCC conflict...'))
        logger.info(return_statement + "========= P R O D U C T === O N B O A R D E D ======")


        logger.info("++++++++++++++++++++++++++++++++++++++++++  2.3 Manufacturer creates the batch ++++++++++++++++++++++++++++++++++++++")        
        driver.execute_lambda(lambda executor: create_batch(executor, person_ids["Manufacturer"],product_id, InputData.batch),
                                lambda retry_attempt: logger.info('Retrying due to OCC conflict...'))


    # ################################################################################################################### 
        logger.info("++++++++++++++++++++++++++++++++++++++++++  3.0 Buyer creates the order ++++++++++++++++++++++++++++++++++++++")

        InputData.purchaseorderdetails.update({"ProductId":product_id})
        purchase_order_id = driver.execute_lambda(lambda executor: create_purchase_order_to_manufacturer(executor, person_ids["Buyer"],InputData.purchaseorderdetails),
                                lambda retry_attempt: logger.info('Retrying due to OCC conflict...'))

    ################################################################################################################### 
        logger.info("++++++++++++++++++++++++++++++++++++++++++  4.0 Manufacturer accepts the order to create invoice ++++++++++++++++++++++++++++++++++++++")
        invoice_id = driver.execute_lambda(lambda executor: accept_order(executor, purchase_order_id, person_ids["Manufacturer"]),
                                lambda retry_attempt: logger.info('Retrying due to OCC conflict...'))


    ################################################################################################################### 
        logger.info("++++++++++++++++++++++++++++++++++++++++++  5.0 Manufacturer initiates the shipment ++++++++++++++++++++++++++++++++++++++")
        transporttype = 1
        pick_up_request_id, container_ids = driver.execute_lambda(lambda executor: initiate_shipment(executor, sc_entity_ids['FEDX'],transporttype,purchase_order_id, person_ids["Manufacturer"]),
                                lambda retry_attempt: logger.info('Retrying due to OCC conflict...'))
        
    ####################################################################################################################    
        logger.info("++++++++++++++++++++++++++++++++++++++++++  6.0 carrier company comes and assigns the IoT to container  ++++++++++++++++++++++++++++++++++++++")

        i_number = 0
        for container_id in container_ids:
            for iot in iot_ids:
                driver.execute_lambda(lambda executor: assign_iot(executor,iot_ids[i_number],container_id,person_ids['ExportDriver']),
                                lambda retry_attempt: logger.info('Retrying due to OCC conflict...'))
                i_number = i_number + 1
                if i_number ==3 or i_number == 6:
                    break

        logger.info("++++++++++++++++++++++++++++++++++++++++++  7.0 carrier company picks up the container ++++++++++++++++++++++++++++++++++++++")

        
        lorry_reciept_ids,airway_bill_ids, bill_of_lading_ids = driver.execute_lambda(lambda executor: pick_up_order(executor, pick_up_request_id,person_ids["ExportDriver"],sc_entity_ids["FEDX"],sc_entity_ids["TexasAirport"],sc_entity_ids["VancouverAirport"]),
                                lambda retry_attempt: logger.info('Retrying due to OCC conflict...'))

    ####################################################################################################################    
        logger.info("++++++++++++++++++++++++++++++++++++++++++  8.0 Export customs approves the export  ++++++++++++++++++++++++++++++++++++++")

        approvaltype = 'ExportApproval'
        for container_id in container_ids:
            driver.execute_lambda(lambda executor: custom_approval(executor, container_id,approvaltype, person_ids["ExportCustom"]),
            lambda retry_attempt: logger.info('Retrying due to OCC conflict...'))

     ####################################################################################################################    

        logger.info("++++++++++++++++++++++++++++++++++++++++++  9.0 Export Carrier company approves the lading bill  ++++++++++++++++++++++++++++++++++++++")
        
        for airway_bill_id in airway_bill_ids:
            driver.execute_lambda(lambda executor: approve_lading_bill(executor, airway_bill_id, person_ids["ExportDriver"]),
            lambda retry_attempt: logger.info('Retrying due to OCC conflict...'))

     ####################################################################################################################    
        logger.info("++++++++++++++++++++++++++++++++++++++++++  10.0 Import customs approves the import  ++++++++++++++++++++++++++++++++++++++")

        warehouse_id = "asdasdawdad"
        for container_id in container_ids:
            driver.execute_lambda(lambda executor: approve_import_customs(executor, container_id, person_ids["ImportCustom"],warehouse_id),
            lambda retry_attempt: logger.info('Retrying due to OCC conflict...'))
        
     ####################################################################################################################    
        logger.info("++++++++++++++++++++++++++++++++++++++++++  11.0 Import tranport to distrubtor begins  ++++++++++++++++++++++++++++++++++++++")
        
        driver.execute_lambda(lambda executor: deliver_product_to_distributor(executor, pick_up_request_id,person_ids["ImportDriver"]),
        lambda retry_attempt: logger.info('Retrying due to OCC conflict...'))
        
     ####################################################################################################################    
        logger.info("++++++++++++++++++++++++++++++++++++++++++  12.0  Buyer approves the delivery ++++++++++++++++++++++++++++++++++++++")
    
        driver.execute_lambda(lambda executor: approve_order_delivery(executor, purchase_order_id,person_ids["Buyer"]),
        lambda retry_attempt: logger.info('Retrying due to OCC conflict...'))
    
    ####################################################################################################################    
        logger.info("++++++++++++++++++++++++++++++++++++++++++  13.0  Buyer/Distributor updates its minimum selling price and amount ++++++++++++++++++++++++++++++++++++++")
    
        driver.execute_lambda(lambda executor: update_price_and_minimum_selling_amount(executor,product_id, InputData.Distributor["MinimumSellingAmount"], InputData.Distributor["NewProductPrice"], person_ids["Buyer"]),
        lambda retry_attempt: logger.info('Retrying due to OCC conflict...'))


    ####################################################################################################################    
        logger.info("++++++++++++++++++++++++++++++++++++++++++  14.0  Hospital places a new order to distributor ++++++++++++++++++++++++++++++++++++++")

        InputData.purchaseorderdetails_to_distributor.update({"ProductId":product_id})
        purchase_order_to_distributor_id = driver.execute_lambda(lambda executor: create_purchase_order_to_distributor(executor,InputData.purchaseorderdetails_to_distributor,sc_entity_ids["CDC"],person_ids["HospitalPurchaser"]),
        lambda retry_attempt: logger.info('Retrying due to OCC conflict...'))


    ####################################################################################################################    
        logger.info("++++++++++++++++++++++++++++++++++++++++++  15.0  Distributor Accepts the Order and Initiates the shipment++++++++++++++++++++++++++++++++++++++")

        dist_invoice_id = driver.execute_lambda(lambda executor: accept_order(executor, purchase_order_to_distributor_id, person_ids["Buyer"]))
        transport_type = 3 #land
        dist_pick_up_request_id = driver.execute_lambda(lambda executor: initiate_distributor_shipment(executor, purchase_order_to_distributor_id, person_ids["Buyer"],sc_entity_ids["FEDX"], transport_type),
        lambda retry_attempt: logger.info('Retrying due to OCC conflict...'))
    ####################################################################################################################    
        logger.info("++++++++++++++++++++++++++++++++++++++++++  16.0  Local delivery driver picks up the order ++++++++++++++++++++++++++++++++++++++")

        dist_lorry_reciept_ids = driver.execute_lambda(lambda executor: deliver_product_to_final_entity(executor, dist_pick_up_request_id,person_ids["LocalDriver"]),
        lambda retry_attempt: logger.info('Retrying due to OCC conflict...'))

    ####################################################################################################################    
        logger.info("++++++++++++++++++++++++++++++++++++++++++  17.0  driver completes delivery and hospital approves the delivery ++++++++++++++++++++++++++++++++++++++")

        driver.execute_lambda(lambda executor: approve_order_delivery(executor, purchase_order_to_distributor_id,person_ids["HospitalPurchaser"]),
        lambda retry_attempt: logger.info('Retrying due to OCC conflict...'))


        logger.info('=================================================================================================================================================')
        logger.info('=================================================================================================================================================')
        logger.info('===============                      ==========                   ==============            ==============      =================================')
        logger.info('===============                      ==========                   ==============            ==============      =================================')
        logger.info('===============      ==========================                   ==============      ==      ============      =================================')
        logger.info('===============      ================================      =====================      ===      ===========      =================================')
        logger.info('===============      ================================      =====================      ====      ==========      =================================')
        logger.info('===============                      ================      =====================      =====      =========      =================================')
        logger.info('===============                      ================      =====================      ======      ========      =================================')
        logger.info('===============      ================================      =====================      =======      =======      =================================')
        logger.info('===============      ================================      =====================      ========      ======      =================================')
        logger.info('===============      ================================      =====================      =========      =====      =================================')
        logger.info('===============      ================================      =====================      ==========      ====      =================================')
        logger.info('===============      ================================      =====================      ===========      ===      =================================')
        logger.info('===============      =========================                   ===============      ============      ==      =================================')
        logger.info('===============      =========================                   ===============      =============             =================================')
        logger.info('===============      =========================                   ===============      ==============            =================================')
        logger.info('=================================================================================================================================================')
        logger.info('=================================================================================================================================================')


except Exception:
    logger.exception('Error processing the protoype.')
finally:
    print("Prototype Ended.")
