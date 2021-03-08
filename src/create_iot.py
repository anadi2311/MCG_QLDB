## In real-life scenarios IoT's will already be mapped to the containers
## And in Initiating shipment -- instead of creating a container by inputting data in the containers table
## Similar logic to putting batches in cases will be followed --> out of all the containers a container will be found which is empty and free and will be assigned


from logging import basicConfig, getLogger, INFO
from connect_to_ledger import create_qldb_driver
from amazon.ion.simpleion import dumps, loads
logger = getLogger(__name__)
basicConfig(level=INFO)


from constants import Constants
from register_person import get_index_number
from insert_document import insert_documents
from register_person import get_scentityid_from_personid
from sampledata.sample_data import convert_object_to_ion, get_value_from_documentid,document_exist,update_document
from accept_requests_for_admin import person_is_superadmin


def create_iot(transaction_executor,person_id, iot):
    if person_is_superadmin(transaction_executor,person_id):
        iot_number = get_index_number(transaction_executor,Constants.IOT_TABLE_NAME,"IoTNumber")
        iot.update({"IoTNumber": iot_number})
        iot_type = iot['IoTType']
        if iot_type ==1:
            iot_name = "Temperature Sensor"
        elif iot_type == 2:
            iot_name = "Humidity Sensor"
        elif iot_type == 3:
            iot_name = "Location Sensor"
        else:
            iot_name = "UnkownSensor"
        
        iot.update({"IoTName":iot_name})
        iot_id = insert_documents(transaction_executor,Constants.IOT_TABLE_NAME, [iot])
        logger.info(" ================== I O T ======= O N B O A R D E D ====================")
        return iot_id [0]
    else:
        raise Exception("You are not a Super admin")


# create iot in iot table
## update iot ids in containers
def assign_iot(transaction_executor, iot_id,container_id,person_id):
    # person_id must be super admin
    actual_sc_entity_id = get_scentityid_from_personid(transaction_executor,person_id)
    carrier_id = get_value_from_documentid(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_id,"CarrierCompanyId")
    if actual_sc_entity_id == carrier_id[0]:
        if document_exist(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_id):
            update_document(transaction_executor,Constants.IOT_TABLE_NAME,"ContainerId",iot_id,container_id)
            statement = "FROM {} AS s by id WHERE id = '{}' INSERT INTO s.IotIds VALUE ?".format(Constants.CONTAINER_TABLE_NAME,container_id)
            # print(statement)
            cursor = transaction_executor.execute_statement(statement,iot_id) 
            try:
                next(cursor)
                logger.info(" ========== I o T ========= A S S I G N E D ============")
            except:
                raise Exception("Problem in Iot assignment")
        else:
            raise Exception("Container not found")
    else:
        raise Exception("Not authorized!")
    


if __name__ == '__main__': 
    try:
        with create_qldb_driver() as driver:
            
            _iot = {
                "IoTNumber": "",
                "IoTType": 3, ## 1 for temperatire ---- 2 for Humdity ----------- 3 for location
                "IoTName":"Location Sensor",
                "ContainerId":"4NTN71QJWSxHLTbRrmoLRf"
            }
            personid = "9MCnNPlg1vVFKrbFguGHQo"
            driver.execute_lambda(lambda executor: create_iot(executor,personid,_iot))
    except Exception:
        logger.exception('Error registering IoT.')  




