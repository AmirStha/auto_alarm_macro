import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    conf_file = {
        'lambda': {
            '4xx_count': {
                'AlarmName': '4xxErrors',
                'MetricName': 'Errors',
                'EvaluationPeriods': '1',
                'ComparisonOperator': 'GreaterThanThreshold',
                "DimensionsName": 'FunctionName',
                'Namespace': 'AWS/Lambda', 
                'Period': '60',
                'Statistic': 'Sum', 
                'Threshold': 5,
                'Unit': 'Count'
            },
            'invocations_count':{
                'AlarmName': 'Invocations',
                'MetricName': 'Invocations',
                'EvaluationPeriods': '1',
                'ComparisonOperator': 'GreaterThanThreshold',
                "DimensionsName": 'FunctionName',
                'Namespace': 'AWS/Lambda', 
                'Period': '60',
                'Statistic': 'Sum',
                'Threshold': 5,
                'Unit': 'Count'
            },
            'throttles_count': {
                'AlarmName': 'Throttles',
                'MetricName': 'Throttles',
                'EvaluationPeriods': '1',
                'ComparisonOperator': 'GreaterThanThreshold',
                "DimensionsName": 'FunctionName',
                'Namespace': 'AWS/Lambda', 
                'Period': '60',
                'Statistic': 'Sum', 
                'Threshold': 5,
                'Unit': 'Count'
            } 
        },
        'ec2': {
            'cpu_utilization': {
                'AlarmName': 'CPUUtilization',
                'MetricName': 'CPUUtilization', 
                'EvaluationPeriods': '5',
                'ComparisonOperator': 'GreaterThanOrEqualToThreshold', 
                "DimensionsName": 'InstanceId',
                'Namespace': 'AWS/EC2', 
                'Period': '120', 
                'Statistic': 'Average', 
                'Threshold': '85', 
                'Unit': 'Percent'
            },
            'status_check': {
                'AlarmName':'StatusCheck',
                'MetricName':'StatusCheckFailed_Instance', 
                'EvaluationPeriods': '5', 
                'ComparisonOperator': 'GreaterThanOrEqualToThreshold',                                                                       
                "DimensionsName": 'InstanceId',
                'Namespace': 'AWS/EC2', 
                'Period': '120', 
                'Statistic': 'Average',
                'Threshold': '20', 
                'Unit': 'Percent'
            }
        }
    }

    alarm_dictionary = {}
    fragment = event["fragment"]
    monitoring_topic = os.environ['SNSTopic']
    logger.info('Input Template: {}'.format(fragment))
    resources = fragment['Resources']

    logger.info(">>>>>>>>>>> event['params']: {}".format(event['params']))

    for resource in resources:
        logger.info('Searching {} for resource type'.format(resource))
        resource_json = resources[resource]
        try:   
            if resource_json['Type'] == 'AWS::Lambda::Function':
                print(">>>>>>>>>>>>>>>>>> resource_json", resource_json)
                # if resource_json and resource_json['FunctionName']:
                #     print(">>>>>>>>>>>>>>>>>> ", resource_json['FunctionName'])
                print("This is a lambda resource")
                logger.info('Resource {} is a lambda function'.format(resource))
                lambda_alarms = aws_alarms(resource,monitoring_topic,resource_json, conf_file['lambda'])
                alarm_dictionary.update(lambda_alarms)
            # elif resource_json['Type'] == 'AWS::EC2::Instance':
            #     logger.info('Resource {} is an EC2'.format(resource))
            #     ec2_alarms = aws_alarms(resource,monitoring_topic,resource_json, conf_file['ec2'])
            #     alarm_dictionary.update(ec2_alarms)
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

def aws_alarms(resource, monitoring_topic, resource_json, conf):
    print("aws_alarms")
    alarm_dict = {}
    for _,v in conf.items():
        resource_alarm = generate_alarm(resource, monitoring_topic, {
                                        'AlarmName': v['AlarmName'],
                                        'MetricName': v['MetricName'],
                                        'EvaluationPeriods': v['EvaluationPeriods'],
                                        'ComparisonOperator': v['ComparisonOperator'],
                                        "Dimensions": [{"Name": v['DimensionsName'],"Value": {"Ref": f'{resource}'}}],
                                        'Namespace': v['Namespace'], 
                                        'Period': v['Period'],
                                        'Statistic': v['Statistic'], 
                                        'Threshold': v['Threshold'],
                                        'Unit': v['Unit']}, resource_json)
        alarm_dict.update(resource_alarm)
    print("alarm_dict: ", alarm_dict)
    return alarm_dict

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
