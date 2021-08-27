import requests
import json

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

