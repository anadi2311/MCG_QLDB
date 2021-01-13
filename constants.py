class Constants:
    """
    Constant values used throughout this tutorial.
    """
    LEDGER_NAME = "MCG-TEST"
    PERSON_TABLE_NAME = "Persons"
    SCENTITY_TABLE_NAME = " SCEntities"
    JOINING_REQUEST_TABLE_NAME = "JoiningRequest"
    PRODUCT_TABLE_NAME = "Products"


    SUPERADMIN_REQUEST_TABLE_NAME = "McgRequests"  
    # SUPERADMIN_PRODUCTREQUEST_TABLE_NAME = "McgProductRequest"  
       
    PERSON_ID_INDEX_NAME ="EmployeeId"
    SCENTITY_ID_INDEX_NAME = "ScentityIdentificationCode"
    JOINING_REQUESTID_INDEX_NAME = "JoiningRequestId"
    SUPERADMIN_REQUEST_INDEX_NAME = "MCGRequestId"  
    # SUPERADMIN_PRODUCTREQUEST_INDEX_NAME = "ProductRequestId"
    PRODUCT_ID_INDEX_NAME = "ProductId"  



    # JOURNAL_EXPORT_S3_BUCKET_NAME_PREFIX = "qldb-tutorial-journal-export"
    # USER_TABLES = "information_schema.user_tables"
    # S3_BUCKET_ARN_TEMPLATE = "arn:aws:s3:::"
    # LEDGER_NAME_WITH_TAGS = "tags"

    RETRY_LIMIT = 4