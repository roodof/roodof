# Masaüstü teslimi — 6 Kasım 2026

Kullanıcı Windows PLER'i tarayıcı yerine kendi penceresinde istedi. Aynı kaynak ve ölçüm
motoru korunur. Kaynak sürüm 0.3.0; kamuya açık sürüm hâlâ 0.2.31. Yayın/davet gönderilmez.

## Görev sırası

1. Kendi penceresi, özel erişim kanalı, izin/navigasyon sınırları.
2. Kapanışta arka plan işlemini durdurma; demo, yardım ve dosya indirme akışları.
3. Windows portable paket; Electron/Python ve bileşen lisanslarını birlikte taşıma.
4. Güncellemede sürüm seçimi/masaüstü yeniden açılışı; kaynak ve geliştirici doğrulaması.
5. **SON GÖREV — Temiz Windows kabulü (bekliyor).** Sabitlenmiş son paketi Python/PLER
   olmayan ortamda dene: normal/demo açılışı, standart kullanıcı, ASCII dışı yol, dolu port,
   yedek/dışa aktarım, süreç kapanışı, güncelleme, başarısız açılışta geri dönüş ve kaldırma.

Önceki kullanıcı demo gözlemleri eski tarayıcılı .31 paketindedir; masaüstü kabulü sayılmaz.
Sandbox/başka makine sonucu geliştirici provasıyla karıştırılmaz. Bu son test, daha sonraki
profesyonel pilot veya sürekli bakımın sona erdiği anlamına gelmez.

## Yapı ve üretim

PLER.exe mevcut sürüm seçimi/kilit mekanizmasıyla Python'ı --desktop modunda çalıştırır.
Paketli Electron yalnız kendi localhost servisini açar. Erişim anahtarı komut satırına veya
masaüstü terminal çıktısına yazılmaz; yalnız alt sürecin ortamıyla gider. Node/ön-yükleme köprüsü
renderer'a verilmez. Ayrı oturum, context isolation, sandbox ve mevcut CSP korunur.
Harici sayfalar uygulama içine yüklenmez; HTTPS yardım bağlantıları sistem tarayıcısında açılır.
Ana pencere veya backend kapanınca diğeri de kapanır. Wheel/terminal tarayıcı girişi korunur.

Electron 45.2.3 kilitlidir; Chromium motorunu taşır ve paket boyutunu artırır.
Güncelleyici 2 ilk elle geçiş gerektirir; veri şemaları değişmez. Authenticode imzası ve
temiz ortam kabulü açık. Kaynak siteye, eski indirmelere veya özel anahtarlara dokunulmaz.

desktop/ içinde npm ci, ardından gerekirse node node_modules/electron/install.js çalıştırılır.
tools/build_windows_portable.py mevcut Python runtime, C# derleyicisi ve kilitli Electron ile
yeni klasöre özel aday üretir. Gerçek kontroller ve teslim yolu reports/desktop-v1/REPORT.md'de.

Masaüstü oturumu geçicidir: arayüz dili/filtre tercihleri yeniden açılışta sıfırlanabilir.
Kalıcı PLER geçmişi/iş kayıtları ayrı yerel veri klasöründe korunur. İşletim sistemi
bildirim izinleri bu adayda kapalıdır; uygulama içi kota uyarıları çalışır.

Geliştirme/paketleme ve geliştirici kontrolü 1–4 tamamlandı. Son aday ZIP ve gerçekleşen
kontroller için ../../reports/desktop-v1/REPORT.md. Son görev 5 hâlâ bekliyor.
