'use strict';
// Every word the page shows, per language. Same keys in each; a missing one falls back to English.
const I18N=/*I18N*/{
"en": {
"title": "PLER · My usage",
"skip": "Skip to content",
"brand_label": "PLER home",
"caption": "Your agent usage, from your own logs.",
"local": "This computer only",
"close": "Close",
"lang_toggle": "Türkçe",
"lang_toggle_label": "Sayfayı Türkçe göster",
"head_eyebrow": "A record of the work you already did",
"head_title": "My usage",
"head_intro": "Which agent used how much, in which project?",
"refresh": "Read logs again",
"export": "Download summary ↓",
"period_label": "Active sessions",
"period_7": "Active in the last 7 days",
"period_30": "Active in the last 30 days",
"period_90": "Active in the last 90 days",
"period_all": "All sessions",
"agent_label": "Agent",
"agent_all": "All agents",
"project_label": "Project",
"project_all": "All projects",
"status_preparing": "Preparing local logs…",
"progress_label": "Reading agent logs",
"scope": "Tokens cover the selected sessions in full. The period selects sessions by their last activity; it is not spending split by day.",
"mix_eyebrow": "Usage mix",
"mix_title": "What did the agents read and produce?",
"token_input": "New input",
"token_cache": "Read from cache",
"token_write": "Written to cache",
"token_output": "Output",
"mix_note": "These four parts are separate and add up to the total. Reasoning is part of output and is not added twice. Reading from the cache also uses resources.",
"projects_eyebrow": "Projects",
"projects_title": "Where does usage build up?",
"models_eyebrow": "Models",
"models_title": "Split shown in the logs",
"sessions_eyebrow": "Sessions",
"sessions_title": "Look into your sessions.",
"search_label": "Search sessions",
"search_placeholder": "Project, model or session code",
"sort_label": "Sort",
"sort_tokens": "Most tokens",
"sort_recent": "Most recently active",
"sort_started": "Most recently started",
"sort_issues": "Most errors / interruptions",
"search_scope": "Search narrows only this list; the summary above and the downloaded JSON follow the main filters. Open a session to see coincident local Git events. The record span includes waiting; it is not continuous working time.",
"table_caption": "Selected sessions. Click a project name to open the session details.",
"th_project": "Project / agent / session",
"th_dates": "Start → last activity",
"th_tokens": "Total tokens",
"th_calls": "Model calls",
"th_cache": "Input from cache",
"search_empty": "No session matches your search.",
"search_clear": "Clear search",
"more": "Show more sessions",
"more_count": "Show more sessions ({count})",
"empty_title": "No sessions in this selection.",
"empty_no_logs_title": "No local agent logs found.",
"empty_no_logs_text": "PLER reads Claude Code and Codex records on this computer. Use one of these agents, then read the logs again. Ordinary Claude desktop chats are not included.",
"empty_text": "Widen the filters, or read the logs again after using your agent.",
"empty_unreadable": "Some agent logs could not be fully read. Check the records and folder access, then read the logs again. The available data is incomplete.",
"filter_clear": "Show all sessions",
"footer_privacy": "Prompts, replies, commands and tool output never reach this page.",
"footer_local": "No model calls · Nothing is sent anywhere",
"dialog_title": "Session details",
"dialog_close": "Close session details",
"unknown": "Unknown",
"not_logged": "Not logged",
"err_unreachable": "Cannot reach PLER. Check that the app is open and try again.",
"err_closed": "PLER seems closed. Run the pler command to open it again.",
"err_read": "The logs could not be read. Reload the page.",
"closed": "PLER closed. Run the pler command to open it again.",
"dur_s": "{n} s",
"dur_m": "{n} min",
"dur_h": "{n} h",
"big_9": "billion",
"big_6": "million",
"big_3": "thousand",
"project_gone": "The selected project is no longer in the logs. Showing all projects.",
"previous_kept": " Showing the previous summary; the new selection could not be loaded.",
"reading": "Reading Claude Code and Codex logs. Large archives can take a while…",
"scanning": "Reading logs…",
"showing_previous": " Showing the previous summary.",
"last_read": "Last read: {at} · found {claude} and {codex}.",
"demo_banner": "Demo: every log, project and commit here is invented. Your own agent logs are not read.",
"unreadable_coverage": "{files} could not be fully read. Verified records are included; totals may be incomplete. ",
"all_read": "Every readable record of the sources found was used.",
"cross_period": " {sessions} started before the selected period; their whole totals are included.",
"status_unreadable": " · {files} not fully read; totals may be incomplete",
"unknown_calls": " {sessions} have no complete per-call split; call counts cover known records only.",
"stat_total": "Total tokens",
"stat_total_note": "{share} of it is context read again from the cache",
"stat_fresh": "Tokens outside the cache",
"stat_fresh_note": "New input, cache writes and output",
"stat_sessions": "Sessions",
"stat_calls": "Logged model calls",
"tokens": "{n} tokens",
"agent_note": "{sessions} · {calls} · {share} of input from cache · {errors} · {aborted}",
"insights_eyebrow": "Your situation",
"insights_title": "What do your logs tell you?",
"inspect_session": "Open this session →",
"insights_note": "These are observations from your own logs, not results of a controlled experiment. Each comes with the numbers behind it.",
"out_reset": "It was {used} full at the last record; the window reset {reset}. The current level is recorded when the agent runs again.",
"out_full": "Full. Resets {reset}.",
"pace_hour": "at this window's pace ({rate} an hour)",
"pace_day": "at the average of the last {days} days ({rate} a day)",
"out_fills": "Warning: {pace} it fills around {full}; it resets {reset}.",
"out_lasts": "{pace} it does not fill before it resets ({reset}).",
"out_nopace": "Resets {reset}. Not enough records yet to estimate the pace.",
"out_stale": "The last sample was {used} used. It is too old for a current level or forecast; read the logs again after the agent runs.",
"out_historical": "The log recorded {used} used. Its reset time is missing, so the current level is unknown.",
"quota_eyebrow": "Account quota",
"quota_title": "Where is the quota, and where is it heading?",
"window_300": "5-hour",
"window_10080": "Weekly",
"window_other": "{n}-minute",
"quota_aria": "{agent} {window} quota used",
"last_record": " Last record: {at}.",
"codex_unknown": "Codex · No quota percentage in the logs read. Remaining quota unknown.",
"claude_unknown": "Claude Code · Remaining quota unknown: Claude Code does not write its quota percentage to its logs.",
"claude_events": " Recorded in the selected sessions: {events}.",
"claude_setup_before": "To see it, run once in a terminal: ",
"claude_setup_after": ". This is supported in terminal Claude Code; quota data from the desktop app is not confirmed. You are asked before any setting changes.",
"claude_events_selected": "Recorded in the selected Claude Code sessions: {events}.",
"quota_note": "The quota is account-wide; concurrent sessions move the same meter. No live account query is made; values are the latest sample in the logs.",
"sessions_count": "{shown} / {sessions}",
"searching": " · searching {sessions}",
"open_detail": " · open details",
"start": "Start",
"last_activity": "Last activity",
"span": "Record span: {d}",
"field_agent": "Agent",
"field_code": "Session code",
"field_span": "Record span",
"field_active": "Working time logged by the agent",
"field_total": "Total tokens",
"field_reasoning": "Reasoning (part of output)",
"field_calls": "Model calls",
"field_prompts": "Requests",
"field_issues": "Errors / interrupted",
"field_tools": "Tool calls",
"field_files": "Distinct files (as logged)",
"detail_intro": "The record span is the time between the first and last event and includes waiting. Working time is shown only when the agent logged it.",
"models_in_session": "Models in this session",
"git_title": "Git during this session",
"git_scope": "Local Git events between this session's first and last record. Other people and agents may have been working at the same time; these events do not prove authorship. A commit still on a branch may have been undone by a later commit.",
"git_no_repo": "Neither this session's folder nor the files it edited are in an available local Git repository.",
"git_linked": "Repositories checked: {repos}. A repository counts when the session started in it or edited a file in it, so an agent started in a parent folder is still linked to the repository it changed.",
"git_outcome": "Commits recorded in this time: {kept} of {total} are still on a local or remote-tracking branch.",
"git_outcome_off": "No longer on any branch: {n} (amended, rebased, reset or on a deleted branch). A rewritten commit can still carry the same change.",
"git_outcome_unknown": "Could not be checked: {n} (missing or borrowed objects, a shallow or very long history).",
"git_on_branch": "on a branch",
"git_off_branch": "not on a branch",
"git_no_history": "This repository has no readable local HEAD history. It may be disabled or expired; no activity count can be inferred.",
"git_unavailable": "Local Git history could not be read. Your usage totals are still available.",
"git_not_scanned": "Git history has not been checked in this snapshot. Read the logs again to check it.",
"git_unknown_time": "The session's start or end is missing, so Git activity cannot be matched to it.",
"git_zero": "No matching event in the available local history. This does not mean no work was done or no commits exist.",
"git_limited": "Coverage is partial: the local history starts after the session, contains unreadable entries, changed during the read, or exceeds the read limit.",
"git_history_from": "Earliest available local event: {at}. Reflogs are local records, not the full commit history.",
"git_details": "View local events",
"git_more": "{n} additional matching events are counted above; the newest 20 are listed.",
"git_commit": "Commit recorded",
"git_amend": "Commit amended",
"git_reset": "HEAD reset",
"git_checkout": "Checkout / branch switch",
"git_merge": "Merge operation",
"git_rebase": "Rebase operation",
"git_other": "Other HEAD movement",
"git_row": "Git · {events}",
"noun_git_event": [
"local event",
"local events"
],
"noun_repository": [
"repository",
"repositories"
],
"split_unknown": "Call split unknown",
"files_note": "The file count shows logged edits. It does not show that the changes were kept or that the work was finished.",
"burn": "Rise of the account meter during the session: {items}. Concurrent sessions included.",
"burn_item": "{window} {points} percentage points",
"metadata_note": "Session metadata is shown. Prompt and reply text never reach this page.",
"export_file": "pler-usage-summary.json",
"noun_session": [
"session",
"sessions"
],
"noun_request": [
"request",
"requests"
],
"noun_call": [
"call",
"calls"
],
"noun_model_call": [
"model call",
"model calls"
],
"noun_logged_call": [
"logged call",
"logged calls"
],
"noun_error": [
"error",
"errors"
],
"noun_interrupted_turn": [
"interrupted turn",
"interrupted turns"
],
"noun_interruption": [
"interruption",
"interruptions"
],
"noun_file": [
"file",
"files"
],
"noun_claude_file": [
"Claude Code log file",
"Claude Code log files"
],
"noun_codex_file": [
"Codex log file",
"Codex log files"
],
"noun_limit_event": [
"limit event",
"limit events"
],
"noun_day": [
"day",
"days"
],
"quality_header": "Data quality:",
"stat_known_total": "Known token usage",
"export_retry": "Download again",
"export_preparing": "Preparing summary…",
"export_started": "Summary prepared. Check your browser downloads; if it did not start,",
"table_scroll_help": "Scroll sideways for more columns. With a keyboard, focus the table area and use the left and right arrows."
},
"tr": {
"title": "PLER · Kullanımım",
"skip": "İçeriğe geç",
"brand_label": "PLER ana sayfa",
"caption": "Ajan kullanımın, kendi kayıtlarından.",
"local": "Yalnız bu bilgisayar",
"close": "Kapat",
"lang_toggle": "English",
"lang_toggle_label": "Show the page in English",
"head_eyebrow": "Zaten yaptığın işin kaydı",
"head_title": "Kullanımım",
"head_intro": "Hangi ajan, hangi projede, ne kadar kaynak kullandı?",
"refresh": "Kayıtları yenile",
"export": "Özeti indir ↓",
"period_label": "Etkin oturumlar",
"period_7": "Son 7 günde etkin",
"period_30": "Son 30 günde etkin",
"period_90": "Son 90 günde etkin",
"period_all": "Tüm oturumlar",
"agent_label": "Ajan",
"agent_all": "Tüm ajanlar",
"project_label": "Proje",
"project_all": "Tüm projeler",
"status_preparing": "Yerel kayıtlar hazırlanıyor…",
"progress_label": "Ajan kayıtları okunuyor",
"scope": "Tokenlar seçilen oturumların tamamını kapsar. Dönem, oturumun son etkinliğine göre seçilir; günlere bölünmüş harcama değildir.",
"mix_eyebrow": "Kullanımın bileşimi",
"mix_title": "Ajanlar neyi okudu, neyi üretti?",
"token_input": "Yeni girdi",
"token_cache": "Önbellekten okunan",
"token_write": "Önbelleğe yazılan",
"token_output": "Çıktı",
"mix_note": "Bu dört alan birbirinden ayrıdır ve toplama girer. Akıl yürütme çıktının içindedir; ikinci kez eklenmez. Önbellekten okuma da kaynak kullanımıdır.",
"projects_eyebrow": "Projeler",
"projects_title": "Kullanım nerede birikiyor?",
"models_eyebrow": "Modeller",
"models_title": "Kayıtta görünen dağılım",
"sessions_eyebrow": "Oturumlar",
"sessions_title": "Oturumlarını incele.",
"search_label": "Oturum ara",
"search_placeholder": "Proje, model veya oturum kodu",
"sort_label": "Sıralama",
"sort_tokens": "En çok token kullanan",
"sort_recent": "En son etkin",
"sort_started": "En yeni başlayan",
"sort_issues": "En çok hata / kesinti",
"search_scope": "Arama yalnız bu listeyi daraltır; üstteki özet ve indirilen JSON ana filtreleri izler. Aynı zamana denk gelen yerel Git hareketleri için oturumu aç. Kayıt aralığı beklemeleri de içerir; kesintisiz çalışma süresi değildir.",
"table_caption": "Seçilen oturumlar. Proje adına basarak oturum ayrıntısını açabilirsin.",
"th_project": "Proje / ajan / oturum",
"th_dates": "Başlangıç → son etkinlik",
"th_tokens": "Toplam token",
"th_calls": "Model çağrısı",
"th_cache": "Girdide önbellek",
"search_empty": "Aramana uyan oturum yok.",
"search_clear": "Aramayı temizle",
"more": "Daha fazla oturum göster",
"more_count": "Daha fazla oturum göster ({count})",
"empty_title": "Bu seçimde oturum bulunamadı.",
"empty_no_logs_title": "Yerel ajan kaydı bulunamadı.",
"empty_no_logs_text": "PLER bu bilgisayardaki Claude Code ve Codex kayıtlarını okur. Bu ajanlardan birini kullandıktan sonra kayıtları yeniden oku. Claude masaüstündeki normal sohbetler dahil değildir.",
"empty_text": "Filtreleri genişlet veya ajanını kullandıktan sonra kayıtları yeniden oku.",
"empty_unreadable": "Bazı ajan kayıtları tamamen okunamadı. Kayıtları ve klasör erişimini kontrol edip yeniden oku. Gösterilebilen veri eksik.",
"filter_clear": "Tüm oturumları göster",
"footer_privacy": "İstek, yanıt, komut ve araç çıktısı bu ekrana alınmaz.",
"footer_local": "Model çağrısı yok · Dışarı veri gönderilmez",
"dialog_title": "Oturum ayrıntısı",
"dialog_close": "Oturum ayrıntısını kapat",
"unknown": "Bilinmiyor",
"not_logged": "Kayıtta yok",
"err_unreachable": "PLER’e ulaşılamıyor. Uygulamanın açık olduğunu kontrol edip yeniden dene.",
"err_closed": "PLER kapalı görünüyor. Yeniden açmak için pler komutunu çalıştırın.",
"err_read": "Kayıt okunamadı. Sayfayı yenileyin.",
"closed": "PLER kapandı. Yeniden açmak için pler komutunu çalıştırın.",
"dur_s": "{n} sn",
"dur_m": "{n} dk",
"dur_h": "{n} sa",
"big_9": "milyar",
"big_6": "milyon",
"big_3": "bin",
"project_gone": "Seçilen proje artık kayıtlarda bulunmuyor. Tüm projeler gösteriliyor.",
"previous_kept": " Önceki özet gösteriliyor; yeni seçim yüklenemedi.",
"reading": "Claude Code ve Codex kayıtları okunuyor. Büyük arşivlerde biraz sürebilir…",
"scanning": "Kayıtlar okunuyor…",
"showing_previous": " Önceki özet gösteriliyor.",
"last_read": "Son okuma: {at} · {claude}, {codex} bulundu.",
"demo_banner": "Deneme: buradaki bütün kayıtlar, projeler ve commit'ler uydurmadır. Kendi ajan kayıtların okunmuyor.",
"unreadable_coverage": "{files} tamamen okunamadı. Doğrulanabilen kayıtlar dahil; toplamlar eksik olabilir. ",
"all_read": "Bulunan kaynakların okunabilen kayıtları kullanıldı.",
"cross_period": " {sessions} seçilen dönemden önce başlamış; tüm oturum toplamı dahil.",
"status_unreadable": " · {files} tam okunamadı; toplamlar eksik olabilir",
"unknown_calls": " {sessions} için çağrı ayrımı tam değil; çağrı sayısı yalnız bilinen kayıtlardır.",
"stat_total": "Toplam token",
"stat_total_note": "{share} kadarı önbellekten yeniden okunan bağlam",
"stat_fresh": "Önbellek dışı token",
"stat_fresh_note": "Yeni girdi, önbelleğe yazılan ve çıktı",
"stat_sessions": "Oturum",
"stat_calls": "Kayıtlı model çağrısı",
"tokens": "{n} token",
"agent_note": "{sessions} · {calls} · girdinin {share} kadarı önbellekten · {errors} · {aborted}",
"insights_eyebrow": "Durumun",
"insights_title": "Kayıtların sana ne söylüyor?",
"inspect_session": "Bu oturumu incele →",
"insights_note": "Bunlar senin kayıtlarındaki gözlemler; kontrollü bir deney sonucu değil. Her birinin dayanağı yanındaki sayılardır.",
"out_reset": "Son kayıtta {used} doluydu; pencere {reset} sıfırlandı. Şu anki doluluk, ajan yeniden çalışınca kayda geçer.",
"out_full": "Dolu. Sıfırlanma: {reset}.",
"pace_hour": "bu penceredeki çalışma hızıyla (saatte {rate})",
"pace_day": "son {days} günün ortalamasıyla (günde {rate})",
"out_fills": "Uyarı: {pace} {full} civarı dolar; sıfırlanma {reset}.",
"out_lasts": "{pace} sıfırlanmadan ({reset}) dolmaz.",
"out_nopace": "Sıfırlanma: {reset}. Hız tahmini için henüz yeterli kayıt yok.",
"out_stale": "Son ölçümde {used} kullanılmıştı. Ölçüm, güncel doluluk veya tahmin için eski; ajan çalıştıktan sonra kayıtları yeniden oku.",
"out_historical": "Kayıtta {used} kullanılmıştı. Sıfırlanma zamanı eksik olduğu için güncel doluluk bilinmiyor.",
"quota_eyebrow": "Hesap kotası",
"quota_title": "Kota nerede, nereye gidiyor?",
"window_300": "5 saatlik",
"window_10080": "Haftalık",
"window_other": "{n} dakikalık",
"quota_aria": "{agent} {window} kota doluluğu",
"last_record": " Son kayıt: {at}.",
"codex_unknown": "Codex · Okunan kayıtlarda kota yüzdesi bulunamadı. Kalan kota bilinmiyor.",
"claude_unknown": "Claude Code · Kalan kota bilinmiyor: Claude Code kayıtlarına kota yüzdesi yazmaz.",
"claude_events": " Seçilen oturumlarda kaydedilen: {events}.",
"claude_setup_before": "Görmek için terminalde bir kez ",
"claude_setup_after": " çalıştır. Terminaldeki Claude Code desteklenir; masaüstü uygulamasından kota verisi gelmesi doğrulanmadı. Ayar değişmeden önce onayın sorulur.",
"claude_events_selected": "Seçilen Claude Code oturumlarında kaydedilen: {events}.",
"quota_note": "Kota hesap genelindedir; eşzamanlı oturumlar aynı ölçeri etkiler. Anlık hesap sorgusu yapılmaz; değerler kayıtlardaki son örnektir.",
"sessions_count": "{shown} / {sessions}",
"searching": " · {sessions} içinde arama",
"open_detail": " · ayrıntıyı aç",
"start": "Başlangıç",
"last_activity": "Son etkinlik",
"span": "Kayıt aralığı: {d}",
"field_agent": "Ajan",
"field_code": "Oturum kodu",
"field_span": "Kayıt aralığı",
"field_active": "Ajanın kaydettiği çalışma süresi",
"field_total": "Toplam token",
"field_reasoning": "Akıl yürütme (çıktının içinde)",
"field_calls": "Model çağrısı",
"field_prompts": "İstek",
"field_issues": "Hata / yarıda kesilen",
"field_tools": "Araç çağrısı",
"field_files": "Farklı dosya (kayda geçen)",
"detail_intro": "Kayıt aralığı ilk ve son olay arasındaki zamandır; beklemeleri de içerir. Çalışma süresi yalnız ajan kaydettiyse gösterilir.",
"models_in_session": "Bu oturumdaki modeller",
"git_title": "Oturum sırasında Git",
"git_scope": "Oturumun ilk ve son kaydı arasındaki yerel Git hareketleri. Aynı anda başka kişiler ve ajanlar da çalışmış olabilir; bu hareketler yazarı kanıtlamaz. Hâlâ dalda olan bir commit sonraki bir commit'le geri alınmış olabilir.",
"git_no_repo": "Ne bu oturumun klasörü ne de düzenlediği dosyalar erişilebilir bir yerel Git deposunda.",
"git_linked": "Kontrol edilen depolar: {repos}. Oturum bir depoda başladıysa ya da bir deponun dosyasını düzenlediyse o depo sayılır; böylece üst klasörde başlatılan bir ajan da değiştirdiği depoya bağlanır.",
"git_outcome": "Bu sürede kaydedilen commit'ler: {total} commit'ten {kept} tanesi hâlâ yerel ya da uzak izleme dalında.",
"git_outcome_off": "{n} tanesi artık hiçbir dalda değil: düzeltildi (amend), yeniden sıralandı, reset edildi ya da silinen bir dalda kaldı. Yeniden yazılan bir commit aynı değişikliği taşımaya devam edebilir.",
"git_outcome_unknown": "{n} tanesi kontrol edilemedi: eksik ya da başka depodan ödünç nesneler, sığ ya da çok uzun geçmiş.",
"git_on_branch": "dalda",
"git_off_branch": "dalda değil",
"git_no_history": "Bu depoda okunabilir yerel HEAD geçmişi yok. Kayıt kapalı veya süresi dolmuş olabilir; hareket sayısı çıkarılamaz.",
"git_unavailable": "Yerel Git geçmişi okunamadı. Kullanım toplamların gösterilmeye devam ediyor.",
"git_not_scanned": "Bu özette Git geçmişi kontrol edilmemiş. Kontrol etmek için kayıtları yeniden oku.",
"git_unknown_time": "Oturumun başlangıcı veya sonu eksik; Git hareketleriyle zaman eşleştirmesi yapılamıyor.",
"git_zero": "Erişilebilir yerel geçmişte bu aralığa uyan hareket yok. Bu, iş yapılmadığı veya commit olmadığı anlamına gelmez.",
"git_limited": "Kapsam kısmi: yerel geçmiş oturumdan sonra başlıyor, okunamayan kayıtlar var, okuma sırasında değişti veya okuma sınırını aşıyor.",
"git_history_from": "Erişilebilir en eski yerel hareket: {at}. Bu günlük, tüm commit geçmişi değildir.",
"git_details": "Yerel hareketleri göster",
"git_more": "Eşleşen {n} hareket daha yukarıdaki sayılara dahil; en yeni 20 hareket listeleniyor.",
"git_commit": "Commit kaydedildi",
"git_amend": "Commit düzeltildi",
"git_reset": "Reset işlemi",
"git_checkout": "Checkout / dal değişimi",
"git_merge": "Birleştirme işlemi",
"git_rebase": "Yeniden sıralama (rebase)",
"git_other": "Diğer HEAD hareketi",
"git_row": "Git · {events}",
"noun_git_event": "yerel hareket",
"noun_repository": "depo",
"split_unknown": "Çağrı ayrımı bilinmiyor",
"files_note": "Dosya sayısı kayda geçmiş düzenlemeleri gösterir. Değişikliklerin kalıcı olduğu veya işin tamamlandığı doğrulanmış değildir.",
"burn": "Oturum sırasında hesap ölçerindeki artış: {items}. Eşzamanlı oturumlar dahildir.",
"burn_item": "{window} {points} yüzde puan",
"metadata_note": "Oturum üstbilgileri gösteriliyor. İstek ve yanıt metinleri bu ekrana alınmadı.",
"export_file": "pler-kullanim-ozeti.json",
"noun_session": "oturum",
"noun_request": "istek",
"noun_call": "çağrı",
"noun_model_call": "model çağrısı",
"noun_logged_call": "kayıtlı çağrı",
"noun_error": "hata",
"noun_interrupted_turn": "yarıda kesilen tur",
"noun_interruption": "kesinti",
"noun_file": "dosya",
"noun_claude_file": "Claude Code dosyası",
"noun_codex_file": "Codex dosyası",
"noun_limit_event": "sınır olayı",
"noun_day": "gün",
"quality_header": "Veri kalitesi:",
"stat_known_total": "Bilinen token kullanımı",
"export_retry": "Yeniden indir",
"export_preparing": "Özet hazırlanıyor…",
"export_started": "Özet hazır. Tarayıcı indirmelerini kontrol edin; başlamadıysa",
"table_scroll_help": "Diğer sütunlar için yana kaydırın. Klavyede tablo alanına gelip sol ve sağ oklarını kullanın."
}
}/*END*/;
// Language: ?lang=, then the saved choice, then the browser; every other word comes from I18N above.
const LANG=(()=>{const asked=new URLSearchParams(location.search).get('lang');if(asked in I18N)return asked;try{const saved=localStorage.getItem('pler-lang');if(saved in I18N)return saved;}catch(_){}return (navigator.language||'').toLowerCase().startsWith('tr')?'tr':'en';})();
const LOCALE=LANG==='tr'?'tr-TR':undefined;
function t(key,values={}){const text=I18N[LANG][key]??I18N.en[key];return String(text).replace(/\{(\w+)\}/g,(match,name)=>name in values?values[name]:match);}
function count(n,noun,shown){const words=I18N[LANG]['noun_'+noun]??I18N.en['noun_'+noun];return (shown??number(n))+' '+(Array.isArray(words)?words[n===1?0:1]:words);}
const $=id=>document.getElementById(id);
let token='';
const accessMatch=location.hash.match(/^#access=([a-f0-9]{64})$/);
if(accessMatch){
  token=accessMatch[1];
  try{sessionStorage.setItem('pler-access',token);}catch(_){}
  history.replaceState(null,'',location.pathname+location.search);
}else{try{token=sessionStorage.getItem('pler-access')||'';}catch(_){}}
const number=value=>value==null?t('unknown'):new Intl.NumberFormat(LOCALE,{maximumFractionDigits:0}).format(value);
function node(tag,cls,text){const n=document.createElement(tag);if(cls)n.className=cls;if(text!=null)n.textContent=text;return n;}
function notice(message){$('notice').textContent=message||'';$('notice').hidden=!message;}
function applyLanguage(){
  document.documentElement.lang=LANG;document.title=t('title');
  for(const item of document.querySelectorAll('[data-i18n]'))item.textContent=t(item.dataset.i18n);
  for(const item of document.querySelectorAll('[data-i18n-placeholder]'))item.placeholder=t(item.dataset.i18nPlaceholder);
  for(const item of document.querySelectorAll('[data-i18n-label]'))item.setAttribute('aria-label',t(item.dataset.i18nLabel));
}
function switchLanguage(){const other=LANG==='tr'?'en':'tr';try{localStorage.setItem('pler-lang',other);}catch(_){}location.search='?lang='+other;}
async function api(path,options={}){
  let response;
  try{response=await fetch(path,{cache:'no-store',...options,headers:{...options.headers,'X-PLER-Token':token}});}catch(_){throw new Error(t('err_unreachable'));}
  let body;
  try{body=await response.json();}catch(_){throw new Error(t('err_closed'));}
  if(!response.ok){const error=new Error(body.error||t('err_read'));error.code=body.code;throw error;}
  return body;
}
async function post(path,body){return api(path+'?lang='+LANG,{method:'POST',headers:{'Content-Type':'application/json','X-PLER-Token':token},body:JSON.stringify(body)});}
async function closeApp(){
  try{await post('/api/quit',{});usageState.stopped=true;usageState.revision++;clearTimeout(usageState.timer);clearInterval(usageState.clock);document.querySelectorAll('button,select,input').forEach(item=>item.disabled=true);notice(t('closed'));}
  catch(error){notice(error.message);}
}
const usageState={data:null,revision:0,pageSize:20,timer:null,clock:null,stopped:false,loading:false,exporting:false,downloadUrl:null};
const usageAgents={'claude-code':'Claude Code',codex:'Codex'};
const usageTokens=[['input',t('token_input')],['cache_read',t('token_cache')],['cache_write',t('token_write')],['output',t('token_output')]];
const usagePct=value=>value==null?t('unknown'):new Intl.NumberFormat(LOCALE,{style:'percent',maximumFractionDigits:1}).format(value);
const usageDate=value=>value?new Intl.DateTimeFormat(LOCALE,{dateStyle:'short',timeStyle:'short'}).format(new Date(value)):t('not_logged');
const usageWindow=minutes=>minutes===300?t('window_300'):minutes===10080?t('window_10080'):t('window_other',{n:minutes});
function usageDuration(seconds){
  if(seconds==null||!Number.isFinite(seconds)||seconds<0)return t('not_logged');
  if(seconds<60)return t('dur_s',{n:Math.floor(seconds)});
  const minutes=Math.floor(seconds/60),days=Math.floor(minutes/1440),hours=Math.floor(minutes%1440/60),rest=minutes%60;
  return days?count(days,'day')+(hours?' '+t('dur_h',{n:hours}):''):hours?t('dur_h',{n:hours})+(rest?' '+t('dur_m',{n:rest}):''):t('dur_m',{n:minutes});
}
const usageSessionCode=session=>session.id.slice(0,8);
const gitLabels={commit:'git_commit',amend:'git_amend',reset:'git_reset',checkout:'git_checkout',merge:'git_merge',rebase:'git_rebase',other:'git_other'};
function usageShort(value){for(const [power,size] of [[9,1e9],[6,1e6],[3,1e3]])if(value>=size)return new Intl.NumberFormat(LOCALE,{maximumFractionDigits:1}).format(value/size)+' '+t('big_'+power);return number(value);}
function usageQuery(){return new URLSearchParams({days:$('usage-period').value,agent:$('usage-agent').value,project:$('usage-project').value,lang:LANG}).toString();}
async function loadUsage(){
  if(usageState.stopped)return;
  const revision=++usageState.revision;
  usageState.loading=true;
  if(usageState.downloadQuery&&usageState.downloadQuery!==usageQuery())clearUsageDownload();
  syncExportButton();$('usage-content').setAttribute('aria-busy','true');
  try{const data=await api('/api/usage?'+usageQuery());if(revision!==usageState.revision)return;usageState.data=data;renderUsage(data);
    if(data.state==='idle'){await refreshUsage();return;}
    clearTimeout(usageState.timer);if(data.state==='scanning'&&!usageState.stopped)usageState.timer=setTimeout(loadUsage,1500);
  }catch(error){if(revision!==usageState.revision)return;if(error.code==='unknown_project'&&$('usage-project').value!=='all'){$('usage-project').value='all';notice(t('project_gone'));loadUsage();return;}$('usage-status').textContent=error.message+(usageState.data?.has_snapshot?t('previous_kept'):'');$('usage-progress').hidden=true;$('usage-refresh').disabled=false;}
  finally{if(revision===usageState.revision){usageState.loading=false;syncExportButton();$('usage-content').setAttribute('aria-busy','false');restoreActionFocus();}}
}
async function refreshUsage(){
  rememberActionFocus($('usage-refresh'));
  clearUsageDownload();
  $('usage-refresh').disabled=true;$('usage-status').textContent=t('reading');$('usage-progress').hidden=false;
  try{await post('/api/usage/refresh',{});await loadUsage();}catch(error){if(usageState.stopped)return;$('usage-status').textContent=error.message;$('usage-refresh').disabled=false;$('usage-progress').hidden=true;}
  finally{restoreActionFocus();}
}
function renderUsage(data){
  $('usage-refresh').disabled=data.state==='scanning';$('usage-progress').hidden=data.state!=='scanning';syncExportButton();
  $('usage-demo').hidden=!data.demo;
  $('usage-status').textContent=data.state==='scanning'?t('scanning')+(data.has_snapshot?t('showing_previous'):''):data.error||t('last_read',{at:usageDate(data.scanned_at),claude:count(data.sources.claude_files,'claude_file'),codex:count(data.sources.codex_files,'codex_file')});
  const selected=$('usage-project').value;$('usage-project').replaceChildren(node('option','',t('project_all')));$('usage-project').firstChild.value='all';
  for(const project of data.project_options){const option=node('option','',project.name);option.value=project.id;$('usage-project').append(option);}$('usage-project').value=data.project_options.some(p=>p.id===selected)?selected:'all';
  $('usage-content').hidden=!data.has_snapshot;$('usage-empty').hidden=!data.has_snapshot||Boolean(data.totals.sessions);
  for(const id of ['usage-totals','usage-mix','usage-columns','usage-session-section'])$(id).hidden=!data.totals.sessions;
  const noFiles=!data.sources.claude_files&&!data.sources.codex_files;
  $('usage-empty').querySelector('h2').textContent=t(noFiles?'empty_no_logs_title':'empty_title');
  $('usage-empty').querySelector('p').textContent=t(data.sources.unreadable?'empty_unreadable':noFiles?'empty_no_logs_text':'empty_text');
  $('usage-filter-clear').hidden=!data.project_options.length;$('usage-coverage').hidden=noFiles;
  if(!data.has_snapshot)return;
  const qualityIssues=data.quality?.issues||[];
  $('usage-quality').hidden=!qualityIssues.length;
  $('usage-quality').textContent=qualityIssues.length?t('quality_header')+' '+qualityIssues.map(item=>item.detail).join(' '):'';
  $('usage-coverage').textContent=(data.sources.unreadable?t('unreadable_coverage',{files:count(data.sources.unreadable,'file')})+data.sources.issues.map(i=>i.reason+': '+i.files).join(' · '):t('all_read'))+(data.period.cross_period_sessions?t('cross_period',{sessions:count(data.period.cross_period_sessions,'session')}):'');
  if(data.sources.unreadable)$('usage-status').textContent+=t('status_unreadable',{files:count(data.sources.unreadable,'file')});
  if(data.unknown_call_sessions)$('usage-coverage').textContent+=t('unknown_calls',{sessions:count(data.unknown_call_sessions,'session')});
  const totals=data.totals;
  // Most of an agent's tokens are the same context read again from the cache; say so next to the total.
  const cached=totals.tokens.cache_read;
  $('usage-totals').replaceChildren(...[[t(data.quality?.tokens_complete===false?'stat_known_total':'stat_total'),usageShort(totals.total_tokens),totals.total_tokens?t('stat_total_note',{share:usagePct(cached/totals.total_tokens)}):''],[t('stat_fresh'),usageShort(totals.total_tokens-cached),t('stat_fresh_note')],[t('stat_sessions'),number(totals.sessions),count(totals.prompts,'request')],[t('stat_calls'),number(totals.calls),data.quality?.calls_complete===false?t('split_unknown'):'']].map(([label,value,note])=>{const item=node('article','usage-stat');item.append(node('span','',label),node('strong','',value));if(note)item.append(node('small','',note));return item;}));
  $('usage-agents').replaceChildren(...Object.entries(data.agents).map(([agent,row])=>{const article=node('article','usage-agent');const head=node('div','usage-agent-head');head.append(node('h3','',usageAgents[agent]||agent),node('strong','',t('tokens',{n:usageShort(row.total_tokens)})));const strip=node('div','token-strip');strip.setAttribute('role','img');strip.setAttribute('aria-label',usageTokens.map(([key,label])=>label+': '+number(row.tokens[key])).join('; '));
    for(const [key,label] of usageTokens){const segment=node('span','token-'+key.replace('cache_read','cache').replace('cache_write','write'));segment.style.width=(row.total_tokens?row.tokens[key]/row.total_tokens*100:0)+'%';segment.title=label+': '+number(row.tokens[key]);strip.append(segment);}
    article.append(head,strip,node('p','section-note',t('agent_note',{sessions:count(row.sessions,'session'),calls:count(row.calls,'model_call'),share:usagePct(row.cache_read_share),errors:count(row.errors,'error'),aborted:count(row.aborted,'interrupted_turn')})));return article;
  }));
  renderUsageInsights(data);renderUsageQuota(data);
  $('usage-projects').replaceChildren(...data.projects.slice(0,8).map(project=>{const row=node('div','usage-rank');const button=node('button','text-button',project.name);button.addEventListener('click',()=>{$('usage-project').value=project.id;$('usage-project').focus();usageState.pageSize=20;loadUsage();});row.append(button,node('strong','',usageShort(project.total_tokens)),node('small','',count(project.sessions,'session')));return row;}));
  $('usage-models').replaceChildren(...data.models.slice(0,8).map(model=>{const row=node('div','usage-rank');row.append(node('span','model-name',model.model==='unknown'?t('unknown'):model.model),node('strong','',usageShort(model.total_tokens)),node('small','',(usageAgents[model.agent]||model.agent)+' · '+count(model.calls,'call')));return row;}));
  renderUsageSessions();
}
function renderUsageInsights(data){
  const box=$('usage-insights'),notes=(data.insights||[]).filter(note=>note.kind!=='quota'||['full','fills_before_reset'].includes(quotaWindowNow(note.evidence).state));box.hidden=!notes.length;
  box.replaceChildren(node('span','eyebrow',t('insights_eyebrow')),node('h2','',t('insights_title')));
  const list=node('div','usage-insight-list');
  for(const note of notes){const card=node('article','usage-insight '+note.level);card.append(node('h3','',note.title),node('p','',note.detail));if(note.kind==='concentration'){const button=node('button','text-button',t('inspect_session'));button.addEventListener('click',()=>{if(data.sessions.length)openUsageSession(data.sessions[0]);});card.append(button);}list.append(card);}
  box.append(list,node('p','section-note',t('insights_note')));
}
function quotaWindowNow(window,now=Date.now()){
  const reset=Date.parse(window.resets_at),at=Date.parse(window.at);
  if(!Number.isFinite(reset))return {...window,state:'historical'};
  if(reset<=now)return {...window,state:'reset'};
  const age=(window.max_age_seconds??(window.window_minutes<1440?1800:86400))*1000;
  if(!Number.isFinite(at)||now-at>age||at>now+300000||(window.used_percent<100&&Date.parse(window.full_at)<=now))return {...window,state:'stale'};
  return window;
}
function usageOutlookText(window){
  const reset=usageDate(window.resets_at);
  if(window.state==='reset')return t('out_reset',{used:usagePct(window.used_percent/100),reset});
  if(window.state==='stale')return t('out_stale',{used:usagePct(window.used_percent/100)});
  if(window.state==='historical')return t('out_historical',{used:usagePct(window.used_percent/100)});
  if(window.state==='full')return t('out_full',{reset});
  const pace=window.percent_per_hour!=null?t('pace_hour',{rate:usagePct(window.percent_per_hour/100)}):window.percent_per_day!=null?t('pace_day',{days:Math.round(window.history_days),rate:usagePct(window.percent_per_day/100)}):'';
  if(window.state==='fills_before_reset')return t('out_fills',{pace,full:usageDate(window.full_at),reset});
  if(window.state==='lasts_until_reset')return t('out_lasts',{pace:pace[0].toUpperCase()+pace.slice(1),reset});
  return t('out_nopace',{reset});
}
function renderUsageQuota(data){
  // Codex rows come from its logs; Claude Code rows only from PLER's status line (pler statusline --install).
  const outlook=data.outlook||[],codex=outlook.filter(row=>row.agent!=='claude-code'),claude=outlook.filter(row=>row.agent==='claude-code');
  const windows=[...(codex.length?codex:data.quota.latest),...claude].map(window=>quotaWindowNow(window)),box=$('usage-quota');box.hidden=!windows.length&&!data.totals.sessions;box.replaceChildren(node('span','eyebrow',t('quota_eyebrow')),node('h2','',t('quota_title')));
  for(const window of windows){const agent=window.agent==='claude-code'?'Claude Code':'Codex';const card=node('div','usage-quota-row'+(window.state==='fills_before_reset'||window.state==='full'?' warn':''));const label=usageWindow(window.window_minutes);const unknown=['reset','stale','historical'].includes(window.state);const progress=node('progress');progress.max=100;progress.value=unknown?0:window.used_percent;progress.hidden=unknown;progress.setAttribute('aria-label',t('quota_aria',{agent,window:label}));card.append(node('span','',agent+' · '+label),progress,node('strong','',unknown?'—':usagePct(window.used_percent/100)),node('small','',usageOutlookText(window)+t('last_record',{at:usageDate(window.at)})));if(unknown)card.classList.add('quota-old');box.append(card);}
  if(!codex.length&&!data.quota.latest.length&&data.sources.codex_files)box.append(node('p','quota-unavailable',t('codex_unknown')));
  const rejected=data.claude_limit_events.rejected||0;
  if(!claude.length&&data.sources.claude_files){const note=node('p','quota-unavailable',t('claude_unknown')+(rejected?t('claude_events',{events:count(rejected,'limit_event')}):''));note.append(document.createElement('br'),t('claude_setup_before'),node('code','','pler statusline --install'),t('claude_setup_after'));box.append(note);}
  else if(rejected)box.append(node('p','section-note',t('claude_events_selected',{events:count(rejected,'limit_event')})));
  box.append(node('p','section-note',t('quota_note')));
}
function renderUsageSessions(){
  if(!usageState.data)return;
  const all=usageState.data.sessions,query=$('usage-session-search').value.trim().toLocaleLowerCase(LOCALE);
  const sessions=all.filter(session=>[session.project,usageAgents[session.agent]||session.agent,'#'+usageSessionCode(session),...session.models.map(model=>model.model)].some(value=>value.toLocaleLowerCase(LOCALE).includes(query)));
  const order=$('usage-session-sort').value;
  const stamp=value=>value?Date.parse(value):-Infinity;
  const byTime=(a,b,key)=>stamp(b[key])-stamp(a[key])||b.total_tokens-a.total_tokens||a.id.localeCompare(b.id);
  sessions.sort((a,b)=>order==='recent'?byTime(a,b,'ended'):order==='started'?byTime(a,b,'started'):order==='issues'?(b.errors+b.aborted)-(a.errors+a.aborted)||byTime(a,b,'ended'):b.total_tokens-a.total_tokens||byTime(a,b,'ended'));
  const visible=sessions.slice(0,usageState.pageSize);
  $('usage-session-count').textContent=t('sessions_count',{shown:number(visible.length),sessions:count(sessions.length,'session')})+(query?t('searching',{sessions:count(all.length,'session')}):'');
  $('usage-sessions').replaceChildren(...visible.map(session=>{
    const row=node('tr'),first=node('td'),button=node('button','text-button',session.project),code=usageSessionCode(session);
    button.setAttribute('aria-label',session.project+' · '+(usageAgents[session.agent]||session.agent)+' · '+code+t('open_detail'));button.addEventListener('click',()=>openUsageSession(session));
    first.append(button,node('small','task-subject',(usageAgents[session.agent]||session.agent)+' · #'+code));
    if(session.models.length)first.append(node('small','session-model',session.models.map(model=>model.model).join(', ')));
    if(session.errors||session.aborted)first.append(node('small','session-issues',count(session.errors,'error')+' · '+count(session.aborted,'interruption')));
    if(session.git_activity?.matched_events)first.append(node('small','session-git-hint',t('git_row',{events:count(session.git_activity.matched_events,'git_event')})));
    const dates=node('td','session-dates');
    for(const [name,value] of [[t('start'),session.started],[t('last_activity'),session.ended]]){const line=node('div'),time=node('time','',usageDate(value));if(value)time.dateTime=value;line.append(node('span','date-label',name+': '),time);dates.append(line);}
    dates.append(node('small','task-subject',t('span',{d:usageDuration(session.span_seconds)})));
    row.append(first,dates,node('td','task-number',number(session.total_tokens)),node('td','task-number',session.calls_complete?number(session.calls):t('unknown')),node('td','task-number',usagePct(session.cache_read_share)));return row;
  }));
  $('usage-search-empty').hidden=Boolean(sessions.length);$('usage-more').hidden=usageState.pageSize>=sessions.length;
  $('usage-more').textContent=t('more_count',{count:number(Math.min(20,sessions.length-visible.length))});
}
function renderGitActivity(content,activity){
  if(!activity||['not_repository','not_scanned'].includes(activity.state))return;
  const box=node('details','session-git');box.append(node('summary','',t('git_title')));
  const states={not_repository:'git_no_repo',no_history:'git_no_history',unavailable:'git_unavailable',not_scanned:'git_not_scanned',unknown_time:'git_unknown_time'};
  if(!activity||activity.state!=='ready'){box.append(node('p','',t(states[activity?.state]||'git_not_scanned')));content.append(box);return;}
  box.append(node('p','',t('git_scope')));
  if(activity.repositories)box.append(node('p','git-linked',t('git_linked',{repos:count(activity.repositories,'repository')})));
  if(activity.matched_events){
    const counts=node('div','git-counts');
    for(const [kind,n] of Object.entries(activity.counts)){const item=node('div');item.append(node('strong','',number(n)),node('span','',t(gitLabels[kind]||'git_other')));counts.append(item);}box.append(counts);
    const made=activity.commits;
    if(made?.total){box.append(node('p','git-outcome',t('git_outcome',{kept:number(made.on_branch),total:number(made.total)})));
      if(made.off_branch)box.append(node('p','',t('git_outcome_off',{n:number(made.off_branch)})));
      if(made.unknown)box.append(node('p','',t('git_outcome_unknown',{n:number(made.unknown)})));}
    const details=node('details','git-events'),summary=node('summary','',t('git_details')),list=node('ol');details.open=activity.events.length<=5;
    for(const event of activity.events){const item=node('li'),time=node('time','',usageDate(event.at));time.dateTime=event.at;const label=node('span','',t(gitLabels[event.kind]||'git_other'));if(event.commit)label.append(node('code','git-event-ref',event.commit));if(event.on_branch!=null)label.append(node('small','git-branch'+(event.on_branch?'':' git-branch-off'),t(event.on_branch?'git_on_branch':'git_off_branch')));item.append(time,label);list.append(item);}
    details.append(summary,list);box.append(details);
    if(activity.omitted_events)box.append(node('p','',t('git_more',{n:number(activity.omitted_events)})));
  }else box.append(node('p','',t('git_zero')));
  if(activity.coverage_limited)box.append(node('p','git-limited',t('git_limited')));
  box.append(node('p','git-history-note',t('git_history_from',{at:usageDate(activity.history_from)})));content.append(box);
}
function openUsageSession(session){
  $('usage-session-title').textContent=session.project;const content=$('usage-session-detail'),dl=node('dl');
  const fields=[[t('field_agent'),usageAgents[session.agent]||session.agent],[t('field_code'),'#'+usageSessionCode(session)],[t('start'),usageDate(session.started)],[t('last_activity'),usageDate(session.ended)],[t('field_span'),usageDuration(session.span_seconds)],[t('field_active'),usageDuration(session.active_ms==null?null:session.active_ms/1000)],[t('field_total'),number(session.total_tokens)],...usageTokens.map(([key,label])=>[label,number(session.tokens[key])]),[t('field_reasoning'),number(session.tokens.reasoning)],[t('field_calls'),session.calls_complete?number(session.calls):t('unknown')],[t('field_prompts'),number(session.prompts)],[t('field_issues'),session.errors+' / '+session.aborted],[t('field_tools'),number(session.tool_calls)],[t('field_files'),number(session.edited_files)]];
  fields.forEach(([label,value])=>dl.append(node('dt','',label),node('dd','',value)));content.replaceChildren(node('p','session-detail-intro',t('detail_intro')),dl);
  if(session.models.length){content.append(node('h3','detail-model-title',t('models_in_session')));for(const model of session.models){const row=node('div','usage-rank');row.append(node('span','model-name',model.model==='unknown'?t('unknown'):model.model),node('strong','',t('tokens',{n:number(model.total_tokens)})),node('small','',session.calls_complete?count(model.calls,'logged_call'):t('split_unknown')));content.append(row);}}
  content.append(node('p','section-note',t('files_note')));
  for(const note of session.notes)content.append(node('p','section-note',note));
  if(session.quota_burn.length)content.append(node('p','section-note',t('burn',{items:session.quota_burn.map(w=>t('burn_item',{window:usageWindow(w.window_minutes),points:w.percentage_points})).join(' · ')})));
  renderGitActivity(content,session.git_activity);
  content.append(node('p','section-note',t('metadata_note')));$('usage-session-dialog').showModal();
}
function clearUsageDownload(){
  if(usageState.downloadUrl)URL.revokeObjectURL(usageState.downloadUrl);
  usageState.downloadUrl=null;
  usageState.downloadQuery=null;
  $('usage-download-result').hidden=true;
  $('usage-download-link').removeAttribute('href');
}
function rememberActionFocus(button){if(document.activeElement===button)usageState.actionFocus=button;}
function restoreActionFocus(){
  const button=usageState.actionFocus;
  if(!button||usageState.stopped)return;
  if(document.activeElement!==document.body&&document.activeElement!==button){usageState.actionFocus=null;return;}
  if(button.isConnected&&!button.disabled){button.focus();usageState.actionFocus=null;}
}
function syncExportButton(){
  const filters=usageState.data?.filters;
  const matches=filters&&String(filters.days)===$('usage-period').value&&filters.agent===$('usage-agent').value&&filters.project===$('usage-project').value;
  const button=$('usage-export');
  button.disabled=usageState.stopped||usageState.loading||usageState.exporting||!usageState.data?.has_snapshot||!matches;
  button.textContent=t(usageState.exporting?'export_preparing':'export');
  button.setAttribute('aria-busy',String(usageState.exporting));
}
async function exportUsage(){
  if(usageState.stopped||usageState.exporting||!usageState.data?.has_snapshot||$('usage-export').disabled)return;
  const query=usageQuery();
  rememberActionFocus($('usage-export'));
  usageState.exporting=true;clearUsageDownload();syncExportButton();notice('');
  try{
    const data=await api('/api/usage/export?'+query);
    if(usageState.stopped||query!==usageQuery())return;
    usageState.downloadUrl=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));
    usageState.downloadQuery=query;
    const link=$('usage-download-link');link.href=usageState.downloadUrl;link.download=t('export_file');
    $('usage-download-status').textContent=t('export_started');$('usage-download-result').hidden=false;link.click();
  }catch(error){if(!usageState.stopped)notice(error.message);}
  finally{usageState.exporting=false;syncExportButton();restoreActionFocus();}
}
function showMoreUsageSessions(){
  const previous=$('usage-sessions').children.length;
  usageState.pageSize+=20;renderUsageSessions();
  $('usage-sessions').querySelectorAll('button')[previous]?.focus();
}
function reconnectFromAccessLink(){if(/^#access=[a-f0-9]{64}$/.test(location.hash))location.reload();}
applyLanguage();
$('lang-toggle').addEventListener('click',switchLanguage);$('close-app').addEventListener('click',closeApp);$('usage-refresh').addEventListener('click',refreshUsage);$('usage-export').addEventListener('click',exportUsage);$('usage-close-session').addEventListener('click',()=>$('usage-session-dialog').close());$('usage-more').addEventListener('click',showMoreUsageSessions);
for(const id of ['usage-period','usage-agent','usage-project'])$(id).addEventListener('change',()=>{usageState.pageSize=20;loadUsage();});
for(const id of ['usage-session-search','usage-session-sort'])$(id).addEventListener(id==='usage-session-search'?'input':'change',()=>{usageState.pageSize=20;renderUsageSessions();});
$('usage-search-clear').addEventListener('click',()=>{$('usage-session-search').value='';usageState.pageSize=20;renderUsageSessions();$('usage-session-search').focus();});
$('usage-filter-clear').addEventListener('click',()=>{$('usage-period').value='0';$('usage-agent').value='all';$('usage-project').value='all';$('usage-session-search').value='';$('usage-period').focus();usageState.pageSize=20;loadUsage();});
// Age the displayed snapshot without re-reading logs or making any network request.
function updateSnapshotClock(){if(!usageState.stopped&&!document.hidden&&usageState.data?.has_snapshot){renderUsageQuota(usageState.data);renderUsageInsights(usageState.data);}}
usageState.clock=setInterval(updateSnapshotClock,30000);
document.addEventListener('visibilitychange',updateSnapshotClock);
window.addEventListener('focus',updateSnapshotClock);
window.addEventListener('hashchange',reconnectFromAccessLink);
loadUsage();
