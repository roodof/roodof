// First-run tour (driver.js): four short steps over the real controls, shown once. In the desktop
// window, whose browser storage is fresh every launch, the window remembers "seen" (desktop/main.cjs
// reads data-tour-seen on close and passes ?tour=seen next time). Escape or a click outside ends it.
import { driver } from 'driver.js';

export function mountTour({ tr, show }) {
  const root = document.documentElement;
  let seen = new URLSearchParams(location.search).get('tour') === 'seen';
  try { seen = seen || localStorage.getItem('pler-tour') === 'seen'; } catch {}
  const remember = () => { root.dataset.tourSeen = '1'; try { localStorage.setItem('pler-tour', 'seen'); } catch {} };
  if (seen) root.dataset.tourSeen = '1';
  const words = tr ? {
    next: 'İleri', prev: 'Geri', done: 'Başla', progress: '{{current}} / {{total}}',
    steps: [
      ['.ws-nav', 'Beş bölüm', 'Oturumlar, İşlerim, Kullanım, Kotalar ve Ayarlar. Hepsi yalnız bu bilgisayardaki kayıtlardan okunur.'],
      ['.wb-filterbar', 'Ajan ve dönem', 'Claude Code, Codex ya da ikisi; 7, 30, 90 gün veya tümü. Seçim bütün sayfalara uygulanır.'],
      ['#sessions-grid', 'Bir oturum aç', 'Satıra tıkla: ayrıntılar sağda açılır. ↑ ↓ ile oturumlar arasında gezinebilirsin.'],
      ['[data-route=work]', 'İşine ad ver', 'İşlerim\'de bir iş oluştur ve oturumları bağla; o işin toplam kullanımını gör.'],
      ['.ws-find', 'Her yere Ctrl K', 'Bölümler arasında klavyeyle geç. Bu turu bir daha göstermeyiz.']
    ]
  } : {
    next: 'Next', prev: 'Back', done: 'Start', progress: '{{current}} / {{total}}',
    steps: [
      ['.ws-nav', 'Five sections', 'Sessions, My work, Usage, Limits and Settings, all read from the records on this computer only.'],
      ['.wb-filterbar', 'Agent and period', 'Claude Code, Codex or both; 7, 30, 90 days or all time. The choice applies to every page.'],
      ['#sessions-grid', 'Open a session', 'Click a row: its details open on the right. Move between sessions with ↑ ↓.'],
      ['[data-route=work]', 'Name your work', 'Create a work item in My work and link sessions to it to see its total usage.'],
      ['.ws-find', 'Ctrl K anywhere', 'Jump between sections from the keyboard. This tour will not show again.']
    ]
  };
  let started = false;
  return {
    // Called after each data render; starts once, on the sessions page, when there is something to point at.
    maybeStart(data) {
      // Automated checks (navigator.webdriver) never see it, so they can click the page as before.
      if (seen || started || navigator.webdriver || !data?.has_snapshot || !data.totals?.sessions) return;
      if (matchMedia('(max-width: 760px)').matches) return;
      started = true;
      show('sessions');
      requestAnimationFrame(() => {
        const steps = words.steps.filter(([selector]) => document.querySelector(selector))
          .map(([element, title, description]) => ({ element, popover: { title, description } }));
        if (!steps.length) return;
        const tour = driver({
          showProgress: true, progressText: words.progress, nextBtnText: words.next, prevBtnText: words.prev, doneBtnText: words.done,
          animate: !matchMedia('(prefers-reduced-motion: reduce)').matches, overlayOpacity: 0.62, stagePadding: 6, stageRadius: 7,
          allowClose: true, popoverClass: 'ws-tour', steps,
          onDestroyed: () => { seen = true; remember(); }
        });
        tour.drive();
      });
    }
  };
}
