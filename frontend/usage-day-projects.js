// Use consecutive local midnights. A civil day need not be 24 hours long.
export function dayBounds(key) {
  const start = new Date(key + 'T00:00:00');
  const end = new Date(start.getFullYear(), start.getMonth(), start.getDate() + 1);
  return { start: start.toISOString(), end: end.toISOString() };
}

export function mountDayProjects({ tr, number, parent, load, onSelect, create }) {
  const words = tr ? {
    title: 'Güne göre projeler', day: 'Gün', total: n => n + ' kayıtlı token',
    loading: 'Proje kullanımı hesaplanıyor…', empty: 'Bu gün için zamanı doğrulanmış proje kullanımı yok.',
    error: 'Günlük döküm alınamadı.', retry: 'Tekrar dene',
    partial: n => `Seçili filtrelere uyan ${n} oturumun kullanımı bütünüyle tarihlendirilemedi.`,
    boundary: n => `${n} kayıtlı yanıt gün sınırını aştığı için bu güne eklenmedi.`,
    resolution: 'Grafik saatlik dilimleri, bu liste tam gün sınırlarını kullanır.',
  } : {
    title: 'Projects by day', day: 'Day', total: n => n + ' recorded tokens',
    loading: 'Calculating project usage…', empty: 'No project usage with a verified time for this day.',
    error: 'Could not load the daily breakdown.', retry: 'Try again',
    partial: n => `Usage could not be fully dated for ${n} ${n === '1' ? 'session' : 'sessions'} matching these filters.`,
    boundary: n => `${n} recorded ${n === '1' ? 'response crosses' : 'responses cross'} a day boundary and could not be assigned to this day.`,
    resolution: 'The chart groups usage by hour. This list uses exact local day boundaries.',
  };
  const head = create('div', 'ws-day-project-head');
  const label = create('label', '', words.day);
  const date = create('input');
  date.type = 'date';
  label.append(date);
  head.append(create('h3', '', words.title), label);
  const status = create('p', 'section-note');
  status.setAttribute('role', 'status');
  const retry = create('button', 'secondary', words.retry);
  retry.type = 'button';
  retry.hidden = true;
  const list = create('ul', 'ws-day-project-list');
  const coverage = create('p', 'section-note');
  const edge = create('p', 'section-note');
  parent.append(head, status, retry, list, coverage, edge);

  let data, controller, signature;
  function refresh() {
    const params = data?.scanned_at && date.value && date.validity.valid
      ? { snapshot: data.scanned_at, days: data.filters.days, agent: data.filters.agent,
          project: data.filters.project, ...dayBounds(date.value) }
      : null;
    const next = params && JSON.stringify(params);
    if (signature === next) return;
    signature = next;
    controller?.abort();
    list.replaceChildren();
    edge.textContent = '';
    retry.hidden = true;
    status.textContent = params ? words.loading : '';
    if (!params) return;
    const signal = (controller = new AbortController()).signal;
    load(params, signal).then(result => {
      if (signal.aborted) return;
      status.textContent = result.projects.length ? words.total(number(result.total_tokens)) : words.empty;
      const hourBoundary = [params.start, params.end].every(instant => instant.endsWith(':00:00.000Z'));
      edge.textContent = [
        result.boundary_calls ? words.boundary(number(result.boundary_calls)) : '',
        !hourBoundary || result.boundary_calls ? words.resolution : '',
      ].filter(Boolean).join(' ');
      const rows = result.projects.map(project => {
        const row = create('li');
        row.append(create('span', '', project.name), create('strong', '', number(project.tokens)));
        return row;
      });
      list.replaceChildren(...rows);
    }).catch(() => {
      if (signal.aborted) return;
      status.textContent = words.error;
      retry.hidden = false;
    });
  }
  date.addEventListener('change', () => {
    if (date.value && date.validity.valid) onSelect(date.value);
    refresh();
  });
  retry.addEventListener('click', () => { signature = null; refresh(); });
  return {
    update(snapshot, keys = []) {
      data = snapshot;
      parent.hidden = !data?.scanned_at || !keys.length;
      const partial = data?.dated_usage?.unallocated_sessions || 0;
      coverage.textContent = partial ? words.partial(number(partial)) : '';
      if (parent.hidden) {
        data = null;
      } else {
        date.min = keys[0];
        date.max = keys.at(-1);
        if (!date.value || !date.validity.valid) date.value = keys.at(-2) || date.max;
      }
      refresh();
    },
    select(key) {
      date.value = key;
      refresh();
    },
  };
}
