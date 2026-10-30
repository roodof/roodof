"""Invented Claude Code transcripts and Codex rollouts shaped like real ones (long texts, patches, commands,
tool output, usage rows) for the speed guard. Deterministic; nothing here comes from a real log."""
import json
import random
import time

WORDS = ('cart', 'total', 'invented', 'shop', 'discount', 'payment', 'return', 'value', 'line', 'check', 'ğüşıöç',
         'quote"d', 'tab\there', 'slash\\path', 'new\nline', 'emoji✓', 'number', '1234', 'test', 'build')
USAGE = dict(input_tokens=12, cache_read_input_tokens=48000, cache_creation_input_tokens=900, output_tokens=420,
             cache_creation=dict(ephemeral_1h_input_tokens=900, ephemeral_5m_input_tokens=0))


def best(function, runs=3):
    """The shortest of `runs` wall-clock timings: the least disturbed by other work on the machine."""
    times = []
    for _ in range(runs):
        started = time.perf_counter()
        function()
        times.append(time.perf_counter() - started)
    return min(times)


def _text(rng, size):
    words, length = [], 0
    while length < size:
        word = rng.choice(WORDS)
        words.append(word)
        length += len(word) + 1
    return ' '.join(words)


def _line(row):
    return (json.dumps(row) + '\n').encode('utf-8')


def claude_lines(turns, session='invented-session', seed=7):
    rng, lines = random.Random(seed), []
    for turn in range(turns):
        at = '2026-10-30T%02d:%02d:%02d.000Z' % (turn // 3600 % 24, turn // 60 % 60, turn % 60)
        base = dict(sessionId=session, timestamp=at, cwd='/work/shop', gitBranch='main', version='2.1.300')
        lines.append(_line(dict(base, type='user', uuid='u-%d' % turn,
                                message=dict(role='user', content=_text(rng, rng.randint(200, 3000))))))
        message = dict(id='m-%d' % turn, model='claude-opus-5-5', role='assistant', usage=USAGE)
        blocks = [dict(type='text', text=_text(rng, rng.randint(300, 2000)))]
        if turn % 3 == 0:
            command = 'python -m pytest -q' if turn % 2 else "cat > notes.txt <<'EOF'\n" + _text(rng, 3000) + '\nEOF'
            blocks.append(dict(type='tool_use', id='t-%d' % turn, name='Bash', input=dict(command=command)))
        elif turn % 3 == 1:
            blocks.append(dict(type='tool_use', id='t-%d' % turn, name='Edit', input=dict(
                file_path='/work/shop/src/cart_%d.py' % (turn % 40), old_string=_text(rng, 1500),
                new_string=_text(rng, 1800))))
        for block in blocks:
            lines.append(_line(dict(base, type='assistant', requestId='r-%d' % turn, message=dict(message, content=[block]))))
        if len(blocks) > 1:
            lines.append(_line(dict(base, type='user', uuid='a-%d' % turn, message=dict(role='user', content=[dict(
                type='tool_result', tool_use_id='t-%d' % turn, is_error=turn % 7 == 0,
                content=_text(rng, rng.randint(1000, 20000)))]))))
    return lines


def codex_lines(turns, session='invented-rollout', seed=11):
    rng = random.Random(seed)
    lines = [_line(dict(timestamp='2026-10-30T00:00:00.000Z', type='session_meta',
                        payload=dict(id=session, cwd='/work/engine', cli_version='0.163.0')))]
    total = 0
    for turn in range(turns):
        at = '2026-10-30T%02d:%02d:%02d.500Z' % (turn // 3600 % 24, turn // 60 % 60, turn % 60)
        def add(kind, payload):
            lines.append(_line(dict(timestamp=at, type=kind, payload=payload)))
        if turn % 10 == 0:
            add('turn_context', dict(model='gpt-6.1-sol', effort='high', cwd='/work/engine'))
            add('response_item', dict(type='message', role='user', content=[dict(type='input_text', text=_text(rng, 2000))]))
        add('response_item', dict(type='reasoning', encrypted_content=''.join(rng.choice('ABCDEFabcdef0123456789+/')
                                                                             for _ in range(rng.randint(2000, 6000)))))
        if turn % 2:
            patch = '*** Begin Patch\n*** Update File: src/engine_%d.rs\n@@\n-%s\n+%s\n*** End Patch' % (
                turn % 30, _text(rng, 1500), _text(rng, 1700))
            add('response_item', dict(type='custom_tool_call', name='apply_patch', call_id='c-%d' % turn, input=patch))
        else:
            add('response_item', dict(type='function_call', name='shell', call_id='c-%d' % turn,
                                      arguments=json.dumps(dict(command=['bash', '-lc', 'cargo test --quiet']))))
            add('event_msg', dict(type='item_completed', item=dict(type='CommandExecution', id='i-%d' % turn,
                                  command=['bash', '-lc', 'cargo test --quiet'], exit_code=turn % 4,
                                  aggregated_output=_text(rng, rng.randint(1000, 15000)))))
        add('response_item', dict(type='function_call_output', call_id='c-%d' % turn, output=_text(rng, rng.randint(500, 8000))))
        usage = dict(input_tokens=60000 + turn, cached_input_tokens=58000, output_tokens=300, reasoning_output_tokens=120)
        total += 60300 + turn
        add('token_usage_record', dict(response_id='resp-%d' % turn, usage=usage))
        add('event_msg', dict(type='token_count', info=dict(total_token_usage=dict(usage, input_tokens=total)),
                              rate_limits=dict(primary=dict(used_percent=turn % 100, window_minutes=300, resets_at=1790000000),
                                               plan_type='pro')))
    return lines
