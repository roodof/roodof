// My work: work items as cards (FormKit auto-animate), linking several sessions at once through a
// cmdk picker, and sonner toasts for confirmations. app.js keeps every write and its checks:
// cards select through the existing picker, links go through performWorkAction one by one.
import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { flushSync } from 'react-dom';
import { Command } from 'cmdk';
import { Toaster, toast } from 'sonner';
import autoAnimate from '@formkit/auto-animate';
import { createElement as createIcon, Plus, Link2, Check } from 'lucide';

function el(tag, cls, text) { const node = document.createElement(tag); if (cls) node.className = cls; if (text !== undefined && text !== null) node.textContent = text; return node; }
const $ = id => document.getElementById(id);
const icon = (node, size = 15) => createIcon(node, { width: size, height: size, 'stroke-width': 1.7, 'aria-hidden': 'true' });

export function mountWork({ tr }) {
  const lang = tr ? 'tr-TR' : 'en-US';
  const words = tr ? {
    cards: 'İşlerin', newWork: 'Yeni iş', sessions: n => n + ' oturum', noSessions: 'Henüz oturum yok', tokens: 'token',
    link: 'Oturumları bağla', search: 'Oturum adı, proje veya model ara…', empty: 'Eşleşen oturum yok.', linked: 'bağlı',
    selected: n => n + ' oturum seçildi', none: 'Bağlamak için oturum seç', confirm: n => n + ' oturumu bağla', cancel: 'Vazgeç',
    linking: (i, n) => `Bağlanıyor ${i}/${n}…`, done: n => n + ' oturum işe bağlandı.', stopped: 'Bağlama durdu; bağlananlar kaydedildi.',
    whileLinking: 'Bağlama sürüyor; işlem bitene kadar pencere açık kalır.',
    pickerTitle: title => '“' + title + '” işine oturum bağla', hint: '↑ ↓ gezin · Enter seç · Esc kapat'
  } : {
    cards: 'Your work', newWork: 'New work', sessions: n => n + (n === 1 ? ' session' : ' sessions'), noSessions: 'No sessions yet', tokens: 'tokens',
    link: 'Link sessions', search: 'Search session title, project or model…', empty: 'No matching sessions.', linked: 'linked',
    selected: n => n + (n === 1 ? ' session selected' : ' sessions selected'), none: 'Choose sessions to link', confirm: n => 'Link ' + n + (n === 1 ? ' session' : ' sessions'), cancel: 'Cancel',
    linking: (i, n) => `Linking ${i}/${n}…`, done: n => n + (n === 1 ? ' session linked.' : ' sessions linked.'), stopped: 'Linking stopped; the links made so far are saved.',
    whileLinking: 'Linking is in progress; this window stays open until it finishes.',
    pickerTitle: title => 'Link sessions to “' + title + '”', hint: '↑ ↓ move · Enter choose · Esc close'
  };
  const number = value => Number(value).toLocaleString(lang);
  const agentName = agent => agent === 'codex' ? 'Codex' : 'Claude Code';

  // ---- Toasts: success and "saved, refresh" notices become sonner toasts; errors keep the banner too.
  const toastHost = el('div', 'ws-toasts'); document.body.append(toastHost);
  createRoot(toastHost).render(<Toaster theme="dark" position="bottom-right" closeButton={false} duration={3200} toastOptions={{ className: 'ws-toast' }} />);
  const banner = $('notice');
  let lastToast = '';
  new MutationObserver(() => {
    const text = banner.textContent.trim(), kind = banner.dataset.kind;
    if (!text || banner.hidden) { lastToast = ''; return; }
    if (text === lastToast) return;
    lastToast = text;
    if (kind === 'success') { toast.success(text); banner.hidden = true; }
    else if (kind === 'warning') toast.warning(text);
    else toast.error(text);
  }).observe(banner, { childList: true, characterData: true, subtree: true, attributes: true, attributeFilter: ['hidden', 'data-kind'] });

  // ---- Work cards above the existing controls; the select stays as the source of truth.
  const select = $('usage-work-select'), controls = select?.closest('.work-controls') || select?.parentElement;
  const wrap = el('section', 'ws-work-cards'); wrap.setAttribute('aria-label', words.cards);
  const grid = el('div', 'ws-work-grid'); wrap.append(grid);
  controls?.before(wrap);
  (select?.closest('.work-form') || select?.parentElement)?.classList.add('ws-picker-replaced');
  document.body.classList.add('has-work-cards');
  autoAnimate(grid, { duration: 220, easing: 'cubic-bezier(.2,.8,.2,1)', disrespectUserMotionPreference: false });
  const cards = new Map();
  const newCard = el('button', 'ws-work-card ws-work-new'); newCard.type = 'button';
  newCard.append(icon(Plus, 16), el('span', '', words.newWork));
  newCard.addEventListener('click', () => { const input = $('usage-work-create-title'); input?.focus(); input?.scrollIntoView({ block: 'center', behavior: 'smooth' }); });

  function card(item) {
    let node = cards.get(item.id);
    if (!node) {
      node = el('button', 'ws-work-card'); node.type = 'button'; node.dataset.id = item.id;
      node.addEventListener('click', () => { select.value = item.id; select.dispatchEvent(new Event('change', { bubbles: true })); paint(); });
      cards.set(item.id, node);
    }
    const sessions = new Map((usageState.data?.sessions || []).map(row => [row.id, row]));
    const agents = new Set(item.session_ids.map(id => sessions.get(id)?.agent).filter(Boolean));
    const top = el('div', 'ws-work-top'), marks = el('span', 'ws-work-agents');
    for (const agent of ['claude-code', 'codex']) if (agents.has(agent)) { const mark = el('i', 'ws-agent-dot ws-agent-' + agent); mark.title = agentName(agent); marks.append(mark); }
    top.append(el('strong', '', item.title), marks);
    const meta = el('span', 'ws-work-meta', item.linked_sessions ? words.sessions(item.linked_sessions) + (item.total_tokens ? ' · ' + (typeof usageShort === 'function' ? usageShort(item.total_tokens) : number(item.total_tokens)) + ' ' + words.tokens : '') : words.noSessions);
    const foot = el('span', 'ws-work-foot');
    foot.append(el('code', '', '#' + item.id.slice(0, 8)));
    if (item.outcome && item.outcome !== 'not_recorded' && typeof workOutcomeName === 'function') foot.append(el('span', 'ws-work-outcome ' + item.outcome, workOutcomeName(item.outcome)));
    node.replaceChildren(top, meta, foot);
    node.setAttribute('aria-pressed', String(item.id === workState.selected));
    return node;
  }

  function paint() {
    const items = usageState.data?.work_items?.readable === true ? usageState.data.work_items.items : [];
    wrap.hidden = !items.length;
    const order = items.map(card);
    for (const [id, node] of cards) if (!items.some(item => item.id === id)) { node.remove(); cards.delete(id); }
    order.forEach((node, index) => { if (grid.children[index] !== node) grid.insertBefore(node, grid.children[index] || null); });
    if (grid.lastElementChild !== newCard) grid.append(newCard);
    linkButton.disabled = typeof selectedWork !== 'function' || !selectedWork() || (typeof workBlocked === 'function' && workBlocked());
  }

  // ---- Link several sessions at once (cmdk). Each link is the same checked write as before.
  const linkButton = el('button', 'primary ws-link-open'); linkButton.type = 'button';
  linkButton.append(icon(Link2, 15), el('span', '', words.link));
  const dialog = el('dialog', 'ws-link-dialog'); document.body.append(dialog);
  const pickerRoot = createRoot(dialog);
  let linking = false;
  dialog.addEventListener('cancel', event => { if (linking) event.preventDefault(); });
  dialog.addEventListener('close', () => flushSync(() => pickerRoot.render(null)));
  dialog.addEventListener('click', event => { if (event.target === dialog && !linking) dialog.close(); });

  function Picker({ work, rows }) {
    const [chosen, setChosen] = useState(() => new Set()), [busy, setBusy] = useState('');
    const linked = new Set(work.session_ids);
    const toggle = id => { if (busy || linking || linked.has(id)) return; setChosen(previous => { const next = new Set(previous); next.has(id) ? next.delete(id) : next.add(id); return next; }); };
    async function confirm() {
      if (linking || !chosen.size || !dialog.open) return;
      linking = true;
      dialog.setAttribute('aria-busy', 'true');
      const ids = [...chosen]; let done = 0;
      try {
        for (const session of ids) {
          // Also stop remaining writes if the application closes this dialog programmatically.
          if (!dialog.open) break;
          setBusy(words.linking(done + 1, ids.length));
          const ok = await performWorkAction({ action: 'link', id: work.id, session }, { focus: 'work' });
          if (!ok) break;
          done++;
        }
        if (done === ids.length) toast.success(words.done(done)); else if (done) toast.warning(words.stopped);
      } catch {
        toast.error(words.stopped);
      } finally {
        linking = false;
        dialog.removeAttribute('aria-busy');
        setBusy('');
        if (dialog.open) dialog.close();
      }
    }
    return <Command className="ws-cmdk" label={words.pickerTitle(work.title)} loop>
      <div className="ws-cmdk-head"><strong>{words.pickerTitle(work.title)}</strong><kbd>{busy ? '…' : 'Esc'}</kbd></div>
      <Command.Input className="ws-cmdk-input" placeholder={words.search} disabled={Boolean(busy)} autoFocus />
      <Command.List className="ws-cmdk-list">
        <Command.Empty className="ws-cmdk-empty">{words.empty}</Command.Empty>
        {rows.map(row => {
          const isLinked = linked.has(row.id), isChosen = chosen.has(row.id), code = '#' + row.id.slice(0, 8);
          return <Command.Item key={row.id} value={row.id} disabled={isLinked || Boolean(busy)} onSelect={() => toggle(row.id)}
            keywords={[row.title||'', row.project, agentName(row.agent), code, typeof usageDate === 'function' ? usageDate(row.ended) : '', ...row.models.map(model => model.model)]}
            className={'ws-cmdk-item' + (isChosen ? ' chosen' : '')} data-agent={row.agent}>
            <span className="ws-cmdk-check" aria-hidden="true">{isChosen || isLinked ? <CheckIcon /> : null}</span>
            <span className="ws-cmdk-main"><strong>{row.title || (typeof usageSessionName === 'function' ? usageSessionName(row) : row.project)}</strong><small>{agentName(row.agent)} · {typeof usageDate === 'function' ? usageDate(row.ended) : ''} · <code>{code}</code></small></span>
            <span className="ws-cmdk-side">{isLinked ? <em>{words.linked}</em> : <>{typeof usageShort === 'function' ? usageShort(row.total_tokens) : number(row.total_tokens)} <small>{words.tokens}</small></>}</span>
          </Command.Item>;
        })}
      </Command.List>
      <div className="ws-cmdk-foot">
        <span>{busy || (chosen.size ? words.selected(chosen.size) : words.none)}</span>
        <span className="ws-cmdk-hint">{busy ? words.whileLinking : words.hint}</span>
        <button type="button" className="secondary" onClick={() => dialog.close()} disabled={Boolean(busy)}>{words.cancel}</button>
        <button type="button" className="primary" onClick={confirm} disabled={!chosen.size || Boolean(busy)}>{words.confirm(chosen.size || 0)}</button>
      </div>
    </Command>;
  }
  function CheckIcon() { return <span ref={element => { if (element && !element.firstChild) element.append(icon(Check, 13)); }} />; }

  linkButton.addEventListener('click', () => {
    if (linking) return;
    const work = typeof selectedWork === 'function' ? selectedWork() : null;
    if (!work) return;
    const rows = (usageState.data?.sessions || []).slice(0, 400);
    flushSync(() => pickerRoot.render(<Picker key={work.id + ':' + Date.now()} work={work} rows={rows} />));
    dialog.showModal();
    dialog.querySelector('.ws-cmdk-input')?.focus();
  });
  const add = document.querySelector('.wb-add-sessions');
  if (add) { add.classList.remove('primary'); add.classList.add('secondary'); add.before(linkButton); }

  return { update: paint };
}
