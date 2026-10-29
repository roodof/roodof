"""Count contributing local source groups, without inferring account identity.

Only paths already selected/discovered by the log reader are considered. No
filesystem queries or provider identifiers are needed, stored or published.
"""
import ntpath
import posixpath
import re


def _namespace(agent,root):
    value=str(root).replace('\\','/').rstrip('/')
    if re.match(r'^[A-Za-z]:/',value):
        value=ntpath.normpath(value).replace('\\','/').casefold()
    else:
        value=posixpath.normpath(value)
        if value.startswith('//'):
            parts=value.split('/')
            if len(parts)>3 and parts[2].casefold() in ('wsl$','wsl.localhost'):
                parts[2]='wsl.localhost';parts[3]=parts[3].casefold()
                value='/'.join(parts)
    parent,name=value.rsplit('/',1) if '/' in value else ('',value)
    conventional=('sessions','archived_sessions') if agent=='codex' else ('projects',)
    return parent or '/' if name in conventional else value


def source_groups(claude_manifest,codex_manifest,claude_paths,codex_paths):
    result={}
    for agent,manifest,paths in (('claude-code',claude_manifest,claude_paths),('codex',codex_manifest,codex_paths)):
        groups=set()
        for path in paths:
            root=manifest.scope(path)
            if root is not None: groups.add(_namespace(agent,root))
        result[agent]=len(groups)
    return result
