# MCG_QLDB_Q1
Link to schemas that the ledger will follow can be found [here](https://drive.google.com/drive/u/0/folders/1IS2HPOj-qn73skQApdlg8dsEcCPBwvka)


## step 1

Create an Amazon Web Service account

## step 2
Requirements:

*   Install Amazon cli : https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html
*   Python3 : https://www.python.org/downloads/

## step 3
Open terminal and **cd** into the MCG_QLDB folder

## step 4
Input the environment variables
<br/> *They should be in this format*:

---
export AWS_ACCESS_KEY_ID="asdasdadasdasdaad"
<br/>export AWS_SECRET_ACCESS_KEY="asdasdadasdadsadads"
<br> export AWS_SESSION_TOKEN = "lkhasldkhlkhlkahsdlkahsldkahsldkhalsdhalkdhalkshdlkhhhhhhkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk"

----------------------

## Step 5:
Follow the below steps to create ledger, onboard persons and entites:<br/>
1. In the same terminal type <br/> 
    ```terminal 
    python create_ledger.py
    ```
    <br/>
    You should see following output in the terminal: <br/>

    ```terminal

    buzzlite@buzzlite-hp-laptop-14-cf0xxx:~/MCG_QLDB-Q1$ python create_ledger.py
    INFO:botocore.credentials:Found credentials in environment variables.
    INFO:__main__:Let's create the ledger named: MCG-TEST...
    INFO:__main__:Success. Ledger state: CREATING.
    INFO:__main__:Waiting for ledger to become active...
    INFO:__main__:The ledger is still creating. Please wait...
    INFO:__main__:The ledger is still creating. Please wait...
    INFO:__main__:Success. Ledger is active and ready to use.
    ```
2. In the same terminal type <br/> 
    ```terminal 
    python create_table.py
    ```
    <br/>
    You should see following output in the terminal: <br/>

    ```terminal

    buzzlite@buzzlite-hp-laptop-14-cf0xxx:~/MCG_QLDB-Q1$ python create_table.py
    INFO:botocore.credentials:Found credentials in environment variables.
    INFO:__main__:Creating the ' SCEntities' table...
    INFO:__main__: SCEntities table created successfully.
    INFO:__main__:Creating the 'Persons' table...
    INFO:__main__:Persons table created successfully.
    INFO:__main__:Creating the 'JoiningRequest' table...
    INFO:__main__:JoiningRequest table created successfully.
    INFO:__main__:Tables created successfully..
    ```
3. In the same terminal type <br/> 
    ```terminal 
    python create_index.py
    ```
    <br/>
    You should see following output in the terminal: <br/>

    ```terminal

    buzzlite@buzzlite-hp-laptop-14-cf0xxx:~/MCG_QLDB-Q1$ python create_index.py
    INFO:__main__:Creating indexes on all tables in a single transaction...
    INFO:botocore.credentials:Found credentials in environment variables.
    INFO:__main__:Creating index on 'EmployeeId'...
    INFO:__main__:Creating index on 'ScentityIdentificationCode'...
    INFO:__main__:Creating index on 'JoiningRequestId'...
    INFO:__main__:Indexes created successfully.
    ```
4. The sample data folder contains the mock data that will be inputed first to facilitate further functions. 
   </br>
    
    In the same terminal type <br/> 
    ```terminal 
    python insert_documents.py
    ```
    <br/>
    You should see following output in the terminal: <br/>

    ```terminal
    buzzlite@buzzlite-hp-laptop-14-cf0xxx:~/MCG_QLDB-Q1$ python insert_document.py 
    INFO:botocore.credentials:Found credentials in environment variables.
    INFO:__main__:Inserting some documents in the Persons table...
    INFO:__main__:Updating PersonIds for 'SCENTITY' ...
    INFO:__main__:[{'ScEntityName': ' Pfizer', 'ScEntityLocation': '123 ABC St, Texas, USA', 'ScEntityContact': '1234567890', 'ScEntityIdentificationCode': 'JXkY1234', 'ScEntityIdentificationCodeType': 'BusinessNumber', 'isApprovedByAdmin': False, 'ScentityTypeCode': 2, 'PersonIds': [], 'JoiningRequests': []}]
    INFO:__main__:[]
    INFO:__main__:['3Qv6MVetkVb5AozExa9ZMc', 'BqZVUy9o3sLJwhOzkfp6ON', 'ADR2aHw1m8XJ30wnMlqGU8']
    INFO:__main__:[{'ScEntityName': ' Pfizer', 'ScEntityLocation': '123 ABC St, Texas, USA', 'ScEntityContact': '1234567890', 'ScEntityIdentificationCode': 'JXkY1234', 'ScEntityIdentificationCodeType': 'BusinessNumber', 'isApprovedByAdmin': False, 'ScentityTypeCode': 2, 'PersonIds': ['3Qv6MVetkVb5AozExa9ZMc', 'BqZVUy9o3sLJwhOzkfp6ON'], 'JoiningRequests': []}]
    INFO:__main__:Inserting some documents in the  SCEntities table...
    INFO:__main__:Documents inserted successfully!
    ```
5. We will test four cases for registering entites and companies on qldb.
</br> For each case make the changes in the following part of mock data in *register_person.py* :

    ``` python
   
        if __name__ == '__main__':
            """
            Register a new driver's license.
            """
            try:
                with create_qldb_driver() as driver:
                    
                    new_person = {
                    'EmployeeId': 'BOB123',
                    'FirstName': 'Bob',
                    'LastName': 'Doe',
                    'isSuperAdmin' : False,
                    'isAdmin' : False,
                    'PersonContact': {
                        "Email": "Bob.Doe@ubc.ca",
                        'Phone' : "8888888888",
                        'Address': 'FirstNewUser'
                    }}
        
        
                    new_sc_entity = {
                    "ScEntityName" : " Moderna",
                    "ScEntityLocation" : "345 DEF St, ON, CAN",
                    "ScEntityContact": "1234567890",
                    "isApprovedByAdmin": False,
                    "ScentityTypeCode": 2,
                    "PersonIds": [],
                    "JoiningRequests" : [],
                    "ScEntityIdentificationCode" : "ABCD1234",    
                    "ScEntityIdentificationCodeType" : "BusinessNumber"               
                    }

   ```
   * ### case 1 : New Person and new entity
        Make no change to the code. In this case a new person and a new entity will be created. Notice that even if the person chooses to not become admin- it will be assigned admin privledge to accept joining request if it is making new entities.
        </br>
        In the terminal type:

        ``` terminal
        python register_person.py
        ```

        You should get following output:
        ``` terminal
        buzzlite@buzzlite-hp-laptop-14-cf0xxx:~/MCG_QLDB-Q1$ python register_person.py 
        INFO:botocore.credentials:Found credentials in environment variables.
        INFO:__main__:Person not found.
        INFO:insert_document:Inserting some documents in the Persons table...
        INFO:__main__:Existing Person Ids are: [['3Qv6MVetkVb5AozExa9ZMc', 'BqZVUy9o3sLJwhOzkfp6ON']]
        INFO:__main__:Registering new driver's entity...
        INFO:__main__:Entity not found. Registering new Entity
        INFO:__main__: Request not found
        INFO:__main__:Person with person id :2pdvi32jwVx1ebi9fti25g was made an admin.
        INFO:insert_document:Inserting some documents in the  SCEntities table...
        INFO:__main__:Successfully registered new SCEntity with ScEntityIdentificationCode : ABCD1234 and ScEntityId: 1iSbvTczupdEflpMBThUSc.
        ```
   * ### case 2 : existing Person and new entity
        Change *SCentityIdentificationCode* to a random string but do not make any chane in *new_person*. For example:
        ``` python
        new_sc_entity = {
                    "ScEntityName" : " CompanyA",
                    "ScEntityLocation" : "abad,asdasd,asdad",
                    "ScEntityContact": "1234567890",
                    "isApprovedByAdmin": False,
                    "ScentityTypeCode": 2,
                    "PersonIds": [],
                    "JoiningRequests" : [],
                    "ScEntityIdentificationCode" : "RUTYTU1234",    
                    "ScEntityIdentificationCodeType" : "BusinessNumber"               
                    }
        ```
        and type:
        ``` terminal
        python register_person.py
        ```
        You should get following ouput:
        ```terminal
        buzzlite@buzzlite-hp-laptop-14-cf0xxx:~/MCG_QLDB-Q1$ python register_person.py 
        INFO:botocore.credentials:Found credentials in environment variables.
        INFO:__main__:Person already exists.
        INFO:__main__:Person with  employee_Id BOB123 already exists with PersonId: 2pdvi32jwVx1ebi9fti25g .
        INFO:__main__:Existing Person Ids are: [['3Qv6MVetkVb5AozExa9ZMc', 'BqZVUy9o3sLJwhOzkfp6ON'], '2pdvi32jwVx1ebi9fti25g']
        INFO:__main__:Person with personId '2pdvi32jwVx1ebi9fti25g' already belongs to a SC Entity
        ```


   * ### case 3 : new Person and existing entity
        replace the *new_person* in *register_person.py* by following:
        ```python
            new_person = {
            'EmployeeId': 'JANE123',
            'FirstName': 'JANE',
            'LastName': 'DOE',
            'isSuperAdmin' : False,
            'isAdmin' : False,
             'PersonContact': {
                "Email": "JAN.Doe@ubc.ca",
                'Phone' : "8888888888",
                'Address': 'FirstNewUser'
             }}
        ```
        and type:

        ``` terminal
        python register_person.py
        ```
        You should get following ouput:
        ```terminal
        buzzlite@buzzlite-hp-laptop-14-cf0xxx:~/MCG_QLDB-Q1$ python register_person.py 
        INFO:botocore.credentials:Found credentials in environment variables.
        INFO:__main__:Person not found.
        INFO:insert_document:Inserting some documents in the Persons table...
        INFO:__main__:Existing Person Ids are: [['3Qv6MVetkVb5AozExa9ZMc', 'BqZVUy9o3sLJwhOzkfp6ON'], '7j4KS5jx2C2D7jfkySod2g', '2pdvi32jwVx1ebi9fti25g']
        INFO:__main__:Registering new driver's entity...
        INFO:__main__:Entity already exists
        INFO:__main__: Entity already exist. Sending request to join it.
        INFO:__main__: Request not found
        INFO:insert_document:Inserting some documents in the JoiningRequest table...
        INFO:__main__:Sending request to the company Admin.
        INFO:__main__:Request sent with id 65vrXPWIXMqClbnei3PV8D
        ```

   * ### case 4 : exising Person and existing entity
        We can divide this case into two subcases - 
        #### subcase 1:
        An exisiting person first sends request to an existing entity and then tries to create a new entity.
        ```python
             new_sc_entity = {
            "ScEntityName" : " CompanyB",
            "ScEntityLocation" : "abad,asdasd,asdad",
            "ScEntityContact": "1234567890",
            "isApprovedByAdmin": False,
            "ScentityTypeCode": 2,
            "PersonIds": [],
            "JoiningRequests" : [],
            "ScEntityIdentificationCode" : "ASDSD1234",    
            "ScEntityIdentificationCodeType" : "BusinessNumber"               
            }

        ```
        #### subcase 1:
        An exisiting person already associated with an exisiting entity tries to send request to another existing entity.

        ```python
        new_sc_entity = {
            "ScEntityName" : " Moderna",
            "ScEntityLocation" : "345 DEF St, ON, CAN",
            "ScEntityContact": "1234567890",
            "isApprovedByAdmin": False,
            "ScentityTypeCode": 2,
            "PersonIds": [],
            "JoiningRequests" : [],
            "ScEntityIdentificationCode" : "ABCD1234",    
            "ScEntityIdentificationCodeType" : "BusinessNumber"               
            }
        ```


        In both the cases you will get the same output:
    
        ```terminal
        buzzlite@buzzlite-hp-laptop-14-cf0xxx:~/MCG_QLDB-Q1$ python register_person.py 
        INFO:botocore.credentials:Found credentials in environment variables.
        INFO:__main__:Person already exists.
        INFO:__main__:Person with  employee_Id JAN123 already exists with PersonId: Kgq2FBics1x6F4HMReubLj .
        INFO:__main__:Existing Person Ids are: [['3Qv6MVetkVb5AozExa9ZMc', 'BqZVUy9o3sLJwhOzkfp6ON'], '7j4KS5jx2C2D7jfkySod2g', '2pdvi32jwVx1ebi9fti25g']
        INFO:__main__:Registering new driver's entity...
        INFO:__main__:Entity not found. Registering new Entity
        INFO:__main__:Request already sent with id : 65vrXPWIXMqClbnei3PV8D
        INFO:__main__:Please wait for your company admin to approve the request.
        ```

6. Open *accept_joining_request.py* and replace 
*request_id* by "65vrXPWIXMqClbnei3PV8D"

    ```python
    if __name__ == '__main__':
        """
        Register a new driver's license.
        """
        try:
            with create_qldb_driver() as driver:
                
                request_id = "65vrXPWIXMqClbnei3PV8D"        
    
                driver.execute_lambda(lambda executor: approve_joining_request(executor,request_id))
        except Exception:
            logger.exception('Error accepting the request.')
    ```

        In the same terminal type

    ```terminal
    python accept_joining_request.py
    ```
    You should get following output: 
    ```terminal
    INFO:botocore.credentials:Found credentials in environment variables.
    INFO:__main__: Request exists.
    INFO:__main__:value of isAccepted in 65vrXPWIXMqClbnei3PV8D is : [0] 
    INFO:__main__:value of SenderPersonId in 65vrXPWIXMqClbnei3PV8D is : ['Kgq2FBics1x6F4HMReubLj'] 
    INFO:__main__:value of ScentityIdentificationCode in 65vrXPWIXMqClbnei3PV8D is : [RUTYTU1234] 
    INFO:__main__:Person Joined to the SCentity
    INFO:__main__:Request : 65vrXPWIXMqClbnei3PV8D Accepted
    ```
    In the same terminal type again:
    ```terminal
    python accept_joining_request.py
    ```
    Because request is already accepted now you will get:
    ```terminal
    buzzlite@buzzlite-hp-laptop-14-cf0xxx:~/MCG_QLDB-Q1$ python accept_joining_request.py 
    INFO:botocore.credentials:Found credentials in environment variables.
    INFO:__main__: Request exists.
    INFO:__main__:value of isAccepted in 65vrXPWIXMqClbnei3PV8D is : [1] 
    INFO:__main__:Request Already accepted
    ```
    #### **It is highly recommended to perform SELECT queryies in query editor on QLDB Console to check tables are changing and how data is inputting**
