# Work goals, follow-ups and comprehension — pilot annex

Predeclared preparation, 3 November 2026. **No participant has been recruited or tested by this work.** This annex makes R03/R05/R06 executable once the owner chooses to run a pilot. It supplements [PILOT.md](PILOT.md); it does not replace its tasks, participant mix, privacy requirements, five-person targets or next-week repeated-use criterion. Keep original-protocol results and annex results separate. Do not revise thresholds after seeing results.

## Freeze the candidate and comparison first

Record the actual candidate version, ZIP/wheel SHA-256, platform, language and protocol revision before the first session. The current public package is .31; the later Help clarification is still an unreleased source change. Do not attribute that clarification to an unchanged .31 package. A candidate must pass its technical/privacy acceptance before participant use. A passed consistency gate alone is insufficient.

Use the participant's current method as the comparison, for the same bounded task and available evidence. Alternate the method order by task and participant so practice does not always favor Roodof. Record the order before starting. Do not exclude people who are slower, cannot finish, lack a useful current method or have insufficient logs; report those cases and the comparison's limits.

Default to invented demo records. If someone chooses their own existing records, they approve the scope locally; no prompts, replies, project paths, log files, backups, access links or account secrets are collected. A pseudonym such as P01 is sufficient in the result sheet. Do not require extra paid agent calls to manufacture usable samples. No recruitment, message or invitation is authorized by this document.

## Day 0 tasks

Give one task at a time without naming the controls to click. The facilitator answer column stays out of a participant handout. Task timings cover the participant's actions and waits, including startup/reading waits; the seven-day observation period is not active task time.

| ID | Participant prompt | Independent completion and evidence |
|---|---|---|
| W1 | Find two sessions you recognize and collect them under a named piece of work. / Tanıdığın iki oturumu bulup adlandırdığın bir işe bağla. | Both intended session codes are linked, other sessions are not; the participant explains full-session scope. Record creation, locating, linking and return-to-work time/actions separately. Do not read conversation content to identify a session. |
| W2 | Link one of those sessions to another piece of work and explain the totals. / Oturumlardan birini ikinci bir işe de bağla ve toplamları açıkla. | Both work subtotals may include the same session; their sum is not the deduplicated combined usage. Task cost or token allocation between tasks is unknown. A mistaken sum is an interpretation failure, even if the links saved. |
| W3 | Write what this work should achieve, record its current outcome, then find that information again after changing a filter. / İşin hedefini ve şu anki sonucunu kaydet; filtreyi değiştirip bu bilgileri yeniden bul. | The intended goal/outcome/note persists for the whole work. The participant distinguishes their own outcome from test/Git observations and from a session's Useful/Wasted verdict. Neither tokens nor a passing test establish completion. |
| W4 | Record a change you want to try and explain when a useful comparison would become possible. / Denemek istediğin değişikliği kaydet ve ne zaman anlamlı karşılaştırma yapabileceğini açıkla. | A saved follow-up has an explicit observation/change and frozen baseline. The participant understands the later equal seven-day window, explicit review, comparable tasks/models and sufficient dated evidence. Insufficient samples are a valid unresolved result, not a reason to invent a gain. |

Do not count facilitator-completed actions as independent success. Stop a task on an apparent private-data exposure or data-loss risk. Preserve a failed task as a failed task; correction and a later retest get new records rather than replacing the original.

## Day 7 or later

The participant may choose to return; a calendar reminder or facilitator message is not evidence of spontaneous repeated use. No automatic message is sent by this protocol. Record whether use was self-initiated, prompted or facilitator-led, and the specific recurring decision it served.

| ID | Participant prompt | Independent completion and evidence |
|---|---|---|
| W5 | Review the change you recorded, using the available later evidence. What can you conclude and what remains unknown? / Kaydettiğin değişikliği sonraki verilerle değerlendir. Ne söyleyebilirsin, ne bilinmiyor? | Read current sources, link the relevant later sessions and save an explicit review. Comparable groups require at least three sessions in each equal seven-day window and the participant's similar-task/context assessment. Changed history, different models or missing evidence must leave the result unresolved. Record no-data, no-return and abandoned cases. Never change clocks or fabricate records to force a result. |
| W6 | Would you return to Roodof for a particular task next week? Show what you would use it for. / Gelecek hafta hangi somut iş için geri gelirdin? Nasıl kullanacağını göster. | Record the reason and any actual next-week return separately from a positive comment or a stated intention. Ask what it replaces in the existing workflow. Payment interest, including the tentative $3/month idea, is exploratory and is not measured conversion or demand. |

## Comprehension cards — facilitator key

Ask for an explanation before giving the answer. Record the participant's initial answer, correctness and any help using a short sanitized paraphrase. These are deliberately invented scenarios. Do not show answer text in the participant prompt.

| ID | Invented prompt | Correct interpretation |
|---|---|---|
| C1 | Roodof shows 100,000 recorded tokens and a $1.20 API list-price equivalent. What did you actually pay? / Gerçekte ne ödedin? | Unknown. A hypothetical list-price equivalent is not the subscription invoice or full account spending. Missing or unpriced usage is not zero-cost usage. |
| C2 | Some requests are absent from the retained records. How large is the missing amount? / Eksik tutar ne kadar? | Unknown; Roodof cannot infer a percentage or a general error bound from the absent records. A source warning may identify an observed problem but cannot enumerate never-seen history. |
| C3 | The last quota observation is two hours old. Does the displayed value describe the provider account right now? / Bu değer hesabın şu anki kotası mı? | No current provider lookup was made. It is a dated observation; other use may consume the same quota. A forecast assumes the observed pace continues. Stale/uncertain data cannot prove remaining capacity. |
| C4 | Session A has 100k tokens, B 60k, C 40k. Work 1 links A+B; Work 2 links A+C. What are the combined tokens and either task's exact cost? / Birleşik kullanım ve görevlerin kesin maliyeti nedir? | Work subtotals are 160k and 140k, but the deduplicated union is 200k. Adding work subtotals gives 300k and double-counts A. Whole-session links do not allocate a session's usage or establish exact task costs. |
| C5 | Project names are hidden in a JSON export. Can it be shared as anonymous? Can a private backup be sent to support? / Dosya anonim mi; özel yedek desteğe gönderilebilir mi? | Masked JSON still carries identifying times/models/session codes; review before any intentional sharing. A private backup can carry paths, identifiers and private work metadata, is not anonymous and is not a support attachment. Agent logs/credentials/access links are never requested. |

Apply the original protocol's critical-interpretation rule to these scope/privacy explanations: a misleading interpretation requires a product/help correction and a fresh run. Report annex card results separately; do not declare the full pilot passed from these five invented cards.

## Effort record — one row per task and method

Record candidate, pseudonym, language, platform, invented/participant-approved-local source, task, comparison method, preassigned order, start/stop and elapsed seconds. Also record:

- Deliberate UI actions: each navigation/click/keyboard shortcut is one action; filling a text field is one entry action, not one action per character. Use the same definition for both methods. Record waits and text length separately if they explain a timing difference.
- Wrong turns, failed saves, misunderstood filters, repeated searches, lost drafts, help opens and facilitator interventions. Count the intervention even if the task later completes.
- Result: independent completion, completed with help, incorrect, abandoned or unavailable evidence. Explain the failure in a sanitized note and preserve it in the denominator.
- What decision the participant could defend, what remained unknown, and whether it affected an actual later action. A smaller token count is not a quality or causal-savings outcome.

Blank local record:

| Participant | Candidate/hash | Language/platform | Task/method/order | Source category | Elapsed sec / wait sec | Actions / help count | Result / friction | Later use and decision |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |

Keep identifying reference material on the participant's own computer. Before any agreed result sharing, the participant reviews the sanitized row. This protocol does not collect telemetry or authorize sending anything to a service.

## Report without changing the criteria

Use the original five-person core criteria from PILOT.md, including all critical tasks, four-of-five independent finding/filtering/export and three-of-five concrete next-week uses. For this annex, preregister that **at least four of five participants complete each of W1–W4 independently** as an additional product-friction target; report each task's denominator and every failure, not only an average. W5 needs actual elapsed observation time and sufficient data; unresolved evidence is reported rather than converted into success. Keep this annex target separate from the original protocol's acceptance.

Summarize individual and median active-task time/actions against the existing method, plus help, errors and abandonment. Five participants do not establish a general time-saving percentage or a paid conversion rate. The work is closed only with real recorded observations and necessary corrections/retests; this prepared annex closes preparation, not R03/R05/R06's evidence requirements.
