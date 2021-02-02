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
from sampledata.sample_data import convert_object_to_ion, get_value_from_documentid,document_exist,update_document
from accept_requests_for_admin import person_is_superadmin



def create_iot(transaction_executor,iot):
    iot_number = get_index_number(transaction_executor,Constants.IOT_TABLE_NAME,"IoTNumber")
    iot.update({"IoTNumber": iot_number})
    logger.info("iot_number is :{}".format(iot_number))
    iot_id = insert_documents(transaction_executor,Constants.IOT_TABLE_NAME, [iot])
    print(iot_id)
    return iot_id [0]

# create iot in iot table
## update iot ids in containers
def create_and_assign_iot(transaction_executor, iot,person_id):
    # person_id must be super admin
    if person_is_superadmin(transaction_executor,person_id):
        container_id = iot["ContainerId"]
        if document_exist(transaction_executor,Constants.CONTAINER_TABLE_NAME,container_id):
            iot_id = create_iot(transaction_executor,iot)
            statement = "FROM {} AS s by id WHERE id = '{}' INSERT INTO s.IotIds VALUE ?".format(Constants.CONTAINER_TABLE_NAME,container_id)
            # print(statement)
            cursor = transaction_executor.execute_statement(statement,iot_id) 
            try:
                next(cursor)
                logger.info(" ========== I o T ========= C R E A T E D ========== A N D ====== A D D E D ============")
            except:
                logger.info("Problem in Iot assignment")
        else:
            logger.info("Container not found")
    else:
        logger.info("You are not an admin")
    


if __name__ == '__main__': 
    try:
        with create_qldb_driver() as driver:
            
            io_t = {
                "IoTNumber": "",
                "IoTType": 3, ## 1 for temperatire ---- 2 for Humdity ----------- 3 for location
                "IoTName":"Location Sensor",
                "ContainerId":"Ad3ACY526Hg8LXV0RxexhO"
            }
            personid = "0007Uwl5XmzEpE7jSQLxpe"
            driver.execute_lambda(lambda executor: create_and_assign_iot(executor, io_t,personid))
    except Exception:
        logger.exception('Error registering IoT.')  




