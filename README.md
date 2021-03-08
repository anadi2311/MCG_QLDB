# MCG_QLDB_Q1
Link to schemas that the ledger will follow can be found [here](https://drive.google.com/drive/u/0/folders/1IS2HPOj-qn73skQApdlg8dsEcCPBwvka)


For this use case we follow the following process flow:

![Process Flow](https://drive.google.com/uc?export=view&id=1f3VTwtJc_a45mu3zPwF3BvLG6To3r-Ur)


## step 1

Create an Free tier [Amazon Web Service account](https://signin.aws.amazon.com/signin?redirect_uri=https%3A%2F%2Faws.amazon.com%2Fmarketplace%2Fmanagement%2Fsignin%3Fstate%3DhashArgs%2523%26isauthcode%3Dtrue&client_id=arn%3Aaws%3Aiam%3A%3A015428540659%3Auser%2Faws-mp-seller-management-portal&forceMobileApp=0&code_challenge=azqjpcm1Vjza6tpSER_vY-5Fd-OLJD7xbxeseNdqciM&code_challenge_method=SHA-256)

## step 2
To Set up environment we will use docker container.
*   [Get  Docker](https://docs.docker.com/get-docker/)

## step 3
Open terminal and **cd** into the MCG_QLDB folder

## step 4
Input the environment variables into the terminal
<br/> *They should be in this format*:

---
export AWS_ACCESS_KEY_ID="asdasdadasdasdaad"
<br/>export AWS_SECRET_ACCESS_KEY="asdasdadasdadsadads"
<br> export AWS_SESSION_TOKEN = "lkhasldkhlkhlkahsdlkahsldkahsldkhalsdhalkdhalkshdlkhhhhhhkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk"

----------------------

## step 5

In the terminal build the image using 

```terminal
docker build -t mcg-qldb-image .
```

and then run the image

```terminal
docker run --env AWS_ACCESS_KEY_ID --env AWS_SECRET_ACCESS_KEY --env AWS_SESSION_TOKEN  mcg-qldb-image
```
