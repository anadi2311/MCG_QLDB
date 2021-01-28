from logging import basicConfig, getLogger, INFO
from connect_to_ledger import create_qldb_driver
from amazon.ion.simpleion import dumps, loads
logger = getLogger(__name__)
basicConfig(level=INFO)


from constants import Constants
from register_person import get_index_number
from insert_document import insert_documents
from sampledata.sample_data import convert_object_to_ion, get_value_from_documentid,document_exist,update_document

# pick_up container requested by carrier ---> for every container
#