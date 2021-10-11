from aac import util


def validate(validate_me):

    foundInvalid = False
    errMsgList = []

    for model in validate_me.values():
        isValid, errMsg = validate_general(model)
        if not isValid:
            # print("Enum Validation Failed: {}".format(errMsg))
            foundInvalid = True
            errMsgList = errMsgList + errMsg

    # combine parsed types and AaC built-in types
    aac_data, aac_enums = util.getAaCSpec()
    # ext_types = {}

    isValid, errMsg = validate_cross_references(validate_me)
    if not isValid:
        foundInvalid = True
        errMsgList = errMsgList + errMsg

    isValid, errMsg = validate_enum_values(validate_me)
    if not isValid:
        foundInvalid = True
        errMsgList = errMsgList + errMsg

    for ext in util.getModelsByType(validate_me, "ext"):
        type_to_extend = validate_me[ext]["extension"]["type"]
        if type_to_extend in aac_data or type_to_extend in aac_enums:
            apply_extension(validate_me[ext], aac_data, aac_enums)
        else:
            apply_extension(validate_me[ext], util.getModelsByType(validate_me, "data"), util.getModelsByType(validate_me, "enum"))

    return not foundInvalid, errMsgList


def validate_general(validate_me: dict) -> tuple[bool, list]:

    model = validate_me.copy()
    # remove any imports before validation
    if "import" in model:
        del model["import"]

    # any model can only have a single root
    if len(list(model.keys())) > 1:
        return False, ["AaC Validation Error: yaml file has more than one root defined"]

    # ensure the model has a known root
    root_name = list(model.keys())[0]
    if root_name not in util.getRoots():
        return False, [f"AaC Validation Error: yaml file has an unrecognized root {root_name}.  Known roots {util.getRoots()}"]

    # get the root type to validate against
    root_type = ""
    aac_data, aac_enums = util.getAaCSpec()
    for field in util.search(aac_data["root"], ["data", "fields"]):
        if field["name"] == root_name:
            root_type = field["type"]
            break

    return validate_model_entry(root_name, root_type, model[root_name], aac_data, aac_enums)


# def validate_enum(model) -> tuple[bool, list]:
#     """
#     Validates an Architecture-as-Code enum type.
#     An enum is a core type of AaC and not driven by the AaC yaml spec.
#     An enum contains a list of enumerated type definitions. Each enumerated type must have a name and a list of values.

#     :prarm model: the enum definition to be validated
#     :returns: boolean, errorMessage if boolean is False
#     """
#     # an enum item has a key of 'enum', and no other keys
#     if len(list(model.keys())) > 1:
#         return False, [
#             "yaml file has more than one root type, cannot validate (programming error)"
#         ]

#     if "enum" not in model.keys():
#         return False, ["the root type for enum must be 'enum'"]

#     enum = model["enum"]

#     # an enum must have a name
#     if "name" not in enum:
#         return False, ["data item missing name"]

#     # an enum must have a lit of values
#     if "values" not in enum:
#         return False, ["enum item missing values"]

#     values = enum["values"]

#     if not isinstance(values, list):
#         return False, ["enum item values should be a list"]

#     return True, [""]


# def validate_data(model, spec, enums):
#     """
#     Validates an Architecture-as-Code data type.
#     A data is a core type of AaC and not driven by the AaC yaml spec.
#     The data definition contains a list of type definitions. Each type definition must have a name and a list of fields.
#     Optionally, a type definition may specify required fields - all fields not required in the type definition are optional (just like a JSON schema).

#     :prarm model: the data definition to be validated
#     :param spec: the specification of all data types - dict[data name, data model] (this is just used to ensure a named type is known, aka has been parsed) (this includes AaC base types)
#     :returns: boolean, errorMessage if boolean is False
#     """
#     # a data item has a key of 'data', and no other keys  TODO:  import is also a valid root...need to make sure this is handled correctly
#     if len(list(model.keys())) > 1:
#         return False, [
#             "yaml file has more than one root type, cannot validate (programming error)"
#         ]
#     if "data" not in model.keys():
#         return False, ["the root type for data must be 'data'"]

#     data = model["data"]
#     # a data item has a name - this may be considered the type name - this is a list type so data has multiple data items

#     if "name" not in data:
#         return False, ["data missing name"]
#     name = data["name"]

#     # a data items has fields - this should be a list of dicts
#     if "fields" not in data:
#         return False, ["validate_data: data item missing fields"]
#     fields = data["fields"]
#     field_names = []
#     if not isinstance(fields, list):
#         return False, ["validate_data: data items fields should be a list"]

#     # validate fields
#     for field in fields:
#         if not isinstance(field, dict):
#             return False, ["valadate_data: data field definition must be a dict"]
#         # each field has a name
#         if "name" not in field:
#             return False, ["validate_data: field is missing name"]
#         field_name = field["name"]
#         field_names.append(field_name)
#         # print("field_name = {}".format(field_name))

#         # each field has a type - the type should be known in the spec
#         if "type" not in field:
#             return False, ["validate_data: field {} is missing type".format(field_name)]

#     # a data item may define required fields - ensure each required field is present in fields
#     if "required" in data:  # if required isn't present then all fields are optional
#         for required_field in data["required"]:
#             if required_field not in field_names:
#                 return False, [
#                     "validate_data: required field {} is not defined in {}".format(
#                         required_field, name
#                     )
#                 ]

#     return True, ""


def validate_cross_references(all_models):
    all_types = []

    models = util.getModelsByType(all_models, "model")
    data = util.getModelsByType(all_models, "data")
    enums = util.getModelsByType(all_models, "enum")

    all_types.extend(models.keys())
    all_types.extend(data.keys())
    all_types.extend(enums.keys())
    all_types.extend(util.getPrimitives())

    foundInvalid = False
    errMsgs = []

    for model_name in data.keys():
        data_entry = data[model_name]
        data_model_types = util.search(data_entry, ["data", "fields", "type"])
        # print("processing {} - data_model_types: {}".format(model_name, data_model_types))
        for data_model_type in data_model_types:
            isList, baseTypeName = getSimpleBaseTypeName(data_model_type)
            if baseTypeName not in all_types:
                foundInvalid = True
                errMsgs.append(
                    "Data model [{}] uses undefined data type [{}]".format(
                        model_name, baseTypeName
                    )
                )

    for model_name in models.keys():
        model_entry = models[model_name]
        model_entry_types = util.search(model_entry, ["model", "components", "type"])
        model_entry_types.extend(util.search(model_entry, ["model", "behavior", "input", "type"]))
        model_entry_types.extend(util.search(model_entry, ["model", "behavior", "output", "type"]))
        # print("processing {} - model_entry_types: {}".format(model_name, model_entry_types))
        for model_entry_type in model_entry_types:
            isList, baseTypeName = getSimpleBaseTypeName(model_entry_type)
            if baseTypeName not in all_types:
                foundInvalid = True
                errMsgs.append(
                    "Model model [{}] uses undefined data type [{}]".format(
                        model_name, baseTypeName
                    )
                )

    if not foundInvalid:
        return True, ""
    else:
        return False, errMsgs


def validate_enum_values(all_models):

    models = util.getModelsByType(all_models, "model")
    data = util.getModelsByType(all_models, "data")
    enums = util.getModelsByType(all_models, "enum")

    # at least for now, only models use actual enum values (rather than just types) in their definitions
    # first find the enum usage in the model definition
    enum_fields = {}  # key: type name  value: field
    for data_name in data:
        data_model = data[data_name]
        fields = util.search(data_model, ["data", "fields"])
        for field in fields:
            field_type = getSimpleBaseTypeName(field["type"])
            if field_type in enums.keys():
                enum_fields[data_name] = field
    # print("validate_enum_values: enum fields = {}".format(enum_fields))

    # find serach paths to the usage
    enum_validation_paths = {}
    for enum_name in enums.keys():
        if enum_name == "Primitives":
            # skip primitives
            continue
        found_paths = findEnumFieldPaths(enum_name, "model", "model", data, enums)
        # print("{} found_paths: {}".format(enum_name, found_paths))
        enum_validation_paths[enum_name] = found_paths

    # then ensure the value provided in the model is defined in the enum
    foundInvalid = False
    errMsgList = []

    valid_values = []
    for enum_name in enum_validation_paths.keys():
        if enum_name == "Primitives":
            # skip primitives
            continue

        valid_values = util.search(enums[enum_name], ["enum", "values"])
        # print("Enum {} valid values: {}".format(enum_name, valid_values))

        for model_name in models:
            for path in found_paths:
                for result in util.search(models[model_name], path):
                    # print("Model {} entry {} has a value {} being validated by the enumeration {}: {}".format(model_name, path, result, enum_name, valid_values))
                    if result not in valid_values:
                        foundInvalid = True
                        errMsgList.append(
                            "Model {} entry {} has a value {} not allowed in the enumeration {}: {}".format(
                                model_name, path, result, enum_name, valid_values
                            )
                        )

    if not foundInvalid:
        return True, [""]
    else:
        return False, errMsgList


def findEnumFieldPaths(find_enum, data_name, data_type, data, enums) -> list:
    # print("findEnumFieldPaths: {}, {}, {}".format(find_enum, data_name, data_type))
    data_model = data[data_type]
    fields = util.search(data_model, ["data", "fields"])
    enum_fields = []
    for field in fields:
        isList, field_type = getSimpleBaseTypeName(field["type"])
        if field_type in enums.keys():
            # only report the enum being serached for
            if field_type == find_enum:
                enum_fields.append([field["name"]])
            else:
                continue
        elif field_type not in util.getPrimitives():
            found_paths = findEnumFieldPaths(find_enum, field["name"], field_type, data, enums)
            for found in found_paths:
                entry = found.copy()
                # entry.insert(0, field["name"])
                enum_fields.append(entry)

    retVal = []
    for enum_entry in enum_fields:
        entry = enum_entry.copy()
        entry.insert(0, data_name)
        retVal.append(entry)
    return retVal


def getSpecRequiredFields(spec_model, name):
    return util.search(spec_model, [name, "data", "required"])


def getSpecFieldNames(spec_model, name):
    retVal = []
    fields = util.search(spec_model, [name, "data", "fields"])
    for field in fields:
        retVal.append(field["name"])
    return retVal


def getSimpleBaseTypeName(type_declaration):
    if type_declaration.endswith("[]"):
        return True, type_declaration[0:-2]
    else:
        return False, type_declaration


def getModelObjectFields(spec_model, enum_spec, name):
    retVal = {}
    fields = util.search(spec_model, [name, "data", "fields"])
    for field in fields:
        isList, field_type_name = getSimpleBaseTypeName(field["type"])
        isEnum = field_type_name in enum_spec.keys()
        isPrimitive = field_type_name in util.getPrimitives()
        if not isEnum and not isPrimitive:
            retVal[field["name"]] = field["type"]

    return retVal


# def validate_model(model, data_spec, enum_spec):
#     # a model item has a key of 'model', and no other keys   TODO:  import is also a valid root...need to make sure this is handled correctly
#     if "model" not in model.keys():
#         return False, ["the root type for model must be 'model'"]

#     return validate_model_entry("model", "model", model["model"], data_spec, enum_spec)


def validate_model_entry(name, model_type, model, data_spec, enum_spec):
    """
    Validate an Architecture-as-Code model.  A model item is a root of the AaC approach.
    Unlike enum and data, the content and structure of a model is not "hard coded", but specified in the data definition of a model in the yaml file that models AaC itself.
    This was put in place to support extensibility and customization, but does create a bit of "inception" that can be difficult to reason about.

    :param model: The model to be validated.
    :param data_specs: The data definitions of the modelled system (including AaC base types).
    """

    # make sure the model fields are correct per the spec
    model_spec_fields = getSpecFieldNames(data_spec, model_type)
    model_spec_required_fields = getSpecRequiredFields(data_spec, model_type)
    model_fields = list(model.keys())

    # check that required fields are present
    for required_field in model_spec_required_fields:
        if required_field not in model_fields:
            return False, ["model {} is missing required field {}".format(name, required_field)]

    # check that model fields are recognized per the spec
    for model_field in model_fields:
        if model_field not in model_spec_fields:
            return False, ["model {} contains unrecognized field {}".format(name, model_field)]

    # look for any field that is not a primitive type and validate the contents
    object_fields = getModelObjectFields(data_spec, enum_spec, model_type)
    if len(object_fields) == 0:
        # there are only primitives, validation successful
        return True, [""]

    for field_name in object_fields:
        if field_name not in model.keys():
            # print("in model {} object field {} is not present but optional".format(name, field_name))
            continue
        field_type = object_fields[field_name]
        sub_model = model[field_name]
        isList, field_type_name = getSimpleBaseTypeName(field_type)
        if isList:
            if not sub_model:  # list is empty
                pass
            else:
                for sub_model_item in sub_model:
                    isValid, errMsg = validate_model_entry(
                        field_name, field_type_name, sub_model_item, data_spec, enum_spec
                    )
                    if not isValid:
                        return isValid, errMsg
        else:
            isValid, errMsg = validate_model_entry(
                field_name, field_type_name, sub_model, data_spec, enum_spec
            )
            if not isValid:
                return isValid, errMsg

    return True, [""]


# def validate_usecase(usecase, model_spec, data_spec, enum_spec):

#     foundInvalid = False
#     errMsgList = []

#     # a usecase item has a key of 'usecase', and no other keys   TODO:  import is also a valid root...need to make sure this is handled correctly
#     if "usecase" not in usecase.keys():
#         # nothing to validate so return immediately
#         return False, ["the root type for usecase must be 'usecase'"]

#     # validate against the aac spec
#     isValid, errMsg = validate_model_entry(
#         "usecase", "usecase", usecase["usecase"], data_spec, enum_spec
#     )
#     if not isValid:
#         foundInvalid = True
#         errMsgList = errMsgList + errMsg

#     use_case_title = usecase["usecase"]["title"]
#     # get a map of participant name to type
#     participant_map = {}
#     for participant in util.search(usecase, ["usecase", "participants"]):
#         participant_map[participant["name"]] = participant["type"]

#     # validate usecase participant types
#     participant_types = util.search(usecase, ["usecase", "participants", "type"])
#     for part_type in participant_types:
#         # the character ~ at the begenning of the type suppresses type validation
#         if (not part_type.startswith("~")) and (part_type not in model_spec):
#             foundInvalid = True
#             errMsgList.append(
#                 "usecase [{}] participant type [{}] is not defined".format(
#                     use_case_title, part_type
#                 )
#             )

#     # make sure source and target are known participants and the action exists on the target
#     participant_names = util.search(usecase, ["usecase", "participants", "name"])
#     steps = util.search(usecase, ["usecase", "steps"])
#     for step in steps:
#         source = step["source"]
#         target = step["target"]
#         action = step["action"]

#         if source not in participant_names:
#             foundInvalid = True
#             errMsgList.append(
#                 "Use Case [{}] validation error: source {} not found in participants {}".format(
#                     use_case_title, source, participant_names
#                 )
#             )

#         if target not in participant_names:
#             foundInvalid = True
#             errMsgList.append(
#                 "Use Case [{}] validation error: target {} not found in participants {}".format(
#                     use_case_title, target, participant_names
#                 )
#             )

#         # suppress action validation if target type starts with ~ character
#         if not participant_map[target].startswith("~"):
#             if action not in util.search(
#                 model_spec[participant_map[target]], ["model", "behavior", "name"]
#             ):
#                 foundInvalid = True
#                 errMsgList.append(
#                     "Use Case [{}] validation error: target {} does not define action {}".format(
#                         use_case_title, target, action
#                     )
#                 )

#     if not foundInvalid:
#         return True, [""]
#     else:
#         return False, errMsgList


# def validate_extension(extension, data_spec, enum_spec):

#     foundInvalid = False
#     errMsgList = []

#     # an extension item has a key of 'extension', and no other keys   TODO:  import is also a valid root...need to make sure this is handled correctly
#     if "extension" not in extension.keys():
#         # nothing to validate so return immediately
#         return False, ["the root type for extension must be 'extension'"]

#     # validate against the aac spec
#     isValid, errMsg = validate_model_entry(
#         "extension", "extension", extension["extension"], data_spec, enum_spec
#     )
#     if not isValid:
#         foundInvalid = True
#         errMsgList = errMsgList + errMsg

#     # make sure the extension is extending something that exists in the model
#     type_to_extend = extension["extension"]["type"]
#     if "enumExt" in extension["extension"]:
#         if type_to_extend not in enum_spec:
#             foundInvalid = True
#             errMsgList.append(
#                 "Enum Extension [{}] validation error:  cannot extend enum {} because it does not exist".format(
#                     extension["name"], type_to_extend
#                 )
#             )
#     else:
#         if type_to_extend not in data_spec:
#             foundInvalid = True
#             errMsgList.append(
#                 "Data Extension [{}] validation error:  cannot extend data {} because it does not exist".format(
#                     extension["name"], type_to_extend
#                 )
#             )

#     if not foundInvalid:
#         return True, [""]
#     else:
#         return False, errMsgList


def apply_extension(extension, data, enums):
    type_to_extend = extension["extension"]["type"]
    if "enumExt" in extension["extension"]:
        # apply the enum extension
        updated_values = (
            enums[type_to_extend]["enum"]["values"] + extension["extension"]["enumExt"]["add"]
        )
        enums[type_to_extend]["enum"]["values"] = updated_values
    else:
        # apply the data extension
        updated_fields = (
            data[type_to_extend]["data"]["fields"] + extension["extension"]["dataExt"]["add"]
        )
        data[type_to_extend]["data"]["fields"] = updated_fields

        if "required" in extension["extension"]["dataExt"]:
            updated_required = (
                data[type_to_extend]["data"]["required"] + extension["extension"]["dataExt"]["required"]
            )
            data[type_to_extend]["data"]["fields"] = updated_required