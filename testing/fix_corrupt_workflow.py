import json

WORKFLOW_PATH = "Your\\Workflow\\Path\\File.json"


def fix_workflow():
    f = open(WORKFLOW_PATH)
    workflow = json.load(f)
    for node in workflow["nodes"]:
        inputs = node.get("inputs", None)
        if inputs is not None:
            for input in inputs:
                if type(input["type"]) is list:
                    input["type"] = "*"
    for link in workflow["links"]:
        if type(link[5]) is list:
            link[5] = "*"

    save_workflow(workflow)


def save_workflow(workflow):
    json_object = json.dumps(workflow, indent=4)
    with open(WORKFLOW_PATH, "w") as outfile:
        outfile.write(json_object)


fix_workflow()
