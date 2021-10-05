import ArchParser
import ArchValidator
import ArchUtil

def umlComponent(archFile) -> str:

    
    model_types, data_types, enum_types, use_case_types, ext_types = ArchParser.parse(archFile)
    
    puml_lines = []
    puml_lines.append("@startuml")
    for root_model_name in find_root_names(model_types):
        print_component_content(model_types[root_model_name], [], puml_lines, model_types)
    puml_lines.append("@enduml")

    retVal = ""
    for line in puml_lines:
        retVal = retVal + line + "\n"
    return retVal

def find_root_names(models):
    root = ""
    model_names = list(models.keys())
    
    if len(model_names) == 1:
        return model_names
    
    # there are multiple models, so we have to look through them
    subs = []  # names of subconponent models
    for name in model_names:
        model = models[name]
        components = ArchUtil.search(model, ["model", "components"])
        for component in components:
            # component is a Field type
            component_type = component["type"]
            # make sure this is a model type (not a data type)
            if component_type in model_names:
                # add the component type to the list of subs
                subs.append(component_type)

    # remove the subs types from model names
    res = [i for i in model_names if i not in subs]
    return res

def print_component_content(root, existing, puml_lines, model_types):

    model_name = root["model"]["name"]

    # define UML interface for each input
    inputs = ArchUtil.search(root, ["model", "behavior", "input"])
    for input in inputs:
        if (not input["type"] in existing):
            puml_lines.append("interface {}".format(input["type"]))
            existing.append(input["type"])

    # define UML interface for each output
    outputs = ArchUtil.search(root, ["model", "behavior", "output"])
    for output in outputs:
        if (not output["type"] in existing):
            puml_lines.append("interface {}".format(output["type"]))
            existing.append(output["type"])

    # define UML package for each component
    components = ArchUtil.search(root, ["model", "components"])
    
    if len(components) > 0:
        # if the model has a components, show it as a package
        puml_lines.append("package \"{}\" {{".format(model_name))
        existing.append(model_name)
        for component in components:
            # component is a Field type
            component_name = component["name"]
            component_type = component["type"]
            print_component_content(model_types[component_type], existing, puml_lines, model_types)
        
        puml_lines.append("}")
    else:
        # if there are no components, show it as a class
        inputs = ArchUtil.search(root, ["model", "behavior", "input"])
        for input in inputs:
            puml_lines.append("{} -> [{}] : {}".format(input["type"], model_name, input["name"]))
        outputs = ArchUtil.search(root, ["model", "behavior", "output"])
        for output in outputs:
            puml_lines.append("[{}] -> {} : {}".format(model_name, output["type"], output["name"]))


def umlSequence(archFile: str) -> str:

    model_types, data_types, enum_types, use_case_types, ext_types = ArchParser.parse(archFile)
    
    puml_lines = []
    
    for use_case_title in find_root_names(use_case_types):
        # start the uml
        puml_lines.append("@startuml")

        # add the title
        puml_lines.append("title {}".format(use_case_title))
        
        # declare participants
        participants = ArchUtil.search(use_case_types[use_case_title], ["usecase", "participants"])
        for participant in participants:  # each participant is a field type
            puml_lines.append("participant {} as {}".format(participant["type"], participant["name"]))

        # process steps
        steps = ArchUtil.search(use_case_types[use_case_title], ["usecase", "steps"])
        for step in steps:  # each step of a step type
            puml_lines.append("{} -> {} : {}".format(step["source"], step["target"], step["action"]))

        # end the uml 
        puml_lines.append("@enduml")
        puml_lines.append("")  # just put a blank line in between sequence diagrams for now  TODO revisit this decision later

    retVal = ""
    for line in puml_lines:
        retVal = retVal + line + "\n"
    return retVal
    
