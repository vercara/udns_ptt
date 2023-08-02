udns_ptt
======================

This repository, udns_ptt, stands for "UltraDNS Push-to-Teams" and contains a Lambda handler which parses the telemetry event JSON that is output by Vercara's UDNS product's push notification mechanism then creates a Message Card to be consumed by a MS Teams webhook.  

## Creating the Lambda Function

You'll need to create a Lambda function and give it an endpoint. I used the "Function URL" feature of Lambda, but this can also be done through the API Gateway.

1. Select the radio button for "Author from scratch"
2. Name your function
3. For "Runtime," choose Python 3.xx
4. Expand "Advanced Settings"
5. Check the box next to "Enable function URL"
6. Select "NONE" for "Auth type"
    * The UDNS push notifications won't be capable of sending an authorization header, but you can restrict your function url to their specific IPs. I will get to this below.
7. Click "Create Function"

## Creating a Deployment Package

I'm using the 'requests' module, so we should include that in the deployment package. Assuming you're in the root directory of this repo, do the following:

```bash
mkdir lambda_package
pip install dnspython -t lambda_package
cp src/lambda_function.py lambda_package/lambda_function.py
zip -r lambda_package.zip lambda_package
```

Upload this in the Management Console (or through the CLI). In the UI:

1. Pull up your Lambda function
2. Click "Upload from" then select ".zip file"
3. Upload "lambda_package.zip"

## Set the Environment Variables

There are two environment variables used by this function and one is required.

### WEBHOOK_URL

The `WEBHOOK_URL` is the link to the webhook you've configured in Teams. Follow these steps to create one:

1. Go to your Teams channel
2. Click on the "..." in the top right
3. Click on "Connectors"
4. Search for "Incoming Webhook"
    * If the button next to it says "Add," then click that to Add the plugin and navigate back to Connectors to proceed
5. Click "Configure"
6. Give your webhook a name
7. Click "Create"
8. Copy the URL, this is where you will push the notifications

Go to your Lambda function in the Management Console.

1. Click on the "Configuration" tab
2. In the left-hand navigation pane, click "Environment variables"
3. Click "Edit"
4. Click "Add environment variable"
5. Under "Key" enter "WEBHOOK_URL"
6. Under "Value" paste the URL you copied from Teams
7. Click "Save"

### WHITELISTED_IPS

By default the function will allow requests from anyone. By defining the "WHITELISTED_IPS" variable, you will restrict access to certain IPs, the ones belonging to UDNS's push notification application servers.

1. Again, navigate to the "Configuration" tab in Lambda
2. Click "Environment variables"
3. "Edit"
4. "Add environment variable"
5. This time enter "WHITELISTED_IPS" as the "Key"
6. For the value, paste in your list of IPs, separated by commas like so: `52.87.134.132,52.201.155.120,52.201.103.62,52.201.155.234,52.10.123.90,52.10.63.3,52.39.68.132`
7. Click "Save"

## Creating the Push Notification

In the UDNS UI, or through the API, you need to create a Push Notification. The UDNS system will test the endpoint to make sure it's responsive before it will start publishing messages to it. I'll describe how to create one through the API and include Postman collection in the "postman" directory.

1. Send an authorization request to the UDNS REST API and generate a Bearer token. The request body is x-www-form-urlencoded and needs to contain a grant_type and your username/password.

`POST https://api.ultradns.com/authorization/token`

```bash
grant_type:password
username:{your_username}
password:{your_password}
```

The response will contain an object with a "bearer_token" parameter. All subsequent requests to the API must contain this in the authorization header.

`Authorization: Bearer {your_token}`

2. Send the request to test your endpoint. This will return an ID which you can use to check the status of your Push Notification configuration.

`POST https://api.ultradns.com/accounts/{your_account_name}/telemetryWebhook/test`

The body needs to contain the following.

```json
{
    "url": "{your_lambda_endpoint}",
    "type": "TEST_TELEMETRY_WEBHOOK"
}
```

It will respond back with an object containing the telemetry ID.

```json
{
    "telemetryEventId": "3e58c9a7-5e7b-405f-8bf6-b8bad72a32e8",
    "telemetryEventType": "TEST_TELEMETRY_WEBHOOK",
    "telemetryEventTime": "2023-06-22 12:13:33.441",
    "environment": "test",
    "accountName": "{your_account_name}"
}
```

3. You can append this ID to the end of the test URI and request its status using a GET request.

`GET https://api.ultradns.com/accounts/{your_account_name}/telemetryWebhook/test/{telemetry_event_id}`

If there was an issue creating the telemetry event then there will be an error message containing a reason, but if the creation was successful there will simply be an HTTP 200 response code and no body.

4. Send a request to the "Create" endpoint. The payload will include your Lambda url and the events for which you want to receive notifications.

`POST https://api.ultradns.com/accounts/{your_account_name}/settings/PUSH_NOTIFICATIONS`

```json
{
    "webhooks": [
        {
            "enable": true,
            "url": "{your_lambda_endpoint}",
            "include": {
                "ALL_CHANGES": true
            }
        }
    ]
}
```

All of the params available for the "include" object are: ALL_CHANGES, DOMAIN_CHANGES, RECORD_CHANGES, USER_GROUP_CHANGES, ALL_EVENTS, ZONE_EVENTS, FAILOVER_EVENT, DNSSEC_EVENT, XFR_EVENTS, ZONE_TRANSFER_SUCCESS, ZONE_TRANSFER_FAILURE, AUTHENTICATION_EVENTS, LOGIN_SUCCESS and LOGIN_FAILURE

### From the UI

In the UDNS UI follow these steps:

1. Click on "Accounts" in the left-hand navigation
2. Click on your account name
3. Navigate to the "Notification Settings" tab
4. Under "Realtime Push Notification" click "+Add"
5. Enter a name for your endpoint and the Lambda URL
6. Click "Test Connection"
7. Click "Configure Channels"
8. Configure your desired channels and save

## License

This project is licensed under the terms of the MIT license. See LICENSE.md for more details.