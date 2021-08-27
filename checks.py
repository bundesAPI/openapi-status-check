import schemathesis
from schemathesis import checks
from schemathesis.runner.events import AfterExecution

from utils import get_secret

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
                            if type(value) is str and "%25" in value:
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
