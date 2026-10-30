"""Explicit local backup commands. No scan, model call or provider/account query.

The core validates each complete bundle before saving or publishing a restored
folder. This interface prints only a fixed public summary, including on failure.
"""
import argparse
import json
import sys

from .i18n import language, say


class _Arguments(ValueError):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        # argparse's default message can copy an arbitrary file path into JSON
        # callers' logs. Human help still describes every accepted option.
        raise _Arguments()


def _failure(code, lang, as_json):
    codes = {'arguments', 'invalid', 'unsupported', 'limit', 'unsafe_path', 'exists', 'io', 'busy'}
    code = code if code in codes else 'io'
    if as_json:
        print(json.dumps(dict(ok=False, code=code)))
    else:
        print(say(lang, 'backup.error.' + code), file=sys.stderr)
    return 2 if code == 'arguments' else 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    lang = language()
    as_json = '--json' in argv
    parser = _Parser(prog='pler backup', description=say(lang, 'backup.help'),
                     epilog=say(lang, 'backup.privacy'), allow_abbrev=False)
    parser.add_argument('action', choices=('create', 'check', 'restore'), help=say(lang, 'backup.action_help'))
    parser.add_argument('file', help=say(lang, 'backup.file_help'))
    parser.add_argument('--to', metavar='FOLDER', help=say(lang, 'backup.to_help'))
    parser.add_argument('--json', action='store_true', help=say(lang, 'backup.json_help'))
    try:
        args = parser.parse_args(argv)
        if (args.action == 'restore') != (args.to is not None):
            raise _Arguments()
    except _Arguments:
        return _failure('arguments', lang, as_json)

    from .usage import backup
    try:
        if args.action == 'create':
            value = backup.write_file(backup.create(), args.file)
        else:
            data = backup.read_file(args.file)
            value = backup.inspect(data) if args.action == 'check' else backup.restore(data, args.to)
    except backup.BackupError as error:
        return _failure(error.code, lang, args.json)
    except (OSError, ValueError, OverflowError, MemoryError):
        return _failure('io', lang, args.json)

    # A future core may carry diagnostics privately; only these documented
    # version/count fields belong in a command's public output.
    names = ('format', 'version', 'parser_version', 'schema_version', 'created_at',
             'archive_files', 'verdicts', 'quota_samples', 'retention_enabled', 'files', 'bytes')
    public = {name: value[name] for name in names if name in value}
    if args.json:
        print(json.dumps(dict(ok=True, action=args.action, **public)))
    else:
        print(say(lang, 'backup.' + args.action + '_done', **public))
        print(say(lang, 'backup.restore_open' if args.action == 'restore' else 'backup.privacy'))
    return 0
