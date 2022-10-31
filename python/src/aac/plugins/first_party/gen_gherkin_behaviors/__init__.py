"""Generated AaC Plugin hookimpls module for the aac-gen-gherkin-behaviors plugin."""
# WARNING - DO NOT EDIT - YOUR CHANGES WILL NOT BE PROTECTED
# This file is auto-generated by the aac gen-plugin and may be overwritten.

from aac.cli.aac_command import AacCommand, AacCommandArgument
from aac.plugins import hookimpl
from aac.plugins.first_party.gen_gherkin_behaviors.gen_gherkin_behaviors_impl import gen_gherkin_behaviors
from aac.plugins.plugin import Plugin
from aac.plugins._common import get_plugin_definitions_from_yaml


@hookimpl
def get_plugin() -> Plugin:
    """
    Returns information about the plugin.

    Returns:
        A collection of information about the plugin and what it contributes.
    """
    *_, plugin_name = __package__.split(".")
    plugin = Plugin(plugin_name)
    plugin.register_commands(_get_plugin_commands())
    plugin.register_definitions(_get_plugin_definitions())
    return plugin


def _get_plugin_commands() -> list[AacCommand]:
    gen_gherkin_behaviors_arguments = [
        AacCommandArgument(
            "architecture-file",
            "The yaml file containing the data models to generate as Gherkin feature files.",
            "file",
        ),
        AacCommandArgument(
            "output-directory",
            "The directory to write the generated Gherkin feature files to.",
            "directory",
        ),
    ]

    plugin_commands = [
        AacCommand(
            "gen-gherkin-behaviors",
            "Generate Gherkin feature files from Arch-as-Code model behavior scenarios.",
            gen_gherkin_behaviors,
            gen_gherkin_behaviors_arguments,
        ),
    ]

    return plugin_commands


def _get_plugin_definitions():
    return get_plugin_definitions_from_yaml(__package__, "gen_gherkin_behaviors.yaml")
