// Drawn menus for the main dropdowns. The page's own <select> stays in the document as the single
// source of truth: this only shows its options in a Base UI menu and writes the choice back with a
// normal change event, so every existing handler keeps working.
import React, { useSyncExternalStore } from 'react';
import { createRoot } from 'react-dom/client';
import { Select } from '@base-ui/react/select';
import { CSPProvider } from '@base-ui/react/csp-provider';
import { createElement as createIcon, ChevronDown, Check } from 'lucide';

const icon = (node, size) => element => { if (element && !element.firstChild) element.append(createIcon(node, { width: size, height: size, 'stroke-width': 2, 'aria-hidden': 'true' })); };

function Menu({ store, label }) {
  const state = useSyncExternalStore(store.subscribe, store.read);
  const items = state.options.map(option => ({ value: option.value, label: option.label }));
  return <Select.Root items={items} value={state.value} disabled={state.disabled} onValueChange={store.choose}>
    <Select.Trigger className="ws-select" aria-label={label}>
      <Select.Value />
      <Select.Icon className="ws-select-icon"><span ref={icon(ChevronDown, 14)} /></Select.Icon>
    </Select.Trigger>
    <Select.Portal>
      <Select.Positioner sideOffset={6} align="start" alignItemWithTrigger={false} collisionPadding={12} className="ws-select-layer">
        <Select.Popup className="ws-select-popup">
          <Select.List className="ws-select-list">
            {state.options.map(option => <Select.Item key={option.value} value={option.value} disabled={option.disabled} className="ws-select-item">
              <Select.ItemText>{option.label}</Select.ItemText>
              <Select.ItemIndicator className="ws-select-check"><span ref={icon(Check, 13)} /></Select.ItemIndicator>
            </Select.Item>)}
          </Select.List>
        </Select.Popup>
      </Select.Positioner>
    </Select.Portal>
  </Select.Root>;
}

function enhance(select) {
  if (!select || select.dataset.menu) return;
  select.dataset.menu = 'on';
  const listeners = new Set();
  let snapshot = null;
  const compute = () => JSON.stringify({ value: select.value, disabled: select.disabled, options: [...select.options].map(option => ({ value: option.value, label: option.textContent, disabled: option.disabled })) });
  let key = compute(); snapshot = JSON.parse(key);
  const sync = () => { const next = compute(); if (next === key) return; key = next; snapshot = JSON.parse(next); listeners.forEach(listener => listener()); };
  const store = {
    subscribe(listener) { listeners.add(listener); return () => listeners.delete(listener); },
    read: () => snapshot,
    choose(value) { if (value === select.value) return; select.value = value; select.dispatchEvent(new Event('change', { bubbles: true })); sync(); }
  };
  // The page also sets the value from code, which fires no event: watch that on this element only.
  for (const name of ['value', 'selectedIndex']) {
    const base = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, name);
    Object.defineProperty(select, name, { configurable: true, get() { return base.get.call(this); }, set(next) { base.set.call(this, next); sync(); } });
  }
  select.addEventListener('change', sync);
  new MutationObserver(sync).observe(select, { childList: true, subtree: true, attributes: true, characterData: true });
  const label = select.getAttribute('aria-label') || select.labels?.[0]?.textContent.trim() || select.closest('label')?.querySelector('span')?.textContent.trim() || '';
  const host = document.createElement('span');
  host.className = 'ws-select-host';
  select.after(host);
  select.classList.add('ws-select-native'); select.tabIndex = -1; select.setAttribute('aria-hidden', 'true');
  // The app allows only its own stylesheet files; the scrollbar rule Base UI would inject lives in premium.css.
  createRoot(host).render(<CSPProvider disableStyleElements><Menu store={store} label={label} /></CSPProvider>);
}

export function mountSelectMenus() {
  for (const id of ['usage-project', 'usage-session-sort']) enhance(document.getElementById(id));
}
