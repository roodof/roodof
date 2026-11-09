"""Content-free live diagnostics. Only allowlisted codes/counts and observation state leave here.

No log contents, provider/session IDs, paths, titles, exception messages or access keys.
Nothing is persisted and nothing is sent to a support service.
"""
from collections import Counter

from . import __version__

# code: stage, unit, level, English title/action, Turkish title/action
CATALOG = {
 'title_provided': ('titles','sessions','info','Agent title is available','The title comes from the agent’s saved title metadata.', 'Ajan başlığı mevcut','Başlık, ajanın kaydettiği başlık bilgisinden okundu.'),
 'title_not_recorded': ('titles','sessions','info','No title in readable metadata','Use a work name, or rename the session in the agent and refresh records.', 'Okunabilen başlık bilgisi yok','İş adı kullanabilir veya ajan içinde oturumu yeniden adlandırıp kayıtları yenileyebilirsin.'),
 'title_archive_only': ('titles','sessions','info','Retained history has no saved title','PLER does not archive agent titles. Add the original source if available, or use a work name.', 'Saklanan geçmiş başlık içermez','PLER ajan başlıklarını arşivlemez. Varsa asıl kaynağı ekle veya iş adı kullan.'),
 'title_location_unknown': ('titles','sessions','info','Title location is not recognized','This log layout has no supported title-index location. Use a work name or add the standard agent log folder.', 'Başlık kaynağının konumu tanınmadı','Bu kayıt düzeninde desteklenen başlık indeksi konumu bulunamadı. İş adı kullan veya standart ajan kayıt klasörünü ekle.'),
 'title_metadata_missing': ('titles','sessions','info','Title metadata was not found','Check that the original records still exist. A missing title does not mean usage records were lost.', 'Başlık dosyası bulunamadı','Asıl kayıtların yerinde olduğunu kontrol et. Başlık yokluğu kullanım kaydı kaybı anlamına gelmez.'),
 'title_metadata_large': ('titles','sessions','info','Title index exceeds the read limit','Title indexes are limited to 4 MiB each. Use a work name; usage accounting has separate limits.', 'Başlık indeksi okuma sınırını aşıyor','Başlık indeksleri dosya başına 4 MiB ile sınırlı. İş adı kullanabilirsin; kullanım hesabının sınırları ayrıdır.'),
 'title_read_budget': ('titles','sessions','info','Title-read budget reached','Each refresh reads at most 64 MiB of title metadata, newest sessions first. Other sessions keep their fallback name.', 'Başlık okuma bütçesine ulaşıldı','Her yenilemede en fazla 64 MiB başlık bilgisi, yeni oturumlardan başlanarak okunur. Diğerlerinde alternatif ad korunur.'),
 'title_access_denied': ('titles','sessions','warning','Title metadata is not accessible','Check folder permissions and refresh records. Usage records may still be readable.', 'Başlık kaynağına erişim yok','Klasör izinlerini kontrol edip kayıtları yenile. Kullanım kayıtları yine de okunabiliyor olabilir.'),
 'title_source_restricted': ('titles','sessions','info','Title source is outside the allowed read scope','PLER will not broaden filesystem access for a title. WSL title indexes outside selected roots are also restricted. Use a work name.', 'Başlık kaynağı izin verilen okuma kapsamında değil','PLER başlık için dosya erişimini genişletmez. Seçili kök dışındaki WSL başlık indeksleri de kısıtlıdır. İş adı kullanabilirsin.'),
 'title_wsl_not_running': ('titles','sessions','info','WSL title source is stopped','Start the distribution yourself, then refresh. PLER does not start distributions.', 'WSL başlık kaynağı çalışmıyor','Dağıtımı kendin başlattıktan sonra yenile. PLER dağıtımları başlatmaz.'),
 'title_wsl_unavailable': ('titles','sessions','info','WSL title status could not be checked','Check WSL availability and refresh. The fallback name remains usable.', 'WSL başlık durumu kontrol edilemedi','WSL erişimini kontrol edip yenile. Alternatif ad kullanılmaya devam eder.'),
 'title_metadata_invalid': ('titles','sessions','info','Some title metadata could not be decoded','A title may be absent or older. Keep the original logs; rename in the agent or use a work name.', 'Başlık bilgisinin bir kısmı çözümlenemedi','Başlık görünmeyebilir veya eski olabilir. Asıl kayıtları koru; ajan içinde yeniden adlandır veya iş adı kullan.'),
 'title_metadata_unreadable': ('titles','sessions','warning','Title metadata could not be read','Check source access and refresh. This status alone does not change recorded usage totals.', 'Başlık kaynağı okunamadı','Kaynağa erişimi kontrol edip yenile. Yalnız bu durum, kayıtlı kullanım toplamlarını değiştirmez.'),
 'title_window_limited': ('titles','sessions','info','Title lookup covers only the start and end of the log','Claude rename lookup reads the first and last 64 KiB. A rename in the middle may be missed; rename in the agent and refresh.', 'Başlık taraması kaydın başı ve sonuyla sınırlı','Claude adlandırmaları için ilk ve son 64 KiB okunur. Ortadaki değişiklik atlanabilir; ajan içinde yeniden adlandırıp yenile.'),
 'title_read_changed': ('titles','sessions','info','Title metadata changed during the read','Refresh after the agent finishes writing. The fallback name is kept for this read.', 'Başlık okunurken dosya değişti','Ajan yazmayı bitirdikten sonra yenile. Bu okumada alternatif ad korunur.'),
 'title_not_checked': ('titles','sessions','info','Title lookup has not been completed','Refresh records to check supported live title metadata.', 'Başlık kontrolü henüz tamamlanmadı','Desteklenen canlı başlık bilgisini kontrol etmek için kayıtları yenile.'),
 'title_demo': ('titles','sessions','info','Demo records do not use real agent titles','This example does not look up your agent metadata. Try a work name to organize the invented sessions.', 'Örnek kayıtlarda gerçek ajan başlığı aranmaz','Bu örnek ajan başlık bilgilerini okumaz. Uydurma oturumları düzenlemek için iş adı kullanabilirsin.'),
 'source_missing': ('logs','sources','warning','A selected source was not found','Open Log folders, check the selected location and refresh. Keep retained history.', 'Seçili kaynak bulunamadı','Kayıt klasörlerini aç, seçili konumu kontrol edip yenile. Saklanan geçmişi koru.'),
 'source_access_denied': ('logs','sources','warning','A source could not be accessed','Check folder permissions in Log folders, then refresh. Readable records remain included.', 'Kaynağa erişim engellendi','Kayıt klasörlerindeki izinleri kontrol edip yenile. Okunabilen kayıtlar dahil kalır.'),
 'source_restricted': ('logs','sources','warning','A source path was refused','Use a supported local folder or an explicitly selected running WSL source. Links inside a log folder are not followed.', 'Kaynak yolu reddedildi','Desteklenen yerel klasör veya açıkça seçilmiş çalışan WSL kaynağı kullan. Kayıt klasörü içindeki bağlantılar izlenmez.'),
 'source_wsl_stopped': ('logs','sources','warning','A selected WSL distribution is stopped','Start it yourself and refresh records; PLER does not start it.', 'Seçili WSL dağıtımı çalışmıyor','Dağıtımı kendin başlatıp kayıtları yenile; PLER dağıtımı başlatmaz.'),
 'source_wsl_unavailable': ('logs','sources','warning','Running WSL distributions could not be checked','Check WSL availability, then refresh. Existing retained history is kept.', 'Çalışan WSL dağıtımları kontrol edilemedi','WSL erişimini kontrol edip yenile. Mevcut saklanan geçmiş korunur.'),
 'source_read_limit': ('logs','sources','warning','A log or discovery read limit was reached','Recorded totals may be incomplete. Keep originals and select the relevant log folders; repeated refreshes do not remove limits.', 'Kayıt veya keşif okuma sınırına ulaşıldı','Toplamlar eksik olabilir. Asıl kayıtları koru ve ilgili kayıt klasörlerini seç; tekrar yenilemek sınırları kaldırmaz.'),
 'source_invalid': ('logs','sources','warning','Some log rows are invalid or incomplete','Refresh after writing finishes. If it persists, keep the originals and report this diagnostic code; do not edit logs to force a total.', 'Bazı kayıt satırları bozuk veya eksik','Yazma bitince yenile. Sürerse asıl dosyaları koruyup bu tanılama kodunu bildir; toplamı düzeltmek için kayıtları elle değiştirme.'),
 'source_reasoning': ('logs','sources','warning','Token fields are inconsistent','PLER cannot safely reconcile these records. Keep the originals and report this code; affected usage remains incomplete.', 'Token alanları birbiriyle tutarsız','PLER bu kayıtları güvenle uzlaştıramıyor. Asıl dosyaları koruyup bu kodu bildir; etkilenen kullanım eksik kalır.'),
 'source_unreadable': ('logs','sources','warning','A source could not be read','Check the folder and whether files are still being written, then refresh. The diagnostic contains no raw error text.', 'Kaynak okunamadı','Klasörü ve dosyaya yazmanın sürüp sürmediğini kontrol edip yenile. Tanılama ham hata metni içermez.'),
 'archive_unverified': ('history','sources','warning','Retained sources could not be verified','Restore access to selected originals and refresh. Keep the archive; its older values are not proof of current contents.', 'Saklanan kaynaklar doğrulanamadı','Seçili asıl kaynaklara erişimi düzeltip yenile. Arşivi koru; eski değerler güncel içeriğin kanıtı değildir.'),
 'archive_error': ('history','operations','warning','Retained history had a read or write error','Keep the data folder and original logs. Check a private backup before attempting recovery; clearing history is not a repair.', 'Saklanan geçmiş okunurken veya yazılırken hata oluştu','Veri klasörünü ve asıl kayıtları koru. Kurtarmadan önce özel yedeği kontrol et; geçmişi silmek onarım değildir.'),
 'archive_evicted': ('history','sources','warning','Some history exceeded retention limits','Re-read accessible originals or inspect an earlier private backup. Deleted originals cannot be recreated by refreshing.', 'Bazı geçmiş kayıtlar saklama sınırını aştı','Erişilebilir asıl kayıtları yeniden oku veya eski özel yedeği incele. Silinmiş asıl kayıtlar yenilemeyle oluşturulamaz.'),
 'git_unavailable': ('git','repositories','info','Git observation is unavailable','Check local repository access. Usage totals remain separate; missing Git evidence does not prove no work was done.', 'Git gözlemi kullanılamıyor','Yerel depoya erişimi kontrol et. Kullanım toplamı ayrıdır; Git kanıtı yokluğu iş yapılmadığını göstermez.'),
 'git_no_history': ('git','repositories','info','No local Git history was found','There may be no reflog yet. Continue using session usage; PLER does not fetch remote history.', 'Yerel Git geçmişi bulunamadı','Henüz reflog olmayabilir. Oturum kullanımını inceleyebilirsin; PLER uzak Git geçmişini çekmez.'),
 'git_limited': ('git','repositories','info','Git observation is partial','The read was bounded, contained unreadable entries or changed while reading. Refresh after repository activity finishes.', 'Git gözlemi kısmi','Okuma sınırlıydı, çözümlenemeyen satırlar vardı veya geçmiş okuma sırasında değişti. Depo işlemleri bitince yenile.'),
 'source_preferences': ('settings','operations','error','Saved log-folder preferences could not be read','Open Log folders in Settings. Keep the preference file and check access; PLER did not overwrite it.', 'Kayıt klasörü tercihleri okunamadı','Ayarlar içindeki Kayıt klasörlerini aç. Tercih dosyasını koru ve erişimi kontrol et; PLER üzerine yazmadı.'),
 'identity_preferences': ('settings','operations','error','Session identity links could not be preserved','Keep the PLER data folder and original logs. Check access or inspect a private backup; existing links were not reassigned.', 'Oturum kimliği bağlantıları korunamadı','PLER veri klasörünü ve asıl kayıtları koru. Erişimi veya özel yedeği kontrol et; bağlantılar başka oturuma aktarılmadı.'),
 'saved_metadata': ('settings','operations','warning','Some saved choices could not be read','Keep the data folder. A damaged or newer preference file is not overwritten; inspect a private backup using Help.', 'Bazı kayıtlı tercihler okunamadı','Veri klasörünü koru. Bozuk veya daha yeni tercih dosyası ezilmez; Yardım üzerinden özel yedeği incele.'),
 'logs_failed': ('logs','operations','error','The log-read step did not finish','Check Log folders and refresh. Any previous usable snapshot is kept; do not clear history to retry.', 'Kayıt okuma adımı tamamlanamadı','Kayıt klasörlerini kontrol edip yenile. Varsa önceki kullanılabilir görünüm korunur; tekrar denemek için geçmişi silme.'),
 'titles_failed': ('titles','operations','error','The title-read step did not finish','Refresh records. Any previous usable snapshot is kept; title lookup is separate from usage accounting.', 'Başlık okuma adımı tamamlanamadı','Kayıtları yenile. Varsa önceki kullanılabilir görünüm korunur; başlık okuma kullanım hesabından ayrıdır.'),
 'git_failed': ('git','operations','error','The Git observation step did not finish','Check local repository access and refresh. Any previous usable snapshot is kept.', 'Git gözlem adımı tamamlanamadı','Yerel depo erişimini kontrol edip yenile. Varsa önceki kullanılabilir görünüm korunur.'),
 'projection_failed': ('summary','operations','error','The report-preparation step did not finish','Keep the current data and download these diagnostic codes for support. Any previous usable snapshot is kept.', 'Görünüm hazırlama adımı tamamlanamadı','Mevcut veriyi koru ve destek için bu tanılama kodlarını indir. Varsa önceki kullanılabilir görünüm korunur.'),
 'scan_limit': ('logs','operations','error','The scan exceeded a bounded read limit','Select the relevant log folders and retry. Keep originals and retained history; repeated refreshes do not remove limits.', 'Tarama sınırlı okuma bütçesini aştı','İlgili kayıt klasörlerini seçip yeniden dene. Asıl kayıtları ve saklanan geçmişi koru; tekrar yenilemek sınırları kaldırmaz.'),
}


def describe(code, lang='en'):
    stage, unit, level, en, action_en, tr, action_tr = CATALOG.get(code, CATALOG['source_unreadable'])
    return dict(code=code if code in CATALOG else 'source_unreadable', stage=stage, unit=unit, level=level,
                title=tr if lang == 'tr' else en, next=action_tr if lang == 'tr' else action_en)


def title_info(status, title, lang='en'):
    reason = status.get('reason') if isinstance(status, dict) else ('provided' if title else 'not_checked')
    code = 'title_' + reason if isinstance(reason, str) and 'title_' + reason in CATALOG else 'title_not_checked'
    state = status.get('state') if isinstance(status, dict) else ('available' if title else 'fallback')
    return dict(state=state if state in ('available','limited','fallback') else 'fallback', **describe(code, lang))


def collect(sources, failure=None):
    counts = Counter()
    source_codes = {'FileNotFoundError':'source_missing','PermissionError':'source_access_denied',
                    'UnsafePath':'source_restricted','WSLNotRunning':'source_wsl_stopped',
                    'WSLUnavailable':'source_wsl_unavailable','ReadLimitExceeded':'source_read_limit',
                    'MalformedRows':'source_invalid','InconsistentReasoning':'source_reasoning'}
    for _, reason in sources.get('skipped', ()):
        counts[source_codes.get(reason, 'source_unreadable')] += 1
    for status in (sources.get('title_status') or {}).values():
        reason = status.get('reason') if isinstance(status, dict) else None
        code = 'title_' + reason if isinstance(reason, str) else ''
        if code in CATALOG and code != 'title_provided': counts[code] += 1
    for snapshot in (sources.get('git_activity') or {}).values():
        if snapshot.get('state') == 'unavailable': counts['git_unavailable'] += 1
        elif snapshot.get('state') == 'no_history': counts['git_no_history'] += 1
        elif snapshot.get('state') == 'ready' and any(snapshot.get(key) for key in ('truncated','skipped','changed')):
            counts['git_limited'] += 1
    archive = sources.get('archive') or {}
    for key, code in (('unverified_files','archive_unverified'),('errors','archive_error'),('evicted_files','archive_evicted')):
        count = archive.get(key, 0)
        if type(count) is int and count > 0: counts[code] += count
    counts['saved_metadata'] += sum(bool(sources.get(key)) for key in ('verdicts_error','work_items_error','claude_plan_error'))
    if failure in CATALOG: counts[failure] += 1
    return [dict(code=code, count=number) for code, number in sorted(counts.items()) if number > 0]


def view(sources, state, scanned_at, failure=None, lang='en'):
    return dict(format=1, version=__version__, state=state if state in ('idle','scanning','ready','error') else 'idle',
                has_snapshot=scanned_at is not None, scanned_at=scanned_at,
                snapshot='previous' if scanned_at is not None and state != 'ready' else 'current' if scanned_at is not None else 'none',
                items=[dict(describe(row['code'], lang), count=row['count']) for row in collect(sources, failure)])
