# BMNT Intake Form API

This documents the Retool Form and AWS Lambda code

```bash
.
├── README.md                   <-- This instructions file
├── retool_form_code            <-- Source code for a lambda function
│   ├── bmntenv/                <-- virtual envrionment that contains the dependencies
│   ├── lambdacode.zip          <-- zip file that contains all the code/dependencies necessary to run on AWS Lambda
├── .gitignore                  <-- gitignore
├── app.py                      <-- python code for both lambda functions that implements the logic of submitting to retool
├── constants.py                <-- file that defines lots of constants. if you need to make a change, it's probably here
```

## Starting From Scratch

#### Setting up your account

Register for an AWS Free Tier Account at [AWS](https://aws.amazon.com).
For this project, the only services we will be using are Lambda, API Gateway, and CloudWatch for logging.

The following steps are modified from a tutorial that can be found here. 
Please refer back to [this](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-create-api-as-simple-proxy-for-lambda.html) for further information

##### Part 1. Setting up the lambda functions

    1. Sign in to the Lambda console at https://console.aws.amazon.com/lambda.
    
    2. On the AWS navigation bar, choose a region (for example, US East (N. Virginia)).
    
        **Note**
    
        Note the region where you create the Lambda function. You'll need it when you create the API.
        
        Choose Functions in the navigation pane.
    
    3. Choose Create function.
    
    4. Choose Author from scratch.
    
    5. Under Basic information, do the following:
    
        a. In Function name, enter submitRetoolProblemToAirtable.
    
        b. From the Runtime dropdown list, choose python 3.6.
    
        c. Under Permissions, expand Choose or create an execution role. From the Execution role dropdown list, choose Create new role from AWS policy templates.
    
        d. In Role name, enter GetStartedLambdaBasicExecutionRole.
    
        e. Leave the Policy templates field blank.
    
        f. Choose Create function.
    
    6. Repeat steps 1-5, but this time use a Function name of updateRetoolProblemInAirtable, and reuse the role you just made in step 5.c and 5.d
    
    At this point, you should have two lambda functions setup. Verify that you can see these functions in the AWS Lambda console -> functions.
    
    Now we wil upload the code for these functions.
    
    1. Click on one of the functions, which should take you to a detail page of the function.
    2. Under the Function Code section, make sure the following values are as below
      * Code entry type: Upload a .zip package
      * Runtime: python3.6
      * Handler: app.submit_problem_handler, or app.updated_problem_handler depending on which lambda function you are configuring
      * Function Package: upload the lambdacode.zip file
      
    Finally, click save in the upper right hand corner. Once the save button stops loading, you are good to go.
        
##### Part 2. Setting up the API

    1. Sign in to the API Gateway console at https://console.aws.amazon.com/apigateway.

    2. If this is your first time using API Gateway, you see a page that introduces you to the features of the service. Choose Get Started. When the Create Example API popup appears, choose OK.

        If this is not your first time using API Gateway, choose Create API.

    3. Create an empty API as follows:

        a. Under Choose the protocol, choose REST.

        b. Under Create new API, choose New API.

        c. Under Settings:

            For API name, enter BMNTIntakeApi.

            If desired, enter a description in the Description field; otherwise, leave it empty.

            Leave Endpoint Type set to Regional.

        d. Choose Create API.

    4. Create the submitproblem and updateproblem resource as follows (do these steps for both):

        a. Choose the root resource (/) in the Resources tree.

        b. Choose Create Resource from the Actions dropdown menu.

        c. Leave Configure as proxy resource unchecked.

        d. For Resource Name, enter submitproblem or updateproblem.

        e. Leave Resource Path set to /submitproblem or /updateproblem.

        f. Leave Enable API Gateway CORS unchecked.

        g. Choose Create Resource.

    5. In a proxy integration, the entire request is sent to the backend Lambda function as-is, via a catch-all ANY method that represents any HTTP method. The actual HTTP method is specified by the client at run time. The ANY method allows you to use a single API method setup for all of the supported HTTP methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, and PUT.

    6. To set up the ANY method, do the following (do this for both submitproblem and updateproblem):

        a. In the Resources list, choose /submitproblem or /updateproblem.

        b. In the Actions menu, choose Create method.

        c. Choose ANY from the dropdown menu, and choose the checkmark icon

        d. Leave the Integration type set to Lambda Function.

        e. Choose Use Lambda Proxy integration.

        f. From the Lambda Region dropdown menu, choose the region where you created the submitRetoolProblemToAirtable and updateRetoolProblemInAirtable Lambda function.

        g. In the Lambda Function field, type any character and choose appropriate lambda function from the dropdown menu.

        h. Leave Use Default Timeout checked.

        i. Choose Save.

        j. Choose OK when prompted with Add Permission to Lambda Function.
        
##### Part 3. Deploying the API

    Deploy the API in the API Gateway console

    1. Choose Deploy API from the Actions dropdown menu.

    2. For Deployment stage, choose [new stage].

    3. For Stage name, enter test.

    4. If desired, enter a Stage description.

    5. If desired, enter a Deployment description.

    6. Choose Deploy.

    7. Note the API's Invoke URL.
    
    This URL will be used in retool in the submitSourced, submitCurated, and submitUpdated queries
    
    
At this point, everything in AWS is set up and ready to go. 
If you need to change things in the code because fields have been updated in airtable, or something is going wrong, here is what you should do.
* Make the necessary code changes. These should only happen in app.py and constants.py.
* Replace these files in the lambdacode.zip file. If you open up the zip, replace the existing versions with the updated versions, and zip the folder again you will be good to go
* Alternatively, if you're good with the command line: 
```bash 
User$ zip -g lambdacode.zip ../app.py
```
* Reupload this zip file to both lambda functions as you did in the last steps of part 1

If you only needed to make changes in the code, that is all you have to do.

## Retool Form

The retool form structure has not changed too much since the previous version. The main thing to keep up to date with here is the labels and values for the dropdown fields.
This is the most common cause for an error returned by the api. 

The other place where you will most likely need to make changes is in the javascript queries:
* sourcedProblem, curatedProblem, updatedProblem

This is straightforward code that takes the information provided in retool, and packages it as key-value pairs for the api we just set up.
If a field name changes in airtable, it will need to be changed in one or all of these queries. This is case sensitive. 
* Ex 1: If the field "employee_sourced_curated" changes to "employee", you would need to change the place in the code where it says "data.employee_sourced_curated = **_employee_sourced_curated.value" to "data.employee = **_employee_sourced_curated.value"
* Ex 2: If the field "sponsor_name" change to "Sponsor Name", you would need to change the place in the code where it says "data.sponsor_name = **_sponsor_name.value" to "data["Sponsor Name"] = **_sponsor_name.value"

The queries problemSearch, listSubGroupS, listSubGroupC, listSubgroupU should not require any changes. If those queries break...
* Check to make sure the table id (the part starting with tbl) is correct
* Check to make sure airtable hasn't change the way their formulas work (the filterByFormula value)
Those are the only things I have ever had to change in those queries. 

Finally, we have the submitSourced, submitCurated, submitUpdated queries. These call the apis that were created above.
* All these queries should be making POST requests
* Make sure the link in the URL box matches the link given to you when you deployed the API.
* For the submitSourced and submitCurated queries, append "submitproblem" to the url (last part should be /test/submitproblem)
* For the submitUpdated query, append "updateproblem" to the url (last part should be /test/updateproblem)
* For Headers, make sure the pair "Content-Type" + "application/json" is included
* For Body, specify JSON in the dropdown
* make a key "data", whose value is "{{ sourcedProblem.data }}" or "{{curatedProblem.data}} " or "{{ updatedProblem.data }}" depending on which query you are in

### CloudWatch Logs

I've added lots of logging statements in the lambda code to make it easier to pinpoint where things are going wrong. These are the lines "log.info" and "log.warn" in the code.
These files can be found in AWS CloudWatch. Go to your AWS console, and in the Find Services box search for CloudWatch and click it.
* On the left hand side of the page in CloudWatch, click on "Logs"
* In the Logs section, click on the lambda function which is having issues.
* Each of the records in these lists represents a time a user interacted with the form. You can use the search box at the top to search for the specific error message, and the corresponding log.
* Read the log and look for where the last [INFO] or [WARN] logging statement was made (towards bottom of list). Between here and the next logging statement is the last place in the code we made it to successfully.
* If there are no [INFO] or [WARN] statements...
* Make sure your API is deployed
* Make sure the link is correct in the Retool queries
* Hope for the best and try again