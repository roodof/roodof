# Oturumu bul → kayıtlı kullanımı anla → uyarı kur

0.9.14 yerel masaüstü adayı, ana oturum akışını sadeleştirir. Public beta 0.9.11 olarak kalır.

- **Bul:** Arama etiketlidir. `/`, Oturumlar açıkken ve bir giriş alanı/pencere/ilk kullanım ekranı etkin değilken aramaya odaklanır. Arama mevcut kapsamın bütün yüklenmiş kayıtlarını tarar; yazı kalıcı tercih dosyasına girmez. Yeni sütun varsayılanı oturum/token/kayıt durumudur. Önceden kaydedilen sütunlar üstündür; Sütunlar’dan diğer alanlar açılır.
- **Anla:** Oturum ayrıntısı mevcut toplamları kullanır. Girdi, cache_read + cache_write ve çıktı ayrı gösterilir; reasoning yeniden eklenmez. Eksik token, kısmi fiyat kapsamı ve bilinmeyen fiyat açıklanır. API fiyatı gerçek fatura değildir. Modeller ve ayrıntılı alanlar katlanır bölümde kalır.
- **Uyarı kur:** Kullanım uyarısı içinde tek bir yerel details düzenleyicisi vardır. Hazır eşikler yalnız kullanıcı tıklayıp kaydettiğinde geçerlidir. Başlangıç önerisi mevcut kaydedilmiş toplamın üstündeki sonraki basamaktır. Aşılmış eşik için açıklama gösterilir; kaydetme yine açık kullanıcı eylemidir. Kaydedilmiş uyarı ve taslak ayrıdır. Katlayıp açmak veya reddedilen POST taslağı silmez. İstemci yeni izleme/fatura hesabı üretmez.
- **İzle:** Mevcut backend/native %80/%100, yaklaşık 10 saniye, en fazla 20 oturum, yalnız açık PLER ve yeterli güncel kayıt şartları değişmez. Ayarlar’daki Kullanım uyarıları → Oturum bul ve uyarı kur, aramaya döner.

Uzun listede seçim, zaten oluşturulmuş Tabulator satırlarına yazılır. Row formatter ilk durumu kurar; render/scroll sonrası tampon satırları dahil mevcut öğeler güncellenir. Görünmeyen kayıtlarda getElement() çağırıp binlerce öğe oluşturulmaz. Liste verisi sayfalama ve arama sözleşmesi aynıdır. İş seçicisindeki **400 sınırı ve work-view.jsx değişmedi**.

Geliştirici kanıtı [session-flow raporundadır](../../reports/session-flow-v1/REPORT.md). Yapay kayıtlı renderer ölçümleri Python log okuma, Electron toplam belleği veya tüm cihazlarda açılış garantisi değildir. Gerçek kullanıcı, gerçek ajan/WSL ve temiz Windows kabulü SON görev olarak açıktır.
