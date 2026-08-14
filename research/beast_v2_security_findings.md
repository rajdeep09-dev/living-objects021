# BEAST v2 Security Findings

## Generated Python must not be treated as trusted

Checkmarx’s March 26, 2025 analysis explains that Python’s object model can allow seemingly restricted in-process execution environments to be bypassed, including paths to remote code execution. The practical design consequence for BEAST v2 is that AST checks and restricted globals are useful pre-flight filters, but they are not a production security boundary by themselves.

Production execution of generated organism code should therefore use a separate sandbox boundary such as an isolated process, container, or stronger runtime with resource limits, no ambient credentials, restricted filesystem/network access, and explicit timeouts. The local implementation can provide deterministic validation and a safe fallback, but must label in-process execution as research mode.

Source: https://checkmarx.com/zero-post/glass-sandbox-complexity-of-python-sandboxing/
