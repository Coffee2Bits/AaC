"""AaC Plugin implementation module for the start-lsp plugin."""
# NOTE: It is safe to edit this file.
# This file is only initially generated by the aac gen-plugin, and it won't be overwritten if the file already exists.

import aac.lang.lsp.server as lsp_server
from aac.plugins.plugin_execution import PluginExecutionResult, plugin_result

plugin_name = "start-lsp"


def start_lsp() -> PluginExecutionResult:
    """Start the IO LSP server."""
    with plugin_result(plugin_name, lsp_server.start_lsp) as result:
        result.messages = [m for m in result.messages if m]
        return result