# Code signing policy

Windows releases of Roodof are built from this repository by the
[Windows build workflow](.github/workflows/windows-build.yml) and are planned to be signed through
SignPath. Free code signing provided by [SignPath.io](https://about.signpath.io/), certificate by
[SignPath Foundation](https://signpath.org/) (application in progress; current releases are unsigned).

## Team roles

- Committers and reviewers: [repository owner](https://github.com/roodof)
- Approvers: [repository owner](https://github.com/roodof)

Every signing request is approved manually. Only artifacts built by the workflow from this
repository are submitted for signing.

## Privacy policy

Roodof reads Claude Code and Codex logs on your own computer and does not send agent data to
any networked system. On Windows, optional update checks contact roodof.com to read the signed
release feed and download the package; they send no agent records. Nothing else is transferred
unless you explicitly request it.
