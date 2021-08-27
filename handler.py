import schemathesis
from schemathesis import checks
from schemathesis.runner.events import AfterExecution
import statuspageio
import requests

class StatuspageClient:
    def __init__(self):
        self.page_id, self.api_key = get_secret()

        self.headers = {
            'Authorization': self.api_key,
        }

    def groups(self):
        response = requests.get(f"https://api.statuspage.io/v1/pages/{self.page_id}/component-groups", headers=self.headers)
        return response.json()

    def paths(self):
        response = requests.get(f'https://api.statuspage.io/v1/pages/{self.page_id}/components?per_page=1100', headers=self.headers)
        return response.json()

    def create_group(self, name, description, components):

        data = [
            ('component_group[name]', name),
            ('component_group[description]', description)
        ]

        for component in components:
            data.append(('component_group[components][]', component),)


        response = requests.post(f"https://api.statuspage.io/v1/pages/{self.page_id}/component-groups",
                                 headers=self.headers, data=data)
        return response.json()


    def update_group(self, group_id, name, description, components):

        data = [
            ('component_group[name]', name),
            ('component_group[description]', description)
        ]

        for component in components:
            data.append(('component_group[components][]', component),)


        response = requests.patch(f"https://api.statuspage.io/v1/pages/{self.page_id}/component-groups/{group_id}",
                                  headers=self.headers, data=data)
        return response.json()

    def create_component(self, name, description, status):
        data = {
            'component[description]': description,
            'component[status]': status,
            'component[name]': name,
            'component[showcase]': True
        }
        response = requests.post(f'https://api.statuspage.io/v1/pages/{self.page_id}/components', headers=self.headers, data=data)
        return response.json()

    def update_component(self, component_id, name, description, status):

        data = {
            'component[description]': description,
            'component[status]': status,
            'component[name]': name,
            'component[showcase]': True
        }

        response = requests.patch(f'https://api.statuspage.io/v1/pages/{self.page_id}/components/{component_id}', headers=self.headers, data=data)
        return response.json()


class SchemaChecker:
    def check(self, path, base_url):
        #schema = schemathesis.from_uri("./openapi.yaml")
        schema = schemathesis.from_uri(path, base_url=base_url)
        runner = schemathesis.runner.from_schema(schema, checks=checks.ALL_CHECKS)

        paths = {}
        for event in runner.execute():
            if isinstance(event, AfterExecution):
                print()
                print(event.result.logs)
                status = None
                failed_examples = []
                num_success = 0
                num_failed = 0
                for check in event.result.checks:
                    ignore_char_found = False

                    # some edge cases

                    # autobahn edge case that should be ok for every other api too
                    if check.example.path_parameters:
                        for param, value in check.example.path_parameters.items():
                            if "%25" in value:
                                ignore_char_found = True
                    if not ignore_char_found:
                        if not status or status == "success":
                            status = check.value
                        if check.value != "success":
                            failed_examples.append(check)
                            num_failed += 1
                        else:
                            num_success += 1

                paths[event.result.verbose_name] = {"status": status, "failed_checks": failed_examples, "num_failed": num_failed,
                                                    "num_success": num_success}

        return paths


import boto3
import base64
from botocore.exceptions import ClientError


def get_secret():

    secret_name = "statuspage"
    region_name = "eu-central-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        print(get_secret_value_response)
        return get_secret_value_response['STATUSPAGE_PAGE_ID'], get_secret_value_response['STATUSPAGE_PAGE_SECRET']


#help(schema)
def run(event, context):

    name = "autobahn-api"
    description = """Was passiert auf Deutschlands Bundesstraßen? API für aktuelle Verwaltungsdaten zu Baustellen, Staus und Ladestationen. Außerdem Zugang zu Verkehrsüberwachungskameras und vielen weiteren Datensätzen.
    """
    checker = SchemaChecker()
    check_paths = checker.check(f"https://raw.githubusercontent.com/bundesAPI/{name}/main/openapi.yaml", "https://verkehr.autobahn.de/o/autobahn")
    #print(paths)
    statuspage = StatuspageClient()

    statuspage_mapping = {}
    # name mapping
    for status_path in statuspage.paths():
        statuspage_mapping[status_path["name"]] = status_path["id"]
    print(statuspage_mapping)

    status_components = []
    for path, path_details in check_paths.items():
        status = "operational"
        if path_details["num_failed"] > 0 and path_details["num_success"] > 0:
            status = "partial_outage"
        elif path_details["num_failed"] > 0 and path_details["num_success"] == 0:
            status = "outage"
        if path in statuspage_mapping:
            result = statuspage.update_component(statuspage_mapping[path], path, " ", status)
            status_components.append(statuspage_mapping[path])
        else:
            result = statuspage.create_component(path, " ", status)
            status_components.append(result["id"])

    # find group id
    group_id = None
    for group in statuspage.groups():
        if group["name"] == name:
            group_id = group['id']

    if not group_id:
        group = statuspage.create_group(name, description, status_components)
        print(group)
        group_id = group['id']
        print(f"created group {group_id}")
    else:
        group = statuspage.update_group(group_id, name, description, status_components)
        print(f"updated group {group_id}")

    response = {
        "statusCode": 200,
        "body": "done"
    }

    return response