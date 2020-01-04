import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    alarm_dictionary = {}
    fragment = event["fragment"]
    monitoring_topic = os.environ['SNSTopic']
    logger.info('Input Template: {}'.format(fragment))
    resources = fragment['Resources']
    for resource in resources:
        logger.info('Searching {} for resource type'.format(resource))
        resource_json = resources[resource]
        try:             
            
            if resource_json['Type'] == 'AWS::Lambda::Function':
                logger.info('Resource {} is a lambda function'.format(resource))
                lambda_alarms = aws_lambda(resource,monitoring_topic,resource_json)
                alarm_dictionary.update(lambda_alarms)
            else:
                logger.info('Resource {} is not of a supported resource type'.format(resource))
        except Exception as e:
            logger.error('ERROR {}'.format(e))
            resp = {
                'requestId': event['requestId'],
                'status': 'failure',
                'fragment': fragment
            }
            return resp
    resources.update(alarm_dictionary)
    logger.info('Final Template: {}'.format(fragment))

    # Send Response to stack
    resp = {
        'requestId': event['requestId'],
        'status': 'success',
        'fragment': fragment
    }
    return resp

def aws_lambda(resource,monitoring_topic,resource_json):
    lambda_dict = {}
    lambda_4xx_count = generate_alarm(resource, monitoring_topic,
                                          {'AlarmName': '4xxErrors', 'MetricName': 'Errors',
                                           'EvaluationPeriods': '1',
                                           'ComparisonOperator': 'GreaterThanThreshold',
                                           "Dimensions": [{"Name": 'FunctionName',"Value": {"Ref": f'{resource}'}}],
                                           'Namespace': 'AWS/Lambda', 'Period': '60',
                                           'Statistic': 'Sum', 'Threshold': 0, 'Unit': 'Count'},resource_json)
    lambda_dict.update(lambda_4xx_count)
    lambda_invocations_count = generate_alarm(resource, monitoring_topic,
                                       {'AlarmName': 'Invocations', 'MetricName': 'Invocations',
                                        'EvaluationPeriods': '1',
                                        'ComparisonOperator': 'GreaterThanThreshold',
                                        "Dimensions": [{"Name": 'FunctionName',"Value": {"Ref": f'{resource}'}}],
                                        'Namespace': 'AWS/Lambda', 'Period': '60',
                                        'Statistic': 'Sum', 'Threshold': 5,
                                        'Unit': 'Count'},resource_json)
    lambda_dict.update(lambda_invocations_count)
    lambda_invocations_count = generate_alarm(resource, monitoring_topic,
                                       {'AlarmName': 'Throttles', 'MetricName': 'Throttles',
                                        'EvaluationPeriods': '1',
                                        'ComparisonOperator': 'GreaterThanThreshold',
                                        "Dimensions": [{"Name": 'FunctionName',"Value": {"Ref": f'{resource}'}}],
                                        'Namespace': 'AWS/Lambda', 'Period': '60',
                                        'Statistic': 'Sum', 'Threshold': 5,
                                        'Unit': 'Count'},resource_json)
    lambda_dict.update(lambda_invocations_count)
    return lambda_dict







def generate_alarm(resource,monitoring_topic,alarm,resource_json):
    alarm_template = {f'{resource}{alarm["AlarmName"]}': {
        "Type": "AWS::CloudWatch::Alarm",
        "Properties": {
            "AlarmActions": [monitoring_topic],
            "AlarmDescription": {
                "Fn::Join": [
                    " - ", [
                        f'{alarm["MetricName"]}',
                        {
                            "Ref": f'{resource}'
                        }
                    ]
                ]
            },
            "AlarmName": {
                "Fn::Join": [
                    "-", [
                        {
                            "Ref": "AWS::StackName"
                        },
                        f'{resource}',
                        f'{alarm["MetricName"]}'
                    ]
                ]
            },
            'EvaluationPeriods': f'{alarm["EvaluationPeriods"]}',
            "ComparisonOperator": f'{alarm["ComparisonOperator"]}',
            "Dimensions": alarm["Dimensions"],
            "MetricName": f'{alarm["MetricName"]}',
            "Namespace": f'{alarm["Namespace"]}',
            "Period": f'{alarm["Period"]}',
            "Statistic": f'{alarm["Statistic"]}',
            "Threshold": f'{alarm["Threshold"]}',
            "Unit": f'{alarm["Unit"]}'
        }
    }}
    condition = resource_json.get('Condition')
    if condition != None:
        alarm_template[f'{resource}{alarm["AlarmName"]}']["Condition"] = condition
        return alarm_template
    else:
        return alarm_template
