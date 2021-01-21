class Constants:
    """
    Constant values used throughout this tutorial.
    """
    LEDGER_NAME = "MCG-TEST"
    PERSON_TABLE_NAME = "Persons"
    SCENTITY_TABLE_NAME = " SCEntities"
    JOINING_REQUEST_TABLE_NAME = "JoiningRequest"
    PRODUCT_TABLE_NAME = "Products"
    PURCHASE_ORDER_TABLE_NAME = "PurchaseOrders"

    SUPERADMIN_REQUEST_TABLE_NAME = "McgRequests"  
    # SUPERADMIN_PRODUCTREQUEST_TABLE_NAME = "McgProductRequest"  
       
    PERSON_ID_INDEX_NAME ="EmployeeId"
    SCENTITY_ID_INDEX_NAME = "ScentityIdentificationCode"
    JOINING_REQUESTID_INDEX_NAME = "JoiningRequestNumber" #create these indexes in the code
    SUPERADMIN_REQUEST_INDEX_NAME = "McgRequestNumber"  #create theses indexes in the code
    # SUPERADMIN_PRODUCTREQUEST_INDEX_NAME = "ProductRequestId"
    PRODUCT_ID_INDEX_NAME = "ProductNumber"  
    PURCHASE_ORDER_ID_INDEX_NAME = 'PurchaseOrderNumber'



    # JOURNAL_EXPORT_S3_BUCKET_NAME_PREFIX = "qldb-tutorial-journal-export"
    # USER_TABLES = "information_schema.user_tables"
    # S3_BUCKET_ARN_TEMPLATE = "arn:aws:s3:::"
    # LEDGER_NAME_WITH_TAGS = "tags"

    RETRY_LIMIT = 4