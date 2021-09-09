from statuspage import StatuspageClient
from checks import SchemaChecker
import requests
import json

def run(event, context):

    projects = [
        {"name": "autobahn-api", "base_url": "https://verkehr.autobahn.de/o/autobahn"},
        {"name": "dwd-api", "base_url": "https://dwd.api.proxy.bund.dev/v30" },
        {"name": "travelwarning-api", "base_url": "https://www.auswaertiges-amt.de/opendata" },
        {"name": "risikogebiete-api", "base_url": "https://api.einreiseanmeldung.de/reisendenportal" },
        {"name": "luftqualitaet-api", "base_url": "https://www.umweltbundesamt.de/api/air_data/v2" },
        {"name": "smard-api", "base_url": "https://www.smard.de/app/chart_data" },
        {"name": "interpol-api", "base_url": "https://ws-public.interpol.int" },
        {"name": "mudab-api", "base_url": "https://geoportal.bafg.de/MUDABAnwendung/rest/BaseController/FilterElements" },
    ]
    for project in projects:
        name = project["name"]
        description = """"""
        checker = SchemaChecker()
        check_paths = checker.check(f"https://raw.githubusercontent.com/bundesAPI/{name}/main/openapi.yaml", project["base_url"])
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

if __name__ == "__main__":
    run(None, None)
