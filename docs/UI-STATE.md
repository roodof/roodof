# Ortak arayüz durumu — 0.9.10

`web/ui-state.js`, controller ve masaüstü görünümlerinin ortak, bellekteki bildirim katmanıdır. Erişim anahtarını, ağ çağrısını veya kalıcı tercihi yönetmez. Ağ ve kayıt işlemlerinin sahibi `app.js`; güvenli kalıcı görünümün sahibi `frontend/view-preferences.js` ve mevcut desktop normalizasyonudur.

## Sözleşme

- Ana filtreler, yerel arama/sıralama/kalite seçimi ve bölüm ortak durumda tutulur. Native kontroller controller girişidir; segmentler, rapor kapsamı ve görünüm hafızası aynı bildirimi dinler. Arama metni kalıcı görünüm dosyasına eklenmez.
- Aynı JavaScript turundaki filtre değişiklikleri tek GET üretir. Sonraki değişiklik önceki GET’i iptal eder; revision kontrolü geç gelen sonucu da reddeder. Metadata POST’ları iptal edilmez veya birleştirilmez. Tarama polling zamanlayıcısını aynı controller yönetir.
- Başlangıçtaki proje seçimi mevcut proje seçenekleriyle doğrulanır. Seçim için ikinci okuma gerekiyorsa geçici, uygulanmamış sonuç yayınlanmaz. Geri yükleme sırasında eski tercih erken ezilmez.
- Tablo projection’ı bir kez filtrelenir/sıralanır. Grid görünür satırları bu projection’dan alır. Gizli eski HTML tablosunda ikinci bir satır listesi üretilmez. Değerlendirme, inspector seçimi ve iş kontrolleri açık bildirimle güncellenir; klavye odağı korunur.
- Genel görünüm ve kota grafikleri görünürken yeni snapshot için güncellenir. Görünüm izleme kayıtları `WeakSet`, tarih sıralama cache’i `WeakMap` kullanır; eski snapshot’ları sırf izleme kaydı için tutmaz.
- `show()` aynı bölümü yeniden açarken yeni veri işlemi, animasyon veya tercih yazısı başlatmaz. İstenen başlık odağı/üste dönme korunur. Eski `pler-screen` anahtarı bir kez okunup güvenli görünüm kaydına taşınır.
- Kaynak/başlangıç modüllerinin bölüm bildirimleri devam eder. İş seçicinin 400 sınırı ve `work-view.jsx` dosyası değiştirilmedi. Toast/animasyon için kalan DOM gözlemcileri veri aktarım kanalı değildir. Boyut değişimini izleyen `ResizeObserver` korunur.

## Geliştirici ölçüm bütçesi

`reports/ui-state-v1/serve.py` gerçek ajan/Git/WSL okumadan 1.000 veya 5.000 uydurma oturum üretir. Karşılaştırma aynı Windows makinesinde headless Edge ve1366×900 görünümle yapılır. Bu, gerçek kayıt ayrıştırıcısı veya temiz Windows kabulü değildir.

5.000 oturum için denetlenen sınırlar: uydurma ilk açılış15sn altında; tekrar projection’ın senkron kısmı100ms altında; tüm geçmiş açıkken GC sonrası renderer JavaScript heap’i128MiB altında; projection başına tek filtre geçişi; aynı turdaki üç ana filtre değişiminde tek GET; aynı bölüme tekrar tıklamada sıfır tercih yazısı; sıfır gizli legacy tablo satırı.

Bu sınırlar ürünün bütün cihazlarda performans garantisi değildir. Heap sayısı Electron/Python toplam belleği veya işletim sistemi çalışma kümesi değildir. Önce/sonra sayılar ve ham ölçümler çalışma raporundadır; ölçekli gerçek kayıt/temiz makine kabulü SON görevdir.
