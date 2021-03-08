
from datetime import datetime

class SampleData:
    """
    Sample domain objects for use throughout this tutorial.
    """
    PERSON = [
        {
            'EmployeeId': 'AdminMCG123',
            'FirstName': 'UBC',
            'LastName': 'CIC',
            'isSuperAdmin' : True,
            'isAdmin' : True,
             'PersonContact': {
                "Email": "UBC.CIC@ubc.ca",
                'Phone' : "9999999999",
                'Address': 'UBC CIC'
        }}
    ]
    


    SCENTITY = [
            {
            "ScEntityName" : "MCG",
            "ScEntityContact":{
                "Email":"MCG@mcg.com",
                "Address":"123 ABC St, Texas, USA",
                "Phone": "1234567890"
            },    
            "ScEntityIdentificationCode" : "admin1234",    
            "ScEntityIdentificationCodeType" : "BusinessNumber",
            "isApprovedBySuperAdmin": True,
            "ScEntityTypeCode": "1",
            "PersonIds": [],
            "JoiningRequests" : [],
            }
        ]

class InputData:

    register_person_data = [
    [
        {"new_person" :{
                'EmployeeId': 'Buyer123',
                'FirstName': 'Buyer',
                'LastName': 'Doe',
                'isSuperAdmin' : False,
                'isAdmin' : False,
                'PersonContact': {
                    "Email": "Bob.Doe@ubc.ca",
                    'Phone' : "8888888888",
                    'Address': 'Pluto'
                    }}},
    {"new_sc_entity": {
                        "ScEntityName" : "CDC",
                        "ScEntityContact":{
                            "Email":"moderna@moderna.com",
                            "Address":"345 DEF St, ON, CAN",
                            "Phone": "1234567890"
                        },
                        "isApprovedBySuperAdmin": True,
                        "ScEntityTypeCode": "2",
                        "PersonIds": [],
                        "JoiningRequests" : [],
                        "PickUpRequests":[],
                        "ScEntityIdentificationCode" : "AS231rrrrr",    
                        "ScEntityIdentificationCodeType" : "BusinessNumber"               
                        }}],
    [
        {"new_person" : {
                        'EmployeeId': 'MAN123',
                        'FirstName': 'Manufacturer',
                        'LastName': 'DOE',
                        'isSuperAdmin' : False,
                        'isAdmin' : False,
                            'PersonContact': {
                                "Email": "MAN.Doe@ubc.ca",
                                'Phone' : "8888888888",
                                'Address': 'your next door neighbor'
                            }}},

        {"new_sc_entity" : {
                        "ScEntityName" : "Moderna",
                        "ScEntityContact":{
                            "Email":"moderna@moderna.com",
                            "Address":"345 DEF St, ON, CAN",
                            "Phone": "1234567890"
                        },
                        "isApprovedBySuperAdmin": False,
                        "ScEntityTypeCode": "2",
                        "PersonIds": [],
                        "JoiningRequests" : [],
                        "PickUpRequests":[],
                        "ScEntityIdentificationCode" : "MODERNA1234",    
                        "ScEntityIdentificationCodeType" : "BusinessNumber"               
    }}],
    [
        {"new_person" : {
                        'EmployeeId': 'TruckDriverAndAdmin',
                        'FirstName': 'ExportDriver',
                        'LastName': 'DOE',
                        'isSuperAdmin' : False,
                        'isAdmin' : False,
                            'PersonContact': {
                                "Email": "JAN.Doe@ubc.ca",
                                'Phone' : "8888888888",
                                'Address': 'FirstNewUser'
                            }}},
        {"new_sc_entity" : {
                        "ScEntityName" : "FEDX",
                        "ScEntityContact":{
                            "Email":"FEDx@FEDx.com",
                            "Address":"345 DEF St, ON, CAN",
                            "Phone": "1234567890"
                        },
                        "isApprovedBySuperAdmin": True,
                        "ScEntityTypeCode": "2",
                        "PersonIds": [],
                        "JoiningRequests" : [],
                        "PickUpRequests":[],
                        "ScEntityIdentificationCode" : "COOODDO1234",    #<<--------must be checked from a govt. available data source
                        "ScEntityIdentificationCodeType" : "BusinessNumber"               
                            }}
    ],
    [
        {"new_person" : {
                        'EmployeeId': 'ExportCustomAgent123',
                        'FirstName': 'ExportCustom',
                        'LastName': 'DOE',
                        'isSuperAdmin' : False,
                        'isAdmin' : False,
                            'PersonContact': {
                                "Email": "Custom.Doe@ubc.ca",
                                'Phone' : "8888888888",
                                'Address': 'FirstNewUser'
                            }}},

        {"new_sc_entity": {
                    "ScEntityName" : "TexasAirport",
                    "ScEntityContact":{
                        "Email":"Tsairport@airport.com",
                        "Address":"345 DEF St, ON, CAN",
                        "Phone": "1234567890"
                    },
                    "isApprovedBySuperAdmin": True,
                    "ScEntityTypeCode": "3",
                    "PersonIds": [],
                    "JoiningRequests" : [],
                    "PickUpRequests":[],
                    "ScEntityIdentificationCode" : "Tx123",    #<<--------must be checked from a govt. available data source
                    "ScEntityIdentificationCodeType" : "IATACode"               
                    }}],
    [
        {"new_person": {
                    'EmployeeId': 'ImpotCustomAgent123',
                    'FirstName': 'ImportCustom',
                    'LastName': 'DOE',
                    'isSuperAdmin' : False,
                    'isAdmin' : False,
                        'PersonContact': {
                            "Email": "Custom.Doe@ubc.ca",
                            'Phone' : "8888888888",
                            'Address': 'FirstNewUser'
                        }}},

        {"new_sc_entity" : {
                    "ScEntityName" : "VancouverAirport",
                    "ScEntityContact":{
                        "Email":"yvrairport@airport.com",
                        "Address":"345 DEF St, ON, CAN",
                        "Phone": "1234567890"
                    },
                    "isApprovedBySuperAdmin": True,
                    "ScEntityTypeCode": "3",
                    "PersonIds": [],
                    "JoiningRequests" : [],
                    "PickUpRequests":[],
                    "ScEntityIdentificationCode" : "YVR123",    #<<--------must be checked from a govt. available data source
                    "ScEntityIdentificationCodeType" : "IATACode"               
                    }}],

    [
        {"new_person": {
                    'EmployeeId': 'Hospitalemployee123',
                    'FirstName': 'HospitalPurchaser',
                    'LastName': 'DOE',
                    'isSuperAdmin' : False,
                    'isAdmin' : False,
                        'PersonContact': {
                            "Email": "Custom.Doe@ubc.ca",
                            'Phone' : "8888888888",
                            'Address': 'FirstNewUser'
                        }}},
        {"new_sc_entity" : {
                    "ScEntityName" : "YVRHospital",
                    "ScEntityContact":{
                        "Email":"yvrairport@airport.com",
                        "Address":"345 DEF St, ON, CAN",
                        "Phone": "1234567890"
                    },
                    "isApprovedBySuperAdmin": True,
                    "ScEntityTypeCode": "5",
                    "PersonIds": [],
                    "JoiningRequests" : [],
                    "PickUpRequests":[],
                    "ScEntityIdentificationCode" : "YVRHOSP123",    #<<--------must be checked from a govt. available data source
                    "ScEntityIdentificationCodeType" : "HospitalCode"               
                    }}],
    [
        {"new_person" : {
                    'EmployeeId': 'IMPORTPDRIVER',
                    'FirstName': 'ImportDriver',
                    'LastName': 'DOE',
                    'isSuperAdmin' : False,
                    'isAdmin' : False,
                    'PersonContact': {
                            "Email": "JAN.Doe@ubc.ca",
                            'Phone' : "8888888888",
                            'Address': 'FirstNewUser'
                    }}},
        {"new_sc_entity" : {
                    "ScEntityName" : "FEDX",
                    "ScEntityContact":{
                        "Email":"FEDx@FEDx.com",
                        "Address":"345 DEF St, ON, CAN",
                        "Phone": "1234567890"
                    },
                    "isApprovedBySuperAdmin": True,
                    "ScEntityTypeCode": "2",
                    "PersonIds": [],
                    "JoiningRequests" : [],
                    "PickUpRequests":[],
                    "ScEntityIdentificationCode" : "COOODDO1234",    #<<--------must be checked from a govt. available data source
                    "ScEntityIdentificationCodeType" : "BusinessNumber"               
                    }}],
[                    
        {"new_person" : {
            'EmployeeId': 'LocalDriver123',
            'FirstName': 'LocalDriver',
            'LastName': 'DOE',
            'isSuperAdmin' : False,
            'isAdmin' : False,
            'PersonContact': {
                    "Email": "JAN.Doe@ubc.ca",
                    'Phone' : "8888888888",
                    'Address': 'FirstNewUser'
            }}},
        {"new_sc_entity" : {
                    "ScEntityName" : "FEDX",
                    "ScEntityContact":{
                        "Email":"FEDx@FEDx.com",
                        "Address":"345 DEF St, ON, CAN",
                        "Phone": "1234567890"
                    },
                    "isApprovedBySuperAdmin": True,
                    "ScEntityTypeCode": "2",
                    "PersonIds": [],
                    "JoiningRequests" : [],
                    "PickUpRequests":[],
                    "ScEntityIdentificationCode" : "COOODDO1234",    #<<--------must be checked from a govt. available data source
                    "ScEntityIdentificationCodeType" : "BusinessNumber"               
                    }}]
    ]


    
    _iot = [
    {
        "IoTNumber": "",
        "IoTType": 3, ## 1 for temperatire ---- 2 for Humdity ----------- 3 for location
        "IoTName":"LocationSensor",
        "ContainerId":""
            },

    {
        "IoTNumber": "",
        "IoTType": 2, ## 1 for temperatire ---- 2 for Humdity ----------- 3 for location
        "IoTName":"HumiditySensor",
        "ContainerId":""
            },
    
    {
        "IoTNumber": "",
        "IoTType": 1, ## 1 for temperatire ---- 2 for Humdity ----------- 3 for location
        "IoTName":"TemperatureSensor",
        "ContainerId":""
            },
        {
        "IoTNumber": "",
        "IoTType": 3, ## 1 for temperatire ---- 2 for Humdity ----------- 3 for location
        "IoTName":"LocationSensor",
        "ContainerId":""
            },

    {
        "IoTNumber": "",
        "IoTType": 2, ## 1 for temperatire ---- 2 for Humdity ----------- 3 for location
        "IoTName":"HumiditySensor",
        "ContainerId":""
            },
    
    {
        "IoTNumber": "",
        "IoTType": 1, ## 1 for temperatire ---- 2 for Humdity ----------- 3 for location
        "IoTName":"TemperatureSensor",
        "ContainerId":""
            }
    ]

    new_product = {
        'ProductCode': "00123451000015", #GTIN for Vaccine with NDC National Drug Code
        'ProductName': "Moderna Vaccine",
        'ProductPrice': 10,
        'MinimumSellingAmount':2, #minimum selling amount in container 
        'ProductsPerContainer':100, #<<---- It denotes how many vaccines will be available in a container <<-- 100 vaccines per container
        'ProductExpiry': 120, #in days
        'ProductStorage': {
            'LowThreshTemp': 0, #in degrees Centigrate
            'HighThreshTemp': 10, #in degree Centigrate
            'HighThreshHumidity': 40 # percentage   
        },
        'ProductHSTarriffNumber':'HGJSI123123',#Used for catergorizing products in export
        'ManufacturerId': "", #change this <<<<---------------------------
        'isApprovedBySuperAdmin':False,
        'BatchTableId': ''
        }

    batch = {
                'BatchNo' :'', #<<--- autoincremented batch numbers from 1 
                'UnitsProduced':1000, # make this automatic by counting length of product instances
                'UnitsRemaining':"",
                'MfgDate':datetime.today().strftime('%Y-%m-%d'),
                'ProductInstances': list(range(1,1001)), #Create 1000 vaccines with SNO from 1 to 1000 ==> can be changed with actual Alphanumeric SNo
                'CaseIds':[]
            }

    purchaseorderdetails = {
                "PurchaseOrderNumber":"",
                "ProductId":"", ## this will be updated in the code
                "OrderQuantity" : 2, ## <<------- number of containers orered ## keep this 2 because max transaction limit is 2
                "Orderer":{
                    "OrdererScEntityId":"",
                    "OrdererPersonId" :""
                },
                "isOrderShipped":False,
                "OrderType":""
            }
    

    Distributor = {
        "MinimumSellingAmount":1,
        "NewProductPrice":21
    }

    purchaseorderdetails_to_distributor = {
                    "PurchaseOrderNumber":"",
                    "ProductId":"",
                    "OrderQuantity" : 1, ## <<------- denotes number of conatienrs
                    "Orderer":{
                        "OrdererScEntityId":"",
                        "OrdererPersonId" :""
                    },
                    "isOrderShipped":False,
                    "OrderType":""
                }
