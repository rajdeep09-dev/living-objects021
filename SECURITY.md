# Security Policy

Report vulnerabilities privately to the repository maintainer rather than opening a public issue with an exploit. Include the affected file, reproduction steps, impact, and a proposed mitigation if available.

The project is research software. The in-process Python sandbox is not a complete production isolation boundary. Use a hardened container or microVM with no network, read-only root filesystem, dropped capabilities, seccomp/AppArmor, cgroups, credential isolation, and independent artifact validation for hostile workloads.
