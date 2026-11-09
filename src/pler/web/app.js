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
"export": "Download JSON ↓",
"help": "Help",
"mask_projects": "Hide project names in JSON",
"mask_projects_note": "Times, models and session codes remain; the file is not anonymous.",
"quality_show": "Show affected sessions ({n})",
"coverage_title": "Before comparing these records",
"coverage_scope": "File access warnings cover all selected log folders. Session and pricing limits follow the main filters.",
"coverage_boundary": "PLER cannot tell whether logs were deleted before its first read. It cannot recover records it never read. A successful read does not prove complete account history.",
"coverage_help": "How to check or recover records",
"coverage_details": "Recorded quality reasons",
"coverage_next": "Next step: ",
"coverage_wsl_unavailable_title": "WSL records are unavailable",
"coverage_wsl_unavailable_impact": "Usage from the unavailable distribution may be missing. A smaller total does not show reduced usage.",
"coverage_wsl_unavailable_next": "Open the selected distribution yourself, check that its log folder is accessible, then choose Read logs again. PLER does not start WSL.",
"coverage_read_limits_title": "The read stopped at a safety limit",
"coverage_read_limits_impact": "Some records were excluded. Totals and comparisons do not cover the full selected source.",
"coverage_read_limits_next": "See Help for selecting fewer source folders or handling oversized records. Changing the page filters or rebuilding the cache does not remove reading limits.",
"coverage_unsafe_path_title": "A source path was excluded",
"coverage_unsafe_path_impact": "Blocked network paths or links inside a log folder may leave records out of the totals.",
"coverage_unsafe_path_next": "Use a supported local source folder or an explicitly selected WSL folder. Check source selection in Help; do not disable path protections.",
"coverage_source_missing_title": "A source disappeared during reading",
"coverage_source_missing_impact": "Available records remain visible, but this read may be incomplete.",
"coverage_source_missing_next": "Check whether the agent moved or removed the file, then read the logs again. Missing originals require an existing copy or a checked PLER backup; retrying cannot recreate them.",
"coverage_invalid_records_title": "Some records could not be interpreted",
"coverage_invalid_records_impact": "Verified usage is included; damaged, unfinished or inconsistent records may leave totals low.",
"coverage_invalid_records_next": "After the agent finishes writing, read the logs again. If the warning remains, preserve the original files and see Help. Do not edit logs or clear the archive to remove the warning.",
"coverage_source_access_title": "Some source files or folders could not be read",
"coverage_source_access_impact": "The visible totals may omit records. This does not prove that those records were deleted.",
"coverage_source_access_next": "Check the selected folders and your read access, then read the logs again. A cache rebuild cannot fix folder access. Keep existing history while investigating.",
"coverage_archive_old_parser_title": "Some history was read by an older reader",
"coverage_archive_old_parser_impact": "The saved interpretation cannot be verified with the current reader while the original source is unavailable. It is not a confirmed current measurement.",
"coverage_archive_old_parser_next": "If the original logs still exist, make them accessible at the selected source and read again. Otherwise preserve the archive; rebuilding the cache cannot upgrade or recreate missing originals.",
"coverage_archive_unverified_title": "Saved history is standing in for unchecked sources",
"coverage_archive_unverified_impact": "PLER is showing earlier metadata. The source's current contents and whether it was deleted are unverified.",
"coverage_archive_unverified_next": "Restore access to the selected source and read again. If access cannot be restored, keep this history as unverified; do not clear the archive.",
"coverage_archive_loss_title": "Some retained history may be missing",
"coverage_archive_loss_impact": "Archive limits or an archive read/write error may leave historical coverage incomplete. A lower total does not show a saving.",
"coverage_archive_loss_next": "Keep the current data. Re-read accessible originals or check an earlier private backup and recover it into a new folder using Help. Clearing the archive does not repair lost history.",
"coverage_retained_history_title": "Some originals are gone; saved metadata remains",
"coverage_retained_history_impact": "Previously retained values are included with their original dates and quality limits. They do not prove complete account history or fresh quota.",
"coverage_retained_history_next": "Back up this history before removing local data. Re-reading or rebuilding the cache cannot recreate deleted originals. Preserve the PLER archive.",
"coverage_incomplete_usage_title": "Some session counts are incomplete",
"coverage_incomplete_usage_impact": "Known values can be inspected, but missing or unreconciled usage prevents a complete comparison. A smaller total alone does not prove improved efficiency.",
"coverage_incomplete_usage_next": "Open the affected sessions and their recorded quality reasons. Re-reading may help unfinished logs; older formats or uncertain histories can remain unknown.",
"coverage_uncertain_attribution_title": "Some usage cannot be assigned reliably",
"coverage_uncertain_attribution_impact": "Session, project or model splits may be uncertain. Do not use those splits to rank work or assign its cost.",
"coverage_uncertain_attribution_next": "Inspect the affected sessions. Naming or linking a work item does not repair missing source attribution; leave unsupported comparisons open.",
"coverage_unpriced_usage_title": "Part of the usage has no API price",
"coverage_unpriced_usage_impact": "The API price equivalent covers priced records only. Unpriced usage is unknown, not free, and the amount is not your subscription bill.",
"coverage_unpriced_usage_next": "Check the priced share and model names before comparing amounts. Missing model or price evidence cannot be filled in by rebuilding the cache.",
"quality_only": "Only sessions with data-quality limits",
"quality_clear": "Show all selected sessions",
"quality_filter_note": "This list filter does not change totals or JSON scope.",
"reedit_brief": "{matched} earlier sessions matched among {eligible} eligible; {pending} unmatched sessions await follow-up. Not evaluable: {excluded}.",
"reedit_caution": "Logged targets do not prove completed changes, waste or quality. Tokens belong to whole sessions.",
"reedit_method": "Scope, method and limits",
"open_outside": "Find this session outside the filters",
"quota_ambiguous": "Conflicting meter history. The current percentage and forecast are unknown. Separate personal/work profiles before comparing their meters.",
"quota_multiple_sources": "Several local source groups contribute history. A common account cannot be verified, so the current percentage and forecast are unknown. Select one source group.",
"metadata_settings": "Local history and reader cache",
"backup_title": "Back up and recover history",
"backup_scope": "Backs up all retained history, verdicts, work titles, goals, outcome notes and links, retention preference and Claude quota samples. Main filters and project-name masking do not apply. Source logs and rebuildable caches are not included.",
"backup_privacy": "The file includes private paths, identifiers and the work details you entered. It is unencrypted and is not an anonymous report. Keep it safe.",
"backup_download": "Download private backup",
"backup_preparing": "Preparing backup…",
"backup_prepared": "Backup prepared. Check your saved downloads; if it did not start,",
"backup_file": "Backup file to check",
"backup_check": "Check backup",
"backup_checking": "Checking backup…",
"backup_check_help": "Checking sends this file only to PLER on this computer, keeps it in memory, and does not restore or change history.",
"backup_guide": "How to restore into a new folder",
"backup_invalid_file": "Choose a nonempty PLER backup within the supported size limit.",
"backup_checked": "Backup checked: PLER {version}, {date}; {files} archived sources, {verdicts} verdicts, {works} work titles, {links} work links and {quota} quota samples. Saved retention: {retention}. History has not been restored or changed.",
"work_eyebrow": "Across sessions and agents",
"work_title": "My work",
"work_outcome_title": "Goal and outcome",
"work_outcome_scope": "Your entry applies to the whole work, independently of filters. PLER does not infer completion or quality from tests, Git or usage.",
"work_goal_label": "Intended result",
"work_outcome_label": "Your outcome",
"work_result_label": "Result or remaining work",
"work_goal_empty": "No goal recorded.",
"work_goal_view": "Goal: {text}",
"work_result_view": "Result / remaining work: {text}",
"work_outcome_view": "Your outcome: {outcome}",
"work_outcome_not_recorded": "Not assessed",
"work_outcome_partial": "Partly completed",
"work_outcome_completed": "Completed",
"work_outcome_not_completed": "Not completed",
"work_outcome_time": "Outcome last recorded: {at}. This is the entry time, not measured completion time.",
"work_details_edit": "Edit goal and outcome",
"work_details_help": "Goal and result notes are optional, up to 1,000 characters each. They are private user entries; normal JSON reports omit them, private backups include them. Drafts stay in this window during language changes.",
"work_details_save": "Save goal and outcome",
"work_details_saved": "Goal and outcome saved.",
"work_details_unsaved": "Unsaved goal or outcome changes.",
"work_details_current": "No unsaved changes.",
"work_details_invalid": "Use up to 1,000 characters per text field, with line breaks and no control characters.",
"work_details_conflict": "Saved details changed in another window. Your draft is kept; review the latest saved version before saving.",
"work_details_latest": "Latest saved version",
"work_details_review": "Your draft stays in the form. Review the saved values below before keeping your draft for the next save or using the saved version. Neither choice writes a change.",
"work_details_keep": "Keep my draft for next save",
"work_details_discard": "Discard draft and use saved",
"work_observations_title": "Recorded observations",
"work_observations_scope": "These follow the main filters and cover whole linked sessions. Test/build counts describe each session's latest visible result; Git activity is a time association. They do not prove that the work met its goal.",
"work_obs_none": "No linked sessions are in the main filters. Widen the selection to inspect observations.",
"work_obs_unavailable": "Observation summary unavailable. Open linked session details to inspect the available evidence.",
"work_obs_test": "Tests",
"work_obs_build": "Builds",
"work_obs_checks": "{kind}: latest visible result passed in {passed} sessions, failed in {failed}, unknown in {unknown}.",
"work_obs_no_checks": "{kind}: no check was recorded in these selected sessions.",
"work_obs_git": "Git history readable in {available} selected sessions; coincident activity in {active}. Limited coverage in {limited}.",
"work_obs_git_unknown": "No readable Git observations for these selected sessions; activity is unknown.",
"work_intro": "Give one job a name, then link its Claude and Codex sessions from session details.",
"work_unreadable": "Saved work could not be read. Editing is disabled to protect it. Use a checked private backup to recover it in a new folder; see Help.",
"work_empty": "No work groups yet. Create one to collect the sessions for a job.",
"work_new_title": "New work title",
"work_placeholder": "For example: prepare the first release",
"work_create": "Create work",
"work_choose": "Choose work",
"work_edit_title": "Work title",
"work_rename": "Save title",
"work_delete": "Delete work…",
"work_summary": "Work groups: {works} · Linked sessions in this selection: {selected}, counted once · Unassigned: {unassigned}. Linked outside the main filters: {outside} · Unavailable: {missing} · Shared by several works in this selection: {overlap}.",
"work_union": "Linked-session summary: {tokens} known tokens · {calls} recorded calls · {api} API price equivalent.",
"work_counts": "Linked: {linked} · Available: {available} · In the main filters: {selected} · Outside the main filters: {outside} · Unavailable: {missing} · Also linked to other work in this selection: {overlap}.",
"work_usage": "Selected linked sessions: {tokens} known tokens · {calls} recorded calls · {api} API price equivalent.",
"work_no_selection": "No linked sessions in the main filters. No usage total is shown for this work.",
"work_quality": "Some selected sessions have incomplete usage or attribution. These are known recorded values, not a complete measurement.",
"work_more": "Show more linked sessions ({n})",
"work_no_members": "Add sessions from Sessions to collect the work here.",
"work_scope": "Usage follows the main filters and covers whole sessions, not the cost of one change. Search and data-quality list filters do not change this scope. A session may belong to several works; their totals cannot be added. The summary counts each linked session once.",
"work_api_note": "API price equivalents use available prices; unpriced usage may be omitted. They are not your subscription bill.",
"work_links_privacy": "Privacy of these links",
"work_privacy": "Titles, goals, outcome notes and links stay on this computer and are excluded from normal JSON summaries. Private backups include them. Missing sessions remain linked by their saved codes; PLER does not attach a different session automatically.",
"work_outside": "Outside the main filters",
"work_missing": "Session unavailable",
"work_unlink": "Unlink",
"work_unlink_label": "Unlink session #{code} from {title}",
"work_delete_heading": "Delete this work?",
"work_delete_help": "Deletes this work's title, goal, outcome notes and session links. Session logs, recorded usage, verdicts and older backups stay unchanged.",
"work_cancel": "Keep work",
"work_delete_confirm": "Delete work and links",
"work_link": "Link to work",
"work_link_choose": "Choose a work to link",
"work_linked_none": "This session is not linked to any work.",
"work_create_link": "Create and link",
"work_session_note": "Link this whole session to one or more works. Its usage is counted once in the general totals.",
"work_title_invalid": "Enter a title of 1–120 characters without control characters.",
"work_failed": "Work could not be saved. Your previous links and title remain visible.",
"work_saved": "Work saved.",
"work_saved_refresh": "Work saved, but the view could not be refreshed. Read the view again before making another change.",
"work_saving": "Saving…",
"work_reload": "Reload saved work",
"work_unpriced": "Unpriced",
"work_api_covered": "{amount} ({share} of tokens priced)",
"retention_label": "Keep metadata after source logs disappear",
"retention_on": "History retention is on. Stored archive: {bytes}; at most {days} unseen days, {files} files and {limit}.",
"retention_off": "History retention is off. Existing archive bytes ({bytes}) are preserved, but are not loaded or updated.",
"retention_help": "The local archive includes identifiers, project/edited paths, models and counts, never prompts or replies. Turning retention off preserves it; clearing deletes the retained history.",
"cache_reset": "Rebuild reader cache",
"cache_reset_help": "Only disposable caches (log readers and code counts) are reset. Archive, quota samples and preferences stay unchanged; the next read may take longer.",
"cache_reset_done": "Reader caches reset; retained history is preserved. Reading the logs again.",
"retention_changed": "History retention preference saved. Reading the selected sources again.",
"retention_short_on": "retention on",
"retention_short_off": "retention off",
"quality_session": "Data-quality limits",
"dated_title": "Dated recorded usage in this period",
"dated_result": "{tokens} tokens · {calls} recorded responses · {sessions} contributing sessions",
"dated_coverage": "Eligible retained sessions: {eligible} of {selected}. Sessions with unallocated usage: {unallocated}.",
"dated_scope": "Only reconciled responses whose recorded times all fall in this interval are counted. Cumulative, undated and uncertain usage is not distributed across dates. This is not a complete account total.",
"dated_interval": "From {since} through {cutoff}. The observation time stays fixed until logs are read again.",
"dated_all": "all dated records",
"dated_exclusions": "Coverage details",
"dated_undated": "Undated responses: {undated}; future responses excluded: {future}; responses before the period: {outside}.",
"dated_incomplete_usage": "Incomplete session usage",
"dated_unverified_attribution": "Unverified ownership",
"dated_missing_event_evidence": "No verified per-response time evidence",
"version_label": "Version {version}",
"archive_clear": "Clear PLER archive",
"archive_clearing": "Clearing archive…",
"archive_clear_help": "Clears the whole PLER archive. Agent logs stay unchanged; copies of deleted sources cannot be recovered.",
"archive_summary": "Selected sessions containing PLER archive metadata: {n}.",
"archive_disabled": "The PLER archive is unavailable; a safe local cache folder is required.",
"archive_cleared": "PLER archive cleared. The remaining source logs are being read again.",
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
"search_placeholder": "Session title, project or model",
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
"th_verdict": "Did it pay off?",
"verdict_useful": "Useful",
"verdict_wasted": "Wasted",
"verdict_group": "Your verdict on session #{code}",
"field_verdict": "Your verdict",
"verdict_summary": "Your verdicts in this selection: {useful} useful ({useful_tokens} tokens, {useful_usd} at list prices) · {wasted} wasted ({wasted_tokens} tokens, {wasted_usd}) · {none} not judged. Saved only on this computer; click a pressed button again to remove it.",
"verdict_hint": "Mark sessions Useful or Wasted with one click; PLER then shows what the wasted ones cost. Saved only on this computer, never sent anywhere.",
"verdict_demo": " Demo verdicts last only while this page is open.",
"verdict_unreadable": "The saved verdicts file could not be read (damaged, or from a newer PLER), so verdicts are shown as not judged and the file is not overwritten.",
"session_work_link": "Link to a work",
"session_work_another": "Link to another work",
"session_work_mode": "Work link type",
"session_work_existing": "Link existing work",
"session_work_new": "Create new work",
"account_limits": "Account limits",
"account_limit_warning": "Account limit warning",
"usage_alert": "Usage alert",
"usage_alerts": "Usage alerts",
"search_empty": "No session matches your search.",
"search_clear": "Clear search",
"more": "Show more sessions",
"more_count": "Show more sessions ({count})",
"empty_title": "No sessions in this selection.",
"empty_no_logs_title": "No local agent logs found.",
"empty_no_logs_text": "PLER reads Claude Code and Codex records on this computer. Use one of these agents, then read the logs again. Ordinary Claude desktop chats are not included.",
"empty_text": "Widen the filters, or read the logs again after using your agent.",
"empty_unreadable": "Some agent logs could not be fully read. Check the records and folder access, then read the logs again. The available data is incomplete.",
"empty_unreadable_title": "The selected records could not be fully read.",
"filter_clear": "Show all sessions",
"footer_privacy": "Prompts, replies, commands and tool output never reach this page.",
"footer_local": "No model calls · Agent data stays local",
"dialog_title": "Session details",
"dialog_close": "Close session details",
"unknown": "Unknown",
"not_logged": "Not logged",
"err_unreachable": "Cannot reach PLER. Check that the app is open and try again.",
"err_closed": "PLER seems closed. Run the pler command to open it again.",
"err_read": "The logs could not be read. Reload the page.",
"closed": "PLER closed. Open PLER again to continue (Windows portable: PLER.exe).",
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
"demo_banner": "Demo data: invented logs and projects. Your own records are not read. Demo work is temporary.",
"unreadable_coverage": "{files} could not be fully read. Verified records are included; totals may be incomplete. ",
"all_read": "Every readable record of the sources found was used. This does not prove complete account history.",
"cross_period": " {sessions} started before the selected period; their whole totals are included.",
"status_unreadable": " · {files} not fully read; totals may be incomplete",
"unknown_calls": " {sessions} have no complete per-call split; call counts cover known records only.",
"stat_total": "Total tokens",
"stat_total_note": "{share} of it is context read again from the cache",
"stat_fresh": "Tokens outside the cache",
"stat_fresh_note": "New input, cache writes and output",
"stat_sessions": "Sessions",
"stat_calls": "Logged model calls",
"stat_api": "API price equivalent",
"stat_api_note": "Recorded responses at standard prices of {date}. Not your bill: a subscription is a flat fee.",
"stat_api_partial": "Covers {share} of tokens; the rest could not be priced. Standard prices of {date}; not your bill.",
"field_api": "API price equivalent",
"tokens": "{n} tokens",
"agent_note": "{sessions} · {calls} · {share} of input from cache · {errors} · {aborted}",
"insights_eyebrow": "Your situation",
"insights_title": "What do your logs tell you?",
"inspect_session": "Open this session →",
"insights_note": "These are observations from your own logs, not results of a controlled experiment. Each comes with the numbers behind it.",
"out_reset": "It was {used} full at the last record; the window reset {reset}. The current level is recorded when the agent runs again.",
"out_full": "Full. Resets {reset}.",
"quota_alert_full": "{agent}: the {window} limit is reached. It resets {reset}.",
"quota_alert_soon": "{agent}: at this pace the {window} limit fills around {full}, in {left}. It resets {reset}.",
"quota_alert_title": "PLER account limit warning",
"live_watch": "Watch account limits",
"live_watch_help": "While this page is open, PLER reads the logs again every 5 minutes and warns when a limit will fill within an hour (a weekly limit: within a day). Each read uses some processor time; this window remembers the choice while it stays open.",
"live_notify_on": "Turn on desktop notifications",
"live_notify_off": "Turn off desktop notifications",
"live_notify_active": "Desktop notifications are on for new warnings.",
"live_notify_blocked": "Notifications are unavailable in this window; the warning still appears here.",
"live_notify_unsupported": "Notifications are unavailable here; the warning still appears on the page.",
"pace_hour": "at this window's pace ({rate} an hour)",
"pace_day": "at the average of the last {days} days ({rate} a day)",
"out_fills": "Warning: {pace} it fills around {full}; it resets {reset}.",
"out_lasts": "{pace} it does not fill before it resets ({reset}).",
"out_nopace": "Resets {reset}. Not enough records yet to estimate the pace.",
"out_plan_changed": " The logged plan changed {at}; only later records are used.",
"out_stale": "The last sample was {used} used. It is too old for a current level or forecast; read the logs again after the agent runs.",
"out_historical": "The log recorded {used} used. Its reset time is missing, so the current level is unknown.",
"quota_eyebrow": "Account quota",
"quota_title": "Account limits and forecasts",
"plans_eyebrow": "Subscription",
"plans_title": "Recorded usage and plan prices",
"plan_choose_label": "Your Claude plan",
"plan_choice_none": "Not chosen",
"plan_choice_pro": "Pro ($20 a month)",
"plan_choice_max": "Max ($100 a month)",
"plan_choice_ultra": "Ultra ($200 a month)",
"plan_choice_api": "API key, no plan",
"plan_named": "{name}, list price ${price} a month",
"plan_api_key": "API key, no plan",
"plan_unchosen": "plan not chosen",
"plan_unlogged": "plan not logged",
"plan_api_line": "Recorded dated responses, API price equivalent: {usd} ({share} of their tokens priced).",
"plan_api_unknown": "An API price equivalent cannot be calculated from priced responses in this period. Missing or unpriced records are unknown, not free.",
"plan_partial": " Retained usage could not be fully dated or verified; the sum may be low.",
"plan_meter_line": "Observed at 100% in {five} of {five_total} sampled 5-hour reset periods and {week} of {week_total} sampled weekly reset periods. Unobserved peaks are unknown.",
"plan_choose_plan": "Choose your Claude plan to compare it with this usage. It is saved only on this computer.",
"plan_no_meter": "No usable Claude Code quota samples were found. For terminal Claude Code, the optional PLER status line can record samples (pler statusline --install). This does not provide desktop quota support.",
"plan_no_meter_codex": "No usable Codex quota samples were found. Read logs again after using Codex; if its logs contain no supported meter, remaining quota stays unknown.",
"plan_larger_ratio_unpublished": "PLER has no verified limit ratio for these plans, so it cannot name a sufficient tier. Review current provider limits, credits and API options.",
"plan_larger_need_unseen": "Observed limit pressure does not establish how much capacity you need. A larger plan is not proven sufficient; model-specific limits and paid extra usage need separate review.",
"plan_api_below_list_price": "Recorded API price equivalent {usd} is below the monthly list price {price}. This does not establish a switching saving or subscription value.",
"plan_lower_observed": "Assuming these samples used {current}, their observed peak was {peak}; {smaller} (list price {price}/month) provides {share} of those published limits. This does not establish that the smaller plan would be enough.",
"plan_lower_weekly_observed": "Assuming these samples used {current}, the observed weekly peak was {peak}; {smaller} (list price {price}/month) provides {share} of that published limit. A 5-hour comparison and overall plan fit are unverified.",
"plan_comparison_expired": "The quota evidence for this comparison has aged or its reset has passed. Read logs again before comparing current plan thresholds.",
"plan_payment_unknown": "Actual payment is not recorded. Plan labels and list prices do not verify billing, credits, discounts, add-ons or historical plan changes.",
"plan_interval": "Dated responses from {since} through {until} (UTC).",
"plan_limit_source_incomplete": "Some sources or retained history could not be read or preserved; price and lower-plan conclusions are withheld.",
"plan_limit_usage_incomplete": "Some retained usage cannot be fully reconciled to dated responses; the recorded amount may be low.",
"plan_limit_unpriced_usage": "Some recorded tokens have no API price. They are unknown, not free; no lower-price conclusion is drawn.",
"plan_limit_multiple_source_groups": "Multiple local source groups do not prove one account. Their usage is not compared to one subscription.",
"plan_limit_plan_changed": "More than one plan appears in the retained logs. A single plan price cannot represent the whole period; limit counts start at the latest change.",
"plan_limit_meter_conflicting": "Conflicting quota history is withheld from period counts and lower-plan comparisons.",
"plan_limit_meter_incomplete": "Some quota samples lack usable dates or reset times. They cannot support a lower-plan comparison.",
"plan_limit_meter_stale": "The latest required quota sample is old or its reset has passed. Read again; no current lower-plan comparison is made.",
"plan_limit_meter_sparse": "A lower-plan comparison needs 14 observed UTC dates spanning at least 14 days, with no sample gap over two days. Sparse samples do not prove low usage.",
"plan_unreadable": "The saved plan choice could not be read (damaged, or from a newer PLER), so it was not overwritten.",
"plan_period": "Last 30 days, all projects. List prices of {date} in US dollars before tax; your bill can differ by region, tax and billing period. Only published limit ratios are used.",
"plan_note": "All selected source folders and all projects are included, independently of page filters. Complete account history is not established. PLER sees recorded coding-agent work; API prices do not establish subscription value. Quota observations cover the account, including use outside these agents.",
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
"field_tests": "Tests the agent ran",
"field_builds": "Builds the agent ran",
"check_detail": "{runs}; last visible run {last}; {passed} passed, {failed} failed, {hidden} not visible",
"check_last_passed": "passed",
"check_last_failed": "failed",
"check_last_none": "none",
"check_test_passed": "Tests: last run passed · {runs}",
"check_test_failed": "Tests: last run failed · {runs}",
"check_test_hidden": "Tests: result not visible · {runs}",
"check_build_passed": "Build: last run passed · {runs}",
"check_build_failed": "Build: last run failed · {runs}",
"check_build_hidden": "Build: result not visible · {runs}",
"check_note": "Tests and builds come from the agent's own commands and their exit codes; the command text is never stored. A result is not visible when the command passed its output on (for example to tail), ran in the background or kept going after the check.",
"detail_intro": "The record span is the time between the first and last event and includes waiting. Working time is shown only when the agent logged it.",
"models_in_session": "Models in this session",
"git_title": "Git during this session",
"git_scope": "Local Git events between this session's first and last record. Other people and agents may have been working at the same time; these events do not prove authorship. A commit still on a branch may have been undone by a later commit.",
"git_no_repo": "Neither this session's folder nor the files it edited are in an available local Git repository.",
"git_linked": "Repositories checked: {repos}. A repository counts when the session started in it or edited a file in it, so an agent started in a parent folder is still linked to the repository it changed.",
"git_outcome": "Commits recorded in this time: {kept} of {total} are still on a local or remote-tracking branch.",
"git_lines": "Lines its commits added that are still in place at HEAD: {share} ({kept} of {added}, measured in {commits}).",
"git_lines_unmeasured": " Not measurable: {n} (a merge, a first commit, a file too large or a commit outside HEAD's history).",
"git_lines_note": "Counted by content: a line moved within its file still counts, a rewritten or moved-file line does not. File contents are read only in memory.",
"lines_kept_row": "Code: {share} of {added} added lines still in place",
"git_outcome_off": "No longer on any branch: {n} (amended, rebased, reset or on a deleted branch). A rewritten commit can still carry the same change.",
"git_outcome_unknown": "Could not be checked: {n} (missing or borrowed objects, a shallow or very long history).",
"reedit_coverage": "Eligible selected sessions: {eligible} of {selected}. Later-session evidence uses all selected log folders: {timeline} of {total} sessions eligible, across agents and projects.",
"reedit_followup": "No later edit target observed after a full 7 days: {n}. This means no match was found in the available records.",
"reedit_cutoff": "Observed through {at}; read the logs again to update this observation.",
"reedit_excluded": "Why selected sessions could not be evaluated",
"reedit_archive_old_parser": "Older archived records",
"reedit_archive_unverified": "Unverified archived sources",
"reedit_uncertain_history": "Independent session history could not be verified",
"reedit_invalid_time": "Missing, invalid or future session times",
"reedit_missing_targets": "No usable absolute edit targets",
"reedit_matches": "Fastest observed pairs · up to 5",
"reedit_match_gap": "Session gap: {gap} · shared edit targets: {targets}",
"reedit_origin": "Earlier: {agent} · {code}",
"reedit_later": "Later: {agent} · {code}",
"reedit_tokens": "Recorded tokens for this whole session: {tokens}{partial}",
"reedit_partial": " · incomplete attribution or token records",
"reedit_outside": "Outside the current filters",
"reedit_subsecond": "less than 1 s",
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
"noun_run": [
"run",
"runs"
],
"noun_commit": [
"commit",
"commits"
],
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
"export_started": "Summary prepared. Check your saved downloads; if it did not start,",
"table_scroll_help": "Scroll sideways for more columns. With a keyboard, focus the table area and use the left and right arrows.",
"follow_title": "Changes to try · weekly follow-up",
"follow_scope": "Record a change to this work, then review two seven-day windows. Uses dated responses in all linked sessions, independently of the main filters. No new model calls.",
"follow_reload": "Reload follow-ups",
"follow_reload_hint": "Open or reload this section to read saved follow-ups.",
"follow_loading": "Reading saved follow-ups…",
"follow_failed": "Follow-ups could not be read. Reload this section.",
"follow_stale": "The source reading is older than five minutes. Read logs again with “Read logs again”, then reload this section before starting or reviewing. Drafts are kept.",
"follow_new": "Try a change",
"follow_trigger": "What prompted this?",
"follow_trigger_quota": "Quota pressure",
"follow_trigger_concentration": "Usage concentration",
"follow_trigger_session_pattern": "Session pattern",
"follow_trigger_other": "Other observation",
"follow_observation": "Your observation (optional)",
"follow_change": "What will you change?",
"follow_private": "Up to 1,000 characters per note. Private local records, included in private backups and excluded from normal reports. Deleting this work also deletes its follow-ups.",
"follow_start": "Save baseline and start",
"follow_caution": "A lower token count does not prove better results, saved money or reduced account quota. Logs may cover only part of a week. Compare the work's outcome separately.",
"follow_empty": "No changes tracked yet. Link the relevant sessions to this work, then record what you want to try.",
"follow_reading": "{since} → {until} (end excluded) · {sessions} sessions · {responses} responses · {tokens} tokens · {excluded} excluded · {missing} missing links",
"follow_before": "Before · saved baseline",
"follow_after": "After · saved review",
"follow_after_preview": "After · not saved yet",
"follow_status_open": "Change in progress",
"follow_status_reviewed": "Review recorded",
"follow_status_cancelled": "Follow-up cancelled",
"follow_reason": "Your reason: {reason}",
"follow_due": "Review from {date}. Link any new sessions belonging to this work before reviewing.",
"follow_wait": "The after window must finish and a fresh source reading must be available before reviewing. PLER records no automatic review.",
"follow_context": "Were the tasks and conditions comparable?",
"follow_context_unknown": "Not assessed",
"follow_context_similar": "Similar tasks and conditions",
"follow_context_different": "Different tasks or conditions",
"follow_context_saved": "Your context assessment: {context}",
"follow_review_note": "Review note (optional, up to 1,000 characters)",
"follow_review": "Save weekly review",
"follow_cancel": "Cancel follow-up, keep baseline",
"follow_delete": "Delete this follow-up",
"follow_delete_confirm": "Permanently delete this follow-up",
"follow_delete_warning": "This removes the baseline, review and notes from the local work record. Existing backup files keep their copies.",
"follow_keep": "Keep follow-up",
"follow_no_comparison": "No numeric comparison:",
"follow_metric": "Observed median of per-session tokens per response, within each agent/project/model group (minimum three sessions in each window). This is a descriptive difference, not a causal result.",
"follow_delta": "{agent} · project #{project} · {model}: {before} → {after} tokens/response ({percent})",
"follow_limit_missing_sessions": "Some linked sessions are missing from the source reading.",
"follow_limit_source_incomplete": "The source reading reports skipped files or archive loss.",
"follow_limit_incomplete_usage": "Some responses could not be dated and reconciled with complete session usage.",
"follow_limit_unknown_scope": "Some sessions have unknown project/model scope or use multiple models.",
"follow_limit_boundary_response": "Some response evidence crosses a window boundary.",
"follow_limit_measurement_limit": "The local measurement bound was reached.",
"follow_limit_baseline_changed": "The original baseline can no longer be reproduced from the current linked sources.",
"follow_limit_parser_changed": "The measurement parser changed after the baseline.",
"follow_limit_context_unknown": "Comparable tasks and conditions have not been confirmed by you.",
"follow_limit_context_different": "You marked the tasks or conditions as different.",
"follow_limit_cohort_changed": "The agent/project/model groups differ between the windows.",
"follow_limit_small_sample": "Each group needs at least three sessions in both windows.",
"follow_limit_zero_baseline": "A baseline group has zero tokens per response.",
"follow_limit_duplicate_sessions": "Duplicate session identities make the source reading ambiguous.",
"follow_minimum": "For a numeric review, each identical agent/project/model group needs at least three sessions in both windows and your assessment of similar tasks. You can still record an unresolved review."
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
"export": "JSON indir ↓",
"help": "Yardım",
"mask_projects": "JSON içinde proje adlarını gizle",
"mask_projects_note": "Zamanlar, modeller ve oturum kodları kalır; dosya anonim değildir.",
"quality_show": "Etkilenen oturumları göster ({n})",
"coverage_title": "Bu kayıtları karşılaştırmadan önce",
"coverage_scope": "Dosya erişimi uyarıları seçili kayıt klasörlerinin tamamını kapsar. Oturum ve fiyat kapsamı ana filtrelere uyar.",
"coverage_boundary": "PLER, ilk okumasından önce kayıt silinip silinmediğini bilemez. Hiç okumadığı kayıtları geri getiremez. Başarılı okuma, hesap geçmişinin eksiksiz olduğunu kanıtlamaz.",
"coverage_help": "Kayıtları kontrol etme ve kurtarma rehberi",
"coverage_details": "Kayıtlı veri kalitesi nedenleri",
"coverage_next": "Sonraki adım: ",
"coverage_wsl_unavailable_title": "WSL kayıtlarına erişilemiyor",
"coverage_wsl_unavailable_impact": "Erişilemeyen dağıtımın kullanımı eksik olabilir. Daha küçük toplam, kullanımın azaldığını göstermez.",
"coverage_wsl_unavailable_next": "Seçili dağıtımı kendin aç, kayıt klasörünün erişilebilir olduğunu kontrol et ve Kayıtları yenile'yi seç. PLER, WSL'yi başlatmaz.",
"coverage_read_limits_title": "Okuma bir güvenlik sınırında durdu",
"coverage_read_limits_impact": "Bazı kayıtlar dışarıda kaldı. Toplamlar ve karşılaştırmalar seçili kaynağın tamamını kapsamaz.",
"coverage_read_limits_next": "Daha az kaynak klasörü seçmek veya aşırı büyük kayıtları ele almak için Yardım'a bak. Sayfa filtrelerini değiştirmek veya önbelleği yeniden kurmak okuma sınırlarını kaldırmaz.",
"coverage_unsafe_path_title": "Bir kaynak yolu dışarıda bırakıldı",
"coverage_unsafe_path_impact": "Engellenen ağ yolları veya kayıt klasörü içindeki bağlantılar, bazı kayıtları toplamların dışında bırakabilir.",
"coverage_unsafe_path_next": "Desteklenen yerel kaynak klasörünü veya açıkça seçilmiş WSL klasörünü kullan. Yardım'daki kaynak seçimini kontrol et; yol korumalarını kapatma.",
"coverage_source_missing_title": "Bir kaynak okuma sırasında kayboldu",
"coverage_source_missing_impact": "Erişilebilen kayıtlar gösteriliyor; ancak bu okuma eksik olabilir.",
"coverage_source_missing_next": "Ajanın dosyayı taşıyıp taşımadığını veya silip silmediğini kontrol et ve kayıtları yenile. Kayıp asıllar için mevcut bir kopya veya denetlenmiş PLER yedeği gerekir; tekrar denemek onları yeniden oluşturmaz.",
"coverage_invalid_records_title": "Bazı kayıtlar yorumlanamadı",
"coverage_invalid_records_impact": "Doğrulanan kullanım dahil edildi; bozuk, yarım veya tutarsız kayıtlar toplamları eksik bırakabilir.",
"coverage_invalid_records_next": "Ajanın yazması bittikten sonra kayıtları yenile. Uyarı sürerse asıl dosyaları koru ve Yardım'a bak. Uyarıyı kaldırmak için kayıtları düzenleme veya arşivi temizleme.",
"coverage_source_access_title": "Bazı kaynak dosyalar veya klasörler okunamadı",
"coverage_source_access_impact": "Görünen toplamların dışında kalan kayıtlar olabilir. Bu, o kayıtların silindiğini kanıtlamaz.",
"coverage_source_access_next": "Seçili klasörleri ve okuma iznini kontrol et, ardından kayıtları yenile. Önbelleği yeniden kurmak klasör erişimini düzeltmez. Sorunu araştırırken mevcut geçmişi koru.",
"coverage_archive_old_parser_title": "Bazı geçmiş kayıtlar eski okuyucuyla okunmuş",
"coverage_archive_old_parser_impact": "Asıl kaynak erişilemezken saklanan yorum güncel okuyucuyla doğrulanamaz. Bu, doğrulanmış güncel bir ölçüm değildir.",
"coverage_archive_old_parser_next": "Asıl kayıtlar duruyorsa seçili kaynakta erişilebilir hale getir ve yeniden oku. Yoksa arşivi koru; önbelleği yeniden kurmak eksik asılları getiremez veya yorumlarını güncelleyemez.",
"coverage_archive_unverified_title": "Kontrol edilemeyen kaynakların yerine saklanan geçmiş gösteriliyor",
"coverage_archive_unverified_impact": "PLER önceki üst veriyi gösteriyor. Kaynağın güncel içeriği ve silinip silinmediği doğrulanmadı.",
"coverage_archive_unverified_next": "Seçili kaynağa erişimi düzelt ve kayıtları yenile. Erişim sağlanamıyorsa bu geçmişi doğrulanmamış olarak koru; arşivi temizleme.",
"coverage_archive_loss_title": "Saklanan geçmişin bir kısmı eksik olabilir",
"coverage_archive_loss_impact": "Arşiv sınırları veya arşiv okuma/yazma hatası geçmiş kapsamını eksik bırakabilir. Daha küçük toplam, tasarruf göstermez.",
"coverage_archive_loss_next": "Mevcut veriyi koru. Erişilebilen asılları yeniden oku veya eski özel yedeği denetleyip Yardım'daki adımlarla yeni klasöre kurtar. Arşivi temizlemek kayıp geçmişi onarmaz.",
"coverage_retained_history_title": "Bazı asıllar silinmiş; saklanan üst veri duruyor",
"coverage_retained_history_impact": "Önceden saklanan değerler özgün tarihleri ve kalite sınırlarıyla dahil edildi. Bunlar eksiksiz hesap geçmişini veya güncel kotayı kanıtlamaz.",
"coverage_retained_history_next": "Yerel veriyi kaldırmadan önce bu geçmişi yedekle. Yeniden okuma veya önbelleği yeniden kurma silinen asılları oluşturamaz. PLER arşivini koru.",
"coverage_incomplete_usage_title": "Bazı oturum sayımları eksik",
"coverage_incomplete_usage_impact": "Bilinen değerler incelenebilir; eksik veya uzlaştırılamayan kullanım tam karşılaştırmayı engeller. Tek başına daha küçük toplam, verimliliğin arttığını kanıtlamaz.",
"coverage_incomplete_usage_next": "Etkilenen oturumları ve kayıtlı veri kalitesi nedenlerini aç. Yeniden okuma yarım kayıtlara yardımcı olabilir; eski biçimler veya belirsiz geçmişler bilinmiyor olarak kalabilir.",
"coverage_uncertain_attribution_title": "Bazı kullanımın dağılımı güvenilir değil",
"coverage_uncertain_attribution_impact": "Oturum, proje veya model dağılımı belirsiz olabilir. Bu dağılımlarla işleri sıralama veya maliyetlerini belirleme.",
"coverage_uncertain_attribution_next": "Etkilenen oturumları incele. Bir işe ad vermek veya oturum bağlamak eksik kaynak eşleştirmesini düzeltmez; dayanağı olmayan karşılaştırmayı açık bırak.",
"coverage_unpriced_usage_title": "Kullanımın bir kısmının API fiyatı yok",
"coverage_unpriced_usage_impact": "API fiyat karşılığı yalnız fiyatlanabilen kayıtları kapsar. Fiyatlanamayan kullanım ücretsiz değil, bilinmiyor; gösterilen tutar abonelik faturası değildir.",
"coverage_unpriced_usage_next": "Tutarları karşılaştırmadan önce fiyatlanan payı ve model adlarını kontrol et. Eksik model veya fiyat bilgisi önbelleği yeniden kurarak tamamlanamaz.",
"quality_only": "Yalnız veri kalitesi sınırlı oturumlar",
"quality_clear": "Seçili oturumların tümünü göster",
"quality_filter_note": "Bu liste filtresi toplamları ve JSON kapsamını değiştirmez.",
"reedit_brief": "Değerlendirilebilen {eligible} önceki oturumdan {matched} tanesi eşleşti; eşleşmeyen {pending} oturum takip bekliyor. Değerlendirilemeyen: {excluded}.",
"reedit_caution": "Hedef kaydı tamamlanmış değişikliği, israfı veya kaliteyi kanıtlamaz. Tokenlar bütün oturuma aittir.",
"reedit_method": "Kapsam, yöntem ve sınırlar",
"open_outside": "Bu oturumu filtrelerin dışında bul",
"quota_ambiguous": "Kota geçmişi çelişkili. Güncel yüzde ve tahmin bilinmiyor. Kişisel/iş profillerinin sayaçlarını ayırarak inceleyin.",
"quota_multiple_sources": "Birden fazla yerel kaynak grubu geçmiş sağlıyor. Ortak hesap doğrulanamadığı için güncel yüzde ve tahmin bilinmiyor. Tek kaynak grubu seçin.",
"metadata_settings": "Yerel geçmiş ve okuma önbelleği",
"backup_title": "Geçmişi yedekle ve kurtar",
"backup_scope": "Saklanan tüm geçmişi, değerlendirmeleri, iş başlıklarını, hedefleri, sonuç notlarını ve bağlantılarını, saklama tercihini ve Claude kota örneklerini yedekler. Ana filtreler ve proje adlarını gizleme seçeneği uygulanmaz. Kaynak kayıtlar ve yeniden kurulabilir önbellekler dahil değildir.",
"backup_privacy": "Dosya özel yollar, kimlikler ve girdiğiniz iş ayrıntılarını içerir. Şifreli değildir ve anonim bir rapor değildir. Güvenli yerde saklayın.",
"backup_download": "Özel yedek indir",
"backup_preparing": "Yedek hazırlanıyor…",
"backup_prepared": "Yedek hazır. İndirilen dosyaları kontrol edin; başlamadıysa",
"backup_file": "Kontrol edilecek yedek dosyası",
"backup_check": "Yedeği kontrol et",
"backup_checking": "Yedek kontrol ediliyor…",
"backup_check_help": "Kontrol, bu dosyayı yalnız bu bilgisayardaki PLER'e gönderir, bellekte tutar; geçmişi geri yüklemez veya değiştirmez.",
"backup_guide": "Yeni klasöre geri yükleme adımları",
"backup_invalid_file": "Desteklenen boyut sınırı içinde, boş olmayan bir PLER yedeği seçin.",
"backup_checked": "Yedek doğrulandı: PLER {version}, {date}; {files} arşiv kaynağı, {verdicts} değerlendirme, {works} iş başlığı, {links} iş bağlantısı ve {quota} kota örneği. Kayıtlı tercih: {retention}. Geçmiş geri yüklenmedi veya değiştirilmedi.",
"work_eyebrow": "Oturumlar ve ajanlar arasında",
"work_title": "İşlerim",
"work_outcome_title": "Hedef ve sonuç",
"work_outcome_scope": "Girdin, filtrelerden bağımsız olarak işin tamamına aittir. PLER test, Git veya kullanımdan tamamlanma ya da kalite sonucu çıkarmaz.",
"work_goal_label": "Hedeflenen sonuç",
"work_outcome_label": "Senin sonucun",
"work_result_label": "Sonuç veya kalan iş",
"work_goal_empty": "Hedef kaydedilmedi.",
"work_goal_view": "Hedef: {text}",
"work_result_view": "Sonuç / kalan iş: {text}",
"work_outcome_view": "Senin sonucun: {outcome}",
"work_outcome_not_recorded": "Değerlendirilmedi",
"work_outcome_partial": "Kısmen tamamlandı",
"work_outcome_completed": "Tamamlandı",
"work_outcome_not_completed": "Tamamlanmadı",
"work_outcome_time": "Sonuç son kaydedildi: {at}. Bu, giriş zamanıdır; ölçülmüş bitiş zamanı değildir.",
"work_details_edit": "Hedefi ve sonucu düzenle",
"work_details_help": "Hedef ve sonuç notları isteğe bağlıdır; her biri en fazla 1.000 karakter olabilir. Bunlar özel kullanıcı girdileridir; normal JSON raporuna girmez, özel yedeğe dahildir. Dil değiştirirken taslaklar bu pencerede korunur.",
"work_details_save": "Hedefi ve sonucu kaydet",
"work_details_saved": "Hedef ve sonuç kaydedildi.",
"work_details_unsaved": "Kaydedilmemiş hedef veya sonuç değişikliği var.",
"work_details_current": "Kaydedilmemiş değişiklik yok.",
"work_details_invalid": "Her metin alanında en fazla 1.000 karakter kullan; satır sonu dışında kontrol karakteri kullanma.",
"work_details_conflict": "Kayıtlı bilgiler başka pencerede değişti. Taslağın korundu; kaydetmeden önce son kayıtlı sürümü incele.",
"work_details_latest": "Son kayıtlı sürüm",
"work_details_review": "Taslağın formda duruyor. Sonraki kayıt için taslağını korumadan veya kayıtlı sürümü kullanmadan önce aşağıdaki bilgileri incele. İki seçim de değişiklik kaydetmez.",
"work_details_keep": "Sonraki kayıt için taslağımı koru",
"work_details_discard": "Taslağı bırak, kayıtlı sürümü kullan",
"work_observations_title": "Kayıtlı gözlemler",
"work_observations_scope": "Ana filtreleri izler ve bağlı oturumların tamamını kapsar. Test/derleme sayıları her oturumun görünen son sonucudur; Git etkinliği zaman eşleşmesidir. İşin hedefe ulaştığını kanıtlamaz.",
"work_obs_none": "Ana filtrelerde bağlı oturum yok. Gözlemleri incelemek için seçimi genişlet.",
"work_obs_unavailable": "Gözlem özeti kullanılamıyor. Mevcut dayanakları incelemek için bağlı oturum ayrıntılarını aç.",
"work_obs_test": "Testler",
"work_obs_build": "Derlemeler",
"work_obs_checks": "{kind}: görünen son sonuç {passed} oturumda geçti, {failed} oturumda başarısız, {unknown} oturumda bilinmiyor.",
"work_obs_no_checks": "{kind}: seçili oturumlarda kontrol kaydı yok.",
"work_obs_git": "Git geçmişi {available} seçili oturumda okunabilir; {active} oturumda aynı zamana denk gelen etkinlik var. {limited} oturumda kapsam sınırlı.",
"work_obs_git_unknown": "Seçili oturumlar için okunabilir Git gözlemi yok; etkinlik bilinmiyor.",
"work_intro": "Bir işe ad verin; ardından oturum ayrıntılarından o işe ait Claude ve Codex oturumlarını bağlayın.",
"work_unreadable": "Kayıtlı işler okunamadı. Onları korumak için düzenleme kapatıldı. Doğrulanmış özel bir yedeği yeni klasöre geri yükleyin; Yardım bölümüne bakın.",
"work_empty": "Henüz iş grubu yok. Bir işe ait oturumları toplamak için iş oluşturun.",
"work_new_title": "Yeni iş başlığı",
"work_placeholder": "Örneğin: ilk sürümü hazırlama",
"work_create": "İş oluştur",
"work_choose": "İş seçin",
"work_edit_title": "İş başlığı",
"work_rename": "Başlığı kaydet",
"work_delete": "İşi sil…",
"work_summary": "{works} iş · Bu seçimde birer kez sayılan {selected} bağlı oturum · {unassigned} bağlanmamış oturum. Ana filtrelerin dışında {outside} bağlı oturum · {missing} erişilemeyen oturum · Birden fazla işe bağlı {overlap} seçili oturum.",
"work_union": "Bağlı oturum özeti: {tokens} bilinen token · {calls} kayıtlı çağrı · {api} API fiyat karşılığı.",
"work_counts": "{linked} bağlı oturum: {available} erişilebilir, {selected} ana filtrelerde, {outside} ana filtrelerin dışında ve {missing} erişilemeyen. {overlap} seçili oturum başka işlere de bağlı.",
"work_usage": "Seçili bağlı oturumlar: {tokens} bilinen token · {calls} kayıtlı çağrı · {api} API fiyat karşılığı.",
"work_no_selection": "Ana filtrelerde bu işe bağlı oturum yok. Bu iş için kullanım toplamı gösterilmiyor.",
"work_quality": "Bazı seçili oturumların kullanım veya kaynak eşleştirmesi eksik. Bunlar bilinen kayıtlı değerlerdir; tam bir ölçüm değildir.",
"work_more": "Daha fazla bağlı oturum göster ({n})",
"work_no_members": "Bu işe ait çalışmaları toplamak için Oturumlar bölümünden oturum ekleyin.",
"work_scope": "Kullanım ana filtreleri izler ve tek bir değişikliğin maliyetini değil, oturumların tamamını kapsar. Arama ve veri kalitesi liste filtreleri bu kapsamı değiştirmez. Bir oturum birden fazla işe bağlanabilir; iş toplamları birbiriyle toplanamaz. Özet, her bağlı oturumu bir kez sayar.",
"work_api_note": "API fiyat karşılıkları mevcut fiyatları kullanır; fiyatı bilinmeyen kullanım dahil edilmeyebilir. Bunlar abonelik faturanız değildir.",
"work_links_privacy": "Bu bağlantıların gizliliği",
"work_privacy": "Başlıklar, hedefler, sonuç notları ve bağlantılar bu bilgisayarda kalır; normal JSON özetlerine eklenmez. Özel yedeklere dahildir. Erişilemeyen oturumlar kayıtlı kodlarıyla bağlı kalır; PLER otomatik olarak başka bir oturuma bağlamaz.",
"work_outside": "Ana filtrelerin dışında",
"work_missing": "Oturuma erişilemiyor",
"work_unlink": "Bağlantıyı kaldır",
"work_unlink_label": "{title} işinden #{code} oturumunun bağlantısını kaldır",
"work_delete_heading": "Bu iş silinsin mi?",
"work_delete_help": "Bu işin başlığı, hedefi, sonuç notları ve oturum bağlantıları silinir. Oturum kayıtları, kullanım değerleri, değerlendirmeler ve eski yedekler korunur.",
"work_cancel": "İşi koru",
"work_delete_confirm": "İşi ve bağlantılarını sil",
"work_link": "İşe bağla",
"work_link_choose": "Bağlanacak işi seçin",
"work_linked_none": "Bu oturum henüz hiçbir işe bağlı değil.",
"work_create_link": "Oluştur ve bağla",
"work_session_note": "Bu oturumun tamamını bir veya daha fazla işe bağlayın. Genel toplamlarda kullanımı bir kez sayılır.",
"work_title_invalid": "Kontrol karakteri içermeyen, 1–120 karakterlik bir başlık girin.",
"work_failed": "İş kaydedilemedi. Önceki başlık ve bağlantılar görünmeye devam ediyor.",
"work_saved": "İş kaydedildi.",
"work_saved_refresh": "İş kaydedildi ancak görünüm yenilenemedi. Yeni bir değişiklikten önce görünümü yeniden okuyun.",
"work_saving": "Kaydediliyor…",
"work_reload": "Kayıtlı işleri yeniden yükle",
"work_unpriced": "Fiyatlanamadı",
"work_api_covered": "{amount} (tokenların {share} kadarı fiyatlandı)",
"retention_label": "Kaynak kayıtlar kaybolunca üst bilgiyi sakla",
"retention_on": "Geçmiş saklama açık. Arşiv: {bytes}; en fazla {days} görülmeyen gün, {files} dosya ve {limit}.",
"retention_off": "Geçmiş saklama kapalı. Mevcut arşiv ({bytes}) korunuyor; yüklenmiyor veya güncellenmiyor.",
"retention_help": "Yerel arşiv kimlikleri, proje/düzenleme yollarını, modelleri ve sayıları içerir; istek ve yanıt içermez. Saklamayı kapatmak arşivi korur; silmek saklanan geçmişi kaldırır.",
"cache_reset": "Okuma önbelleğini yeniden kur",
"cache_reset_help": "Yalnız yeniden kurulabilir önbellekler (kayıt okuyucuları ve kod sayımları) sıfırlanır. Arşiv, kota örnekleri ve tercihler korunur; sonraki okuma daha uzun sürebilir.",
"cache_reset_done": "Okuma önbellekleri sıfırlandı; saklanan geçmiş korundu. Kayıtlar yeniden okunuyor.",
"retention_changed": "Geçmiş saklama tercihi kaydedildi. Seçili kaynaklar yeniden okunuyor.",
"retention_short_on": "saklama açık",
"retention_short_off": "saklama kapalı",
"quality_session": "Veri kalitesi sınırlı",
"dated_title": "Dönem içindeki tarihli kullanım kayıtları",
"dated_result": "{tokens} token · {calls} kayıtlı yanıt · katkı veren {sessions} oturum",
"dated_coverage": "Uygun saklanan oturum: {selected} içinden {eligible}. Kullanımı tarihe dağıtılamayan oturum: {unallocated}.",
"dated_scope": "Yalnız kayıtlı zamanlarının hepsi bu aralıkta olan uzlaştırılmış yanıtlar sayılır. Birikimli, tarihsiz ve belirsiz kullanım günlere dağıtılmaz. Hesabın eksiksiz toplamı değildir.",
"dated_interval": "{since} ile {cutoff} arası. Kayıtlar yeniden okunana kadar gözlem sonu sabittir.",
"dated_all": "tüm tarihli kayıtlar",
"dated_exclusions": "Kapsam ayrıntıları",
"dated_undated": "Tarihsiz yanıt: {undated}; dışlanan gelecek tarihli yanıt: {future}; dönemden önceki yanıt: {outside}.",
"dated_incomplete_usage": "Eksik oturum kullanımı",
"dated_unverified_attribution": "Doğrulanamayan atıf",
"dated_missing_event_evidence": "Doğrulanmış yanıt zamanı yok",
"version_label": "Sürüm {version}",
"archive_clear": "PLER arşivini sil",
"archive_clearing": "Arşiv temizleniyor…",
"archive_clear_help": "Tüm PLER arşivi temizlenir. Ajan kayıtları değişmez; silinmiş kaynakların kopyaları geri alınamaz.",
"archive_summary": "PLER arşivinden veri içeren seçili oturum: {n}.",
"archive_disabled": "PLER arşivi kullanılamıyor; güvenli bir yerel önbellek klasörü gerekir.",
"archive_cleared": "PLER arşivi temizlendi. Kalan kaynak kayıtları yeniden okunuyor.",
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
"search_placeholder": "Oturum adı, proje veya model",
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
"th_verdict": "İşe yaradı mı?",
"verdict_useful": "İşe yaradı",
"verdict_wasted": "Boşa gitti",
"verdict_group": "#{code} oturumu için değerlendirmen",
"field_verdict": "Değerlendirmen",
"verdict_summary": "Bu seçimde değerlendirmelerin: {useful} işe yaradı ({useful_tokens} token, liste fiyatıyla {useful_usd}) · {wasted} boşa gitti ({wasted_tokens} token, {wasted_usd}) · {none} değerlendirilmedi. Yalnız bu bilgisayarda saklanır; kaldırmak için basılı düğmeye yeniden tıkla.",
"verdict_hint": "Oturumları tek tıkla “İşe yaradı” ya da “Boşa gitti” diye işaretle; PLER boşa gidenlerin neye mal olduğunu gösterir. Yalnız bu bilgisayarda saklanır, hiçbir yere gönderilmez.",
"verdict_demo": " Demo değerlendirmeleri yalnız bu sayfa açıkken tutulur.",
"verdict_unreadable": "Kayıtlı değerlendirmeler dosyası okunamadı (bozuk ya da daha yeni bir PLER sürümünden); oturumlar değerlendirilmemiş görünür ve dosyanın üzerine yazılmaz.",
"session_work_link": "Bir işe bağla",
"session_work_another": "Başka bir işe bağla",
"session_work_mode": "İş bağlantısı türü",
"session_work_existing": "Mevcut işe bağla",
"session_work_new": "Yeni iş oluştur",
"account_limits": "Hesap kotaları",
"account_limit_warning": "Hesap kotası uyarısı",
"usage_alert": "Kullanım uyarısı",
"usage_alerts": "Kullanım uyarıları",
"search_empty": "Aramana uyan oturum yok.",
"search_clear": "Aramayı temizle",
"more": "Daha fazla oturum göster",
"more_count": "Daha fazla oturum göster ({count})",
"empty_title": "Bu seçimde oturum bulunamadı.",
"empty_no_logs_title": "Yerel ajan kaydı bulunamadı.",
"empty_no_logs_text": "PLER bu bilgisayardaki Claude Code ve Codex kayıtlarını okur. Bu ajanlardan birini kullandıktan sonra kayıtları yeniden oku. Claude masaüstündeki normal sohbetler dahil değildir.",
"empty_text": "Filtreleri genişlet veya ajanını kullandıktan sonra kayıtları yeniden oku.",
"empty_unreadable": "Bazı ajan kayıtları tamamen okunamadı. Kayıtları ve klasör erişimini kontrol edip yeniden oku. Gösterilebilen veri eksik.",
"empty_unreadable_title": "Seçili kayıtlar tam okunamadı.",
"filter_clear": "Tüm oturumları göster",
"footer_privacy": "İstek, yanıt, komut ve araç çıktısı bu ekrana alınmaz.",
"footer_local": "Model çağrısı yok · Ajan verisi bu bilgisayarda kalır",
"dialog_title": "Oturum ayrıntısı",
"dialog_close": "Oturum ayrıntısını kapat",
"unknown": "Bilinmiyor",
"not_logged": "Kayıtta yok",
"err_unreachable": "PLER’e ulaşılamıyor. Uygulamanın açık olduğunu kontrol edip yeniden dene.",
"err_closed": "PLER kapalı görünüyor. Yeniden açmak için pler komutunu çalıştırın.",
"err_read": "Kayıt okunamadı. Sayfayı yenileyin.",
"closed": "PLER kapandı. Yeniden kullanmak için PLER'i açın (Windows taşınabilir paket: PLER.exe).",
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
"demo_banner": "Demo verileri: kayıtlar ve projeler örnektir. Kendi kayıtların okunmaz. Demo işleri geçicidir.",
"unreadable_coverage": "{files} tamamen okunamadı. Doğrulanabilen kayıtlar dahil; toplamlar eksik olabilir. ",
"all_read": "Bulunan kaynakların okunabilen kayıtları kullanıldı. Bu, hesap geçmişinin eksiksiz olduğunu kanıtlamaz.",
"cross_period": " {sessions} seçilen dönemden önce başlamış; tüm oturum toplamı dahil.",
"status_unreadable": " · {files} tam okunamadı; toplamlar eksik olabilir",
"unknown_calls": " {sessions} için çağrı ayrımı tam değil; çağrı sayısı yalnız bilinen kayıtlardır.",
"stat_total": "Toplam token",
"stat_total_note": "{share} kadarı önbellekten yeniden okunan bağlam",
"stat_fresh": "Önbellek dışı token",
"stat_fresh_note": "Yeni girdi, önbelleğe yazılan ve çıktı",
"stat_sessions": "Oturum",
"stat_calls": "Kayıtlı model çağrısı",
"stat_api": "API fiyat karşılığı",
"stat_api_note": "Kayıtlı yanıtlar, {date} standart fiyatlarıyla. Faturan değildir: abonelik sabit ücretlidir.",
"stat_api_partial": "Tokenların {share} kadarını kapsar; kalanı fiyatlanamadı. {date} standart fiyatları; faturan değildir.",
"field_api": "API fiyat karşılığı",
"tokens": "{n} token",
"agent_note": "{sessions} · {calls} · girdinin {share} kadarı önbellekten · {errors} · {aborted}",
"insights_eyebrow": "Durumun",
"insights_title": "Kayıtların sana ne söylüyor?",
"inspect_session": "Bu oturumu incele →",
"insights_note": "Bunlar senin kayıtlarındaki gözlemler; kontrollü bir deney sonucu değil. Her birinin dayanağı yanındaki sayılardır.",
"out_reset": "Son kayıtta {used} doluydu; pencere {reset} sıfırlandı. Şu anki doluluk, ajan yeniden çalışınca kayda geçer.",
"out_full": "Dolu. Sıfırlanma: {reset}.",
"quota_alert_full": "{agent}: {window} sınır doldu. Sıfırlanma: {reset}.",
"quota_alert_soon": "{agent}: bu hızla {window} sınır {full} civarında, {left} sonra dolar. Sıfırlanma: {reset}.",
"quota_alert_title": "PLER hesap kotası uyarısı",
"live_watch": "Hesap kotalarını izle",
"live_watch_help": "Bu sayfa açıkken PLER kayıtları 5 dakikada bir yeniden okur ve bir sınır bir saat içinde (haftalık sınırda bir gün içinde) dolacaksa uyarır. Her okuma biraz işlemci zamanı kullanır; seçim pencere açıkken hatırlanır.",
"live_notify_on": "Masaüstü bildirimlerini aç",
"live_notify_off": "Masaüstü bildirimlerini kapat",
"live_notify_active": "Yeni uyarılar için masaüstü bildirimleri açık.",
"live_notify_blocked": "Bu pencerede bildirimler kullanılamıyor; uyarı yine burada görünür.",
"live_notify_unsupported": "Burada bildirimler kullanılamıyor; uyarı yine sayfada görünür.",
"pace_hour": "bu penceredeki çalışma hızıyla (saatte {rate})",
"pace_day": "son {days} günün ortalamasıyla (günde {rate})",
"out_fills": "Uyarı: {pace} {full} civarı dolar; sıfırlanma {reset}.",
"out_lasts": "{pace} sıfırlanmadan ({reset}) dolmaz.",
"out_nopace": "Sıfırlanma: {reset}. Hız tahmini için henüz yeterli kayıt yok.",
"out_plan_changed": " Kayıtlı plan {at} tarihinde değişti; yalnız sonraki kayıtlar kullanılıyor.",
"out_stale": "Son ölçümde {used} kullanılmıştı. Ölçüm, güncel doluluk veya tahmin için eski; ajan çalıştıktan sonra kayıtları yeniden oku.",
"out_historical": "Kayıtta {used} kullanılmıştı. Sıfırlanma zamanı eksik olduğu için güncel doluluk bilinmiyor.",
"quota_eyebrow": "Hesap kotası",
"quota_title": "Hesap kotaları ve tahminler",
"plans_eyebrow": "Abonelik",
"plans_title": "Kayıtlı kullanım ve plan fiyatları",
"plan_choose_label": "Claude planın",
"plan_choice_none": "Seçilmedi",
"plan_choice_pro": "Pro (ayda 20 $)",
"plan_choice_max": "Max (ayda 100 $)",
"plan_choice_ultra": "Ultra (ayda 200 $)",
"plan_choice_api": "API anahtarı, plan yok",
"plan_named": "{name}, liste fiyatı ayda {price} $",
"plan_api_key": "API anahtarı, plan yok",
"plan_unchosen": "plan seçilmedi",
"plan_unlogged": "plan kayıtlarda yok",
"plan_api_line": "Kayıtlı tarihli yanıtların API fiyat karşılığı: {usd} (tokenlarının {share} kadarı fiyatlandı).",
"plan_api_unknown": "Bu dönemde fiyatlanabilen yanıtlardan API fiyat karşılığı hesaplanamıyor. Eksik veya fiyatlanamayan kayıtlar ücretsiz değil, bilinmiyor.",
"plan_partial": " Saklanan kullanımın tamamı tarihlenemedi veya doğrulanamadı; toplam düşük olabilir.",
"plan_meter_line": "Yüzde 100 gözlenen: örnek alınan {five_total} beş saatlik sıfırlama döneminin {five} tanesi, {week_total} haftalık dönemin {week} tanesi. Gözlenmeyen tepe değerler bilinmiyor.",
"plan_choose_plan": "Bu kullanımla karşılaştırmak için Claude planını seç. Seçim yalnız bu bilgisayarda saklanır.",
"plan_no_meter": "Kullanılabilir Claude Code kota örneği bulunamadı. Terminal Claude Code için isteğe bağlı PLER durum satırı örnek kaydedebilir (pler statusline --install). Bu, masaüstü kota desteği sağlamaz.",
"plan_no_meter_codex": "Kullanılabilir Codex kota örneği bulunamadı. Codex'i kullandıktan sonra kayıtları yenile; kayıtlarında desteklenen ölçer yoksa kalan kota bilinmiyor olarak kalır.",
"plan_larger_ratio_unpublished": "PLER'de bu planlar için doğrulanmış sınır oranı yok; yeterli olacak planı belirleyemez. Sağlayıcının güncel sınırlarını, kredileri ve API seçeneklerini incele.",
"plan_larger_need_unseen": "Gözlenen sınıra dayanma, gereken kapasiteyi belirlemez. Büyük planın yeteceği kanıtlanmıyor; modele özel sınırlar ve ücretli ek kullanım ayrıca incelenmeli.",
"plan_api_below_list_price": "Kayıtlı API fiyat karşılığı {usd}, aylık liste fiyatı {price} altında. Bu, geçişte tasarrufu veya aboneliğin değerini kanıtlamaz.",
"plan_lower_observed": "Bu örneklerin {current} planında alındığı varsayımıyla gözlenen tepe {peak}; {smaller} (liste fiyatı ayda {price}) yayımlanmış sınırların {share} kadarını sağlar. Bu, küçük planın yeteceğini kanıtlamaz.",
"plan_lower_weekly_observed": "Bu örneklerin {current} planında alındığı varsayımıyla haftalık gözlenen tepe {peak}; {smaller} (liste fiyatı ayda {price}) yayımlanmış haftalık sınırın {share} kadarını sağlar. Beş saatlik karşılaştırma ve genel plan yeterliliği doğrulanmadı.",
"plan_comparison_expired": "Bu karşılaştırmanın kota kanıtı eskidi veya sıfırlama zamanı geçti. Güncel plan sınırlarını karşılaştırmadan önce kayıtları yenile.",
"plan_payment_unknown": "Gerçek ödeme kayıtlı değil. Plan adları ve liste fiyatları faturayı, kredileri, indirimleri, ek kullanımı veya geçmiş plan değişimlerini doğrulamaz.",
"plan_interval": "{since} ile {until} arasındaki tarihli yanıtlar (UTC).",
"plan_limit_source_incomplete": "Bazı kaynaklar veya saklanan geçmiş okunamadı ya da korunamadı; fiyat ve küçük plan sonuçları gösterilmiyor.",
"plan_limit_usage_incomplete": "Saklanan kullanımın bir kısmı tarihli yanıtlarla tam uzlaştırılamıyor; kayıtlı tutar düşük olabilir.",
"plan_limit_unpriced_usage": "Bazı kayıtlı tokenların API fiyatı yok. Ücretsiz değil, bilinmiyor; daha düşük fiyat sonucu çıkarılmıyor.",
"plan_limit_multiple_source_groups": "Birden fazla yerel kaynak grubu tek hesabı kanıtlamaz. Kullanımları tek abonelikle karşılaştırılmıyor.",
"plan_limit_plan_changed": "Saklanan kayıtlarda birden fazla plan var. Tek bir plan fiyatı bütün dönemi temsil edemez; sınır sayımları son değişimden başlar.",
"plan_limit_meter_conflicting": "Çelişen kota geçmişi dönem sayımlarından ve küçük plan karşılaştırmasından çıkarıldı.",
"plan_limit_meter_incomplete": "Bazı kota örneklerinin tarihi veya sıfırlama zamanı kullanılamıyor. Küçük plan karşılaştırmasını destekleyemez.",
"plan_limit_meter_stale": "Gerekli son kota örneği eski veya sıfırlama zamanı geçti. Yeniden oku; güncel küçük plan karşılaştırması yapılmıyor.",
"plan_limit_meter_sparse": "Küçük plan karşılaştırması için en az 14 güne yayılan 14 ayrı UTC gününde gözlem ve en fazla iki günlük örnek aralığı gerekir. Seyrek örnekler düşük kullanımı kanıtlamaz.",
"plan_unreadable": "Kayıtlı plan seçimi okunamadı (bozuk ya da daha yeni bir PLER sürümünden); bu yüzden üzerine yazılmadı.",
"plan_period": "Son 30 gün, bütün projeler. {date} liste fiyatları, vergi hariç ABD doları; faturan bölgeye, vergiye ve ödeme dönemine göre değişebilir. Yalnız yayımlanmış sınır oranları kullanılır.",
"plan_note": "Sayfa filtrelerinden bağımsız olarak seçili kaynak klasörlerinin ve projelerin tamamı dahil. Eksiksiz hesap geçmişi kanıtlanmıyor. PLER kayıtlı kodlama ajanı işini görür; API fiyatları aboneliğin değerini belirlemez. Kota gözlemleri bu ajanlar dışındaki kullanımla birlikte hesap genelini kapsar.",
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
"field_tests": "Ajanın çalıştırdığı testler",
"field_builds": "Ajanın çalıştırdığı derlemeler",
"check_detail": "{runs}; görünen son çalıştırma: {last}; {passed} geçti, {failed} kaldı, {hidden} görünmüyor",
"check_last_passed": "geçti",
"check_last_failed": "kaldı",
"check_last_none": "yok",
"check_test_passed": "Testler: son çalıştırma geçti · {runs}",
"check_test_failed": "Testler: son çalıştırma kaldı · {runs}",
"check_test_hidden": "Testler: sonuç görünmüyor · {runs}",
"check_build_passed": "Derleme: son çalıştırma geçti · {runs}",
"check_build_failed": "Derleme: son çalıştırma kaldı · {runs}",
"check_build_hidden": "Derleme: sonuç görünmüyor · {runs}",
"check_note": "Testler ve derlemeler ajanın kendi komutlarından ve çıkış kodlarından gelir; komut metni hiçbir yerde saklanmaz. Komut çıktısını başka bir komuta aktardıysa (örneğin tail), arka planda çalıştıysa ya da kontrolden sonra devam ettiyse sonuç görünmez.",
"detail_intro": "Kayıt aralığı ilk ve son olay arasındaki zamandır; beklemeleri de içerir. Çalışma süresi yalnız ajan kaydettiyse gösterilir.",
"models_in_session": "Bu oturumdaki modeller",
"git_title": "Oturum sırasında Git",
"git_scope": "Oturumun ilk ve son kaydı arasındaki yerel Git hareketleri. Aynı anda başka kişiler ve ajanlar da çalışmış olabilir; bu hareketler yazarı kanıtlamaz. Hâlâ dalda olan bir commit sonraki bir commit'le geri alınmış olabilir.",
"git_no_repo": "Ne bu oturumun klasörü ne de düzenlediği dosyalar erişilebilir bir yerel Git deposunda.",
"git_linked": "Kontrol edilen depolar: {repos}. Oturum bir depoda başladıysa ya da bir deponun dosyasını düzenlediyse o depo sayılır; böylece üst klasörde başlatılan bir ajan da değiştirdiği depoya bağlanır.",
"git_outcome": "Bu sürede kaydedilen commit'ler: {total} commit'ten {kept} tanesi hâlâ yerel ya da uzak izleme dalında.",
"git_lines": "Commit'lerinin eklediği satırlardan HEAD'de hâlâ yerinde olan: {share} ({added} satırın {kept} tanesi; {commits} ölçüldü).",
"git_lines_unmeasured": " Ölçülemeyen: {n} (birleştirme, ilk commit, çok büyük dosya ya da HEAD geçmişinde olmayan commit).",
"git_lines_note": "İçeriğe göre sayılır: dosyası içinde yer değiştiren satır yerinde sayılır; yeniden yazılan ya da dosyası taşınan satır sayılmaz. Dosya içerikleri yalnız bellekte okunur.",
"lines_kept_row": "Kod: eklenen {added} satırın {share} kadarı yerinde",
"git_outcome_off": "{n} tanesi artık hiçbir dalda değil: düzeltildi (amend), yeniden sıralandı, reset edildi ya da silinen bir dalda kaldı. Yeniden yazılan bir commit aynı değişikliği taşımaya devam edebilir.",
"git_outcome_unknown": "{n} tanesi kontrol edilemedi: eksik ya da başka depodan ödünç nesneler, sığ ya da çok uzun geçmiş.",
"reedit_coverage": "Değerlendirilebilen seçili oturum: {selected} içinden {eligible}. Sonraki oturum kanıtı, seçili kayıt klasörlerinin tamamından alınır: ajan ve proje ayrımı olmadan {total} oturumdan {timeline} tanesi değerlendirilebilir.",
"reedit_followup": "7 günü tamamladığı hâlde sonraki düzenleme hedefi gözlenmeyen: {n}. Bu, mevcut kayıtlarda eşleşme bulunamadığı anlamına gelir.",
"reedit_cutoff": "Gözlem sonu: {at}; güncellemek için kayıtları yeniden oku.",
"reedit_excluded": "Seçili oturumların değerlendirilememe nedenleri",
"reedit_archive_old_parser": "Eski okuyucuyla arşivlenen kayıtlar",
"reedit_archive_unverified": "Doğrulanamayan arşiv kaynakları",
"reedit_uncertain_history": "Bağımsız oturum geçmişi doğrulanamadı",
"reedit_invalid_time": "Eksik, geçersiz veya gelecekteki oturum zamanları",
"reedit_missing_targets": "Kullanılabilir tam düzenleme hedefi yok",
"reedit_matches": "En kısa aralıklı gözlenen eşleşmeler · en fazla 5",
"reedit_match_gap": "Oturumlar arası süre: {gap} · ortak düzenleme hedefi: {targets}",
"reedit_origin": "Önceki: {agent} · {code}",
"reedit_later": "Sonraki: {agent} · {code}",
"reedit_tokens": "Bu oturumun tamamı için kayıtlı token: {tokens}{partial}",
"reedit_partial": " · token veya atıf kayıtları eksik",
"reedit_outside": "Geçerli filtrelerin dışında",
"reedit_subsecond": "1 sn'den az",
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
"noun_run": "çalıştırma",
"noun_commit": "commit",
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
"export_started": "Özet hazır. İndirilen dosyaları kontrol edin; başlamadıysa",
"table_scroll_help": "Diğer sütunlar için yana kaydırın. Klavyede tablo alanına gelip sol ve sağ oklarını kullanın.",
"follow_title": "Dene ve takip et · haftalık inceleme",
"follow_scope": "Bu iş için bir değişiklik kaydet, sonra iki yedi günlük dönemi incele. Ana filtrelerden bağımsız olarak tüm bağlı oturumların tarihli yanıtlarını kullanır. Yeni model çağrısı yapmaz.",
"follow_reload": "Takipleri yeniden yükle",
"follow_reload_hint": "Kayıtlı takipleri okumak için bölümü aç veya yeniden yükle.",
"follow_loading": "Kayıtlı takipler okunuyor…",
"follow_failed": "Takipler okunamadı. Bu bölümü yeniden yükle.",
"follow_stale": "Kaynak okuması beş dakikadan eski. Başlatmadan veya incelemeden önce “Kayıtları yenile” ile kayıtları oku, sonra bu bölümü yeniden yükle. Taslakların korunur.",
"follow_new": "Bir değişiklik dene",
"follow_trigger": "Bu kararı ne tetikledi?",
"follow_trigger_quota": "Kota baskısı",
"follow_trigger_concentration": "Kullanım yoğunlaşması",
"follow_trigger_session_pattern": "Oturum örüntüsü",
"follow_trigger_other": "Diğer gözlem",
"follow_observation": "Gözlemin (isteğe bağlı)",
"follow_change": "Neyi değiştireceksin?",
"follow_private": "Not başına en fazla 1.000 karakter. Özel yerel kayıtlar; özel yedeğe dahil edilir, normal raporlara eklenmez. Bu işi silmek takiplerini de siler.",
"follow_start": "Başlangıcı kaydet ve başlat",
"follow_caution": "Daha düşük token sayısı daha iyi sonuç, para tasarrufu veya hesap kotasında azalma kanıtlamaz. Kayıtlar haftanın yalnızca bir bölümünü kapsayabilir. İşin sonucunu ayrıca değerlendir.",
"follow_empty": "Henüz takip edilen değişiklik yok. İlgili oturumları bu işe bağla, sonra denemek istediğin değişikliği kaydet.",
"follow_reading": "{since} → {until} (bitiş hariç) · {sessions} oturum · {responses} yanıt · {tokens} token · {excluded} dışlanan · {missing} eksik bağlantı",
"follow_before": "Önce · kayıtlı başlangıç",
"follow_after": "Sonra · kayıtlı inceleme",
"follow_after_preview": "Sonra · henüz kaydedilmedi",
"follow_status_open": "Değişiklik takip ediliyor",
"follow_status_reviewed": "İnceleme kaydedildi",
"follow_status_cancelled": "Takip iptal edildi",
"follow_reason": "Senin gerekçen: {reason}",
"follow_due": "{date} itibarıyla incele. İncelemeden önce bu işe ait yeni oturumları bağla.",
"follow_wait": "İnceleme için sonraki dönem bitmeli ve güncel kaynak okuması bulunmalı. PLER otomatik inceleme kaydetmez.",
"follow_context": "Görevler ve koşullar karşılaştırılabilir miydi?",
"follow_context_unknown": "Değerlendirilmedi",
"follow_context_similar": "Benzer görev ve koşullar",
"follow_context_different": "Farklı görev veya koşullar",
"follow_context_saved": "Koşullara ilişkin değerlendirmen: {context}",
"follow_review_note": "İnceleme notu (isteğe bağlı, en fazla 1.000 karakter)",
"follow_review": "Haftalık incelemeyi kaydet",
"follow_cancel": "Takibi iptal et, başlangıcı koru",
"follow_delete": "Bu takibi sil",
"follow_delete_confirm": "Bu takibi kalıcı olarak sil",
"follow_delete_warning": "Bu işlem başlangıcı, incelemeyi ve notları yerel iş kaydından kaldırır. Mevcut yedek dosyalarındaki kopyalar kalır.",
"follow_keep": "Takibi koru",
"follow_no_comparison": "Sayısal karşılaştırma yapılamadı:",
"follow_metric": "Her araç/proje/model grubunda oturum başına yanıt token ortalamalarının gözlenen medyanı (iki dönemde de en az üç oturum). Bu betimsel bir farktır, nedensellik kanıtı değildir.",
"follow_delta": "{agent} · proje #{project} · {model}: {before} → {after} token/yanıt ({percent})",
"follow_limit_missing_sessions": "Bağlı oturumlardan bazıları kaynak okumasında bulunmuyor.",
"follow_limit_source_incomplete": "Kaynak okumasında atlanan dosya veya arşiv kaybı var.",
"follow_limit_incomplete_usage": "Bazı yanıtların tarihi ve tam oturum kullanımı doğrulanamadı.",
"follow_limit_unknown_scope": "Bazı oturumlarda proje/model kapsamı bilinmiyor veya birden fazla model kullanılmış.",
"follow_limit_boundary_response": "Bazı yanıt kayıtları dönem sınırını aşıyor.",
"follow_limit_measurement_limit": "Yerel ölçüm sınırına ulaşıldı.",
"follow_limit_baseline_changed": "İlk başlangıç ölçümü güncel bağlı kaynaklardan yeniden üretilemiyor.",
"follow_limit_parser_changed": "Başlangıçtan sonra ölçüm ayrıştırıcısı değişmiş.",
"follow_limit_context_unknown": "Görev ve koşulların benzerliğini henüz değerlendirmedin.",
"follow_limit_context_different": "Görev veya koşulları farklı olarak işaretledin.",
"follow_limit_cohort_changed": "İki dönemin araç/proje/model grupları farklı.",
"follow_limit_small_sample": "Her grupta iki dönemde de en az üç oturum gerekir.",
"follow_limit_zero_baseline": "Başlangıç gruplarından birinde yanıt başına token sıfır.",
"follow_limit_duplicate_sessions": "Yinelenen oturum kimlikleri kaynak okumasını belirsizleştiriyor.",
"follow_minimum": "Sayısal inceleme için aynı araç/proje/model grubunda iki dönemde de en az üç oturum ve benzer görev değerlendirmen gerekir. Sonucu açık kalan bir incelemeyi de kaydedebilirsin."
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
function notice(message,kind='error'){$('notice').textContent=message||'';$('notice').hidden=!message;$('notice').dataset.kind=kind;}
function applyLanguage(){
  document.documentElement.lang=LANG;document.title=t('title');
  for(const item of document.querySelectorAll('[data-i18n]'))item.textContent=t(item.dataset.i18n);
  for(const item of document.querySelectorAll('[data-i18n-placeholder]'))item.placeholder=t(item.dataset.i18nPlaceholder);
  for(const item of document.querySelectorAll('[data-i18n-label]'))item.setAttribute('aria-label',t(item.dataset.i18nLabel));
  $('usage-help').href='/help?lang='+LANG;
  $('usage-backup-guide').href='/help?lang='+LANG+'#backup';
}
function switchLanguage(){const other=LANG==='tr'?'en':'tr';try{localStorage.setItem('pler-lang',other);sessionStorage.setItem('pler-view',JSON.stringify({days:$('usage-period').value,agent:$('usage-agent').value,project:$('usage-project').value,search:$('usage-session-search').value,sort:$('usage-session-sort').value,quality:Boolean($('usage-quality-only').checked),mask:Boolean($('usage-export-mask').checked),work:workViewMemory()}));}catch(_){}workState.navigation=true;location.search='?lang='+other;}
async function api(path,options={}){
  let response;
  try{response=await fetch(path,{cache:'no-store',...options,headers:{...options.headers,'X-PLER-Token':token}});}catch(error){if(error?.name==='AbortError')throw error;throw new Error(t('err_unreachable'));}
  let body;
  try{body=await response.json();}catch(_){throw new Error(t('err_closed'));}
  if(!response.ok){const error=new Error(body.error||t('err_read'));error.code=body.code;error.reason=body.reason;throw error;}
  return body;
}
async function post(path,body){return api(path+'?lang='+LANG,{method:'POST',headers:{'Content-Type':'application/json','X-PLER-Token':token},body:JSON.stringify(body)});}
async function closeApp(){
  try{await post('/api/quit',{});usageState.stopped=true;usageState.revision++;clearTimeout(usageState.timer);clearInterval(usageState.clock);clearUsageBackupDownload();document.querySelectorAll('button,select,input,textarea').forEach(item=>item.disabled=true);notice(t('closed'));}
  catch(error){notice(error.message);}
}
const usageState={data:null,revision:0,pageSize:20,timer:null,clock:null,stopped:false,loading:false,exporting:false,downloadUrl:null};
try{const stored=sessionStorage.getItem('pler-ui-view-v1')||new URLSearchParams(location.search).get('view')||localStorage.getItem('pler-ui-view-v1')||'null';const saved=JSON.parse(sessionStorage.getItem('pler-view')||'null')||JSON.parse(stored)?.filters;sessionStorage.removeItem('pler-view');if(saved&&['0','7','30','90'].includes(saved.days)&&['all','codex','claude-code'].includes(saved.agent)&&typeof saved.project==='string'&&/^(all|[a-f0-9]{24})$/.test(saved.project)){usageState.restore=saved;usageState.workRestore=saved.work;$('usage-period').value=saved.days;$('usage-agent').value=saved.agent;if(typeof saved.search==='string')$('usage-session-search').value=saved.search.slice(0,160);if(['tokens','recent','started','issues'].includes(saved.sort))$('usage-session-sort').value=saved.sort;$('usage-quality-only').checked=saved.quality===true;$('usage-export-mask').checked=saved.mask!==false;}}catch(_){}
const usageAgents={'claude-code':'Claude Code',codex:'Codex'};
const usageUI=PlerUIState.create({filters:readUsageFilters()});
let sessionGridActive=false;
function readUsageFilters(){return {days:$('usage-period').value,agent:$('usage-agent').value,project:$('usage-project').value||'all',sort:$('usage-session-sort').value,quality:$('usage-quality-only').checked,search:$('usage-session-search').value};}
function syncUsageFilters(){usageUI.publish('filters',readUsageFilters());usageUI.publish('restoring',Boolean(usageState.restore));}
function setUsageFilters(patch){
  const next=PlerUIState.filters(patch,usageUI.get().filters);
  for(const [key,id] of Object.entries({days:'usage-period',agent:'usage-agent',project:'usage-project',sort:'usage-session-sort',search:'usage-session-search'}))if($(id).value!==next[key])$(id).value=next[key];
  $('usage-quality-only').checked=next.quality;usageUI.publish('filters',next);
}
function publishUsage(){const loading=Boolean(usageState.reading||usageState.refreshing),changed=usageState.loading!==loading;usageState.loading=loading;usageUI.publish('restoring',Boolean(usageState.restore));usageUI.publish('data',usageState.data);usageUI.publish('loading',loading);usageUI.publish('readError',Boolean(usageState.readError));if(changed){syncExportButton();syncArchiveButton();}}
window.plerUI=Object.freeze({get:usageUI.get,subscribe:usageUI.subscribe,
 setScreen:name=>usageUI.publish('screen',name),setFilters:setUsageFilters,
 useSessionGrid(){sessionGridActive=true;$('usage-sessions').replaceChildren();renderUsageSessions();}});
const usageTokens=[['input',t('token_input')],['cache_read',t('token_cache')],['cache_write',t('token_write')],['output',t('token_output')]];
const usagePct=value=>value==null?t('unknown'):new Intl.NumberFormat(LOCALE,{style:'percent',maximumFractionDigits:1}).format(value);
const usageUsd=value=>value==null?t('unknown'):new Intl.NumberFormat(LOCALE,{style:'currency',currency:'USD',maximumFractionDigits:value<100?2:0}).format(value);
const usagePriceDate=value=>typeof value==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(value)?new Intl.DateTimeFormat(LOCALE,{dateStyle:'medium',timeZone:'UTC'}).format(new Date(value+'T00:00:00Z')):t('unknown');
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
function usageQuery(){const f=usageUI.get().filters;return new URLSearchParams({days:f.days,agent:f.agent,project:f.project,lang:LANG}).toString();}
const scheduleUsageLoad=PlerUIState.coalesce(performUsageLoad);
function loadUsage(){syncUsageFilters();return scheduleUsageLoad();}
async function performUsageLoad(){
  if(usageState.stopped)return;
  // One owner for GET lifetime and polling; mutation POSTs are never aborted here.
  usageState.readError=false;
  clearTimeout(usageState.timer);usageState.timer=null;
  usageState.requestController?.abort();const controller=usageState.requestController=new AbortController();
  const revision=++usageState.revision;
  usageState.reading=true;
  publishUsage();
  if(usageState.downloadQuery&&usageState.downloadQuery!==usageQuery())clearUsageDownload();
  syncExportButton();$('usage-content').setAttribute('aria-busy','true');
  try{const data=await api('/api/usage?'+usageQuery(),{signal:controller.signal});if(revision!==usageState.revision)return;const previous=usageState.data;usageState.data=data;if(renderUsage(data)===false)usageState.data=previous;publishUsage();
    if(data.state==='idle'){await refreshUsage();return;}
    clearTimeout(usageState.timer);if(data.state==='scanning'&&!usageState.stopped)usageState.timer=setTimeout(loadUsage,1500);
  }catch(error){if(revision!==usageState.revision||error?.name==='AbortError')return;usageState.readError=true;if(error.code==='unknown_project'&&$('usage-project').value!=='all'){setUsageFilters({project:'all'});notice(t('project_gone'));loadUsage();return;}$('usage-status').textContent=error.message+(usageState.data?.has_snapshot?t('previous_kept'):'');$('usage-progress').hidden=true;$('usage-refresh').disabled=false;}
  finally{if(revision===usageState.revision){usageState.reading=false;publishUsage();$('usage-content').setAttribute('aria-busy','false');restoreActionFocus();}}
}
async function refreshUsage(){
  if(usageState.workBusy||usageState.stopped)return;
  usageState.readError=false;
  usageState.refreshing=true;publishUsage();
  rememberActionFocus($('usage-refresh'));
  clearUsageDownload();
  $('usage-refresh').disabled=true;$('usage-status').textContent=t('reading');$('usage-progress').hidden=false;
  try{await post('/api/usage/refresh',{});await loadUsage();}catch(error){if(usageState.stopped)return;usageState.readError=true;$('usage-status').textContent=error.message;$('usage-refresh').disabled=false;$('usage-progress').hidden=true;}
  finally{usageState.refreshing=false;publishUsage();restoreActionFocus();}
}
function renderUsage(data){
  $('usage-refresh').disabled=data.state==='scanning';$('usage-progress').hidden=data.state!=='scanning';syncExportButton();
  renderUsageArchive(data);
  $('usage-demo').hidden=!data.demo;
  $('usage-status').textContent=data.state==='scanning'?t('scanning')+(data.has_snapshot?t('showing_previous'):''):data.error||t('last_read',{at:usageDate(data.scanned_at),claude:count(data.sources.claude_files,'claude_file'),codex:count(data.sources.codex_files,'codex_file')});
  const selected=$('usage-project').value;$('usage-project').replaceChildren(node('option','',t('project_all')));$('usage-project').firstChild.value='all';
  for(const project of data.project_options){const option=node('option','',project.name);option.value=project.id;$('usage-project').append(option);}$('usage-project').value=data.project_options.some(p=>p.id===selected)?selected:'all';
  syncUsageFilters();
  if(restoreUsageSelection(data))return false;
  renderWorkItems(data);
  $('usage-content').hidden=!data.has_snapshot;$('usage-empty').hidden=!data.has_snapshot||Boolean(data.totals.sessions);
  for(const id of ['usage-totals','usage-mix','usage-columns','usage-session-section'])$(id).hidden=!data.totals.sessions;
  const noFiles=!data.sources.claude_files&&!data.sources.codex_files;
  $('usage-empty').querySelector('h2').textContent=t(noFiles&&data.sources.unreadable?'empty_unreadable_title':noFiles?'empty_no_logs_title':'empty_title');
  $('usage-empty').querySelector('p').textContent=t(data.sources.unreadable?'empty_unreadable':noFiles?'empty_no_logs_text':'empty_text');
  $('usage-filter-clear').hidden=!data.project_options.length;$('usage-coverage').hidden=noFiles;
  if(!data.has_snapshot)return;
  renderCoverageGuidance(data);
  renderDatedUsage(data.dated_usage);
  $('usage-coverage').textContent=(data.sources.unreadable?t('unreadable_coverage',{files:count(data.sources.unreadable,'file')})+data.sources.issues.map(i=>i.reason+': '+i.files).join(' · '):t('all_read'))+(data.period.cross_period_sessions?t('cross_period',{sessions:count(data.period.cross_period_sessions,'session')}):'');
  if(data.sources.unreadable)$('usage-status').textContent+=t('status_unreadable',{files:count(data.sources.unreadable,'file')});
  if(data.unknown_call_sessions)$('usage-coverage').textContent+=t('unknown_calls',{sessions:count(data.unknown_call_sessions,'session')});
  const totals=data.totals;
  // Most of an agent's tokens are the same context read again from the cache; say so next to the total.
  const cached=totals.tokens.cache_read;
  $('usage-totals').replaceChildren(...[[t(data.quality?.tokens_complete===false?'stat_known_total':'stat_total'),usageShort(totals.total_tokens),totals.total_tokens?t('stat_total_note',{share:usagePct(cached/totals.total_tokens)}):''],[t('stat_fresh'),usageShort(totals.total_tokens-cached),t('stat_fresh_note')],[t('stat_sessions'),number(totals.sessions),count(totals.prompts,'request')],[t('stat_calls'),number(totals.calls),data.quality?.calls_complete===false?t('split_unknown'):''],[t('stat_api'),totals.api_priced_tokens?usageUsd(totals.api_usd):t('unknown'),t(totals.api_priced_share>=0.9995?'stat_api_note':'stat_api_partial',{share:usagePct(totals.api_priced_share),date:usagePriceDate(data.api_prices?.as_of)})]].map(([label,value,note])=>{const item=node('article','usage-stat');item.append(node('span','',label),node('strong','',value));if(note)item.append(node('small','',note));return item;}));
  $('usage-agents').replaceChildren(...Object.entries(data.agents).map(([agent,row])=>{const article=node('article','usage-agent');const head=node('div','usage-agent-head');head.append(node('h3','',usageAgents[agent]||agent),node('strong','',t('tokens',{n:usageShort(row.total_tokens)})));const strip=node('div','token-strip');strip.setAttribute('role','img');strip.setAttribute('aria-label',usageTokens.map(([key,label])=>label+': '+number(row.tokens[key])).join('; '));
    for(const [key,label] of usageTokens){const segment=node('span','token-'+key.replace('cache_read','cache').replace('cache_write','write'));segment.style.width=(row.total_tokens?row.tokens[key]/row.total_tokens*100:0)+'%';segment.title=label+': '+number(row.tokens[key]);strip.append(segment);}
    article.append(head,strip,node('p','section-note',t('agent_note',{sessions:count(row.sessions,'session'),calls:count(row.calls,'model_call'),share:usagePct(row.cache_read_share),errors:count(row.errors,'error'),aborted:count(row.aborted,'interrupted_turn')})));return article;
  }));
  renderUsageInsights(data);renderUsageQuota(data);renderUsagePlans(data);renderQuotaAlerts();syncLiveControls();
  $('usage-projects').replaceChildren(...data.projects.slice(0,8).map(project=>{const row=node('div','usage-rank');const button=node('button','text-button',project.name);button.addEventListener('click',()=>{$('usage-project').value=project.id;$('usage-project').focus();usageState.pageSize=20;loadUsage();});row.append(button,node('strong','',usageShort(project.total_tokens)),node('small','',count(project.sessions,'session')));return row;}));
  $('usage-models').replaceChildren(...data.models.slice(0,8).map(model=>{const row=node('div','usage-rank');row.append(node('span','model-name',model.model==='unknown'?t('unknown'):model.model),node('strong','',usageShort(model.total_tokens)),node('small','',(usageAgents[model.agent]||model.agent)+' · '+count(model.calls,'call')));return row;}));
  renderUsageSessions();
}
function renderCoverageGuidance(data){
  const box=$('usage-data-guidance'),list=$('usage-data-guidance-items');
  const issues=data.quality?.issues||[],notices=data.coverage?.notices||[];
  box.hidden=!data.has_snapshot||(!notices.length&&!issues.length);
  list.replaceChildren();
  for(const item of notices){
    // The server sends fixed codes, never source paths or exception messages.
    const prefix='coverage_'+item.code;
    if(!Object.prototype.hasOwnProperty.call(I18N.en,prefix+'_title'))continue;
    const row=node('li'),next=node('p','coverage-next');
    next.append(node('strong','',t('coverage_next')),document.createTextNode(t(prefix+'_next')));
    row.append(node('h3','',t(prefix+'_title')),node('p','',t(prefix+'_impact')),next);list.append(row);
  }
  $('usage-coverage-help').href='/help?lang='+LANG+'#coverage';
  $('usage-quality-details').hidden=!issues.length;
  $('usage-quality').textContent=issues.map(item=>item.detail).join(' ');
  const affected=data.quality_affected_sessions??data.sessions.filter(sessionHasQualityLimits).length;
  $('usage-quality-show').hidden=!affected;
  $('usage-quality-show').textContent=t('quality_show',{n:number(affected)});
}
function restoreUsageSelection(data){
  if(!usageState.restore||!data.has_snapshot)return false;
  const desired=usageState.restore.project;usageState.restore=null;
  if(desired!=='all'&&data.project_options.some(p=>p.id===desired)&&data.filters.project!==desired){setUsageFilters({project:desired});loadUsage();return true;}
  usageUI.publish('restoring',false);
  return false;
}
function renderDatedUsage(value){
  // A partial dated sum beside whole-session totals reads as a contradiction; the JSON keeps its coverage counts.
  const box=$('usage-dated');box.hidden=!value?.retained_usage_fully_dated;if(box.hidden)return;
  box.replaceChildren(node('h2','',t('dated_title')),node('p','dated-result',t('dated_result',{tokens:number(value.total_tokens),calls:number(value.response_calls),sessions:number(value.contributing_sessions)})),node('p','section-note',t('dated_coverage',{eligible:number(value.eligible_sessions),selected:number(value.selected_sessions),unallocated:number(value.unallocated_sessions)})),node('p','section-note',t('dated_scope')));
  const details=node('details','');details.append(node('summary','',t('dated_exclusions')),node('p','section-note',t('dated_interval',{since:value.since?usageDate(value.since):t('dated_all'),cutoff:usageDate(value.cutoff)})),node('p','section-note',t('dated_undated',{undated:number(value.undated_response_calls),future:number(value.future_response_calls),outside:number(value.outside_period_calls)})));
  const reasons={archive_old_parser:'reedit_archive_old_parser',archive_unverified:'reedit_archive_unverified',uncertain_history:'reedit_uncertain_history',incomplete_usage:'dated_incomplete_usage',unverified_attribution:'dated_unverified_attribution',missing_event_evidence:'dated_missing_event_evidence'};
  const list=node('ul','');for(const reason of Object.keys(reasons))if(value.excluded?.[reason])list.append(node('li','',t(reasons[reason])+': '+number(value.excluded[reason])));details.append(list);box.append(details);
}
function renderUsageInsights(data){
  usageState.insightQuotaStates=quotaInsightStates(data);
  const box=$('usage-insights'),notes=(data.insights||[]).filter(note=>note.kind!=='quota'||['full','fills_before_reset','ambiguous'].includes(quotaWindowNow(note.evidence).state));box.hidden=!notes.length;
  box.replaceChildren(node('span','eyebrow',t('insights_eyebrow')),node('h2','',t('insights_title')));
  const list=node('div','usage-insight-list');
  for(const note of notes){const card=node('article','usage-insight '+note.level);card.append(node('h3','',note.title));if(note.kind==='subsequent_edit')appendSubsequentEdit(card,data,note.evidence||data.reedit,note.detail);else card.append(node('p','',note.detail));if(note.kind==='concentration'){const button=node('button','text-button',t('inspect_session'));button.addEventListener('click',()=>{if(data.sessions.length)openUsageSession(data.sessions[0]);});card.append(button);}list.append(card);}
  box.append(list,node('p','section-note',t('insights_note')));
}
function appendSubsequentEdit(card,data,observation,detail=''){
  if(!observation)return;
  card.className+=' usage-reedit';
  const excludedCount=Object.values(observation.excluded||{}).reduce((sum,n)=>sum+n,0);
  card.append(node('p','',t('reedit_brief',{matched:number(observation.matched_sessions||0),eligible:number(observation.eligible_sessions),pending:number(observation.pending_sessions||0),excluded:number(excludedCount)})),node('p','section-note',t('reedit_caution')));
  const method=node('details','');method.append(node('summary','',t('reedit_method')));
  if(detail)method.append(node('p','section-note',detail));
  method.append(node('p','section-note',t('reedit_coverage',{eligible:number(observation.eligible_sessions),selected:number(observation.origin_sessions),timeline:number(observation.timeline_eligible_sessions),total:number(observation.timeline_sessions)})));
  method.append(node('p','section-note',t('reedit_followup',{n:number(observation.observed_unmatched_sessions)})));
  method.append(node('p','section-note',t('reedit_cutoff',{at:usageDate(observation.cutoff)})));
  const reasons={archive_old_parser:'reedit_archive_old_parser',archive_unverified:'reedit_archive_unverified',uncertain_history:'reedit_uncertain_history',invalid_time:'reedit_invalid_time',missing_targets:'reedit_missing_targets'};
  const excluded=Object.keys(reasons).filter(reason=>observation.excluded?.[reason]>0);
  if(excluded.length){method.append(node('p','section-note',t('reedit_excluded')));const list=node('ul','');for(const reason of excluded)list.append(node('li','',t(reasons[reason])+': '+number(observation.excluded[reason])));method.append(list);}card.append(method);
  const matches=(observation.matches||[]).slice(0,5);
  if(!matches.length)return;
  const pairs=node('details','');pairs.append(node('summary','',t('reedit_matches')));
  const list=node('ol','reedit-pairs');
  for(const match of matches){
    const item=node('li','');
    const gap=match.gap_seconds>0&&match.gap_seconds<1?t('reedit_subsecond'):usageDuration(match.gap_seconds);
    item.append(node('p','',t('reedit_match_gap',{gap,targets:number(match.matching_targets)})));
    for(const role of ['origin','later']){
      // Only the public opaque code and fixed agent names enter this view.
      const id=match[role+'_id'],agent=usageAgents[match[role+'_agent']]||t('unknown');
      const code=typeof id==='string'&&/^[a-f0-9]{24}$/.test(id)?id.slice(0,8):t('unknown');
      const session=(data.sessions||[]).find(row=>row.id===id);
      const line=node('p',''),label=t(role==='origin'?'reedit_origin':'reedit_later',{agent,code});
      if(session){const button=node('button','text-button',label);button.addEventListener('click',()=>openUsageSession(session));line.append(button);}
      else if(typeof id==='string'&&/^[a-f0-9]{24}$/.test(id)){const button=node('button','text-button',label+' · '+t('open_outside'));button.addEventListener('click',()=>inspectUsageSession(id));line.append(button);}
      else line.append(node('span','',label+' · '+t('reedit_outside')));
      const tokens=match[role+'_tokens'];
      line.append(node('br',''),node('small','',t('reedit_tokens',{tokens:number(tokens),partial:match[role+'_usage_complete']?'':t('reedit_partial')})));
      item.append(line);
    }
    list.append(item);
  }
  pairs.append(list);card.append(pairs);
}
function quotaWindowNow(window,now=Date.now()){
  if(window.state==='ambiguous')return window;
  const reset=Date.parse(window.resets_at),at=Date.parse(window.at);
  if(!Number.isFinite(reset))return {...window,state:'historical'};
  if(reset<=now)return {...window,state:'reset'};
  const age=(window.max_age_seconds??(window.window_minutes<1440?1800:86400))*1000;
  if(!Number.isFinite(at)||now-at>age||at>now+300000||(window.used_percent<100&&Date.parse(window.full_at)<=now))return {...window,state:'stale'};
  return window;
}
// Live quota warning: from the server's forecast (forecast.py) and the clock. Warn when a window is full, or
// fills before its reset within the lead time; optionally read the logs again on a timer and notify once.
const QUOTA_ALERT_LEAD={300:3600e3,10080:86400e3},LIVE_EVERY=5*60e3;
const liveState={watch:false,notify:false,notified:new Set(),timer:null};
function quotaAlerts(data,now=Date.now()){
  const found=[];
  for(const row of data?.outlook||[]){
    const window=quotaWindowNow(row,now),key=[window.agent,window.window_minutes,window.resets_at].join('|');
    if(window.state==='full')found.push({key:key+'|full',level:'full',window});
    else if(window.state==='fills_before_reset'&&Date.parse(window.full_at)-now<=(QUOTA_ALERT_LEAD[window.window_minutes]??3600e3))
      found.push({key:key+'|soon',level:'soon',window});
  }
  return found;
}
function quotaAlertText(alert,now=Date.now()){
  const window=alert.window,values={agent:usageAgents[window.agent]||window.agent,window:usageWindow(window.window_minutes),reset:usageDate(window.resets_at)};
  return alert.level==='full'?t('quota_alert_full',values):t('quota_alert_soon',{...values,full:usageDate(window.full_at),left:usageDuration((Date.parse(window.full_at)-now)/1000)});
}
function liveSave(){try{localStorage.setItem('pler-live',JSON.stringify({watch:liveState.watch,notify:liveState.notify}));sessionStorage.setItem('pler-quota-notified',JSON.stringify([...liveState.notified].slice(-50)));}catch(_){}}
function liveLoad(){
  try{const saved=JSON.parse(localStorage.getItem('pler-live')||'{}');liveState.watch=saved.watch===true;liveState.notify=saved.notify===true;
    for(const key of JSON.parse(sessionStorage.getItem('pler-quota-notified')||'[]'))if(typeof key==='string')liveState.notified.add(key);}catch(_){}
  if(typeof Notification==='undefined'||Notification.permission!=='granted')liveState.notify=false;
}
function notifyQuota(alerts){
  if(!liveState.notify||typeof Notification==='undefined'||Notification.permission!=='granted')return;
  for(const alert of alerts){
    if(liveState.notified.has(alert.key))continue;
    liveState.notified.add(alert.key);liveSave();
    try{new Notification(t('quota_alert_title'),{body:quotaAlertText(alert),tag:alert.key});}catch(_){}
  }
}
function renderQuotaAlerts(){
  const box=$('usage-quota-alert'),alerts=usageState.data?.has_snapshot&&!usageState.stopped?quotaAlerts(usageState.data):[];
  box.hidden=!alerts.length;box.replaceChildren(...alerts.map(alert=>node('span','',quotaAlertText(alert))));
  notifyQuota(alerts);
  usageUI.publish('quota',{count:alerts.length});
}
function syncLiveControls(){
  const box=$('usage-live');box.hidden=!usageState.data?.has_snapshot||usageState.stopped;
  $('usage-live-watch').checked=liveState.watch;
  const desktop=typeof navigator!=='undefined'&&/Electron\//.test(navigator.userAgent);
  const supported=!desktop&&typeof Notification!=='undefined',blocked=supported&&Notification.permission==='denied';
  $('usage-live-notify').hidden=!supported||blocked;$('usage-live-notify').textContent=t(liveState.notify?'live_notify_off':'live_notify_on');
  $('usage-live-note').textContent=!supported?t('live_notify_unsupported'):blocked?t('live_notify_blocked'):liveState.notify?t('live_notify_active'):'';
}
function liveBusy(){
  const active=document.activeElement;
  return usageState.stopped||usageState.loading||usageState.workBusy||usageState.planSaving||usageState.data?.state==='scanning'
    ||Boolean(document.querySelector('dialog[open]'))||(['INPUT','TEXTAREA','SELECT'].includes(active?.tagName)&&active.type!=='checkbox');
}
async function liveTick(){
  // A timed read never interrupts typing, an open dialog or another action; it simply waits for the next tick.
  if(!liveState.watch||liveBusy())return;
  try{await post('/api/usage/refresh',{});await loadUsage();}catch(_){}
}
function setLiveWatch(on){
  liveState.watch=on;liveSave();clearInterval(liveState.timer);liveState.timer=on?setInterval(liveTick,LIVE_EVERY):null;syncLiveControls();
}
async function toggleQuotaNotifications(){
  if(liveState.notify){liveState.notify=false;liveSave();syncLiveControls();return;}
  if(typeof Notification==='undefined'){syncLiveControls();return;}
  let permission=Notification.permission;
  if(permission==='default')try{permission=await Notification.requestPermission();}catch(_){permission='denied';}
  liveState.notify=permission==='granted';liveSave();syncLiveControls();
  if(liveState.notify)renderQuotaAlerts();
}
function usageOutlookText(window){
  // A logged plan change bounds the history: say so, whatever the state.
  return usageOutlookState(window)+(window.plan_changed_at?t('out_plan_changed',{at:usageDate(window.plan_changed_at)}):'');
}
function usageOutlookState(window){
  if(window.state==='ambiguous')return t(window.reason==='multiple_source_groups'?'quota_multiple_sources':'quota_ambiguous');
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
const planNames={pro:'Pro',max:'Max',ultra:'Ultra',go:'Go',plus:'Plus'};
const planFindings={choose_plan:'plan_choose_plan',no_meter:'plan_no_meter',larger_ratio_unpublished:'plan_larger_ratio_unpublished',larger_need_unseen:'plan_larger_need_unseen'};
const planChoices={'':'plan_choice_none',pro:'plan_choice_pro',max:'plan_choice_max',ultra:'plan_choice_ultra',api:'plan_choice_api'};
function planLabel(row){
  if(row.plan==='api')return t('plan_api_key');
  if(row.plan)return row.price_usd?t('plan_named',{name:planNames[row.plan]||row.plan,price:number(row.price_usd)}):planNames[row.plan]||row.plan;
  return t(row.agent==='claude-code'?'plan_unchosen':'plan_unlogged');
}
function planFinding(row,finding){
  if(finding==='no_meter'&&row.agent==='codex')return t('plan_no_meter_codex');
  if(finding==='api_below_list_price')return t('plan_api_below_list_price',{usd:usageUsd(row.api_usd),price:usageUsd(row.price_usd)});
  if(finding==='lower_observed'||finding==='lower_weekly_observed'){
    const lower=row.lower_plan_comparison,expires=Date.parse(lower?.expires_at);
    if(!Number.isFinite(expires)||expires<=Date.now())return t('plan_comparison_expired');
    return t(finding==='lower_observed'?'plan_lower_observed':'plan_lower_weekly_observed',
      {peak:usagePct(lower.peak/100),smaller:planNames[lower.plan],price:usageUsd(lower.usd),share:usagePct(lower.share),current:planNames[lower.assumed_plan]});
  }
  return planFindings[finding]?t(planFindings[finding]):'';
}
function agePlanComparisons(){
  for(const line of document.querySelectorAll('#usage-plans .plan-comparison')){
    const expires=Date.parse(line.dataset.expiresAt);
    if(!Number.isFinite(expires)||expires<=Date.now())line.textContent=t('plan_comparison_expired');
  }
}
function planSelect(value,row){
  const label=node('label','plan-choice');label.append(node('span','',t('plan_choose_label')));
  const select=document.createElement('select');select.id='usage-plan-choice';
  for(const key of ['',...value.choices]){const option=node('option','',t(planChoices[key]));option.value=key;select.append(option);}
  select.value=row.plan_word||'';select.disabled=usageState.stopped||value.readable===false||Boolean(usageState.planSaving);
  select.addEventListener('change',()=>setPlan(select.value||null));label.append(select);return label;
}
function renderUsagePlans(data){
  // The advice comes from the server (plans.py); this only lays it out.
  const value=data.plans,box=$('usage-plans');box.hidden=!value?.rows?.length;if(box.hidden)return;
  const title=node('h2','',t('plans_title'));title.id='usage-plans-title';
  box.replaceChildren(node('span','eyebrow',t('plans_eyebrow')),title,node('p','section-note',t('plan_payment_unknown')));
  for(const row of value.rows){
    const card=node('div','plan-row'+(row.findings.includes('limits_reached')?' warn':'')),head=node('div','plan-head');
    head.append(node('strong','',(usageAgents[row.agent]||row.agent)+': '+planLabel(row)));
    if(row.agent==='claude-code')head.append(planSelect(value,row));
    card.append(head,node('p','',row.api_priced_share>0?
      t('plan_api_line',{usd:usageUsd(row.api_usd),share:usagePct(row.api_priced_share)})+(row.usage_partial?t('plan_partial'):''):t('plan_api_unknown')));
    const five=row.meter.find(window=>window.window_minutes===300),week=row.meter.find(window=>window.window_minutes===10080);
    if(five||week)card.append(node('p','',t('plan_meter_line',{five:number(five?.full??0),five_total:number(five?.periods??0),week:number(week?.full??0),week_total:number(week?.periods??0)})));
    if(row.agent==='claude-code'&&value.readable===false)card.append(node('p','plan-finding',t('plan_unreadable')));
    const limits=node('ul','plan-limitations');
    for(const reason of row.limitations||[]){const key='plan_limit_'+reason;if(Object.prototype.hasOwnProperty.call(I18N.en,key))limits.append(node('li','',t(key)));}
    if(limits.children.length)card.append(limits);
    for(const finding of row.findings){
      const text=planFinding(row,finding);if(!text)continue;
      const comparison=['lower_observed','lower_weekly_observed'].includes(finding),line=node('p','plan-finding'+(comparison?' plan-comparison':''),text);
      if(comparison)line.dataset.expiresAt=row.lower_plan_comparison?.expires_at||'';
      card.append(line);
    }
    box.append(card);
  }
  const date=new Intl.DateTimeFormat(LOCALE,{dateStyle:'long',timeZone:'UTC'}).format(new Date(value.prices_as_of+'T12:00:00Z'));
  const period=value.rows[0];
  if(period.since&&period.until){const format=new Intl.DateTimeFormat(LOCALE,{dateStyle:'medium',timeStyle:'short',timeZone:'UTC'});box.append(node('p','section-note',t('plan_interval',{since:format.format(new Date(period.since)),until:format.format(new Date(period.until))})));}
  box.append(node('p','section-note',t('plan_period',{date})),node('p','section-note',t('plan_note')));
}
async function setPlan(plan){
  if(usageState.stopped||usageState.planSaving)return;
  usageState.planSaving=true;
  try{await post('/api/usage/plan',{plan});if(!usageState.stopped)await loadUsage();}
  catch(error){if(!usageState.stopped)notice(error.message);}
  finally{usageState.planSaving=false;}
}
function renderUsageQuota(data){
  // Codex rows come from its logs; Claude Code rows only from PLER's status line (pler statusline --install).
  const outlook=data.outlook||[],codex=outlook.filter(row=>row.agent!=='claude-code'),claude=outlook.filter(row=>row.agent==='claude-code');
  const windows=[...(codex.length?codex:data.quota.latest),...claude].map(window=>quotaWindowNow(window)),box=$('usage-quota');box.hidden=!windows.length&&!data.totals.sessions;box.replaceChildren(node('span','eyebrow',t('quota_eyebrow')),node('h2','',t('quota_title')));
  for(const window of windows){const agent=window.agent==='claude-code'?'Claude Code':'Codex';const card=node('div','usage-quota-row'+(window.state==='fills_before_reset'||window.state==='full'?' warn':''));const label=usageWindow(window.window_minutes);const unknown=['reset','stale','historical','ambiguous'].includes(window.state);const progress=node('progress');progress.max=100;progress.value=unknown?0:window.used_percent;progress.hidden=unknown;progress.setAttribute('aria-label',t('quota_aria',{agent,window:label}));card.append(node('span','',agent+' · '+label),progress,node('strong','',unknown?'—':usagePct(window.used_percent/100)),node('small','',usageOutlookText(window)+t('last_record',{at:usageDate(window.at)})));if(unknown)card.classList.add('quota-old');box.append(card);}
  if(!codex.length&&!data.quota.latest.length&&data.sources.codex_files)box.append(node('p','quota-unavailable',t('codex_unknown')));
  const rejected=data.claude_limit_events.rejected||0;
  if(!claude.length&&data.sources.claude_files){const note=node('p','quota-unavailable',t('claude_unknown')+(rejected?t('claude_events',{events:count(rejected,'limit_event')}):''));note.append(document.createElement('br'),t('claude_setup_before'),node('code','','pler statusline --install'),t('claude_setup_after'));box.append(note);}
  else if(rejected)box.append(node('p','section-note',t('claude_events_selected',{events:count(rejected,'limit_event')})));
  box.append(node('p','section-note',t('quota_note')));
}
function sessionHasQualityLimits(session){return ['tokens_complete','calls_complete','counts_complete','attribution_complete','models_complete'].some(key=>session.quality?.[key]===false);}
function usageVerdictSummary(){
  const data=usageState.data,box=$('usage-verdict-summary');
  if(!box)return;
  box.hidden=!data?.verdicts;if(box.hidden)return;
  if(data.verdicts.readable===false){box.textContent=t('verdict_unreadable');return;}
  // Summed here from the rows so a click updates it without asking the server for the whole view again.
  const sum={useful:{sessions:0,total_tokens:0,api_usd:0},wasted:{sessions:0,total_tokens:0,api_usd:0},none:{sessions:0,total_tokens:0,api_usd:0}};
  for(const session of data.sessions){const row=sum[session.verdict]||sum.none;row.sessions++;row.total_tokens+=session.total_tokens;row.api_usd+=session.api_usd||0;}
  box.textContent=(sum.useful.sessions||sum.wasted.sessions?t('verdict_summary',{useful:count(sum.useful.sessions,'session'),useful_tokens:usageShort(sum.useful.total_tokens),useful_usd:usageUsd(sum.useful.api_usd),wasted:count(sum.wasted.sessions,'session'),wasted_tokens:usageShort(sum.wasted.total_tokens),wasted_usd:usageUsd(sum.wasted.api_usd),none:count(sum.none.sessions,'session')}):t('verdict_hint'))+(data.demo?t('verdict_demo'):'');
}
const checkLines={test:{passed:'check_test_passed',failed:'check_test_failed',hidden:'check_test_hidden'},build:{passed:'check_build_passed',failed:'check_build_failed',hidden:'check_build_hidden'}};
function checkSummaries(session){
  // One short line per kind the agent ran: how its last visible run ended, or that no result was visible.
  const found=['test','build'].filter(kind=>session.checks?.[kind]?.runs).map(kind=>{const row=session.checks[kind],state=row.last||'hidden';return node('small','session-check '+state,t(checkLines[kind][state],{runs:count(row.runs,'run')}));});
  const lines=session.git_activity?.lines;
  if(lines?.added)found.push(node('small','session-check lines',t('lines_kept_row',{share:usagePct(lines.kept/lines.added),added:number(lines.added)})));
  return found;
}
function checkDetail(row){return t('check_detail',{runs:count(row.runs,'run'),last:t(row.last==='passed'?'check_last_passed':row.last==='failed'?'check_last_failed':'check_last_none'),passed:number(row.passed),failed:number(row.failed),hidden:number(row.runs-row.passed-row.failed)});}
function verdictToggle(session){
  const group=node('div','verdict-toggle');group.setAttribute('role','group');group.setAttribute('aria-label',t('verdict_group',{code:usageSessionCode(session)}));
  for(const verdict of ['useful','wasted']){
    const button=node('button','verdict-button verdict-'+verdict,t(verdict==='useful'?'verdict_useful':'verdict_wasted'));button.type='button';
    button.dataset.verdictId=session.id;button.dataset.verdict=verdict;button.setAttribute('aria-pressed',String(session.verdict===verdict));
    button.disabled=usageState.stopped||usageState.data?.verdicts?.readable===false;
    button.addEventListener('click',()=>setVerdict(session.id,button.getAttribute('aria-pressed')==='true'?null:verdict));group.append(button);
  }
  return group;
}
async function setVerdict(id,verdict){
  if(usageState.stopped||usageState.verdictSaving)return;
  usageState.verdictSaving=true;
  try{
    const result=await post('/api/usage/verdict',{id,verdict});if(usageState.stopped)return;
    for(const session of usageState.data?.sessions||[])if(session.id===id)session.verdict=result.verdict;
    // The table row and an open session dialog show the same verdict; update both in place, keeping focus.
    for(const button of document.querySelectorAll('.verdict-button'))if(button.dataset.verdictId===id)button.setAttribute('aria-pressed',String(button.dataset.verdict===result.verdict));
    usageVerdictSummary();
    renderUsageSessions();
  }catch(error){if(!usageState.stopped)notice(error.message);}
  finally{usageState.verdictSaving=false;}
}
function usageSessionName(session){
  if(session.title)return session.title;
  const at=session.started||session.ended;
  return session.project+(at?' · '+usageDate(at):'');
}
const sessionTimeCache=new WeakMap();
function sessionStamp(session,key){let cached=sessionTimeCache.get(session);if(!cached){cached={};sessionTimeCache.set(session,cached);}const value=session[key];if(cached[key]?.value!==value)cached[key]={value,stamp:value?Date.parse(value):-Infinity};return cached[key]?.stamp??-Infinity;}
function filteredUsageSessions(){
  if(!usageState.data)return [];
  const f=usageUI.get().filters,all=usageState.data.sessions,query=f.search.trim().toLocaleLowerCase(LOCALE);
  const works=usageState.data.work_items?.readable===true?usageState.data.work_items.items:[],titles=new Map();
  if(query)for(const item of works)for(const id of item.session_ids){if(!titles.has(id))titles.set(id,[]);titles.get(id).push(item.title);}
  const sessions=all.filter(session=>(!f.quality||sessionHasQualityLimits(session))&&(!query||[session.title||'',session.project,usageAgents[session.agent]||session.agent,'#'+usageSessionCode(session),...session.models.map(model=>model.model),...(titles.get(session.id)||[])].some(value=>value.toLocaleLowerCase(LOCALE).includes(query))));
  const order=f.sort;
  const byTime=(a,b,key)=>sessionStamp(b,key)-sessionStamp(a,key)||b.total_tokens-a.total_tokens||a.id.localeCompare(b.id);
  sessions.sort((a,b)=>order==='recent'?byTime(a,b,'ended'):order==='started'?byTime(a,b,'started'):order==='issues'?(b.errors+b.aborted)-(a.errors+a.aborted)||byTime(a,b,'ended'):b.total_tokens-a.total_tokens||byTime(a,b,'ended'));
  return sessions;
}
function renderUsageSessions(){
  if(!usageState.data)return;
  syncUsageFilters();
  const all=usageState.data.sessions,query=usageUI.get().filters.search.trim().toLocaleLowerCase(LOCALE),sessions=filteredUsageSessions();
  const visible=sessions.slice(0,usageState.pageSize);
  $('usage-session-count').textContent=t('sessions_count',{shown:number(visible.length),sessions:count(sessions.length,'session')})+(query?t('searching',{sessions:count(all.length,'session')}):'');
  if(!sessionGridActive)$('usage-sessions').replaceChildren(...visible.map(session=>{
    const row=node('tr'),first=node('td'),button=node('button','text-button',usageSessionName(session)),code=usageSessionCode(session);
    row.setAttribute('data-session-id',session.id);
    button.setAttribute('aria-label',usageSessionName(session)+' · '+(usageAgents[session.agent]||session.agent)+' · '+code+t('open_detail'));button.addEventListener('click',()=>openUsageSession(session));
    first.append(button,node('small','task-subject',(usageAgents[session.agent]||session.agent)+' · #'+code));
    if(session.source_note)first.append(node('small','session-issues',session.source_note));
    if(session.models.length)first.append(node('small','session-model',session.models.map(model=>model.model).join(', ')));
    if(session.errors||session.aborted)first.append(node('small','session-issues',count(session.errors,'error')+' · '+count(session.aborted,'interruption')));
    if(sessionHasQualityLimits(session))first.append(node('small','session-issues',t('quality_session')));
    if(session.git_activity?.matched_events)first.append(node('small','session-git-hint',t('git_row',{events:count(session.git_activity.matched_events,'git_event')})));
    const dates=node('td','session-dates');
    for(const [name,value] of [[t('start'),session.started],[t('last_activity'),session.ended]]){const line=node('div'),time=node('time','',usageDate(value));if(value)time.dateTime=value;line.append(node('span','date-label',name+': '),time);dates.append(line);}
    dates.append(node('small','task-subject',t('span',{d:usageDuration(session.span_seconds)})));
    const verdict=node('td','verdict-cell');verdict.append(verdictToggle(session),...checkSummaries(session));
    row.append(first,dates,node('td','task-number',number(session.total_tokens)),node('td','task-number',session.calls_complete?number(session.calls):t('unknown')),node('td','task-number',usagePct(session.cache_read_share)),verdict);return row;
  }));
  usageVerdictSummary();
  $('usage-search-empty').hidden=Boolean(sessions.length);$('usage-more').hidden=usageState.pageSize>=sessions.length;
  $('usage-more').textContent=t('more_count',{count:number(Math.min(20,sessions.length-visible.length))});
  usageUI.publish('sessions',{items:visible,total:sessions.length,works:usageState.data.work_items?.readable===true?usageState.data.work_items.items:[]});
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
    const lines=activity.lines;
    if(lines?.added)box.append(node('p','git-outcome',t('git_lines',{share:usagePct(lines.kept/lines.added),kept:number(lines.kept),added:number(lines.added),commits:count(lines.commits,'commit')})+(lines.unmeasured?t('git_lines_unmeasured',{n:number(lines.unmeasured)}):'')),node('p','section-note',t('git_lines_note')));
    const details=node('details','git-events'),summary=node('summary','',t('git_details')),list=node('ol');details.open=activity.events.length<=5;
    for(const event of activity.events){const item=node('li'),time=node('time','',usageDate(event.at));time.dateTime=event.at;const label=node('span','',t(gitLabels[event.kind]||'git_other'));if(event.commit)label.append(node('code','git-event-ref',event.commit));if(event.on_branch!=null)label.append(node('small','git-branch'+(event.on_branch?'':' git-branch-off'),t(event.on_branch?'git_on_branch':'git_off_branch')));item.append(time,label);list.append(item);}
    details.append(summary,list);box.append(details);
    if(activity.omitted_events)box.append(node('p','',t('git_more',{n:number(activity.omitted_events)})));
  }else box.append(node('p','',t('git_zero')));
  if(activity.coverage_limited)box.append(node('p','git-limited',t('git_limited')));
  box.append(node('p','git-history-note',t('git_history_from',{at:usageDate(activity.history_from)})));content.append(box);
}
function openUsageSession(session){
  usageState.sessionRequest=(usageState.sessionRequest||0)+1;
  $('usage-session-title').textContent=usageSessionName(session);const content=$('usage-session-detail'),dl=node('dl');
  const fields=[[t('field_agent'),usageAgents[session.agent]||session.agent],[t('field_code'),'#'+usageSessionCode(session)],[t('start'),usageDate(session.started)],[t('last_activity'),usageDate(session.ended)],[t('field_span'),usageDuration(session.span_seconds)],[t('field_active'),usageDuration(session.active_ms==null?null:session.active_ms/1000)],[t('field_total'),number(session.total_tokens)],[t('field_api'),session.api_priced_share?usageUsd(session.api_usd)+(session.api_priced_share<0.9995?' ('+usagePct(session.api_priced_share)+')':''):t('unknown')],...usageTokens.map(([key,label])=>[label,number(session.tokens[key])]),[t('field_reasoning'),number(session.tokens.reasoning)],[t('field_calls'),session.calls_complete?number(session.calls):t('unknown')],[t('field_prompts'),number(session.prompts)],[t('field_issues'),session.errors+' / '+session.aborted],[t('field_tools'),number(session.tool_calls)],[t('field_files'),number(session.edited_files)],...(session.checks?.test?[[t('field_tests'),checkDetail(session.checks.test)]]:[]),...(session.checks?.build?[[t('field_builds'),checkDetail(session.checks.build)]]:[])];
  fields.forEach(([label,value])=>dl.append(node('dt','',label),node('dd','',value)));
  const verdict=node('div','verdict-dialog');verdict.append(node('span','',t('field_verdict')),verdictToggle(session));
  content.replaceChildren(node('p','session-detail-intro',t('detail_intro')),verdict,dl);
  if(session.source_note)content.append(node('p','notice',session.source_note));
  if(session.models.length){content.append(node('h3','detail-model-title',t('models_in_session')));for(const model of session.models){const row=node('div','usage-rank');row.append(node('span','model-name',model.model==='unknown'?t('unknown'):model.model),node('strong','',t('tokens',{n:number(model.total_tokens)})),node('small','',session.calls_complete?count(model.calls,'logged_call'):t('split_unknown')));content.append(row);}}
  content.append(node('p','section-note',t('files_note')));
  if(session.checks?.test||session.checks?.build)content.append(node('p','section-note',t('check_note')));
  for(const note of session.notes)content.append(node('p','section-note',note));
  if(session.quota_burn.length)content.append(node('p','section-note',t('burn',{items:session.quota_burn.map(w=>t('burn_item',{window:usageWindow(w.window_minutes),points:w.percentage_points})).join(' · ')})));
  renderGitActivity(content,session.git_activity);
  content.append(node('p','section-note',t('metadata_note')));workState.openSession=session.id;renderSessionWorkItems();if(typeof window.plerShowSession==='function')window.plerShowSession(session);else $('usage-session-dialog').showModal();usageUI.publish('selection',session.id);
}
async function inspectUsageSession(id){
  const request=(usageState.sessionRequest||0)+1,revision=usageState.revision;usageState.sessionRequest=request;
  const current=()=>!usageState.stopped&&request===usageState.sessionRequest&&revision===usageState.revision;
  try{const value=await api('/api/usage/session?'+new URLSearchParams({id,lang:LANG}));if(current())openUsageSession(value.session);}
  catch(error){if(current())notice(error.message);}
}
function clearUsageDownload(){
  if(usageState.downloadUrl)URL.revokeObjectURL(usageState.downloadUrl);
  usageState.downloadUrl=null;
  usageState.downloadQuery=null;
  $('usage-download-result').hidden=true;
  $('usage-download-link').removeAttribute('href');
}
function clearUsageBackupDownload(){
  if(usageState.backupUrl)URL.revokeObjectURL(usageState.backupUrl);
  usageState.backupUrl=null;
  if($('usage-backup-download-result'))$('usage-backup-download-result').hidden=true;
  if($('usage-backup-download-link'))$('usage-backup-download-link').removeAttribute('href');
}
function syncBackupControls(){
  const download=$('usage-backup-download'),check=$('usage-backup-check'),file=$('usage-backup-file');
  if(!download||!check||!file)return;
  const data=usageState.data,busy=usageState.stopped||usageState.loading||usageState.exporting||usageState.archiveClearing||usageState.metadataChanging||usageState.backupBusy||usageState.workBusy;
  const unavailable=!data?.has_snapshot||data.demo||!data.archive?.available;
  download.disabled=Boolean(busy||unavailable);check.disabled=Boolean(busy||unavailable||!file.files?.length);file.disabled=Boolean(busy||unavailable);
  download.textContent=t(usageState.backupBusy==='download'?'backup_preparing':'backup_download');
  check.textContent=t(usageState.backupBusy==='check'?'backup_checking':'backup_check');
  download.setAttribute('aria-busy',String(usageState.backupBusy==='download'));check.setAttribute('aria-busy',String(usageState.backupBusy==='check'));
  if($('usage-refresh'))$('usage-refresh').disabled=Boolean(busy||data?.state==='scanning');
}
async function backupResponse(path,body,type){
  let response;
  try{response=await fetch(path+'?lang='+LANG,{method:'POST',cache:'no-store',headers:{'Content-Type':type,'X-PLER-Token':token},body});}
  catch(_){throw new Error(t('err_unreachable'));}
  if(!response.ok){let error;try{error=await response.json();}catch(_){throw new Error(t('err_closed'));}throw new Error(error.error||t('err_read'));}
  return response;
}
async function downloadUsageBackup(){
  const button=$('usage-backup-download');
  if(!button||button.disabled||usageState.backupBusy||usageState.stopped)return;
  if(!confirm(t('backup_privacy')))return;
  rememberActionFocus(button);usageState.backupBusy='download';clearUsageBackupDownload();syncArchiveButton();syncExportButton();notice('');
  try{
    const response=await backupResponse('/api/usage/backup','{}','application/json'),blob=await response.blob();
    if(usageState.stopped)return;
    const link=$('usage-backup-download-link');usageState.backupUrl=URL.createObjectURL(blob);link.href=usageState.backupUrl;link.download='PLER-backup.zip';
    $('usage-backup-download-result').hidden=false;link.click();
  }catch(error){if(!usageState.stopped)notice(error.message);}
  finally{usageState.backupBusy=null;syncArchiveButton();syncExportButton();restoreActionFocus();}
}
async function checkUsageBackup(){
  const button=$('usage-backup-check'),file=$('usage-backup-file')?.files?.[0];
  if(!button||button.disabled||usageState.backupBusy||usageState.stopped)return;
  const maximum=Number(document.querySelector('meta[name="pler-backup-max"]')?.content);
  if(!file||!Number.isFinite(maximum)||maximum<=0||file.size<=0||file.size>maximum){notice(t('backup_invalid_file'));return;}
  rememberActionFocus(button);usageState.backupBusy='check';$('usage-backup-result').hidden=true;syncArchiveButton();syncExportButton();notice('');
  try{
    const response=await backupResponse('/api/usage/backup/check',file,'application/octet-stream'),value=(await response.json()).backup;
    if(usageState.stopped)return;
    $('usage-backup-result').textContent=t('backup_checked',{version:value.version,date:usageDate(value.created_at),files:number(value.archive_files),verdicts:number(value.verdicts),works:number(value.work_items??0),links:number(value.work_links??0),quota:number(value.quota_samples),retention:t(value.retention_enabled?'retention_short_on':'retention_short_off')});
    $('usage-backup-result').hidden=false;
  }catch(error){if(!usageState.stopped)notice(error.message);}
  finally{usageState.backupBusy=null;syncArchiveButton();syncExportButton();restoreActionFocus();}
}
function syncArchiveButton(){
  const button=$('usage-archive-clear'),archive=usageState.data?.archive;
  if(!button)return;
  const busy=usageState.stopped||usageState.loading||usageState.exporting||usageState.archiveClearing||usageState.metadataChanging||usageState.backupBusy||usageState.workBusy;
  button.disabled=Boolean(busy||!archive?.available||(!archive?.stored_bytes&&!archive?.stored_files&&!archive?.errors));
  button.textContent=t(usageState.archiveClearing?'archive_clearing':'archive_clear');
  button.setAttribute('aria-busy',String(Boolean(usageState.archiveClearing)));
  for(const id of ['usage-retention','usage-cache-reset'])if($(id))$(id).disabled=Boolean(busy||!archive?.available);
  syncBackupControls();
  if($('usage-work-items'))syncWorkControls();
}
function renderUsageArchive(data){
  const archive=data.archive,box=$('usage-archive-controls');
  box.hidden=Boolean(data.demo)||!data.has_snapshot||!archive;
  if(!box.hidden){
    const bytes=value=>number(Math.round((value||0)/1024))+' KiB';
    $('usage-archive-status').textContent=archive.available?t(archive.retention_enabled?'retention_on':'retention_off',{bytes:bytes(archive.stored_bytes),days:number(archive.max_days),files:number(archive.max_files),limit:bytes(archive.max_bytes)}):t('archive_disabled');
    $('usage-retention-summary').textContent=t(archive.retention_enabled?'retention_short_on':'retention_short_off');
    $('usage-retention').checked=Boolean(archive.retention_enabled);
    $('usage-archive-clear').hidden=!archive.available;
  }
  syncArchiveButton();
}
async function changeMetadata(action){
  if(usageState.stopped||usageState.metadataChanging||usageState.exporting||usageState.archiveClearing||usageState.backupBusy||usageState.workBusy)return;
  const retention=action==='retention',control=$(retention?'usage-retention':'usage-cache-reset');
  rememberActionFocus(control);usageState.metadataChanging=true;clearUsageDownload();syncArchiveButton();syncExportButton();notice('');
  try{await post(retention?'/api/usage/retention':'/api/usage/cache/reset',retention?{enabled:Boolean(control.checked)}:{});if(usageState.stopped)return;usageState.revision=(usageState.revision||0)+1;usageState.data=null;notice(t(retention?'retention_changed':'cache_reset_done'));await loadUsage();}
  catch(error){if(!usageState.stopped){notice(error.message);if(retention)control.checked=Boolean(usageState.data?.archive?.retention_enabled);}}
  finally{usageState.metadataChanging=false;syncArchiveButton();syncExportButton();restoreActionFocus();}
}
async function clearUsageArchive(){
  const button=$('usage-archive-clear');
  if(usageState.stopped||usageState.archiveClearing||usageState.exporting||button.disabled)return;
  // Copies of deleted logs exist nowhere else: one click must not erase them.
  if(!confirm(t('archive_clear_help')))return;
  rememberActionFocus(button);
  usageState.archiveClearing=true;clearUsageDownload();syncArchiveButton();syncExportButton();notice('');
  try{
    await post('/api/usage/archive/clear',{});
    if(usageState.stopped)return;
    usageState.revision=(usageState.revision||0)+1;
    usageState.data=null;
    $('usage-project').value='all';
    notice(t('archive_cleared'));
    await loadUsage();
  }catch(error){if(!usageState.stopped)notice(error.message);}
  finally{usageState.archiveClearing=false;syncArchiveButton();syncExportButton();restoreActionFocus();}
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
  button.disabled=Boolean(usageState.stopped||usageState.loading||usageState.exporting||usageState.archiveClearing||usageState.metadataChanging||usageState.backupBusy||usageState.workBusy||!usageState.data?.has_snapshot||!matches);
  button.textContent=t(usageState.exporting?'export_preparing':'export');
  button.setAttribute('aria-busy',String(usageState.exporting));
}
async function exportUsage(){
  if(usageState.stopped||usageState.exporting||!usageState.data?.has_snapshot||$('usage-export').disabled)return;
  const query=usageQuery(),revision=usageState.revision,mask=Boolean($('usage-export-mask')?.checked);
  rememberActionFocus($('usage-export'));
  usageState.exporting=true;clearUsageDownload();syncExportButton();syncArchiveButton();notice('');
  try{
    const data=await api('/api/usage/export?'+query+'&mask_projects='+(mask?'1':'0'));
    if(usageState.stopped||query!==usageQuery()||revision!==usageState.revision||mask!==Boolean($('usage-export-mask')?.checked))return;
    usageState.downloadUrl=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));
    usageState.downloadQuery=query;
    const link=$('usage-download-link');link.href=usageState.downloadUrl;link.download=t('export_file');
    $('usage-download-status').textContent=t('export_started');$('usage-download-result').hidden=false;link.click();
  }catch(error){if(!usageState.stopped)notice(error.message);}
  finally{usageState.exporting=false;syncExportButton();syncArchiveButton();restoreActionFocus();}
}
function showMoreUsageSessions(){
  const previous=$('usage-sessions').children.length;
  usageState.pageSize+=20;renderUsageSessions();
  $('usage-sessions').querySelectorAll('button')[previous]?.focus();
}
// Work titles are manual, private metadata. Keep their state separate from measured usage.
const workState={ready:false,selected:'',pageSize:20,createDraft:'',renameDrafts:{},detailDrafts:{},sessionDrafts:{},sessionChoices:{},sessionForms:{},openSession:null,action:0,navigation:false,needsRefresh:false,deleteID:null};
function workViewMemory(){const value={selected:workState.selected,create:workState.createDraft,rename:workState.renameDrafts};if(Object.keys(workState.detailDrafts).length)value.details=workState.detailDrafts;if(Object.keys(followState.drafts).length)value.follow=followState.drafts;if($('usage-work-followups').open)value.followOpen=true;return value;}
function restoreWorkMemory(){
  if(workState.ready)return;workState.ready=true;
  const saved=usageState.workRestore;delete usageState.workRestore;
  if(!saved||typeof saved!=='object')return;
  if(typeof saved.selected==='string'&&/^[a-f0-9]{24}$/.test(saved.selected))workState.selected=saved.selected;
  if(typeof saved.create==='string')workState.createDraft=saved.create.slice(0,240);
  if(saved.followOpen===true)$('usage-work-followups').open=true;
  if(saved.follow&&typeof saved.follow==='object')for(const [id,draft] of Object.entries(saved.follow).slice(0,200)){
    if(!/^[a-f0-9]{24}$/.test(id)||!draft||typeof draft.change!=='string'||typeof draft.observation!=='string'||!followTriggers.includes(draft.trigger))continue;
    const clean={trigger:draft.trigger,change:draft.change.slice(0,2000),observation:draft.observation.slice(0,2000),reviews:{}};
    if(draft.reviews&&typeof draft.reviews==='object')for(const [rid,review] of Object.entries(draft.reviews).slice(0,10))if(/^[a-f0-9]{24}$/.test(rid)&&review&&followContexts.includes(review.context)&&typeof review.note==='string')clean.reviews[rid]={context:review.context,note:review.note.slice(0,2000)};
    followState.drafts[id]=clean;
  }
  if(saved.rename&&typeof saved.rename==='object')for(const [id,title] of Object.entries(saved.rename).slice(0,200))if(/^[a-f0-9]{24}$/.test(id)&&typeof title==='string')workState.renameDrafts[id]=title.slice(0,240);
  if(saved.details&&typeof saved.details==='object')for(const [id,draft] of Object.entries(saved.details).slice(0,200)){
    if(/^[a-f0-9]{24}$/.test(id)&&draft&&typeof draft.goal==='string'&&typeof draft.result_note==='string'
      &&workOutcomes.includes(draft.outcome)&&/^[a-f0-9]{24}$/.test(draft.expected_revision))
      workState.detailDrafts[id]={goal:draft.goal.slice(0,2000),outcome:draft.outcome,result_note:draft.result_note.slice(0,2000),expected_revision:draft.expected_revision,conflict:draft.conflict===true};
  }
}
const workOutcomes=['not_recorded','partial','completed','not_completed'];
const workOutcomeWords={not_recorded:'work_outcome_not_recorded',partial:'work_outcome_partial',completed:'work_outcome_completed',not_completed:'work_outcome_not_completed'};
function workOutcomeName(value){return t(workOutcomeWords[value]||workOutcomeWords.not_recorded);}
function cleanWorkText(value){return value.replace(/\r\n?/g,'\n').trim();}
function workDetails(item){return {goal:item.goal||'',outcome:item.outcome||'not_recorded',result_note:item.result_note||''};}
function validWorkDetails(value){return workOutcomes.includes(value.outcome)&&['goal','result_note'].every(key=>typeof value[key]==='string'&&[...cleanWorkText(value[key])].length<=1000&&!/[\u0000-\u0009\u000b-\u001f\u007f-\u009f\ud800-\udfff\u2028\u2029]/u.test(cleanWorkText(value[key])));}
function changedWorkDetails(item,draft){return Boolean(draft)&&['goal','result_note'].some(key=>cleanWorkText(draft[key])!==(item[key]||''))||Boolean(draft)&&draft.outcome!==(item.outcome||'not_recorded');}
function workDetailsStatus(item){
  const draft=workState.detailDrafts[item.id],status=$('usage-work-details-status');
  status.textContent=t(draft?.conflict?'work_details_conflict':draft&&!validWorkDetails(draft)?'work_details_invalid':changedWorkDetails(item,draft)?'work_details_unsaved':'work_details_current');
}
function captureWorkDetails(){
  const item=selectedWork();if(!item||usageState.stopped||workState.navigation||usageState.workBusy)return;
  const prior=workState.detailDrafts[item.id];
  workState.detailDrafts[item.id]={goal:$('usage-work-goal').value,outcome:$('usage-work-outcome').value,
    result_note:$('usage-work-result-note').value,expected_revision:prior?.expected_revision||item.details_revision||'',conflict:prior?.conflict===true};
  workDetailsStatus(item);syncWorkControls();
}
function renderWorkDetails(item){
  const saved=workDetails(item),draft=workState.detailDrafts[item.id];
  if(draft&&draft.expected_revision!==item.details_revision)draft.conflict=true;
  const fields=draft||saved;
  $('usage-work-goal').value=fields.goal;$('usage-work-outcome').value=fields.outcome;$('usage-work-result-note').value=fields.result_note;
  $('usage-work-goal-view').textContent=saved.goal?t('work_goal_view',{text:saved.goal}):t('work_goal_empty');
  $('usage-work-outcome-view').textContent=t('work_outcome_view',{outcome:workOutcomeName(saved.outcome)});
  $('usage-work-result-view').hidden=!saved.result_note;$('usage-work-result-view').textContent=saved.result_note?t('work_result_view',{text:saved.result_note}):'';
  const when=new Date(item.outcome_at*1000),validTime=item.outcome_at!=null&&Number.isFinite(when.getTime());
  $('usage-work-outcome-time').hidden=!validTime;$('usage-work-outcome-time').textContent=validTime?t('work_outcome_time',{at:usageDate(when.toISOString())}):'';
  $('usage-work-details-conflict').hidden=!draft?.conflict;
  $('usage-work-latest-goal').textContent=saved.goal?t('work_goal_view',{text:saved.goal}):t('work_goal_empty');
  $('usage-work-latest-outcome').textContent=t('work_outcome_view',{outcome:workOutcomeName(saved.outcome)});
  $('usage-work-latest-result').textContent=t('work_result_view',{text:saved.result_note||'—'});
  workDetailsStatus(item);
}
function reviewWorkDetails(keep){
  const item=selectedWork(),draft=item&&workState.detailDrafts[item.id];if(workBlocked()||!draft)return;
  if(keep){draft.expected_revision=item.details_revision;draft.conflict=false;}else delete workState.detailDrafts[item.id];
  notice('');renderWorkDetails(item);syncWorkControls();$('usage-work-goal').focus();
}
function saveWorkDetails(){
  const item=selectedWork(),draft=item&&workState.detailDrafts[item.id];
  if(workBlocked()||!draft||draft.conflict||!validWorkDetails(draft)||!changedWorkDetails(item,draft)||!/^[a-f0-9]{24}$/.test(draft.expected_revision))return;
  return performWorkAction({action:'describe',id:item.id,goal:cleanWorkText(draft.goal),outcome:draft.outcome,
    result_note:cleanWorkText(draft.result_note),expected_revision:draft.expected_revision},{focus:'details'});
}
function renderWorkObservations(item){
  const box=$('usage-work-observations');box.replaceChildren();
  if(!item.selected_sessions){box.append(node('p','section-note',t('work_obs_none')));return;}
  const observed=item.observations;if(!observed){box.append(node('p','section-note',t('work_obs_unavailable')));return;}
  for(const [kind,key] of [['test','work_obs_test'],['build','work_obs_build']]){
    const value=observed[kind];if(!value)continue;
    box.append(node('p','',value.sessions?t('work_obs_checks',{kind:t(key),passed:number(value.passed),failed:number(value.failed),unknown:number(value.unknown)}):t('work_obs_no_checks',{kind:t(key)})));
  }
  const git=observed.git;
  box.append(node('p','',git?.available_sessions?t('work_obs_git',{available:number(git.available_sessions),active:number(git.activity_sessions),limited:number(git.limited_sessions)}):t('work_obs_git_unknown')));
}
// Fetch these private snapshots only when this section is opened, never on initial load.
const followState={key:'',data:null,loading:false,error:'',request:0,drafts:{},deleting:null};
const followTriggers=['quota','concentration','session_pattern','other'],followContexts=['unknown','similar','different'];
function followKey(){const item=selectedWork();return item?JSON.stringify([item.id,usageState.data.scanned_at,item.followup_revision,item.session_ids]):'';}
function followDraft(){const id=selectedWork()?.id;if(!id)return null;return followState.drafts[id]??(followState.drafts[id]={trigger:'other',observation:'',change:'',reviews:{}});}
function validFollowText(text,required=false){const value=cleanWorkText(text);return (!required||value.length>0)&&[...value].length<=1000&&!/[\u0000-\u0009\u000b-\u001f\u007f-\u009f\ud800-\udfff\u2028\u2029]/u.test(value);}
function followDate(value){return new Intl.DateTimeFormat(LANG==='tr'?'tr-TR':'en-GB',{dateStyle:'medium',timeStyle:'short',timeZone:'UTC'}).format(new Date(value))+' UTC';}
function followPercent(value){return new Intl.NumberFormat(LANG==='tr'?'tr-TR':'en-GB',{style:'percent',maximumFractionDigits:2,signDisplay:'exceptZero'}).format(value/100);}
function followReading(value){return t('follow_reading',{since:followDate(value.since),until:followDate(value.until),sessions:number(value.sessions),responses:number(value.responses),tokens:number(value.tokens),excluded:number(value.excluded_sessions+value.boundary_sessions),missing:number(value.missing_sessions)});}
function followWord(prefix,value){return t(prefix+value);}
function followLimits(box,limits){if(!limits?.length)return;const list=node('ul','follow-limits');for(const reason of limits)list.append(node('li','',followWord('follow_limit_',reason)));box.append(list);}
function syncFollowControls(){
  const current=followState.key===followKey(),data=current&&followState.data,blocked=workBlocked()||followState.loading||!data;
  const draft=followState.drafts[selectedWork()?.id];
  $('usage-follow-reload').disabled=workBlocked()||followState.loading;
  for(const id of ['usage-follow-change','usage-follow-observation','usage-follow-trigger'])$(id).disabled=blocked;
  $('usage-follow-start').disabled=blocked||!data.fresh||data.items.some(r=>r.status==='open')||data.items.length>=10||!draft||!validFollowText(draft.change,true)||!validFollowText(draft.observation);
  for(const control of $('usage-follow-records').querySelectorAll('button,select,textarea')){
    const record=data&&data.items.find(r=>r.id===control.followRecord);
    const review=record&&draft?.reviews?.[record.id];
    control.disabled=blocked||!record||(control.followAction==='review'&&(!record.ready||!validFollowText(review?.note||'')));
  }
}
async function loadFollowups(force=false){
  if(!$('usage-work-followups').open||!selectedWork()||workBlocked())return;
  const key=followKey();if(!force&&followState.key===key&&(followState.data||followState.loading||followState.error))return;
  const request=++followState.request,id=selectedWork().id;
  followState.key=key;followState.data=null;followState.loading=true;followState.error='';renderFollowups();syncWorkControls();
  const current=()=>!usageState.stopped&&!workState.navigation&&request===followState.request&&key===followKey()&&$('usage-work-followups').open;
  try{const data=await api('/api/usage/work/followups?'+new URLSearchParams({work:id,lang:LANG}));if(!current())return;
    if(data.ok!==true)throw new Error(t('follow_failed'));followState.data=data;
  }catch(error){if(current())followState.error=error.message;}
  finally{if(request===followState.request){followState.loading=false;if(current()){renderFollowups();syncWorkControls();}}}
}
function renderFollowups(){
  if(!$('usage-work-followups').open)return;
  const status=$('usage-follow-status'),box=$('usage-follow-records'),form=$('usage-follow-form');
  box.replaceChildren();form.hidden=true;
  const data=followState.key===followKey()&&followState.data;
  status.textContent=followState.loading?t('follow_loading'):followState.error||(!data?t('follow_reload_hint'):!data.fresh?t('follow_stale'):'');
  if(!data)return;
  const draft=followDraft();
  for(const record of data.items){
    const card=node('article','follow-record');card.append(node('h3','',followWord('follow_status_',record.status)),node('p','follow-change',record.change));
    card.append(node('p','section-note',t('follow_reason',{reason:followWord('follow_trigger_',record.trigger)})));
    if(record.observation)card.append(node('p','follow-note',record.observation));
    const windows=node('div','follow-windows'),before=node('section','');before.append(node('h4','',t('follow_before')),node('p','',followReading(record.baseline)));windows.append(before);
    const afterValue=record.review?.after||record.after_preview;
    if(afterValue){const after=node('section','');after.append(node('h4','',t(record.status==='reviewed'?'follow_after':'follow_after_preview')),node('p','',followReading(afterValue)));windows.append(after);}card.append(windows);
    if(record.status==='reviewed'){
      card.append(node('p','section-note',t('follow_context_saved',{context:followWord('follow_context_',record.review.context)})));
      if(record.review.note)card.append(node('p','follow-note',record.review.note));
      if(record.comparison.limitations.length){card.append(node('p','follow-unresolved',t('follow_no_comparison')));followLimits(card,record.comparison.limitations);}
      else{card.append(node('p','section-note',t('follow_metric')));for(const c of record.comparison.cohorts)card.append(node('p','follow-delta',t('follow_delta',{agent:usageAgents[c.agent]||c.agent,project:c.project_id.slice(0,8),model:c.model,before:number(c.before),after:number(c.after),percent:followPercent(c.change_percent)})));}
    }else if(record.status==='open'){
      card.append(node('p','section-note',t('follow_due',{date:followDate(record.due_at)})));
      if(record.ready){
        const saved=draft.reviews[record.id]??(draft.reviews[record.id]={context:'unknown',note:''});
        const review=node('form','work-details-form'),label=node('label','',t('follow_context')),select=node('select','');select.id='follow-context-'+record.id;label.htmlFor=select.id;
        for(const value of followContexts){const option=node('option','',followWord('follow_context_',value));option.value=value;select.append(option);}select.value=saved.context;
        const noteLabel=node('label','',t('follow_review_note')),note=node('textarea','');note.rows=2;note.maxLength=2000;note.id='follow-note-'+record.id;noteLabel.htmlFor=note.id;note.value=saved.note;
        select.addEventListener('change',()=>{saved.context=select.value;syncWorkControls();});note.addEventListener('input',()=>{saved.note=note.value;syncWorkControls();});
        const save=node('button','secondary',t('follow_review'));save.type='submit';save.followAction='review';
        for(const control of [select,note,save])control.followRecord=record.id;
        review.addEventListener('submit',event=>{event.preventDefault();runFollowup('review_followup',record);});review.append(label,select,noteLabel,note,save);card.append(review);
      }else card.append(node('p','section-note',t('follow_wait')));
      followLimits(card,record.baseline.limitations);
      const cancel=node('button','quiet',t('follow_cancel'));cancel.type='button';cancel.followRecord=record.id;cancel.addEventListener('click',()=>runFollowup('cancel_followup',record));card.append(cancel);
    }else if(record.cancel_note)card.append(node('p','follow-note',record.cancel_note));
    const remove=node('button','quiet',t(followState.deleting===record.id?'follow_delete_confirm':'follow_delete'));remove.type='button';remove.followRecord=record.id;
    remove.addEventListener('click',()=>{if(followState.deleting!==record.id){followState.deleting=record.id;renderFollowups();syncWorkControls();}else runFollowup('delete_followup',record);});card.append(remove);
    if(followState.deleting===record.id){card.append(node('p','section-note',t('follow_delete_warning')));const keep=node('button','quiet',t('follow_keep'));keep.type='button';keep.followRecord=record.id;keep.addEventListener('click',()=>{followState.deleting=null;renderFollowups();syncWorkControls();});card.append(keep);}
    box.append(card);
  }
  if(!data.items.length)box.append(node('p','section-note',t('follow_empty')));
  if(!data.items.some(r=>r.status==='open')&&data.items.length<10){form.hidden=false;$('usage-follow-baseline').textContent=followReading(data.preview);$('usage-follow-change').value=draft.change;$('usage-follow-observation').value=draft.observation;$('usage-follow-trigger').value=draft.trigger;followLimits(box,data.preview.limitations);}
}
function runFollowup(action,record=null){
  const data=followState.key===followKey()&&followState.data,item=selectedWork(),draft=followDraft();
  if(workBlocked()||followState.loading||!data||!item)return;
  let body={action,id:item.id,expected_revision:action==='start_followup'?data.preview_revision:action==='review_followup'?record.review_revision:record.revision};
  if(action==='start_followup'){
    if(!data.fresh||!validFollowText(draft.change,true)||!validFollowText(draft.observation)||data.items.some(r=>r.status==='open'))return;
    Object.assign(body,{trigger:draft.trigger,observation:cleanWorkText(draft.observation),change:cleanWorkText(draft.change)});
  }else{body.record_id=record.id;if(action==='review_followup'){if(!record.ready)return;const review=draft.reviews[record.id]||{context:'unknown',note:''};if(!validFollowText(review.note))return;Object.assign(body,{context:review.context,note:cleanWorkText(review.note)});}else if(action==='cancel_followup')body.note='';}
  return performWorkAction(body,{focus:'followup'});
}
function workProjection(){return usageState.data?.work_items;}
function selectedWork(){return workProjection()?.items?.find(item=>item.id===workState.selected);}
function workLabel(item){return item.title+' · #'+item.id.slice(0,8);}
function workBlocked(){return Boolean(usageState.stopped||workState.navigation||usageState.loading||usageState.workBusy||usageState.exporting||usageState.archiveClearing||usageState.metadataChanging||usageState.backupBusy||usageState.data?.state==='scanning'||!usageState.data?.has_snapshot||workProjection()?.readable!==true||workState.needsRefresh);}
function validWorkTitle(value){const title=value.trim();return [...title].length>0&&[...title].length<=120&&!/[\u0000-\u001f\u007f-\u009f\ud800-\udfff\u2028\u2029]/u.test(title);}
function workUsageText(key,value){const share=value.api_priced_share,api=!value.total_tokens?'—':!share?t('work_unpriced'):share<0.9995?t('work_api_covered',{amount:usageUsd(value.api_usd),share:usagePct(share)}):usageUsd(value.api_usd);return t(key,{tokens:number(value.total_tokens),calls:value.calls_complete===false?t('unknown'):number(value.calls),api});}
function workQualityLimited(value){return ['tokens_complete','calls_complete','attribution_complete','models_complete'].some(key=>value[key]===false);}
function syncWorkControls(){
  const box=$('usage-work-items');if(!box)return;
  const blocked=workBlocked(),item=selectedWork();
  for(const root of [box,$('usage-session-work-items')])if(root)for(const control of root.querySelectorAll('button,input,select,textarea'))control.disabled=blocked;
  $('usage-work-create').disabled=blocked||!validWorkTitle($('usage-work-create-title').value);
  $('usage-work-select').disabled=blocked||!workProjection()?.items?.length;
  $('usage-work-rename').disabled=blocked||!item||!validWorkTitle($('usage-work-rename-title').value)||$('usage-work-rename-title').value.trim()===item.title;
  $('usage-work-delete').disabled=blocked||!item;
  const draft=item&&workState.detailDrafts[item.id];
  $('usage-work-details-save').disabled=blocked||!draft||draft.conflict||!validWorkDetails(draft)||!changedWorkDetails(item,draft)||!/^[a-f0-9]{24}$/.test(draft.expected_revision);
  $('usage-work-details-keep').disabled=blocked||!draft?.conflict;
  $('usage-work-details-discard').disabled=blocked||!draft;
  $('usage-work-reload').hidden=workProjection()?.readable===true&&!workState.needsRefresh;
  $('usage-work-reload').disabled=Boolean(usageState.stopped||workState.navigation||usageState.loading||usageState.workBusy||usageState.data?.state==='scanning');
  $('usage-work-create').textContent=t(usageState.workBusy==='create'?'work_saving':'work_create');
  const choice=$('usage-session-work-select'),link=$('usage-session-work-link'),create=$('usage-session-work-create'),title=$('usage-session-work-title');
  if(choice){choice.disabled=blocked||choice.options.length<=1;link.disabled=blocked||!choice.value;create.disabled=blocked||!validWorkTitle(title.value);}
  const deleting=Boolean(usageState.workBusy&&workState.deleteID);
  $('usage-work-delete-confirm').disabled=blocked||!workState.deleteID;
  $('usage-work-delete-cancel').disabled=Boolean(usageState.stopped||deleting);
  $('usage-work-delete-confirm').textContent=t(deleting?'work_saving':'work_delete_confirm');
  box.setAttribute('aria-busy',String(Boolean(usageState.workBusy)));
  syncFollowControls();
  usageUI.publish('work',workProjection(),true);
}
function renderWorkItems(data){
  restoreWorkMemory();workState.needsRefresh=false;
  const box=$('usage-work-items'),value=data.work_items,readable=value?.readable===true,items=readable?value.items:[];
  box.hidden=!data.has_snapshot;$('usage-work-unavailable').hidden=readable;
  $('usage-work-empty').hidden=!readable||items.length>0;
  $('usage-work-summary').hidden=!readable||!items.length;
  $('usage-work-create-title').value=workState.createDraft;
  const picker=$('usage-work-select');picker.replaceChildren();
  if(!items.length){const empty=node('option','',t('work_choose'));empty.value='';picker.append(empty);}
  for(const item of items){const option=node('option','',workLabel(item));option.value=item.id;picker.append(option);}
  if(readable&&!items.some(item=>item.id===workState.selected))workState.selected=items[0]?.id||'';
  picker.value=workState.selected;
  if(readable&&items.length){
    const summary=value.summary;
    $('usage-work-summary').replaceChildren(node('span','',t('work_summary',{works:number(summary.items),selected:number(summary.selected_sessions),unassigned:number(summary.unassigned_sessions),outside:number(summary.outside_selection),missing:number(summary.missing_sessions),overlap:number(summary.overlapping_sessions)})));
    if(summary.selected_sessions)$('usage-work-summary').append(node('strong','work-union',workUsageText('work_union',summary)));
    if(summary.selected_sessions&&workQualityLimited(summary))$('usage-work-summary').append(node('span','section-note work-summary-quality',t('work_quality')));
  }
  renderSelectedWork();renderSessionWorkItems();syncWorkControls();
}
function renderSelectedWork(){
  const item=selectedWork(),readable=workProjection()?.readable===true;
  $('usage-work-selected').hidden=!readable||!item;if(!readable||!item)return;
  $('usage-work-rename-title').value=workState.renameDrafts[item.id]??item.title;
  renderWorkDetails(item);renderWorkObservations(item);
  renderFollowups();loadFollowups();
  $('usage-work-counts').textContent=t('work_counts',{linked:number(item.linked_sessions),available:number(item.linked_sessions-item.missing_sessions),selected:number(item.selected_sessions),outside:number(item.outside_selection),missing:number(item.missing_sessions),overlap:number(item.overlapping_sessions)});
  $('usage-work-usage').textContent=item.selected_sessions?workUsageText('work_usage',item):t('work_no_selection');
  $('usage-work-quality').hidden=!item.selected_sessions||!workQualityLimited(item);
  const list=$('usage-work-members'),rows=new Map((usageState.data.sessions||[]).map(row=>[row.id,row])),missing=new Set(item.missing_session_ids),outside=new Set(item.outside_session_ids);
  list.replaceChildren();
  for(const id of item.session_ids.slice(0,workState.pageSize)){
    const line=node('li','work-member'),label=node('div','work-member-label'),row=rows.get(id),code=id.slice(0,8);
    if(missing.has(id))label.append(node('span','', '#'+code),node('small','work-missing',t('work_missing')));
    else{const open=node('button','text-button',(row?row.project+' · '+(usageAgents[row.agent]||row.agent)+' · ':'')+'#'+code);open.type='button';open.addEventListener('click',()=>{if(usageState.stopped)return;if(row)openUsageSession(row);else inspectUsageSession(id);});label.append(open);if(outside.has(id))label.append(node('small','',t('work_outside')));}
    const unlink=node('button','quiet work-unlink',t('work_unlink'));unlink.type='button';unlink.setAttribute('aria-label',t('work_unlink_label',{code,title:item.title}));unlink.addEventListener('click',()=>performWorkAction({action:'unlink',id:item.id,session:id},{focus:'work'}));
    line.append(label,unlink);list.append(line);
  }
  $('usage-work-no-members').hidden=item.session_ids.length>0;
  $('usage-work-more').hidden=item.session_ids.length<=workState.pageSize;
  $('usage-work-more').textContent=t('work_more',{n:number(Math.min(20,item.session_ids.length-workState.pageSize))});
}
function renderSessionWorkItems(){
  const session=workState.openSession;if(!session)return;
  let box=$('usage-session-work-items');if(!box){box=node('section','session-work-items');box.id='usage-session-work-items';$('usage-session-detail').append(box);}
  const previous=$('usage-session-work-editor');
  if(previous?.dataset.sessionId===session&&workState.sessionForms[session])workState.sessionForms[session].open=previous.open;
  box.replaceChildren(node('h3','',t('work_title')));
  const value=workProjection();
  if(value?.readable!==true){box.append(node('p','notice',t('work_unreadable')));return;}
  const linked=value.items.filter(item=>item.session_ids.includes(session)),available=value.items.filter(item=>!item.session_ids.includes(session));
  const state=workState.sessionForms[session]??(workState.sessionForms[session]={open:Boolean(workState.sessionChoices[session]),mode:available.length?'existing':'new'});
  if(!available.length)state.mode='new';
  const list=node('ul','work-members');
  for(const item of linked){const line=node('li','work-member'),unlink=node('button','quiet work-unlink',t('work_unlink'));unlink.type='button';unlink.setAttribute('aria-label',t('work_unlink_label',{code:session.slice(0,8),title:item.title}));unlink.addEventListener('click',()=>performWorkAction({action:'unlink',id:item.id,session},{focus:'session',session}));line.append(node('span','',workLabel(item)),unlink);list.append(line);}box.append(list);
  const form=node('form','work-form'),label=node('label','',t('work_link_choose')),controls=node('div','work-input-action'),select=node('select',''),link=node('button','secondary',t('work_link'));select.id='usage-session-work-select';label.htmlFor=select.id;link.id='usage-session-work-link';link.type='submit';
  const empty=node('option','',t('work_choose'));empty.value='';select.append(empty);
  for(const item of available){const option=node('option','',workLabel(item));option.value=item.id;select.append(option);}
  select.value=available.some(item=>item.id===workState.sessionChoices[session])?workState.sessionChoices[session]:'';
  select.addEventListener('change',()=>{workState.sessionChoices[session]=select.value;syncWorkControls();});
  form.addEventListener('submit',event=>{event.preventDefault();if(select.value)performWorkAction({action:'link',id:select.value,session},{focus:'session',session});});controls.append(select,link);form.append(label,controls);
  const createForm=node('form','work-form'),createLabel=node('label','',t('work_new_title')),createControls=node('div','work-input-action'),title=node('input',''),create=node('button','secondary',t('work_create_link'));title.id='usage-session-work-title';title.maxLength=240;title.autocomplete='off';title.placeholder=t('work_placeholder');title.value=workState.sessionDrafts[session]||'';createLabel.htmlFor=title.id;create.id='usage-session-work-create';create.type='submit';
  title.addEventListener('input',()=>{workState.sessionDrafts[session]=title.value;syncWorkControls();});createForm.addEventListener('submit',event=>{event.preventDefault();createWork(session);});createControls.append(title,create);createForm.append(createLabel,createControls);
  const editor=node('details','session-work-editor');editor.id='usage-session-work-editor';editor.dataset.sessionId=session;editor.open=state.open;
  const toggle=node('summary','',t(linked.length?'session_work_another':'session_work_link'));toggle.id='usage-session-work-toggle';
  editor.append(toggle,node('p','section-note',t('work_session_note')));
  const modes=node('div','session-work-modes');modes.setAttribute('role','group');modes.setAttribute('aria-label',t('session_work_mode'));
  function setMode(mode){state.mode=mode;form.hidden=mode!=='existing';createForm.hidden=mode!=='new';for(const button of modes.children)button.setAttribute('aria-pressed',String(button.dataset.mode===mode));}
  for(const [mode,label] of [['existing',t('session_work_existing')],['new',t('session_work_new')]]){
    const button=node('button','quiet',label);button.type='button';button.dataset.mode=mode;
    if(mode==='existing'&&!available.length)continue;
    button.addEventListener('click',()=>{setMode(mode);(mode==='new'?title:select).focus();});modes.append(button);
  }
  if(available.length)editor.append(modes);
  editor.append(form,createForm);setMode(state.mode);
  editor.addEventListener('toggle',()=>{if(editor.isConnected&&workState.openSession===session)state.open=editor.open;});
  const privacy=node('details','work-link-privacy');privacy.append(node('summary','',t('work_links_privacy')),node('p','section-note',t('work_privacy')));editor.append(privacy);box.append(editor);
  const status=node('p','section-note');status.id='usage-session-work-status';status.setAttribute('role','status');box.append(status);
  syncWorkControls();
}
function createWork(session=null){
  const title=session?workState.sessionDrafts[session]||'':workState.createDraft;
  if(!validWorkTitle(title)){notice(t('work_title_invalid'));return;}
  return performWorkAction({action:'create',title:title.trim(),...(session?{session}:{})},{focus:session?'session':'work',session});
}
function renameWork(){
  const item=selectedWork(),title=$('usage-work-rename-title').value;
  if(!item)return;if(!validWorkTitle(title)){notice(t('work_title_invalid'));return;}
  return performWorkAction({action:'rename',id:item.id,title:title.trim()},{focus:'rename'});
}
function requestWorkDelete(){
  const item=selectedWork();if(workBlocked()||!item)return;
  workState.deleteID=item.id;$('usage-work-delete-name').textContent=workLabel(item);$('usage-work-delete-status').textContent='';$('usage-work-delete-dialog').showModal();syncWorkControls();$('usage-work-delete-cancel').focus();
}
function cancelWorkDelete(){if(usageState.workBusy)return;workState.deleteID=null;$('usage-work-delete-dialog').close();$('usage-work-delete').focus();}
function sessionWorkMessage(context,message){if(context.session&&context.session===workState.openSession&&$('usage-session-work-status'))$('usage-session-work-status').textContent=message;}
async function performWorkAction(body,context={}){
  if(workBlocked())return false;
  const action=++workState.action,current=()=>!usageState.stopped&&!workState.navigation&&action===workState.action;
  usageState.workBusy=body.action;syncArchiveButton();syncExportButton();syncWorkControls();notice('');
  sessionWorkMessage(context,t('work_saving'));
  if(workState.deleteID)$('usage-work-delete-status').textContent=t('work_saving');
  try{
    const following=body.action.endsWith('_followup');
    const result=await post(following?'/api/usage/work/followup':body.action==='describe'?'/api/usage/work/details':'/api/usage/work',body);if(!current())return false;
    if(result.ok!==true)throw new Error(t('work_failed'));
    if(body.action==='create'){
      workState.selected=result.id;workState.pageSize=20;
      if(body.session)delete workState.sessionDrafts[body.session];else workState.createDraft='';
    }
    if(body.action==='rename')delete workState.renameDrafts[body.id];
    if(body.action==='describe')delete workState.detailDrafts[body.id];
    if(following){followState.key='';followState.deleting=null;if(body.action==='start_followup')delete followState.drafts[body.id];else delete followState.drafts[body.id]?.reviews?.[body.record_id];}
    if(body.action==='link')delete workState.sessionChoices[body.session];
    if(body.action==='delete'){
      delete workState.renameDrafts[body.id];if(workState.selected===body.id)workState.selected='';
      delete workState.detailDrafts[body.id];
      delete followState.drafts[body.id];
      workState.deleteID=null;$('usage-work-delete-dialog').close();
    }
    const previous=usageState.data;await loadUsage();if(!current())return false;
    workState.needsRefresh=usageState.data===previous;
    const message=t(workState.needsRefresh?'work_saved_refresh':body.action==='describe'?'work_details_saved':'work_saved');notice(message,workState.needsRefresh?'warning':'success');sessionWorkMessage(context,message);
    return true;
  }catch(error){
    if(current()){
      if(body.action==='describe'&&error.code==='conflict'){
        const draft=workState.detailDrafts[body.id];if(draft)draft.conflict=true;
        const previous=usageState.data;await loadUsage();if(!current())return false;
        workState.needsRefresh=usageState.data===previous;renderSelectedWork();
      }else if(body.action.endsWith('_followup')){followState.key='';followState.data=null;if(!['invalid','limit','early','active','closed','stale','conflict','missing'].includes(error.code))workState.needsRefresh=true;}
      else if(body.action==='describe'&&!['invalid','limit','missing'].includes(error.code))workState.needsRefresh=true;
      notice(error.message);sessionWorkMessage(context,error.message);if(workState.deleteID)$('usage-work-delete-status').textContent=error.message;
    }
    return false;
  }
  finally{
    usageState.workBusy=false;syncArchiveButton();syncExportButton();syncWorkControls();
    if(current()&&body.action.endsWith('_followup'))await loadFollowups(true);
    if(current()){
      const sessionTarget=$('usage-session-work-editor')?.open?(workState.sessionForms[context.session]?.mode==='new'?$('usage-session-work-title'):$('usage-session-work-select')):$('usage-session-work-toggle');
      const target=context.focus==='session'&&workState.openSession===context.session?sessionTarget:context.focus==='details'?$('usage-work-goal'):context.focus==='rename'?$('usage-work-rename-title'):$('usage-work-select');
      if(target&&!target.disabled&&!$('usage-work-delete-dialog').open)target.focus();
    }
  }
}
function reconnectFromAccessLink(){if(/^#access=[a-f0-9]{64}$/.test(location.hash))location.reload();}
applyLanguage();
$('lang-toggle').addEventListener('click',switchLanguage);$('close-app').addEventListener('click',closeApp);$('usage-refresh').addEventListener('click',refreshUsage);$('usage-export').addEventListener('click',exportUsage);$('usage-close-session').addEventListener('click',()=>$('usage-session-dialog').close());$('usage-more').addEventListener('click',showMoreUsageSessions);
$('usage-archive-clear').addEventListener('click',clearUsageArchive);
$('usage-retention').addEventListener('change',()=>changeMetadata('retention'));
$('usage-cache-reset').addEventListener('click',()=>changeMetadata('cache'));
$('usage-backup-download').addEventListener('click',downloadUsageBackup);
$('usage-backup-check').addEventListener('click',checkUsageBackup);
$('usage-backup-file').addEventListener('change',()=>{$('usage-backup-result').hidden=true;syncBackupControls();});
$('usage-work-create-title').addEventListener('input',()=>{workState.createDraft=$('usage-work-create-title').value;syncWorkControls();});
$('usage-work-followups').addEventListener('toggle',()=>{if($('usage-work-followups').open)loadFollowups();else{followState.request++;followState.loading=false;followState.key='';}});
$('usage-follow-reload').addEventListener('click',()=>loadFollowups(true));
$('usage-follow-form').addEventListener('submit',event=>{event.preventDefault();runFollowup('start_followup');});
for(const [id,key] of [['usage-follow-change','change'],['usage-follow-observation','observation'],['usage-follow-trigger','trigger']])$(id).addEventListener(key==='trigger'?'change':'input',()=>{const draft=followDraft();if(draft)draft[key]=$(id).value;syncWorkControls();});
$('usage-work-create-form').addEventListener('submit',event=>{event.preventDefault();createWork();});
$('usage-work-select').addEventListener('change',()=>{workState.selected=$('usage-work-select').value;workState.pageSize=20;renderSelectedWork();syncWorkControls();});
$('usage-work-rename-title').addEventListener('input',()=>{if(workState.selected)workState.renameDrafts[workState.selected]=$('usage-work-rename-title').value;syncWorkControls();});
$('usage-work-rename-form').addEventListener('submit',event=>{event.preventDefault();renameWork();});
for(const id of ['usage-work-goal','usage-work-result-note','usage-work-outcome'])$(id).addEventListener(id==='usage-work-outcome'?'change':'input',captureWorkDetails);
$('usage-work-details-form').addEventListener('submit',event=>{event.preventDefault();saveWorkDetails();});
$('usage-work-details-keep').addEventListener('click',()=>reviewWorkDetails(true));
$('usage-work-details-discard').addEventListener('click',()=>reviewWorkDetails(false));
$('usage-work-more').addEventListener('click',()=>{workState.pageSize+=20;renderSelectedWork();syncWorkControls();});
$('usage-work-delete').addEventListener('click',requestWorkDelete);
$('usage-work-reload').addEventListener('click',loadUsage);
$('usage-work-delete-cancel').addEventListener('click',cancelWorkDelete);
$('usage-work-delete-confirm').addEventListener('click',()=>{if(workState.deleteID)performWorkAction({action:'delete',id:workState.deleteID},{focus:'work'});});
$('usage-work-delete-dialog').addEventListener('cancel',event=>{if(usageState.workBusy)event.preventDefault();else workState.deleteID=null;});
$('usage-session-dialog').addEventListener('close',()=>{if($('usage-session-dialog').open)return;workState.openSession=null;usageState.sessionRequest=(usageState.sessionRequest||0)+1;usageUI.publish('selection',null);});
$('usage-export-mask').addEventListener('change',()=>{clearUsageDownload();syncExportButton();});
$('usage-quality-only').addEventListener('change',()=>{usageState.pageSize=20;renderUsageSessions();});
$('usage-quality-show').addEventListener('click',()=>{$('usage-quality-only').checked=true;$('usage-session-search').value='';usageState.pageSize=20;renderUsageSessions();$('usage-session-section').scrollIntoView({block:'start'});$('usage-quality-only').focus();});
for(const id of ['usage-period','usage-agent','usage-project'])$(id).addEventListener('change',()=>{usageState.pageSize=20;loadUsage();});
for(const id of ['usage-session-search','usage-session-sort'])$(id).addEventListener(id==='usage-session-search'?'input':'change',()=>{usageState.pageSize=20;renderUsageSessions();});
$('usage-search-clear').addEventListener('click',()=>{setUsageFilters({search:''});usageState.pageSize=20;renderUsageSessions();$('usage-session-search').focus();});
$('usage-filter-clear').addEventListener('click',()=>{$('usage-period').value='0';$('usage-agent').value='all';$('usage-project').value='all';$('usage-session-search').value='';$('usage-quality-only').checked=false;$('usage-period').focus();usageState.pageSize=20;loadUsage();});
// Age the displayed snapshot without re-reading logs or making any network request.
function quotaInsightStates(data){return (data.insights||[]).filter(note=>note.kind==='quota').map(note=>quotaWindowNow(note.evidence).state).join(',');}
function updateSnapshotClock(){if(!usageState.stopped&&usageState.data?.has_snapshot){renderQuotaAlerts();if(document.hidden)return;agePlanComparisons();renderUsageQuota(usageState.data);if(quotaInsightStates(usageState.data)!==usageState.insightQuotaStates)renderUsageInsights(usageState.data);}}
usageState.clock=setInterval(updateSnapshotClock,30000);
document.addEventListener('visibilitychange',updateSnapshotClock);
window.addEventListener('focus',updateSnapshotClock);
window.addEventListener('hashchange',reconnectFromAccessLink);
$('usage-live-watch').addEventListener('change',event=>setLiveWatch(event.target.checked));
$('usage-live-notify').addEventListener('click',toggleQuotaNotifications);
liveLoad();if(liveState.watch)setLiveWatch(true);
loadUsage();
