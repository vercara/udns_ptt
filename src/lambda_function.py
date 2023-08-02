import json
import os
import requests

def lambda_handler(event, context):
    webhook_url = os.getenv("WEBHOOK_URL", None)

    if webhook_url is None:
        # Return error message if no webhook URL is set
        return {
            'statusCode': 500, 
            'body': 'Webhook URL is not set'
        }

    source_ip = event["requestContext"]["http"]["sourceIp"]
    whitelisted_ips = os.getenv("WHITELISTED_IPS", None)

    if whitelisted_ips is not None:
        # Split the string into a list, and remove any leading or trailing whitespace from each IP address
        whitelisted_ips = [ip.strip() for ip in whitelisted_ips.split(",")]
        
        if source_ip not in whitelisted_ips:
            return {
                'statusCode': 403, 
                'body': 'Forbidden'
            }

    telemetry_events = json.loads(event['body'])
    
    # If it's a test, return OK
    for event in telemetry_events['telemetryEvents']:
        if event['telemetryEventType'] == 'TEST_TELEMETRY_WEBHOOK':
            return {
                'statusCode': 200,
                'body': 'OK'
            }
    
    # Pull some attributes from the event JSON
    telemetry_event_type = telemetry_events['telemetryEvents'][0]['telemetryEventType']

    telemetry_event = telemetry_events['telemetryEvents'][0]['telemetryEvent']
    object_type = telemetry_event['objectType']
    change_type = telemetry_event['changeType']
    change_time = telemetry_event['changeTime']
    change_source = telemetry_event['application']
    ultra_user = telemetry_event['user']
    ultra_object = telemetry_event['object']
    account_name = telemetry_event['account']
    
    # Define Teams card
    teams_message = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": "{0} {1} {2} {3}".format(account_name, telemetry_event_type, object_type, change_type),
        "sections": [
            {
                "activityTitle": "{0} {1} {2} {3}".format(account_name, telemetry_event_type, object_type, change_type),
                "facts": [
                    {"name": "Time", "value": change_time},
                    {"name": "Object Type", "value": object_type},
                    {"name": "Change Type", "value": change_type},
                    {"name": "Object", "value": ultra_object},
                    {"name": "Account", "value": account_name},
                    {"name": "User", "value": ultra_user},
                    {"name": "Application", "value": change_source}
                ],
                "markdown": True
            }
        ]
    }
    
    # This section will format the specific change details
    if 'detail' in telemetry_event:
        changes_array = telemetry_event['detail']['changes']
        for change in changes_array:
            teams_message['sections'][0]['facts'].extend([
                {"name": "Value", "value": change['value'] if change['value'] else '-'},
                {"name": "From", "value": change['from'] if change['from'] else '-'},
                {"name": "To", "value": change['to'] if change['to'] else '-'}
            ])
    
    # Send the message to Teams
    response = requests.post(webhook_url, json.dumps(teams_message), headers={'Content-Type': 'application/json'})
    response.raise_for_status()
    
    return {
        'statusCode': 200,
        'body': 'OK'
    }