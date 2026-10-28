"""The words PLER says, in English and Turkish, and the number formats of each.

A language is 'en' or 'tr'. The page picks its own from the browser and sends it with every request; the
terminal uses PLER_LANG when set, otherwise Turkish for a Turkish system locale and English for any other.
To add a language, add its table below: a missing entry falls back to English.
"""
import locale
import os

LANGUAGES = ('en', 'tr')

TEXT = {
    'en': {
        # agents and windows
        'window.300': '5-hour', 'window.10080': 'weekly', 'window.other': '{0}-minute',
        'unknown': 'unknown', 'unknown_project': 'unknown project',
        'temp_folders': 'Temporary folders', 'home_folder': 'Home folder (no project)',
        # numbers
        'big.9': 'billion', 'big.6': 'million', 'big.3': 'thousand',
        # page data
        'note.older_codex': 'Older log: only the session total is recorded; the per-call split is unknown.',
        'note.routing_alias': 'The model name is a routing label; the actual model is not logged.',
        'unreadable_file': 'File not fully read',
        'malformed_file': 'Malformed or incomplete log rows',
        'inconsistent_reasoning_file': 'A zeroed usage copy has no matching verified reply snapshot; its usage is unknown',
        'privacy': 'Numbers and session metadata only. Prompts, replies, commands and tool output are never shown.',
        'quality.header': 'Coverage and attribution limits:',
        'quality.invalid_records': 'Some records are invalid or unreadable. Only verified usage is included; the total may be incomplete.',
        'quality.reconciled_copies': 'Some repeated copies have zeroed usage counters. A matching verified snapshot of the same reply supplies the counts; each reply is counted once.',
        'quality.conflicting_usage': 'Conflicting response snapshots could not be reconciled; their usage is excluded from the known total.',
        'quality.unreconciled_totals': 'Some cumulative, inherited or compacted history could not be reconciled. Counts may overlap or be incomplete; they are not a complete account total.',
        'quality.shared_attribution': 'Session or project ownership is uncertain. Conflicting project information is shown as unknown.',
        'quality.unknown_model': 'Some usage has no verified model attribution.',
        'quality.cumulative_usage': 'Cumulative usage is included, but its call and model split is unknown.',
        'quality.unidentified_records': 'Some events lack stable identities; their counts cannot be verified across copied history.',
        'scope': 'The period selects sessions by their last activity. Tokens cover those whole sessions; this is not daily spending.',
        'error.period': 'The period must be 7, 30 or 90 days, or all sessions.',
        'error.agent': 'Choose Claude Code, Codex or all agents.',
        'error.unknown_project': 'The selected project is no longer in the logs. Choose a project from the list.',
        'error.scan': 'The logs could not be read. Check that the agent log folders are accessible and try again.',
        'error.query': 'Choose one period, agent and project.',
        'error.bad_period': 'Choose a valid period.',
        'error.no_snapshot': 'Read the local logs first.',
        'error.not_found': 'Not found.',
        'error.no_action': 'No such action.',
        'error.not_local': 'This request does not come from the local page.',
        'error.token': 'The page session could not be verified. Reload the page.',
        'error.read_token': 'Open the address shown when PLER starts to connect to this report.',
        'error.bad_request': 'Invalid request.',
        'error.fields': 'The request must not carry a folder, command or any other field.',
        'export_file': 'pler-usage-summary.json',
        # observations
        'insight.quota_name': '{agent} {window} quota',
        'insight.full.title': 'Last sample: {name} is full',
        'insight.full.detail': 'It was 100% full at the last record ({at}); it resets {resets}.',
        'insight.pace.hour': 'at this window\'s pace ({rate}% an hour)',
        'insight.pace.day': 'at the average of the last {days} days ({rate}% a day)',
        'insight.fills.title': '{name} may fill before it resets',
        'insight.fills.detail': '{used}% used at the last record. {pace} it fills around {full}; it resets {resets}.',
        'insight.long.title': 'Logged token use differs by session length',
        'insight.long.detail': ('{agent}: in sessions with {long} or more calls, a model call used a median of {long_tokens} tokens; '
                                'in sessions under {short} calls, {short_tokens} ({ratio}x). Tasks, models and settings were not '
                                'held constant. This observation does not establish waste or savings from a new session.'),
        'insight.calls_unknown': 'call count unknown',
        'insight.concentration.title': 'Usage is concentrated in one session',
        'insight.concentration.detail': ('{share}% of the tokens in this selection are in a single {agent} session ({tokens} tokens, '
                                         '{calls}). That session is a good place to start looking at where usage builds up.'),
        'insight.limits.title': 'Claude Code hit its quota limit',
        'insight.limits.detail': ('Refused at the limit in this period: {count}; the last one {last}. With the PLER status line '
                                  'on (pler statusline --install), the page also shows when the quota fills.'),
        'insight.interrupted.title': 'Interrupted turns',
        'insight.interrupted.detail': ('{agent}: {errors} and {aborted} were recorded alongside {requests}. '
                                       'These are event counts; one request can have multiple events. They do not measure wasted work.'),
        # terminal report
        'report.period': 'Sessions active in the last {0} days', 'report.all': 'All records',
        'report.header': ' · from the agent logs on this computer · no model calls, nothing sent',
        'report.total': 'Total: {tokens} tokens · {sessions} · {calls} · {prompts}',
        'report.cache': '  {share} of it is context read again from the cache; outside the cache: {tokens} tokens',
        'report.agent': '  {agent:<12} {tokens:<13} tokens · {sessions} · {share} of input from cache · {errors} · {aborted}',
        'report.notes': 'Highlights:',
        'report.models': 'Models:',
        'report.model': '  {agent:<12} {model:<20} {tokens:<13} tokens · {calls}',
        'report.projects': 'Projects using the most:',
        'report.project': '  {tokens:<13} tokens · {sessions} · {project}',
        'report.largest': 'Largest sessions:',
        'report.session': '  {tokens:<13} tokens · {agent} · {date} · {project}',
        'report.burn_item': '{times}x the {window} quota',
        'report.burn': '                 the account used in this time: ',
        'report.codex_quota': 'Codex quota{plan}, last record {at}:',
        'report.plan': ' (plan: {0})',
        'report.quota_line': '  {window} quota: {used}% used',
        'report.claude_quota': 'Claude Code quota (from the PLER status line), last record {at}:',
        'report.reset': '  {window} quota: reset',
        'report.stale': '  {window} quota: last sample {used}% used; current level unknown (old data)',
        'report.limit_hits': 'Claude Code hit its quota limit {0}.',
        'report.statusline_hint': 'Claude Code does not log its quota percentage. To see it, run once: pler statusline --install',
        'report.read': 'Read: {claude}, {codex}.',
        'report.unreadable': 'Not fully read: {count} ({reasons}). Verified records are included; totals may be incomplete.',
        # command line
        'cli.open': 'PLER is open: {0}  (stop with Ctrl+C or the page\'s "Close" button)',
        'cli.closed': 'PLER closed.',
        'cli.epilog': 'Terminal summary: pler report --help',
        'cli.port': 'Port of the local page (default {0})',
        'cli.no_browser': 'Do not open the browser; only print the address',
        # status line
        'status.context': 'ctx {0}%', 'status.300': '5h {0}%', 'status.10080': 'week {0}%',
        'status.unreadable': '{0} could not be read or is not a JSON object; the file was not touched.',
        'status.other': 'Claude Code already has a status line; it was not replaced:\n  {0}',
        'status.pipe': 'Your own script can pass Claude Code\'s input to PLER too, for example:\n  echo "$input" | {0}',
        'status.installed': 'Already installed: {0}',
        'status.plan': 'This setting will be added to {path}:\n{setting}',
        'status.explain': ('Claude Code runs it on every status refresh. PLER writes only the quota percentages and reset times\n'
                           'to its own cache folder; no conversation, folder or session information is kept. Undo: pler statusline --remove'),
        'status.ask': 'Add it? [y/N] ',
        'status.unchanged': 'Nothing changed.',
        'status.added': 'Added. After restarting Claude Code, its status line shows context and quota; PLER reads the quota from there.',
        'status.unreadable_short': '{0} could not be read; the file was not touched.',
        'status.not_installed': 'No unmodified status line from this PLER installation was found; nothing changed.',
        'status.removed': 'The PLER status line was removed: {0}',
        'status.changed': 'Claude Code settings changed while this operation was pending. Nothing was overwritten; try again.',
        'status.write_failed': 'The settings could not be saved. Check the folder permissions and try again.',
    },
    'tr': {
        'window.300': '5 saatlik', 'window.10080': 'haftalık', 'window.other': '{0} dakikalık',
        'unknown': 'bilinmiyor', 'unknown_project': 'proje bilinmiyor',
        'temp_folders': 'Geçici klasörler', 'home_folder': 'Ev klasörü (proje dışı)',
        'big.9': 'milyar', 'big.6': 'milyon', 'big.3': 'bin',
        'note.older_codex': 'Eski kayıt: birikimli oturum toplamı var; çağrı başına ayrım bilinmiyor.',
        'note.routing_alias': 'Model adı bir yönlendirme etiketi; gerçek model kimliği kayıtta yok.',
        'unreadable_file': 'Dosya tamamen okunamadı',
        'malformed_file': 'Bozuk veya yarım kayıt satırları',
        'inconsistent_reasoning_file': 'Sıfırlanmış kullanım kopyasının eşleşen sağlam yanıt kaydı yok; kullanımı bilinmiyor',
        'privacy': 'Yalnız sayılar ve oturum üstbilgileri. İstek, yanıt, komut ve araç çıktısı gösterilmez.',
        'quality.header': 'Kapsam ve atıf sınırları:',
        'quality.invalid_records': 'Bazı kayıtlar geçersiz veya okunamıyor. Yalnız doğrulanabilen kullanım dahil; toplam eksik olabilir.',
        'quality.reconciled_copies': 'Bazı tekrarlanan kopyaların kullanım sayaçları sıfırlanmış. Sayılar aynı yanıtın eşleşen sağlam kaydından alındı; her yanıt bir kez sayılıyor.',
        'quality.conflicting_usage': 'Çelişen yanıt ölçümleri uzlaştırılamadı; kullanımları bilinen toplamın dışında bırakıldı.',
        'quality.unreconciled_totals': 'Birikimli, devralınan veya özetlenen geçmişin bir bölümü uzlaştırılamadı. Sayılar örtüşebilir veya eksik olabilir; hesabın eksiksiz toplamı değildir.',
        'quality.shared_attribution': 'Oturum veya proje atfı kesin değil. Çelişen proje bilgisi bilinmiyor gösterilir.',
        'quality.unknown_model': 'Kullanımın bir bölümünün model atfı doğrulanamıyor.',
        'quality.cumulative_usage': 'Birikimli kullanım dahil; çağrı ve model dağılımı bilinmiyor.',
        'quality.unidentified_records': 'Bazı olayların sabit kimliği yok; kopya geçmişte sayıları doğrulanamıyor.',
        'scope': 'Dönem, son etkinliğe göre oturum seçer. Tokenlar seçilen oturumların tümünü kapsar; günlük harcama hesabı değildir.',
        'error.period': 'Dönem 7, 30, 90 gün veya tüm oturumlar olmalı.',
        'error.agent': 'Claude Code, Codex veya tüm ajanları seçin.',
        'error.unknown_project': 'Seçilen proje artık kayıtlarda bulunmuyor. Listeden bir proje seçin.',
        'error.scan': 'Kayıtlar okunamadı. Ajan kayıt klasörlerinin erişilebilir olduğunu kontrol edip yeniden deneyin.',
        'error.query': 'Tek dönem, ajan ve proje seçin.',
        'error.bad_period': 'Geçerli bir dönem seçin.',
        'error.no_snapshot': 'Önce yerel kayıtları okuyun.',
        'error.not_found': 'Bulunamadı.',
        'error.no_action': 'İşlem bulunamadı.',
        'error.not_local': 'Bu istek yerel uygulamadan gelmiyor.',
        'error.token': 'Oturum doğrulanamadı. Sayfayı yenileyin.',
        'error.read_token': 'Bu rapora bağlanmak için PLER açılırken gösterilen adresi açın.',
        'error.bad_request': 'Geçersiz istek.',
        'error.fields': 'İstek klasör, komut veya başka bir alan içermemeli.',
        'export_file': 'pler-kullanim-ozeti.json',
        'insight.quota_name': '{agent} {window} kotası',
        'insight.full.title': 'Son kayda göre {name} dolu',
        'insight.full.detail': 'Son kayıtta ({at}) %100 doluydu; {resets} sıfırlanıyor.',
        'insight.pace.hour': 'bu penceredeki çalışma hızıyla (saatte %{rate})',
        'insight.pace.day': 'son {days} günün ortalamasıyla (günde %{rate})',
        'insight.fills.title': '{name} sıfırlanmadan dolabilir',
        'insight.fills.detail': 'Son kayıtta %{used} dolu. {pace} {full} civarı dolar; sıfırlanma {resets}.',
        'insight.long.title': 'Kayıtlı token kullanımı oturum uzunluğuna göre değişiyor',
        'insight.long.detail': ('{agent}: {long} ve daha fazla çağrılı oturumlarda bir model çağrısı ortanca {long_tokens} token '
                                'kullandı; {short} çağrıdan kısa oturumlarda {short_tokens} ({ratio} kat). İşler, modeller ve ayarlar '
                                'sabit tutulmadı. Bu gözlem israfı veya yeni oturum açmanın tasarruf sağlayacağını kanıtlamaz.'),
        'insight.calls_unknown': 'çağrı sayısı bilinmiyor',
        'insight.concentration.title': 'Kullanım tek bir oturumda yoğunlaşıyor',
        'insight.concentration.detail': ('Bu seçimdeki tokenların %{share} kadarı tek bir {agent} oturumunda ({tokens} token, {calls}). '
                                         'Bu oturum, kullanımın nerede biriktiğini incelemek için bir başlangıç.'),
        'insight.limits.title': 'Claude Code kota sınırına takıldı',
        'insight.limits.detail': ('Bu dönemde sınırda geri çevrilen: {count}; sonuncusu {last}. PLER durum satırı açıksa '
                                  '(pler statusline --install) kotanın ne zaman dolacağı da gösterilir.'),
        'insight.interrupted.title': 'Yarıda kalan turlar',
        'insight.interrupted.detail': ('{agent}: {requests} yanında {errors} ve {aborted} kaydedildi. '
                                       'Bunlar olay sayılarıdır; bir istekte birden çok olay olabilir. Boşa giden işi ölçmez.'),
        'report.period': 'Son {0} günde etkin oturumlar', 'report.all': 'Bütün kayıtlar',
        'report.header': ' · bilgisayardaki ajan kayıtlarından · model çağrısı yok, dışarı veri gönderilmedi',
        'report.total': 'Toplam: {tokens} token · {sessions} · {calls} · {prompts}',
        'report.cache': '  bunun {share} kadarı önbellekten yeniden okunan bağlam; önbellek dışı: {tokens} token',
        'report.agent': '  {agent:<12} {tokens:<13} token · {sessions} · girdinin {share} kadarı önbellekten · {errors} · {aborted}',
        'report.notes': 'Öne çıkanlar:',
        'report.models': 'Modeller:',
        'report.model': '  {agent:<12} {model:<20} {tokens:<13} token · {calls}',
        'report.projects': 'En çok harcayan projeler:',
        'report.project': '  {tokens:<13} token · {sessions} · {project}',
        'report.largest': 'En büyük oturumlar:',
        'report.session': '  {tokens:<13} token · {agent} · {date} · {project}',
        'report.burn_item': '{window} kotanın {times} katı',
        'report.burn': '                 bu sürede hesabın harcadığı: ',
        'report.codex_quota': 'Codex kotası{plan}, son kayıt {at}:',
        'report.plan': ' (plan: {0})',
        'report.quota_line': '  {window} kota: %{used} dolu',
        'report.claude_quota': 'Claude Code kotası (PLER durum satırından), son kayıt {at}:',
        'report.reset': '  {window} kota: sıfırlandı',
        'report.stale': '  {window} kota: son ölçüm %{used}; güncel doluluk bilinmiyor (eski veri)',
        'report.limit_hits': 'Claude Code kota sınırına {0} takıldı.',
        'report.statusline_hint': 'Claude Code kota yüzdesini kaydetmez. Görmek için bir kez: pler statusline --install',
        'report.read': 'Okunan: {claude}, {codex}.',
        'report.unreadable': 'Tam okunamayan: {count} ({reasons}). Doğrulanabilen kayıtlar dahil; toplamlar eksik olabilir.',
        'cli.open': 'PLER açık: {0}  (kapatmak için Ctrl+C veya sayfadaki "Kapat")',
        'cli.closed': 'PLER kapandı.',
        'cli.epilog': 'Komut satırı özeti: pler report --help',
        'cli.port': 'Yerel sayfanın portu (varsayılan {0})',
        'cli.no_browser': 'Tarayıcıyı açma; yalnız adresi yaz',
        'status.context': 'bağlam %{0}', 'status.300': '5 saat %{0}', 'status.10080': 'hafta %{0}',
        'status.unreadable': '{0} okunamadı ya da geçerli bir JSON nesnesi değil; dosyaya dokunulmadı.',
        'status.other': 'Claude Code\'da zaten bir durum satırı var; üzerine yazılmadı:\n  {0}',
        'status.pipe': 'Kendi betiğin Claude Code\'un girdisini PLER\'e de verebilir, örneğin:\n  echo "$input" | {0}',
        'status.installed': 'Zaten kurulu: {0}',
        'status.plan': '{path} dosyasına şu ayar eklenecek:\n{setting}',
        'status.explain': ('Claude Code bunu her durum yenilemesinde çalıştırır. PLER yalnız kota yüzdelerini ve sıfırlanma zamanlarını\n'
                           'kendi önbellek klasörüne yazar; konuşma, klasör ve oturum bilgisi saklanmaz. Geri almak: pler statusline --remove'),
        'status.ask': 'Eklensin mi? [e/H] ',
        'status.unchanged': 'Değiştirilmedi.',
        'status.added': 'Eklendi. Claude Code\'u yeniden başlatınca durum satırında bağlam ve kota görünür; PLER kotayı oradan okur.',
        'status.unreadable_short': '{0} okunamadı; dosyaya dokunulmadı.',
        'status.not_installed': 'Bu PLER kurulumuna ait değiştirilmemiş durum satırı bulunamadı; değişiklik yapılmadı.',
        'status.removed': 'PLER durum satırı kaldırıldı: {0}',
        'status.changed': 'İşlem beklerken Claude Code ayarları değişti. Üzerine yazılmadı; yeniden dene.',
        'status.write_failed': 'Ayarlar kaydedilemedi. Klasörün yazma iznini kontrol edip yeniden dene.',
    },
}
YES = {'en': ('y', 'yes'), 'tr': ('e', 'evet', 'y', 'yes')}
NOUNS = {   # English: singular, plural; Turkish keeps one form after a number
    'en': {'session': ('session', 'sessions'), 'request': ('request', 'requests'), 'call': ('call', 'calls'),
           'model_call': ('model call', 'model calls'), 'error': ('error', 'errors'),
           'interrupted': ('interrupted', 'interrupted'), 'interrupted_turn': ('interrupted turn', 'interrupted turns'),
           'time': ('time', 'times'), 'claude_file': ('Claude Code file', 'Claude Code files'),
           'codex_file': ('Codex file', 'Codex files'), 'log_file': ('log file', 'log files')},
    'tr': {'session': 'oturum', 'request': 'istek', 'call': 'çağrı', 'model_call': 'model çağrısı', 'error': 'hata',
           'interrupted': 'yarıda kesilen', 'interrupted_turn': 'yarıda kesilen tur', 'time': 'kez',
           'claude_file': 'Claude Code dosyası', 'codex_file': 'Codex dosyası', 'log_file': 'kayıt dosyası'},
}


def language(environ=None):
    """PLER_LANG if set; else Turkish when the system locale or its code page is Turkish; else English."""
    environ = os.environ if environ is None else environ
    chosen = (environ.get('PLER_LANG') or '').strip().lower()[:2]
    if chosen in LANGUAGES:
        return chosen
    names = [environ.get(name, '') for name in ('LC_ALL', 'LC_MESSAGES', 'LANG')]
    try:
        names.extend(part or '' for part in locale.getlocale())
    except ValueError:
        pass
    joined = ' '.join(names).lower()
    return 'tr' if any(mark in joined for mark in ('tr_', 'turkish', '1254', '8859-9')) else 'en'


def say(lang, key, *args, **values):
    template = TEXT.get(lang, TEXT['en']).get(key) or TEXT['en'][key]
    return template.format(*args, **values) if args or values else template


def count(lang, number, noun, shown=None):
    """'1 session' / '3 sessions' / '4.7 thousand model calls'; `shown` is the number as written, when formatted."""
    words = NOUNS.get(lang, NOUNS['en']).get(noun) or NOUNS['en'][noun]
    word = words if isinstance(words, str) else words[0 if number == 1 else 1]
    return '%s %s' % (number if shown is None else shown, word)


def decimal(value, lang, digits=1):
    """1.5 / 1,5 without trailing zeros."""
    text = ('%.*f' % (digits, value)).rstrip('0').rstrip('.')
    return text.replace('.', ',') if lang == 'tr' else text


def big(value, lang):
    """2.2 billion · 311 million · 7.6 thousand · 950 (Turkish: 2,2 milyar · 311 milyon · 7,6 bin)."""
    if value is None:
        return say(lang, 'unknown')
    for power in (9, 6, 3):
        size = 10 ** power
        if value >= size:
            text = decimal(value / size, lang) if value < size * 100 else '%d' % round(value / size)
            return text + ' ' + say(lang, 'big.%d' % power)
    return str(int(value))


def window(minutes, lang):
    return say(lang, 'window.%s' % minutes) if minutes in (300, 10080) else say(lang, 'window.other', minutes)


def moment(when, lang, year=True):
    """A local date and time: 26.10.2026 14:05 (tr) or 2026-10-26 14:05 (en)."""
    local = when.astimezone()
    if lang == 'tr':
        return local.strftime('%d.%m.%Y %H:%M' if year else '%d.%m %H:%M')
    return local.strftime('%Y-%m-%d %H:%M' if year else '%b %d %H:%M')
