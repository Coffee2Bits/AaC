import os
from tempfile import TemporaryDirectory
from unittest import TestCase

from aac import util, validator, parser
from aac.genplug import (
    _compile_templates,
    _convert_template_name_to_file_name,
    _write_generated_templates_to_file,
    TemplateOutputFile,
    GeneratePluginException,
)


class TestGenPlug(TestCase):
    def setUp(self):
        util.AAC_MODEL = {}
        validator.DEFINED_TYPES = []

    def test_convert_template_name_to_file_name(self):
        plugin_name = "aac-test"
        template_names = ["__init__.py.jinja2", "plugin.py.jinja2", "plugin_impl.py.jinja2"]
        expected_filenames = ["__init__.py", f"{plugin_name}.py", f"{plugin_name}_impl.py"]

        for i in range(len(template_names)):
            expected_filename = expected_filenames[i]
            actual_filename = _convert_template_name_to_file_name(template_names[i], plugin_name)
            self.assertEqual(expected_filename, actual_filename)

    def test_compile_templates(self):
        parsed_model = parser.parse_str(TEST_PLUGIN_YAML_STRING, "")
        plugin_name = "aac_spec"

        generated_templates = _compile_templates(parsed_model)

        generated_template_names = []
        for generated_template in generated_templates:
            generated_template_names.append(generated_template.file_name)

        # Check that the files don't have "-" in the name
        for name in generated_template_names:
            self.assertNotIn("-", name)

        # Check that the expected files were created and named correctly
        self.assertEqual(len(generated_template_names), 4)

        self.assertIn("__init__.py", generated_template_names)
        self.assertIn("setup.py", generated_template_names)
        self.assertIn(f"{plugin_name}.py", generated_template_names)
        self.assertIn(f"{plugin_name}_impl.py", generated_template_names)

    def test__compile_templates_errors_on_multiple_models(self):
        parsed_model = parser.parse_str(
            f"{TEST_PLUGIN_YAML_STRING}\n---\n{SECONDARY_MODEL_YAML_DEFINITION}", "", True
        )

        self.assertRaises(GeneratePluginException, _compile_templates, parsed_model)

    def test__compile_templates_with_model_name_missing_package_prefix(self):
        parsed_model = parser.parse_str(MODEL_YAML_DEFINITION_SANS_PACKAGE_PREFIX, "", False)
        plugin_name = "aac_spec"

        generated_templates = _compile_templates(parsed_model)

        generated_template_names = []
        for generated_template in generated_templates:
            generated_template_names.append(generated_template.file_name)

        # Check that the files don't have "-" in the name
        for name in generated_template_names:
            self.assertNotIn("-", name)

        # Check that the expected files were created and named correctly
        self.assertEqual(len(generated_template_names), 4)

        self.assertIn("__init__.py", generated_template_names)
        self.assertIn("setup.py", generated_template_names)
        self.assertIn(f"{plugin_name}.py", generated_template_names)
        self.assertIn(f"{plugin_name}_impl.py", generated_template_names)

    def test__write_generated_templates_to_file(self):
        template_name = "myTemplate.test"
        template_content = "This is the sample content in my template"
        templates = [TemplateOutputFile(template_name, template_content, True)]

        with TemporaryDirectory() as temp_directory:
            _write_generated_templates_to_file(templates, temp_directory)
            temp_directory_files = os.listdir(temp_directory)

            for template in templates:
                self.assertEqual(len(templates), len(temp_directory_files))
                self.assertIn(template.file_name, temp_directory_files)

                with open(os.path.join(temp_directory, template.file_name)) as file:
                    self.assertEqual(template.content, file.read())


TEST_PLUGIN_YAML_STRING = """
data:
  name: Specification
  fields:
    - name: name
      type: string
    - name: description
      type: string
    - name: subspecs
      type: string[]
    - name: sections
      type: SpecSection[]
    - name: requirements
      type: Requirement[]
  required:
    - name
---
data:
  name: SpecSection
  fields:
    - name: name
      type: string
    - name: description
      type: string
    - name: requirements
      type: Requirement[]
  required:
    - name
---
data:
  name: Requirement
  fields:
    - name: id
      type: string
    - name: shall
      type: string
    - name: parent
      type: string
    - name: attributes
      type: RequirementAttribute[]
  required:
    - id
    - shall
---
data:
  name: RequirementAttribute
  fields:
    - name: name
      type: string
    - name: value
      type: string
  required:
    - name
    - value
---
ext:
  name: addSpecificationToRoot
  type: root
  dataExt:
    add:
      - name: spec
        type: Specification
---
ext:
   name: CommandBehaviorType
   type: BehaviorType
   enumExt:
      add:
         - command
---
model:
  name: aac-spec
  description: aac-spec is a Architecture-as-Code plugin that enables requirement definition and trace in Arch-as-Code models.
  behavior:
    - name: spec-validate
      type: command
      description: 'Validates spec traces within the AaC model'
      input:
        - name: archFile
          type: file
        - name: parsed_model
          type: map
      acceptance:
        - scenario: Valid spec traces are modeled.
          given:
            - The {{spec-validate.input.archFile}} contains a valid architecture specification.
            - The {{spec-validate.input.parsed_model}} contains the parsed content from archFile.
          when:
            - The aac app is run with the spec-validate command.
          then:
            - A message saying spec validation was successful is printed to the console.
    - name: non-cmd-behavior
      type: startup
      description: You shouldn't see me
      acceptance:
        - scenario: Pretend to do something on startup.
          when:
          - when
          then:
          - then
"""

SECONDARY_MODEL_YAML_DEFINITION = """
model:
  name: aac-spec-secondary
  description: aac-spec-secondary is a Architecture-as-Code plugin that enables requirement definition and trace in Arch-as-Code models.
  behavior:
    - name: spec-validate-2
      type: command
      description: 'Validates spec traces within the AaC model'
      input:
        - name: archFile
          type: file
        - name: parsed_model
          type: map
      acceptance:
        - scenario: Valid spec traces are modeled.
          given:
            - The {{spec-validate.input.archFile}} contains a valid architecture specification.
            - The {{spec-validate.input.parsed_model}} contains the parsed content from archFile.
          when:
            - The aac app is run with the spec-validate command.
          then:
            - A message saying spec validation was successful is printed to the console.
    - name: non-cmd-behavior-2
      type: startup
      description: You shouldn't see me
      acceptance:
        - scenario: Pretend to do something on startup.
          when:
          - when
          then:
          - then
"""


MODEL_YAML_DEFINITION_SANS_PACKAGE_PREFIX = """
model:
  name: spec
  description: An Architecture-as-Code plugin that enables requirement definition and trace in Arch-as-Code models.
  behavior:
    - name: spec-validate
      type: command
      description: 'Validates spec traces within the AaC model'
      input:
        - name: archFile
          type: file
        - name: parsed_model
          type: map
      acceptance:
        - scenario: Valid spec traces are modeled.
          given:
            - The {{spec-validate.input.archFile}} contains a valid architecture specification.
            - The {{spec-validate.input.parsed_model}} contains the parsed content from archFile.
          when:
            - The aac app is run with the spec-validate command.
          then:
            - A message saying spec validation was successful is printed to the console.
    - name: non-cmd-behavior-2
      type: startup
      description: You shouldn't see me
      acceptance:
        - scenario: Pretend to do something on startup.
          when:
          - when
          then:
          - then

"""