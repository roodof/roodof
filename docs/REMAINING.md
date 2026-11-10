# Güncel öncelik listesi — frontend, backend ve girişimci bakışları

**10 Kasım 2026 yayın güncellemesi:** Ücretsiz beta0.9.21; Windows kurucusu ana indirme, ZIP/Python isteğe bağlı. Önceki sürüm/yayın kayıtları aşağıda tarihsel kanıttır.400 seçici ertelenmiş durumda. Gerçek ajan/WSL/kullanıcı/temiz Windows kabulü Q01/SON; E01değer veR02lisans/imza kararları açık.

Bu tablo son kaynak incelemesinin güncel iş özetidir. **Güncel yönlendirme:** Kullanıcı 400 sınırına bir süre dokunulmamasını ve diğer işlere devam edilmesini istedi; F01 ertelendi, F02/F03 0.9.6 yerel adayında uygulandı. Aşağıdaki tarihli notlar geçmiş kanıt ve ayrıntılardır. 8 Kasım: Kullanıcı yeni gözlemleri kaydetmeyi ve N01 uyarı eşiğinin uygulanmasını istedi. Diğer açık işler bu tur kendiliğinden tamamlanmış sayılmaz. Ücretsiz masaüstü beta 0.9.11 siteye eşitlendi; canlı indirme ve sürüm imzası doğrulandı. Önceki 0.2.28–0.2.31 indirmelerinin baytları korundu. Temiz Windows ve gerçek kullanıcı kabulü Q01/SON olarak açık. B01b kullanıcı kontrollü ayar aktarımı 0.9.12 yerel adayda tamamlandı; sitedeki ücretsiz beta 0.9.11. Aşağıdaki eski tarihli B01b açık notları tarihsel kapsamı anlatır; güncel durum ilk tabloda ve 0.9.12 bölümündedir.

Öncelik 1 yayın hazırlığında önce ele alınır; öncelik 2 sağlamlaştırma/kapsam kararıdır. Öneri satırı onaylı ilk sürüm kapsamı veya yapılmış özellik sayılmaz. Frontend ekran ve etkileşim doğruluğunu, backend kayıt/veri/işlem doğruluğunu, girişimci kullanıcı faydası ve ticari kapsamı değerlendirir.

| ID / sıra | Kalan iş | Ana bakış | Diğer bakışlarla kapanış ölçütü | Durum |
|---|---|---|---|---|
| F01 / 1 | Toplu bağlama seçicisindeki ilk 400 oturum sınırını kaldır veya açık sayfalama/arama sun | Frontend + backend | Mevcut bir oturum yalnız liste kesildiği için bulunamaz hale gelmez; büyük geçmişte maliyet sınırlı kalır. | Kullanıcı isteğiyle ertelendi; 400 aynen korunacak |
| F02 / 1 | Filtre temizleme yollarında görünen dönem/ajan seçimini gerçek sorguyla eşitle | Frontend | Görünen dönem/ajan, gönderilen sorgu, rapor kapsamı ve görünüm hafızası eşitlendi; temizle tek sorgu üretir. | 0.9.6 uygulandı; SON kabul açık |
| F03 / 1 | Tablo içindeki alt düğmelerin Enter davranışını koru | Frontend | Ajan Enter/Space ile filtreler; başlık bir kez açılır, oklarla odak korunur. Eski close olayı yeniden açılan paneli temizlemez. | 0.9.6 uygulandı; SON kabul açık |
| B01a / 2 | Doğrulanmış yerel dosya taşınırken oturum kimliğini, iş/değerlendirme/bütçeyi koru | Backend | Önceden gözlenmiş aynı fiziksel dosyada eski kod korunur; sadece sağlayıcı ID’siyle aktarım yok. Anotasyon dosyaları yeniden yazılmaz. | 0.9.7 yerel kapsam uygulandı; SON kabul açık |
| B01b / kapsam | Doğrulanamayan taşıma için kullanıcı kontrollü yeniden bağlama | Frontend + backend | Eski/kayıp ayarları canlı hedefe önizleme, açık çakışma seçimi ve koşullu geri alma ile aktar; fiziksel kimlik veya kullanım birleştirmesi yapma. | 0.9.12 yerel adayda uygulandı; gerçek disklerarası/WSL kabulü Q01/SON açık |
| FB01 / 3 | Özel kayıt klasörü ve WSL kaynaklarını uygulamadan yönetme | Frontend + backend | İlk kullanım/Ayarlar üzerinden seç, kontrol et, ekle, kaldır; otomatik kaynaklar, mevcut yol/izin ve çalışan WSL sınırları korunur. | 0.9.8 uygulandı; canlı WSL ve gerçek Windows seçici kabulü Q01/SON açık |
| B02 / 4 | Başlık okuma kapsamı ve görünmeyen başlık nedenleri | Backend + frontend | Oturum ayrıntısında yokluk/arşiv/konum/erişim/bozuk-büyük indeks/bütçe/pencere/değişim açıklanır; kısmi başlık en güncel diye sunulmaz. | 0.9.9 uygulandı; gerçek ajan kabulü Q01/SON açık; arşivde başlık saklama ayrı karar |
| B03 / 4 | İçerik taşımayan hata kodları ve yerel destek tanılaması | Backend + frontend | Kaynak/Git/başlık/geçmiş/tercih/görünüm hazırlama sabit kodlarla ayrılır; yerel indirmede yalnız sürüm/zaman/durum/kod/sayı; sonraki adım var. | 0.9.9 okuma tanılaması uygulandı; temiz makine kabulü Q01/SON açık |
| FB02 / 5 | Ortak arayüz durumu ve büyük geçmiş performansını hedefli sadeleştirme | Frontend + backend | Açık bildirimler, tek filtre projection’ı, birleştirilmiş GET, görünür grafik güncellemesi ve belgeli 1.000/5.000 uydurma geçmiş bütçesi. | 0.9.10 hedefli kapsam uygulandı; gerçek büyük kayıt/temiz makine Q01/SON açık |
| E01 / 6 | Hedef kullanıcı, tekrar kullanım nedeni ve ilk sürüm teklifi | Girişimci | Somut karar faydası ve gerçek kullanıcı geri dönüşü belgelenir; özellik varlığı ödeme talebi sayılmaz. Frontend ilk sonuca ulaşmayı, backend ölçüm sınırlarını destekler. | Öncelik 1, açık |
| E02 / 6 | İlk çıkış ücretsiz beta; sonraki ücretli kapsam | Girişimci | Kullanıcı ilk çıkışın ücretsiz beta olduğunu yeniden teyit etti. Beta için ödeme, abonelik veya ücretli erişim altyapısı gerekmez. Gelecekte ücretlendirme, kapsam ve lisans hakkı yönetimi ayrı karardır. | Ücretsiz beta kararı kesin; sonraki ücretlendirme ertelendi |
| R01 / 7 | Site, indirme, README, yardım ve güncelleme bilgisini tek masaüstü yayınında hizala | Frontend + backend + girişimci | Aynı sürüm, güncel gerçek görüntüler, desteklenen platform/kapsam, doğru paket/hash/kanal ve anlaşılır indirme yolu. Mevcut yayın kullanıcı izni olmadan değiştirilmez. | 0.9.11 ile site/indirme/README/yardım eşitlendi ve canlı doğrulandı; Q01 ayrı |
| I01 / 7 | Tek tıkla Windows kurulumu (PLER-Setup.exe) | Backend + girişimci | Yönetici izni ve soru olmadan kullanıcı klasörüne kurar; Başlat/masaüstü kısayolu ve Uygulamalar kaydı; eski sürümü uygulama kapalıyken değiştirir, aynı/yeni sürümü açar; kaldırma geçmişi varsayılan korur. Electron bildirim kısayolu ikinci "Electron" girdisi açmaz. | Claude bu makinede kurdu/yeniden kurdu/yükseltti/açıkken reddetti/kaldırdı, artık kalmadı. Yayın, imza (SmartScreen) ve temiz Windows kabulü kullanıcı kararı/Q01 açık |
| R02 / 7 | Ürün lisansı, dağıtım koşulları ve Windows yayıncı imzası kararı | Girişimci + backend | Seçilmiş PLER/destek kimliği korunur; imzalı güncelleme manifesti ile Authenticode ayrı ele alınır. Lisans ve imza kararı kullanıcıyla kesinleşir. | Karar bekliyor |
| N01 / uygulandı | Oturum bazlı token / dolar bütçe uyarısı | Frontend + backend + girişimci | Kullanıcı uygulamayı onayladı. 80/100 uyarıları, kalıcı tercih, bağımsız izleme ve yerel masaüstü bildirimi; sınırlar aşağıda. | 0.9.5 yerel adayda tamamlandı; SON kabul açık |
| N02 / uygulandı | Uygulamadan yedek kurtarma ve masaüstü geçmiş seçimi | Frontend + backend | Güvenilir dosyayı incele, yeni konumu gör, açık onayla ayrı klasöre kurtar; masaüstünde aç ve önceki geçmişe dön. Normal açılış seçimi hatırlar; özel veri klasörü kapsamı korunur. | 0.9.13 yerel adayda uygulandı; kaynak kayıtları yerel Git’te; Q01/SON açık |
| Q01 / SON | Son sabit paketin temiz Windows kabulü; ardından genel yayın kararı | Frontend + backend + girişimci | Açılış, kaynak okuma, klavye, kayıt/geri yükleme, güncelleme/geri dönüş, kapanış ve kaldırma aynı son adayda doğrulanır. | Kullanıcı isteğiyle SON görev, bekliyor |

## 0.9.21 — Yayın eşitlemesi

Kullanıcı site, dokümantasyon ve GitHub yayınını açıkça istedi. Kurucu ana indirme, ZIP/Python isteğe bağlı; eski URL/hashler korunur. Yayın kanıtı ../../reports/publish-0.9.21/REPORT.md. Q01gerçek ortam kabulü SON; E01değer veR02lisans/imza kararları açık.400aynı.

## 0.9.21 — Kurulum incelemesi

Claude kurucu/kısayol/Windows sürüm değişiklikleri korundu; setup/uninstall yarışları, çalışan uygulamanın değiştirilmesi ve junction hedeflerine dokunan temizlik düzeltildi. [Kurulum](SETUP.md), [kanıt](../../reports/setup-review-v1/REPORT.md). Mevcut kullanıcı kurulumu ve gerçek kayıtları değiştirilmedi; public0.9.11 ve400 aynı. Q01/SON, E01/R02 açık.

## 0.9.20 — Yükleme hareketi

İskelet ve bekleme çizgisi transform katmanlarında; hızlı geçişte eski giriş iptal. Azaltılmış hareket ve mevcut veriyle yenileme korunur. Kanıt reports/loading-motion-fix-v1 altında.400/public0.9.11 aynı, temiz Windows kabulü SON.

## 0.9.19 — Logo geçişi

Kullanıcının bildirdiği logo tıklamasında belge yenileme kaldırıldı; mevcut Oturumlar ekranı açılır. Fare/Enter, TR/EN ve taslak koruma kontrolü reports/brand-home-fix-v1 altında.400 ve public0.9.11 aynı; gerçek ortam kabulü SON.

## 0.9.18 — UX5 kavram adları ve UX6 yardımcı ekran okunabilirliği

Kullanıcı “5 ve6yı yapalım” dedi. Menü, komut arama, oturum/iş özeti, kullanım uyarısı, yerel bildirim, CLI ve TR/EN yardımda sağlayıcı hesap kotası / kişisel kullanım uyarısı / API fiyat karşılığı ayrımı tamamlandı. Yardımcı ekranlar ortak 12/13/15 px ölçülerinde; çevrimdışı yardım koyu tasarıma alındı. [Davranış](TERMINOLOGY-READABILITY.md), [geliştirici kanıtı](../../reports/terminology-readability-v1/REPORT.md). E01/R02 veQ01/SON açık.400 seçici dosyası ve public0.9.11 aynı.

## 0.9.17 — UX3 korunarak UX4 ilk kullanım

Kullanıcı “3 ve4ü yap” dedi. UX3 zaten0.9.16’da tamamlandı; bu pakette regresyonla korunur. UX4 tek ana eylem (kayıt/klasör/sorun), kapalı ikincil seçenekler, hata halinde bulunabilen oturumlar ve açık tamamlama davranışıyla tamamlandı. [Davranış](FIRST-USE-SIMPLE.md), [geliştirici kanıtı](../../reports/first-use-simple-v1/REPORT.md). UX5 kavram adları ve UX6 yardımcı ekran tipografisi hâlen öneri. E01/R02 veQ01/SON açık;400 ve public0.9.11 aynı.

## 0.9.16 — UX3 aramada çıkmazları kaldırma

Kullanıcı “3ü yap” dedi. Sonuçsuz arama ve boş kapsamda tek kısıtı genişleten eylemler, görünen seçim özeti, boş tabloyu kaldırma, kaynak/okuma hatası ve yeniden deneme yolları tamamlandı. Arama temizleme artık kalite filtresini korur. [Davranış](SEARCH-RECOVERY.md), [geliştirici kanıtı](../../reports/search-recovery-v1/REPORT.md). UX4–6 (ilk kullanım kararları, kavram adları, yardımcı ekran tipografisi) halen öneri; E01/R02 veQ01/SON açık.400 ve public0.9.11 aynı.

## 0.9.15 — İş bağlantısı ve Ayarlar sadeleştirmesi

Kullanıcı önerilen1 ve2 numaralı UX işlerine başlamamızı istedi. Oturum iş bağlantısı tek açılır bölümdedir; mevcut/yeni iş formları aynı anda gösterilmez, taslak korunur. Ayarlar üç grupta, destek araçları açılır satırlardadır; kısayollar hedefi açar. [Davranış](SETTINGS-WORK.md), [geliştirici kanıtı](../../reports/settings-work-v1/REPORT.md). Diğer öneriler (aramada çıkmazlar, ilk kullanım kararları, kavram adları ve tüm yardımcı ekranlarda tipografi) bu teslimde tamamlanmış sayılmaz.400 aynı; E01/R02 veQ01/SON açık; public0.9.11 değişmedi.

## 0.9.14 — Oturum arama, kullanım ve uyarı akışı

Kullanıcı kullanım kolaylığı/hız değerlendirmesindeki öneriyi uygulamamızı istedi. Oturum listesi yeni kullanıcılarda üç temel sütunla başlar; mevcut tercihler korunur. Görünür arama etiketi ve `/` kısayolu; ayrıntıda önce kayıtlı kullanım ve fiyat kapsamı, sonra açılır uyarı düzenleyicisi ve hazır eşikler vardır. Uzun liste seçiminde görünmeyen satır öğeleri oluşturulmaz; kaydırma seçimi güncel tutar. [Akış](SESSION-FLOW.md), [geliştirici ölçümleri](../../reports/session-flow-v1/REPORT.md). 400 dosyası aynı; gerçek kayıt/temiz Windows ve kullanıcı kabulü Q01/SON açık. R02 dağıtım lisansı/imza ve E01 gerçek kullanıcı faydası açık; public beta 0.9.11.

## 0.9.13 — Kaynak kaydı ve uygulamadan kurtarma

Kullanıcı profesyonel değerlendirmedeki sırayı kabul etti. 0.9.12 kaynakları 0948eb4 ve candidate/0.9.12 ile yerel kayda alındı; push/yayın yapılmadı. 0.9.13 Ayarlar’da güvenilir özel yedeği inceleme, yeni konum planı, açık onayla ayrı klasöre kurtarma ve masaüstünde geçmiş değiştirmeyi ekler. Normal masaüstü seçimi hatırlanır; önceki geçmişe dönüş vardır. Özel veri klasörüyle başlayan çalıştırmanın kapsamı korunur. [Sözleşme](HISTORY-RECOVERY.md), [geliştirici kanıtı](../../reports/history-recovery-v1/REPORT.md). Lisans/Authenticode kararı R02, gerçek kullanıcı E01 ve temiz Windows/gerçek ajan kabulü Q01/SON açık. 400 değişmedi; public beta 0.9.11.

## 0.9.12 — Taşınan oturumun ayarlarını yeniden bağlama (yerel aday)

Kullanıcının “4 ü yap aynen” talimatıyla B01b uygulandı. Ayarlar’da eski/arşivdeki kaydın iş bağlantıları, değerlendirmesi ve bütçe eşiği seçilen canlı oturuma taşınır. Aynı işte bağlantı tekilleşir; hedefin diğer bağlantıları ve notları kalır. Çakışan değerlendirme/eşik açık seçim ister; önizleme yazmaz. Son aktarım koşullu geri alınır ve sonraki bağımsız düzenlemeleri korur. İlgili ayar değişmişse geri alma üzerine yazmaz. Kesilen çoklu yazı ortak kilitte tamamlanır; bozuk/beklenmeyen dış değişiklik korunur. Geri alma kopyası özel yereldir ve temizlenebilir; normal rapora veya yedeğe girmez, yedek sonuçtaki ayarları içerir. Önce eski PLER pencereleri kapatılır.

Bu işlem fiziksel dosya kimliğini doğrulamaz, oturum kodlarını ve kullanım toplamlarını değiştirmez; ajan kayıtlarını taşımaz. Yeni kaynak önce eklenip okunur. İki arama bütün yüklenmiş kayıtları 20’lik sayfalarla gezer; ayrı iş seçicisinin 400 sınırı byte düzeyinde aynıdır. İzleyicinin kaynak/fiyat eksikliği sınırları korunur. Gerçek disklerarası taşıma/kopya, canlı WSL ve temiz Windows/gerçek kullanıcı kabulü Q01/SON olarak açık.

[Çalışma kaydı ve yerel paket](../../reports/session-reconnect-v1/REPORT.md): 234 Python kontrolü (232 geçti, 2 platform atlaması), 106 Node kontrolü, iki dilde 390/1440 arayüz ve paketli CPython 3.14.10 aktarım/kurtarma/geri alma doğrulandı. Yerel gerçek masaüstü boş/demo açılış-kapanış ve paket/kaynak eşliği geçti. Sitedeki indirme ve imzalı feed 0.9.11; bu tur yayın/commit/push yapılmadı. E01 beta kullanıcı/geri bildirim, R02 lisans/Windows imzası kararları ve Q01 SON açık; ödeme beta sonrasında.

## 0.9.11 — Ücretsiz masaüstü beta eşitlemesi

Kullanıcı “Eşitle” talimatıyla site, indirme ve ilk kullanım eşitlemesini istedi. Windows ZIP, terminal/tarayıcı wheel, Türkçe/İngilizce site ve paket içi yardım 0.9.11 oldu. Site masaüstü pencereyi, ücretsiz beta kararını, kayıt klasörü seçimini, iş bağlamayı ve %80/%100 oturum uyarılarını doğru kapsamla anlatır. Yaklaşık $3 fiyat önerisi kaldırıldı. Eski tarayıcı sürümünden ilk geçiş yeni klasöre elle çıkarılarak yapılır; güncelleyici uyumluluğu 2, veri biçimleri aynı.

169.55 MB ZIP ayrı public GitHub dağıtımında korunur; site sunucusu sabit, izinli HTTPS kaynaklardan tek normal ZIP olarak akıtır. Tarayıcı JavaScript’i gerekmez. Özel uygulama Git deposu yayımlanmaz. Eski sekiz indirme dosyası bayt düzeyinde değişmedi. Yayın imzası mevcut korumalı anahtarla doğrulandı; Authenticode sağlanmış sayılmaz. Site ve indirme teknik eşliği R01 kapsamında tamamlandı. [Canlı yayın ve kanıt](../../reports/beta-alignment-v1/REPORT.md).

23 site/indirme kontrolü, 2 ilk kullanım kontrolü, tüm 75 Python/web dosyasında wheel/kaynak/paket eşliği, yerel native boş/demo açılış-kapanış ve yerel gerçek tarayıcı ZIP indirmesi geçti; üretim tarayıcı kontrolü indirmeyi tekrarlamadı. Son canlı kontrolde iki dil, imzalı feed, ZIP/hash/CRC, wheel, ekran görüntüleri ve eski indirmeler doğrulandı. Bu geliştirici kontrolleri temiz Windows/gerçek kayıt kabulü değildir; Q01 SON açık. 400 seçici dosyası byte düzeyinde aynı. E01 gerçek tekrar kullanım, B01b ve R02 kararları açık; ücretlendirme beta sonrasına ertelendi.

## 0.9.10 — Ortak filtre, ekran ve yenileme durumu

**FB02 hedefli kapsam uygulandı:** `web/ui-state.js` ile filtreler, ekran, tamamlanmış snapshot, tablo projection’ı ve bekleme/seçim/iş/kota bildirimleri ortak akışta. Segmentler, rapor kapsamı, görünüm hafızası ve grid veri için DOM gözlemlemez. Aynı turdaki ana filtre değişiklikleri tek GET üretir; sonraki seçim eski GET’i iptal eder ve geç yanıtı reddeder. Metadata POST’ları iptal edilmez. İlk proje geri yüklemesinde uygulanmamış ara veri yayınlanmaz. Yenileme POST’u ve onu izleyen GET aynı bekleme durumunu paylaşır; bitince kontroller yeniden açılır.

- Tablo tek filtre/sıralama sonucunu kullanır; gizli legacy tablo listesi üretilmez. Grafikleri taşıyan görünümler yalnız tamamlanmış snapshot ve görünür bölüm için yenilenir. İş taslakları, iş oluşturma/bağlama, klavye, dil/proje hafızası ve ilk okuma hata yolları korunur.
- Aynı ekranı tekrar açmak yeni animasyon/veri işlemi veya tercih yazısı başlatmaz. Güvenli görünüm aynı değerde yeniden yazılmaz; filtrelerin kalıcı kaydı aynı turda birleşir. Arama metni kalıcı görünüm dosyasına eklenmez. Boyut ve görsel feedback için kalan gözlemciler korunur.
- [Çalışma raporu](../../reports/ui-state-v1/REPORT.md) ve [durum sözleşmesi](UI-STATE.md). 5.000 uydurma oturumda filtre geçişi2→1, aynı turdaki GET3→1, aynı ekrana tekrar tıklamada storage yazısı6→0, gözlemci18→8, gizli satır20→0. 1.000/5.000 örneği belgeli geliştirici sınırlarını geçti. Bunlar gerçek log ayrıştırıcısı/temiz Windows veya her cihaz için hız garantisi değildir.
- Node106/106, ilgili Python62/62, build/design, paketli TR/EN filtre/klavye/yeniden açılış, iş/yanıt sırası ve ilk okuma hata yolu, paket runtime ve native smoke geçti. 400 seçici dosyası byte düzeyinde aynı. Public0.2.31 aynı. Gerçek büyük geçmiş ve temiz Windows kabulü Q01/SON. Sıradaki genel öncelik E01: ilk kullanıcı ve somut ilk sürüm vaadi. E02 ilk çıkış ücretsiz beta olarak kesin; sonraki ücretlendirme ayrı aşamadır.

## 0.9.9 — Başlık nedenleri ve okuma tanılaması

**B02 uygulandı:** Oturum ayrıntısında başlık yerine iş/proje adı gösterilmesinin nedeni açıklanır. Okunabilir metadata içinde başlık yok, arşivde başlık tutulmuyor, konum tanınmıyor, dosya yok/erişilemiyor, indeks bozuk/büyük, toplam başlık bütçesi dolu, baş/son pencere sınırlı ve dosya okunurken değişti durumları ayrılır. Başlık indeksi dosya başına4MiB, yenileme toplamı64MiB; Claude ilk/son64KiB. Kısmi başlık en güncel adlandırma diye sunulmaz. Asıl transcript kaybolmuşsa eski Claude indeksindeki başlık mevcut olsa da sınırlı işaretlenir. Başlıklar arşive eklenmedi; WSL başlık erişimi için seçili kök kapsamı genişletilmedi. Kullanım hesap kuralları değişmedi.

**B03 uygulandı:** **Ayarlar → Okuma durumu ve tanılama**, filtrelerden bağımsız sabit kod ve sayılarla kaynak/başlık/geçmiş/Git/tercih/görünüm aşamalarını ve sonraki adımı gösterir. Son başarısız okumada önceki başarılı görünüm olduğu ve zamanı açıkça yazılır. İlk okumada hiç görünüm oluşmasa bile Ayarlar, klasör seçimi ve tanılama açılır; ilk kullanım ve oturum ekranından Sorunu incele kısayolu vardır. Yeni deneme başarılı olduğunda eski hata kodu temizlenir.

- Yerel tanılama JSON’u sadece sürüm, okuma zamanı/durumu, sabit kod/açıklama ve sayıları içerir. Konuşma, başlık, sağlayıcı/oturum kimliği, özel yol, ham hata veya anahtar içermez. Otomatik gönderim/persist edilen hata günlüğü yok. Özel geçmiş yedeğiyle ayrı dosyadır; yedek kaynak yollarını içerebilir.
- Tanılama ve başlık durumu UI/API katmanındadır; normal raporlardan çıkarılır, kayıt önbelleğine/arşive/yedeğe katılmaz. Tek dosyada birden çok hata varsa mevcut okuyucunun ilk etkilenen-dosya nedeni korunur; tanılama her bozuk satırın eksiksiz günlüğü değildir. Tanılamada başlık yokluğu bilgi olarak, kullanım okuma sorunu ayrı uyarı olarak gösterilir.
- [Rapor ve yerel paket](../../reports/read-diagnostics-v1/REPORT.md):213 ilgili Python kontrolü,210 geçti/3 atlama/0 hata; build/design; paketli CPython3.14.10, paketli TR/EN/native indirme/yeniden açılış, boş/demo açılış-kapanış ve kaynak/manifest/ZIPCRC geçti. Uydurma kayıt kullanıldı; gerçek ajan/canlı WSL/temiz makine kabulü Q01/SON. 400 byte düzeyinde aynı; public0.2.31 aynı.
- Sıradaki teknik öncelik FB02: ekranlar arası ortak durumun hedefli sadeleştirilmesi; büyük geçmişte süre/bellek ölçümü olmadan yavaşlık veya hızlanma iddiası yok. B01b ve ticari/yayın kararları açık kalır.

## 0.9.8 — Kayıt klasörlerini uygulamadan yönetme

**FB01 uygulandı:** İlk kullanımda **Kayıt klasörü ekle**, Ayarlar’da **Kayıt klasörleri**. Claude Code veya Codex seç, masaüstündeki klasör seçicisini kullan veya tam yolu gir, **Kontrol et** ile eklenecek kökleri incele, ardından **Klasörü ekle**. Ajan ana klasöründeki mevcut `projects` / `sessions` / `archived_sessions` alt klasörleri seçilir; doğrudan bir kayıt klasörü de kabul edilir. Klasörün erişilebilir olması kullanılabilir oturum içerdiği anlamına gelmez; loglar ekledikten sonra mevcut sınırlı okuyucuyla taranır.

- Standart/ortam değişkeni kaynakları açık kalır. En fazla 12 ek klasör; tekrar kök tekilleştirme, kalıcı `log-sources.json`, revizyon çatışması ve bozuk dosyayı koruma. Seçim yalnız bu bilgisayarda tutulur, seçim dosyası rapora/yedeğe katılmaz. Özel geçmiş yedeği kaynak yollarını içerebilir; geri yüklemeden sonra ek klasörler yeniden seçilir.
- Kaldırılan kaynak taranmaz; kaynak dosyaları ve saklanan özel geçmiş silinmez. Eski iş/bütçe kimliği tahminen yeni bir kaynağa aktarılmaz. B01b açık kalır. Seçim değiştiğinde izleyici eski bağları duraklatır ve yeni taramayla bağlanır.
- WSL yalnız açık seçilen ve zaten çalışan dağıtımlarda mevcut capability üzerinden okunur. Duran/erişilemeyen dağıtım ayrı anlatılır; keyfi ağ paylaşımı reddedilir, dağıtım başlatılmaz. WSL fiziksel taşıma kimliği doğrulanmış sayılmaz. Kullanılamayan önbellekle yalnız WSL okumayı durduran eski kimlik-kayıt uç durumu giderildi; yerel kimlik kanıtı yokken kullanılamayan veri konumuna yazı yapılmaz.
- Tek masaüstü köprüsü sadece yerel klasör seçme işlemini sunar; kendi uygulama/üst çerçeve doğrulanır. Genel dosya, komut veya IPC yetkisi açılmadı. Türkçe/İngilizce, dar ekran, yeniden açılış ve özel yol kapsamı geliştirici verisinde doğrulandı.
- [Rapor, paket ve kanıt](../../reports/log-sources-v1/REPORT.md). 211 farklı ilgili Python kontrolü: 208 geçti/3 atlama/0 hata; Node16/16; build/design; paket runtime, UI ve native smoke geçti. OS klasör seçici sonucunda uydurma dönüş kullanıldı; gerçek seçim etkileşimi/canlı WSL/temiz Windows kabulü Q01/SON olarak açık. 400 aynen korundu, public0.2.31 aynı. Sıradaki teknik öncelik B02/B03: eksik başlığın ve okunamayan kaynağın nedenini anlaşılır gösterme.

## 0.9.7 — Doğrulanmış yerel oturum kimliği

**Uygulanan B01a:** Windows’un yerel disk/dosya kimliği, oluşturulma bilgisi, sağlayıcı/oturum kimliği ve başlangıç zamanı birlikte doğrulanır. Aynı dosyanın desteklenen seçili kaynaklarda yeniden adlandırılması veya aynı disk içinde taşınması ilk oturum kodunu korur. Önce/sonra kaynak örneklemesi yapılır; ağ/WSL yolu dosya kimliği için yoklanmaz. Windows volume GUID’i CPython3.9/3.14 disk-kimliği farkını giderir.

- İş, değerlendirme ve bütçe dosyaları taşınmaz/yeni anahtarla yazılmaz; mevcut kod korunur. Yeni `session-identities.json` yalnız hash’ler ve eski satır kodları tutar, prompt/başlık/yol içermez. En fazla20.000 dosya kanıtı/8MiB/kanıt başına32 ad; sınır/izlenemeyen kaynak/kararsız eşleme açık gösterilir. Bozuk/değişen dosya ezilmez, varsa önceki dashboard korunur.
- Kopya dosya, aynı yolda yeniden yaratılan dosya, çelişen sahip ve yeni sağlayıcı kimliği eski anotasyonları otomatik devralmaz. Bu modül hesap motorunun kopya uzlaştırmasını değiştirmez; yalnız anotasyon kimliği/provenansını korur.
- Doğrulanmış canlı asıl dosyanın bütçesi, eski adın arşiv kaydı nedeniyle durmaz. Ek saklanan kopyalar ancak her tanımlı kullanım ve fiyat/model kanıtı canlıda kapsanıyorsa izlenir. Eksik/çelişen saklanan kullanım veya fiyat kesin kalan bütçe gibi sunulmaz.
- Kimlik kaydı **ve bütçe ayarları** yeni özel yedeğe eklendi. Eski yedekler kabul edilir. Aynı bilgisayarda özgün kaynak nesneleri için doğrulama korunur; başka bilgisayar/disk için otomatik yol/kimlik eşleme sözü yok.
- [Çalışma kaydı ve paket](../../reports/session-identity-v1/REPORT.md). Python242test/0hata/3atlama, Node14, paketli TR/EN/native UI ve paketliCPython3.14 kimlik/geri yükleme geçti. Tam yenileme öncesi dosya nesnesi değişimi de eski bütçeyi devralmaz. 400 sınırı değişmedi. Temiz Windows kabulü SON görev; public0.2.31 aynı. B01b otomatik koruma dışında kalan açık kapsamlardır. Sıradaki genel öncelik FB01 kayıt klasörlerini uygulamadan yönetme.

## 0.9.6 — 400 korunarak filtre ve klavye düzeltmesi

F01 kullanıcı isteğiyle ertelendi; `frontend/work-view.jsx` değişmedi ve 400 kesimi aynı. F02/F03 için [çalışma kaydı](../../reports/filter-keyboard-v1/REPORT.md): boş filtre seçimini temizleme, tek istek, görünür seçim/sorgu/rapor/tercih eşliği; Enter/Space ajan filtresi, başlık açma, ardışık oklar, değerlendirme seçimi ve hızlı close/reopen. TR/EN ve gerçek Electron kapat/yeni profil doğrulandı. Geliştirici kontrolleri temiz Windows kabulünün yerine geçmez; Q01 SON görev. B01a 0.9.7 ile desteklenen yerel dosya kapsamına alındı; B01b belirsiz yeniden eşleme açık.

## Yeni gözlemler — üç bakışın kalan işlere etkisi

Bunlar son kaynak incelemesinin gözlem ve yorumlarıdır; ölçülmemiş performans veya kullanıcı davranışı kanıtı değildir.

- **Frontend / F01–F03:** İlk 400 oturumla sınırlı seçici, eski filtre temizleme yolunda yanlış görünen seçim ve tablo içindeki düğmelerde Enter'ın satıra gitmesi ayrı kabul ölçütleriyle açık. N01 tesliminde açıktılar; F02/F03 0.9.6 ile kapatıldı, F01 kullanıcı isteğiyle ertelendi.
- **Frontend + backend / FB02:** React, Tabulator ve eski kontrolcü arasındaki ortak durum/DOM köprüleri karmaşıklık yaratıyor. Önce tek filtre/oturum durumu ve hedefli büyük geçmiş ölçümü; geniş yeniden yazım için otomatik yetki yok.
- **Backend / B01–B03:** Doğrulanmış aynı yerel dosyanın yolu değişince B01a eski kodu korur; doğrulanamayan kopya/taşıma B01b’de açık; başlık okumalarında boyut/pencere sınırları var; genel okuma hatası nedeni destek için yeterince ayrıştırılmıyor. N01 kaynak taşınmasını tahmin ederek birleştirmeyecek, bulamadığı kaydı açıkça duraklatacak. Güvenli yeniden eşleme B01'de kalır.
- **Frontend + backend / FB01:** İlk kullanım ekranına ve Ayarlar’a özel klasör/WSL seçme, kontrol, ekle/kaldır akışı 0.9.8 ile eklendi. Gerçek OS seçici, canlı WSL ve temiz makine kabulü Q01/SON kapsamında açık.
- **Girişimci / E01–E02:** Arayüz kalitesi ve yeni uyarı özelliği tek başına tekrar kullanım/ödeme isteğini kanıtlamaz. İlk hedef kullanıcı, oturum sırasında verilen karar, ücretsiz/ücretli sınır ve gerçek geri dönüş ayrı iş.
- **Üç bakış / R01–R02:** Yerel masaüstü adayı ile eski site/README/güncelleme kanalı tutarlı hale getirilmeli. Windows uygulama imzası ile imzalı güncelleme manifesti farklıdır; lisans, dağıtım ve fiyat kararı açık. Seçilmiş PLER ve destek adresi korunur.
- **Üç bakış / Q01:** Yeni eşik özelliği de dahil son sabit paketin temiz Windows kabulü EN SON görev olarak kalır. Geliştirici kontrolleri bu kabulün yerine geçmez.

## N01 — Oturum bütçe uyarısı, 0.9.5 yerel adayda uygulandı

**Kullanıcı onayı:** “Yeni gelen gözlem yorumlarını da kalan işlere ekle sonra uyarı eşiğine başla.”

**Kanıt:** [Çalışma raporu ve yerel paket](../../reports/session-budgets-v1/REPORT.md). 53 odaklı Python,14 Node, build/design; paketlenmiş Electron’da gerçek native80/100 bildirimleri, filtrelerden bağımsız küçültülmüş izleme ve yeniden açılışta tekrar önleme doğrulandı. Paket runtime’ı ve bütünlüğü ayrıca denetlendi. Temiz Windows kabulü SON görev olarak açık.

- Oturum ayrıntısında token veya dolar (**API fiyat karşılığı**) eşiği; tüm oturumun kayıtlı toplamını kapsar. Token = input + cache_read + cache_write + output; reasoning ikinci kez eklenmez. Hesap kotası/bağlam penceresi değildir.
- Yüzde 80 ve yüzde 100 için birer bildirim. Doğrudan %100'e sıçrayan kayıt tek %100 bildirimi üretir. Bildirim gösterildikten sonra onay kalıcı tutulur. Aynı ayarı tekrar kaydetmek uyarıları sıfırlamaz; ölçüyü/eşiği değiştirmek yeniden etkinleştirir. Zaten aşılmış bir eşik ilk okuma sonrası uyarılır.
- En fazla 20 izlenen oturum. Ayarlar'da filtrelerden bağımsız izleme listesi, durum ve kapatma; uygulama içinde uyarı şeridi. Bozuk tercih dosyası üzerine yazılmaz, eşzamanlı değişiklik eski sürümle ezilmez.
- Arka plandaki okuyucu yaklaşık 10 saniyede bir yalnız son tam taramanın bildiği ilgili canlı kaynak grubunu denetler. Değişmemiş dosyaları yeniden ayrıştırmaz; grup en fazla 64 dosya, turda en fazla 64 MiB kaynak. Bu bir tam geçmiş yeniden taraması değildir; büyüyen ilgili grup yeniden uzlaştırılır. Yeni dosya/taşınma için kayıtları yenilemek gerekir; otomatik kimlik taşıma B01'de açık.
- Eksik kullanım/atfetme veya eksik dolar fiyatı olduğunda tutar bilinen kayıt olarak görünür, yeni eşik bildirimi bekletilir. Saklanan geçmiş içeren grup, kayıp/okunamayan dosya, okuma sınırı ve 40 saniyeden eski gözlem açık duraklama/güncel değil durumlarıdır; güvenli kalan bütçe sözü yok.
- Dolar hesabı mevcut motorun tam hassasiyetli API liste fiyatı karşılığıdır; gerçek fatura veya abonelik harcaması değildir. “Ayarlandığı andan itibaren” ayrı bütçe bu ilk kapsamda yok.
- Yerel masaüstü bildirimi ana süreçte sabit yerel uçları okuyarak çalışır; tarayıcı izinleri veya renderer erişimi genel olarak açılmaz. Bildirime tıklama oturumu açar. Windows ayarları/Rahatsız Etmeyin bildirimi gizleyebilir; uygulama içi durum kalır. OS teslimi ve süreç çöküşü arasında mutlak exactly-once garantisi yok; normal yeniden açılışta gösterilmiş eşikler tekrarlanmaz.
- Demo eşikleri yalnız bellekte; gerçek eşikler ayrı yerel `session-budgets.json` dosyasında yalnız satır hash'i/ölçü/eşik/revizyon/bildirim onayı tutar. Prompt, başlık veya kaynak yolu saklanmaz. Normal rapora eklenmez. 0.9.5’te özel yedeğe dahil değildi; 0.9.7’de kimlik kaydıyla birlikte özel yedeğe eklendi.
- **Bu bir uyarı eşiğidir.** Ajan kaydı gecikebilir, devam eden çağrı eşiği aşabilir. Oturumu durdurmaz. PLER kapanınca izleme ve arka plan okuyucu durur; kapalı uygulama/tray hizmeti yok.
- Girişimci: uzun oturumun kullanımını fark edip devam kararını verme hipotezi. Ücretli/ücretsiz konumu ve gerçek ödeme talebi E01/E02'de açık. Son temiz Windows kabulü hâlâ Q01/SON.

---

# 0.9.4 güncel not — ilk kullanım

Yerel kayıt durumu ekranı, filtreden bağımsız kaynak sayıları, kayıt yok/okunamadı/saklanan geçmiş açıklamaları, yeniden arama, tek düğmeyle tüm oturumlar ve tamamlanma hafızası eklendi. Ayarlar'dan tekrar açılır; tur artık kullanıcı isteğiyle açılır. Yeni klasör seçme veya hesap bağlama özelliği eklenmedi; mevcut kaynak keşfi kullanılır. Sonraki ürün işi: ücretsiz/ücretli kapsamı ve ilk kullanıcı teklifi. Temiz Windows kabulü SON görev bekliyor.

# 0.9.3 güncel not

Oturum isimleri: Claude Code custom-title / sessions-index özeti ve Codex session_index başlığı tamamlandı. Başlık yoksa mevcut iş adı veya proje/tarih kullanılır. Web ChatGPT geçmişi dahil değildir. Başlıklar kalıcı muhasebe/rapor verisine eklenmez. Çok büyük/okunamayan indekslerde ve Claude baş/son 64 KiB dışında kalan özel adlarda yedek görünüm kullanılır. Silinmiş kaynakların başlıkları arşivde saklanmaz. Temiz Windows kabulü SON görevdir.

# PLER — güncel kalan işler

**7 Kasım — 0.9.2 görünüm tercihleri:** Sütun sırası/görünürlüğü/genişliği, ajan/dönem/proje,
sıralama/veri kalitesi filtresi ve son bölüm normal masaüstü kapat/aç işleminde korunur.
Mevcut desktop-window.json dosyası sınırlı view alanıyla genişletildi; kayıt/veri biçimleri değişmedi.
Yeni boş profillerle gerçek masaüstü yeniden açılışı, dar pencere, sütun sıfırlama ve bozuk kayıt
kontrolleri geçti. Yerel aday reports/view-preferences-v1/delivery/PLER-0.9.2-windows-x64.zip.
Temiz Windows kabulü SON görev kalır; ilk kullanım ve ücretli/ücretsiz sınırı sonraki ayrı işlerdir.


**7 Kasım — 0.9.1 inceleme düzeltmeleri:** Sıfırlanan/eski kotanın güncel yüzde gibi görünmesi,
zaman grafiğinin ilk kısmi günü atlaması ve çoklu bağlamanın Escape/dışarı tıklamayla kapanması
düzeltildi. Altı yeni regresyon kontrolü ve çalışan UI'da saat ilerletme/bağlama doğrulaması var.
Yerel aday reports/review-fixes-v1/delivery/PLER-0.9.1-windows-x64.zip; public .31 değişmedi.
Temiz Windows kabulü en son görev olarak açık kalır.


**7 Kasım, görsel yükseltme:** Yerel aday **0.9.0**. Kullanımda zaman grafiği ve çalışma saatleri haritası,
kotada gösterge ve dolma tahmini, İşlerim'de kartlar ve çoklu oturum bağlama, bildirimler, ilk açılış turu;
masaüstü başlık çubuğu ve pencere/dil/tur hatırlama. [Rapor](../../reports/ui-upgrade-v1/REPORT.md). Public .31 değişmedi. Temiz Windows kabulü EN SON görevdir.

**7 Kasım, tasarım temeli:** Yerel aday **0.8.0**. Tek token kaynağından tek renkli arayüz, yaylı gezinme/filtre
göstergeleri, iskelet ve klavye paleti; her derlemede tasarım sözleşmesi. Son paket ve kontroller
[tasarım temeli raporunda](../../reports/design-foundation-v1/REPORT.md). Public .31 değişmedi. Temiz Windows kabulü EN SON görevdir.

**7 Kasım, UX ilk öncelik grubu:** Yerel aday **0.7.0**. Oturum kimliği, tek tam-veri sıralaması,
okunabilirlik, panel genişliği ve işe bağlama geçişi düzeltildi. 28 maddelik değerlendirmenin
uygulanan/kısmi/açık karşılıkları [UX takip kaydında](UX-REVIEW-2026-11-07.md). Sonraki öncelikler:
kalıcı görünüm tercihleri, çoklu oturum bağlama ve kalan hak odaklı kota ekranı. Public .31 değişmedi.


**7 Kasım:** Kullanıcı arayüzü sadeleştirme ve önerilen görsel bileşenleri kullanma yetkisi verdi.
Yerel yeni aday 0.4.0; genel bakış/oturum/iş/kota/veri alanları ayrıldı. Yeni UI bileşenleri yerel
paketlenir; motor ve kullanıcı veri biçimleri değişmez. Temiz Windows kabulü EN SON görev kalır.

**6 Kasım kullanıcı yönlendirmesi:** PLER kendi masaüstü penceresine geçirilir. Yerel aday
0.3.0; public .31 değiştirilmez. Bu teslimde **temiz Windows testi en son görevdir**;
geliştirme/paketleme ve geliştirici kontrolleri ardından çalıştırılır. Önceki .31 demo gözlemleri
masaüstü kabulü değildir. [Yeni görev sırası](DESKTOP.md). Diğer pilot/imza/lisans açıkları korunur.

2 Kasım 2026; güncel yayımlanan uygulama **0.2.31**. Windows x64 portable güncelleyici uygulandı, yalıtılmış veride sınandı ve mevcut herkese açık siteye yayımlandı. İlk kez 0.2.30 veya öncesinden bir elle geçiş gerekir. Canlı EN/TR sayfaları, ZIP/wheel baytları ve imzalı sürüm bilgisi gerçek paket runtime'ıyla [doğrulandı](../../reports/updater-v1/live-check.json). [Çalışma raporu](../../reports/updater-v1/REPORT.md), [yayın kaydı](../../reports/updater-v1/publication.json), [güncelleyici sözleşmesi](UPDATES.md). Parser `accounting-2026-11-01.1`, kullanım şeması 2, iş bileşeni 3 ve yedek 1 korunur. Önceki 0.2.30 yayını ve eski indirme dosyaları korunur; tarihli eski hazırlama raporları geçmiş kanıttır. Kişilere mesaj veya pilot daveti gönderilmedi. Bu kayıt aktif iş listesidir; [QUALITY.md](../QUALITY.md), [ACCOUNTING.md](../ACCOUNTING.md), [RELEASE.md](RELEASE.md), [ACCEPTANCE.md](ACCEPTANCE.md) ve [PILOT.md](PILOT.md) tamamlayıcı kayıtlardır.

Kullanıcının son satın alma değerlendirmesinden yedi başlık kayda alındı. Bunların dışında, önceki çalışmalardan kalan altı başlık aşağıda ayrı tutulur. Bunların hepsi kod hatası veya yayın engeli değildir: ürün geliştirmesi, doğrulama, kapsam kararı ve mevcut kayıttan çıkarılamayan bilgi ayrılır. Her başlığın tamamlanma durumu ayrıca yazılıdır; bir özelliğin uygulanması gerçek kullanıcı faydasının veya ödeme isteğinin kanıtı değildir.

**Son kullanıcı yönlendirmesi — 2 Kasım:** Profesyonel değerlendirmedeki yedi geri bildirimi önem sırasıyla sakla. Kullanıcı, uygulamada güncelleme bildirimi ve tek tıkla indirme/kurma/yeniden açma deneyimini istedi; otomatik güncellemeyi sona bırakan önceki erteleme bu başlık için kaldırıldı. R01, 0.2.31 Windows paketinde uygulanıp yayımlandı; bağımsız ortam kabulü R04 altında açık. 0.2.30'da güncelleyici yoktur. Diğer katılım/hesap/imza/lisans/ödeme kararları ve gerçek pilot daha sonra kullanıcıyla ele alınır. Yayıncı PLER, destek plersolutions1st@gmail.com; tekrar isim/adres seçimi istenmez. Kimseye e-posta, özel mesaj, duyuru veya davet gönderme yetkisi yok. Yaklaşık 3 dolar aylık fikir kesin fiyat veya talep kanıtı değildir. Mevcut pilot ölçütleri değiştirilmedi.

## 2 Kasım profesyonel değerlendirmesi — öncelikli takip

Aşağıdaki sıra dağıtım/veri kaybı riskini ve istenen güncelleme deneyimini önce alır. R kodları mevcut Y/E işlerinin takip kaydıdır; aynı işi ikinci kez saymaz. R03 en önemli ticari belirsizliktir; gerçek katılımcı gerektiren uygulaması kullanıcıyla daha sonra yürütülür. Yeni özellik uygulanması, gerçek kullanıcı değeri kanıtı sayılmaz.

| Sıra | Takip | Eksik ve somut kapanış | Mevcut iş |
|---|---|---|---|
| 1 | **R01 — Güvenli uygulama içi güncelleme ve geri dönüş** | **0.2.31'de uygulandı ve yayımlandı.** Sabit anahtarla imzalı sürüm/ZIP doğrulaması, özel yedek, ayrı sürüm hazırlığı, atomik seçim ve yeniden açılış var. Başarılı geçiş, açılış hatasında dönüş, başka örnek açıkken koruma, yarım seçim kurtarması ve kötü paket/uyumsuz biçim reddi sınandı. Fiziksel güç kesintisi ve temiz makine matrisi R04'te açık. [Kanıt](../../reports/updater-v1/REPORT.md). | Y07 + Y06 |
| 2 | **R02 — Kurulum güveni ve dağıtım koşulları** | İmzalı son paket, ürün lisansı, desteklenen ortamlar ve destek kanalı netleşir. Yayıncı/adres zaten seçildi; sertifika/lisans kararları kullanıcıyla yürütülür. | Y07 |
| 3 | **R03 — Tekrar kullanım ve ücretli fayda kanıtı** | Yeni iş bağlama/hedef/sonuç/takip akışlarının hangi kararı iyileştirdiği ve sonraki hafta tekrar kullanım gerekçesi gerçek kişilerle gözlenir. Mevcut pilot görevleri eski kitlerle aynı; yeni akışlar için [ek protokol](PILOT-WORKFLOWS.md) 3 Kasım’da hazırlandı; mevcut ölçütler sonuçlara göre değiştirilmez. Gerçek katılımcı, hafta sonrası tekrar kullanım ve ücretli fayda kanıtı açık. Talep veya ödeme isteği uydurulmaz; davet gönderilmez. | E06 + Y01/Y02/Y03 |
| 4 | **R04 — Son adayın bağımsız ortam kabulü** | Temiz standart Windows hesabı, güncel kaynak/kurulu paket CI, hedef tarayıcı/ekran okuyucu ve performans matrisi gerçek kanıtla tamamlanır. CI hesap engeli aşılmadan boş koşu tekrarlanmaz. Güncel kaynakta prizde 3×3 Windows ölçek kabulü geçti; bu bağımsız ortam kabulünün yerine geçmez. | Y07 + E04 |
| 5 | **R05 — Vaatleri desteklenen kapsamla eşleştirme** | Sitedeki genel “eksiksiz ve bir kez sayar” ifadesi desteklenen örüntülerle sınırlanır; yardımda ölçülmemiş “birkaç yüzde düşük” payı genel hata sınırı gibi sunulmaz. Token/fiyat/kota/tam hesap ayrımları örneklerle anlaşılır bulunur. 0.2.31 site sürüm notunda genel sayım vaadi kaldırıldı. 2 Kasım'da kaynak yardımının EN/TR metnindeki ölçülmemiş yüzde iddiası da kaldırıldı; kayda girmeyen kullanımın ve hata payının bilinmediği açıklandı. Yardım düzeltmesi sonraki pakete girecek, yayımlanan .31 dosyaları değiştirilmedi. [Beş kapsam/mahremiyet kartı](PILOT-WORKFLOWS.md) ve cevap anahtarı hazır; gerçek kullanıcı anlama kontrolü açık. | E01/E05 + Y05 |
| 6 | **R06 — Kullanıcının harcadığı çabayı azaltma** | İş oluşturma, çok oturum bulup bağlama, sonuç girme ve haftalık incelemenin adım/süre/terk nedenleri ölçülür. Saptanan sürtünme azaltılır; bütün oturumu işe bağlama ile tek görevin maliyeti birbirine dönüşmez. [Görev, süre/eylem/müdahale ve terk kayıt formu](PILOT-WORKFLOWS.md) hazır; gerçek ölçüm ve bulguya göre sürtünme düzeltmesi açık. | Y01/Y02/Y03 |
| 7 | **R07 — Tek güncel yayın durumu** | **3 Kasım’da normal build/yayın akışında tamamlandı.** İmza, süre, sekiz değişmez indirme, paket/wheel sürümü, gerçek veri biçimleri ve EN/TR sürüm/link/komut/boyut/hash kontrolü build içinde zorunlu. Son kaynak 14/14 testi ve kontrolü geçerek yayımlandı; 28 herkese açık dosya ve uygulama .31 aynı kaldı. [Kanıt](../../reports/release-gate-v1/REPORT.md). | Y07 + E05 |

### R01 uygulama kapsamı ve kabul ölçütleri

**Güncel sonuç:** Aşağıdaki maddeler ilk kabul hedeflerini korur. Format 1 portable yaklaşımı uygulandı; gerçekleşen geliştirici makinesi kanıtları ve henüz ölçülmeyen bağımsız ortam sınırları [raporda](../../reports/updater-v1/REPORT.md) ayrı yazılıdır. Otomatik kontrol yalnız açılışta açık kullanıcı seçimiyle yapılır; periyodik arka plan sorgusu eklenmedi.

**İstenen deneyim:** “Yeni sürüm var → İndir ve güncelle → Hazırlanıyor → Yeniden açıldı.” Erteleme ve açık hata/tekrar deneme seçeneği olur; bildirim güncellemenin yüklenmiş olduğu anlamına gelmez. İlk hedef Windows x64 portable pakettir; Python wheel, macOS ve Linux aynı yöntemle sessizce değiştirilmez. 0.2.30'un içinde güncelleyici yoktur; bu özelliği içeren ilk sürüme bir kez elle geçiş gerekir.

- **Sürümü öğrenme ve gizlilik:** Bilinen HTTPS yayın adresindeki küçük, sürümlü ve doğrulanabilir bildirim okunur. İlk aşamada kullanıcı başlatmalı kontrol; otomatik periyodik kontrol ayrıca açık seçimle etkinleşir. Ajan kaydı, konuşma, proje yolu, hesap anahtarı veya rapor gönderilmez. Güncelleme kontrolünün ağ isteği olduğu ve sunucunun normal bağlantı bilgilerini görebileceği açıklanır; çevrimdışı kullanım devam eder.
- **Paket güveni:** Kaynağı doğrulanmış sürüm bildirimi ve tüm paketin SHA-256 özeti kontrol edilir; yalnız aynı sunucudan alınan hash yayıncı kimliğini kanıtlamaz. İmzalı paket/bildirim ve güvenilen yayın anahtarı/yayıncı stratejisi belirlenir; özel anahtar kodda/pakette tutulmaz. Yanlış imza/hash/ürün/mimari/sürüm veya geri çekilmiş/eski bildirim reddedilir. Boyut/süre/yönlendirme ve arşiv açma sınırları ile yol geçişi/link korumaları gerekir; indirilen doğrulanmamış kod çalıştırılmaz.
- **Windows geçişi:** Mevcut yerel başlatıcı ve paket düzeni korunabilecek mi, yoksa kurulu MSIX/App Installer kanalı mı kullanılacak, uygulama öncesi kısa teknik denemeyle seçilir. Portable yolunda ayrı güncelleyici, indirmeyi ayrı hazırlık klasörüne alır; çalışan dosyalar yerinde yarım bırakılmaz. Kullanıcı süreci güvenli kapanmadan geçiş yapılmaz. Aynı kurulumdaki iki süreç, yazma izni ve boş alan önceden değerlendirilir; yönetici erişimi veya güvenlik uyarısını atlama varsayılmaz.
- **Veri ve geri dönüş:** Arşiv, tercihler, değerlendirmeler, kota örnekleri, iş/hedef/sonuç/takipler ve seçili veri klasörü korunur. Biçimi değiştirecek ilk yazmadan önce doğrulanmış, önceki sürümle uyumlu yedek gerekir. Yeni biçim 3'ü içeren sonradan alınmış yedek 0.2.29 için dönüş yolu değildir. Yeni uygulamanın sağlık/sürüm/veri açılışı sınanır; hata hâlinde eski çalışabilir paket korunur. Yeni kullanıcı düzenlemeleri eski yedekle sessizce ezilmez; veri biçimi uyumsuzsa eski uygulamayı o veriyle başlatmak yerine açık kurtarma yolu gerekir.
- **Anlaşılır arayüz:** Mevcut/yeni sürüm, indirme boyutu, değişiklikler, ilerleme, erteleme ve hata nedeni görülür. İş/sonuç/takip taslağı varken kapanışa zorlanmaz. EN/TR ve klavye/odak davranışı kabulün parçasıdır.
- **Kapanış kanıtı:** Yalıtılmış üretilmiş veride başarılı yükseltme ve yeniden açılış; indirme/açma/geçiş sırasında kesinti, bozuk/yanlış imzalı paket, uyumsuz veri, dolu disk, salt okunur konum, iki süreç ve Türkçe/boşluk içeren yol. Her başarısızlıkta mevcut çalışabilir sürüm ve özel veri korunur; otomatik geri dönüş yeni düzenlemeyi kaybettirmez. Ardından son paket temiz standart kullanıcı ortamında denenir. Prova başarılı olmadan gerçek kullanıcı verisine güncelleme kurulmaz.

**Teknik dayanak:** Windows, uygun biçimde paketlenen uygulamalar için [MSIX/App Installer güncelleme desteği](https://learn.microsoft.com/en-us/windows/msix/app-installer/auto-update-and-repair--overview) sunar; mevcut PLER ZIP'i bu paket biçiminde değildir. [Windows imza doğrulaması](https://learn.microsoft.com/en-us/windows/win32/seccrypto/example-c-program--verifying-the-signature-of-a-pe-file) paket güveni tasarımında incelenecek bir bileşendir. Seçilen uygulama portable format 1'dir: Windows CNG ile sabit anahtarlı sürüm imzası doğrulanır; MSIX'e geçilmedi. Windows yayıncı sertifikası edinilmiş değildir.

## Son değerlendirmeden eklenen yedi başlık

### Y01 — Oturumları yapılan işe bağlama

**Durum:** 0.2.26'da yerel kapsamla tamamlandı; gerçek kullanıcı değeri pilotta sınanmadı. Kanıt: [iş bağlama raporu](../../reports/work-items-v1/REPORT.md). Kaynak testleri Windows Python 3.9 717 geçti/13 atlandı, 3.12 721 çalıştı/0 hata, 3.14 730 çalıştı/0 hata; Linux WSL `/tmp` ve `/var` 730/730; Node 62/62; kurulu wheel ve portable pakette uydurma iş örnekleri, yedek/geri yükleme ve dışa aktarım sınırı doğrulandı. CI hesap ödeme/harcama limiti engeli nedeniyle çalıştırılmadı.

- Kullanıcı birkaç Claude/Codex oturumunu kendi seçtiği bir işe bağlayabilsin. Aynı oturum birkaç işle ilişkiliyse bu belirsizlik görülsün; tutarı kanıtsız oranlarla bölüştürme.
- Başlık/etiket gibi isteğe bağlı kullanıcı girdilerinin yerel saklama, silme, yedek ve dışa aktarma kapsamını açık tanımla. Ajan konuşmalarını toplamak gerekmesin.
- Ortak oturumlar birden fazla işte göründüğünde genel toplam ikinci kez artmasın. Kaynak taşınması veya oturum kimliğinin değişmesi, bağlantıyı sessizce başka oturuma taşımamalı.
- **Kapanış:** Uydurma çok ajanlı/çok oturumlu iş örneklerinde ilişkilendirme, kaldırma, örtüşme, yeniden açılış ve eksik kaynak davranışı doğrulanır; kullanıcı bu görünümden iş kapsamını açıklayabilir.

### Y02 — Gözlemden karara ve haftalık takibe geçiş

**Durum:** 1 Kasım'da kaynakta uygulandı; 0.2.30'da paketlendi ve yayımlandı; 0.2.31'de korunuyor. [Y02 çalışma kanıtı](../../reports/followups-v1/REPORT.md). Kaynak ve arayüz doğrulamaları üretilmiş veriler/simüle hafta ile yapıldı; gerçek bir haftalık kullanıcı kararı, fayda ve tekrar kullanım pilotta açık. **Bağımlılık:** Y01 ve kullanılabilir veri kapsamı.

- **Uygulanan:** Kullanıcı kota/yoğunlaşma/oturum örüntüsü/diğer gerekçesini, gözlemini ve deneyeceği değişikliği bir işe kaydeder. Kaynak okuma zamanı sabit başlangıçtır; önceki ve sonraki dönemler eşit, çakışmayan yedi gündür. Yalnızca tarihli ve uzlaştırılmış yanıtlar ölçülür. Yeni model/provider çağrısı veya zamanlanmış inceleme yok; bölüm açılınca yüklenir. Bir hafta sonrası güncel kaynak okuması ve açık kullanıcı incelemesi gerektirir.
- **Karşılaştırma sınırı:** Her aynı araç/proje/model grubunda iki dönemde de en az üç oturum, yeniden üretilebilen başlangıç ve kullanıcının benzer görev/koşul değerlendirmesi gerekir. Medyan, oturumların yanıt başına token ortalamalarından hesaplanır. Eksik kaynak, değişmiş geçmiş, ayrıştırıcı/model değişimi, dönem sınırını aşan yanıt veya bilinmeyen koşulda sayısal fark üretilmez; gerekçe gösterilir. Nedensellik, kalite, hesap kotası veya para tasarrufu iddiası yok.
- **Saklama/güvenlik:** İş başına 10, toplam 100, aynı işte bir açık takip; iş dosyası 2 MiB sınırı korunur. Özel takipler aynı atomik iş kaydında, normal JSON dışında ve özel yedekte tutulur. İptal başlangıcı korur; takip veya işi silme eski yedekleri silmez. Yeni bileşen biçimi 3 eski 1/2'yi düzenlemeden okur; gerçek yazma 3 kullanır. Eski uygulamalar 3 okuyamaz. İlk açılışa ölçüm eklenmez; ayrı yetkili okuma ve 16 KiB eylem yolu, içerik/kapsam revizyonları ve kaybolmayan taslaklar kullanılır.

- Mevcut kota, yoğunlaşma ve oturum karşılaştırmalarını temel alarak incelenecek durumun dayanağını ve sınırını birlikte sun.
- Kullanıcı bir çalışma değişikliği kaydedebilsin; sonraki dönemde gözlenen değişimi inceleyebilsin. Karşılaştırma aynı dönem/oturum tanımı, sabit gözlem zamanı ve uyumlu model/proje kapsamını kullansın.
- Aktif oturumun bütün toplamını takvim haftasının harcaması diye sunma. İş zorluğu veya veri kapsamı karşılaştırılamıyorsa sonucu açık bırak; nedensellik, otomatik tasarruf veya başarı iddiası üretme.
- **Kapanış:** Eksik/örtüşen dönem, değişen model ve küçük örnek senaryoları yanıltıcı karşılaştırma üretmez; pilotta kullanıcı bir gözlemden savunulabilir karar çıkarıp sonraki gözlemi yorumlayabilir.

### Y03 — İşin hedefi ve tamamlanma sonucunu ilişkilendirme

**Durum:** 1 Kasım'da kaynakta uygulandı; 0.2.30'da paketlendi ve yayımlandı; 0.2.31'de korunuyor. [Y03 çalışma kanıtı](../../reports/work-outcomes-v1/REPORT.md). Kullanıcının hedefi, kendi sonuç durumu ve kalan iş notu, mevcut oturum değerlendirmelerinden ayrı kaydedilir. Gerçek kullanıcı yararı/anlama pilotta açık. **Bağımlılık:** Y01.

- **Uygulanan:** Hedef ve sonuç notu ayrı ayrı en fazla 1.000 karakter; değerlendirilmedi/kısmen tamamlandı/tamamlandı/tamamlanmadı kullanıcı seçimi ve kayıt zamanı. İşin tamamına ait bu girdiler filtreler veya kayıp oturumlarla değişmez. Seçili oturumların son görünür test/derleme sonuçları ve zamansal Git gözlemleri ayrı gösterilir; otomatik tamamlanma/kalite puanı yok.
- **Saklama/güvenlik:** Eski iş biçimi 1 değişmeden okunur; Y03 aşaması biçim 2 ekledi; güncel gerçek düzenleme Y02 ile iş bileşeni biçimi 3 yazar. Uygulama sürümü, kullanım şeması ve parser değişmedi. Hedef/notlar normal JSON'dan çıkarılır, özel yedekte korunur. Çakışan düzenlemede taslak ve son kayıtlı sürüm ayrılır; açık inceleme ve sonraki kayıt olmadan üzerine yazılmaz. Filtre/dil değişimi taslağı kaybettirmez. Eski uygulamalar güncel biçim 3'ü okuyamayacağından geri dönüşte uyumlu yedek gerekir.

- İşin hedefi ile kullanıcının “tamamlandı/kısmen tamamlandı” sonucunu mevcut oturum değerlendirmelerinden ayrı tut.
- Mevcut test/derleme ve Git gözlemleri dayanak olarak birleşsin; bunlar kullanıcı sonucunun yerine geçmesin. İsteğe bağlı görev/PR referansı tasarlanabilir; harici hesap bağlama veya otomatik sorgulama bu kayıtla yetkilendirilmiş sayılmaz.
- **Kapanış:** Geçen test, kalan satır, kullanıcının yararlı değerlendirmesi ve işin tamamlanması birbirine dönüştürülmeden gösterilir; çelişen örneklerde otomatik kalite puanı üretilmez.

### Y04 — Gerçek ödeme, API fiyat karşılığı ve kotanın karar bağlamı

**Durum:** 0.2.27'deki plan kontrolünün güvenilirlik sınırları 1 Kasım'da kaynakta düzeltildi; 0.2.30'da paketlendi ve yayımlandı; 0.2.31'de korunuyor. [Y04 çalışma kanıtı](../../reports/plan-safety-v1/REPORT.md). Önceki [0.2.27 raporu](../../reports/plan-check-v1/REPORT.md) tarihsel uygulamayı anlatır; eski “API daha ucuz / küçük plan yeterdi” sonuçları artık üretilmez. Gerçek ödeme girişi yararlılığı ve profesyonel kullanıcı anlama doğrulaması pilotta açık.

- **Kapanan somut açıklar:** Fiyatlanamayan yanıta rağmen ucuzluk sonucu; seyrek veya eski ölçerden küçük plan sonucu; birden fazla kaynak grubunun tek abonelikle kıyaslanması; kaynak okuma/arşiv hatalarının plan kararından düşmesi. Tarihi/yanıt toplamı uzlaşmayan kullanım, plan değişimi ve çelişen ölçer de sınırlanır.
- **Yeni sınır:** Yalnız kayıtlı tutarın liste fiyatından düşük olduğu sayısal gözlem ile varsayılan plana bağlı gözlenen eşik karşılaştırması kalır. Ödenen tutar `null`, eksiksiz hesap geçmişi `false`; küçük plan yeterliliği veya geçişte tasarruf iddiası yok. En az 14 güne yayılan 14 ayrı UTC gününde örnek, en fazla iki günlük aralık ve güncellik gerekir; bunlar PLER'in gözlem kurallarıdır. Açık sayfada eskiyen eşik karşılaştırması kendiliğinden yeniden okuma mesajına döner.

- API karşılığı, tarih/fiyat kapsamı ve kota gözlemi zaten mevcut; bunları yokmuş gibi yeniden geliştirme.
- Kullanıcının gerçek ödeme bilgisini ayrıca eklemek yararlı mı, pilotta sına. Gerekirse yalnız açıkça seçilen veriye dayalı ayrı karşılaştırma tasarla; kayıtlardaki API karşılığını gerçek abonelik giderine çevirmeye çalışma.
- **Kapanış:** Kullanıcı örnekler üzerinde ödediği para, varsayımsal API karşılığı ve hesap kotasını ayırır. Sağlayıcı faturası veya tam hesap kanıtı olmadan “gerçek harcama/tasarruf/abonelik getirisi” sonucu çıkmaz.

### Y05 — Eksik kapsamı kullanılabilir karara ve giderme adımına bağlama

**Durum:** 1 Kasım'da kaynakta uygulandı ve yapay verilerle doğrulandı; 0.2.30'da paketlendi ve yayımlandı; 0.2.31'de korunuyor. Gerçek kullanıcıların açıklamaları doğru yorumlaması pilotta açık. [Y05 çalışma kanıtı](../../reports/coverage-v1/REPORT.md). **Bağlantı:** E01/E02 hesap motoru ve kaynak kapsamı çalışmalarıdır; bu başlık o sınırları açıklamayı geliştirir, motorun bütün belirsizliklerini çözmez.

- **Uygulanan:** 13 sabit neden için karar etkisi ve güvenli sonraki adım; seçili klasörlerin kaynak uyarıları ile ana filtrelere uyan oturum/fiyat sınırlarının ayrımı. Mevcut kalite nedenleri ve etkilenen oturum filtresi korunur. Türkçe/İngilizce çevrimdışı kurtarma yardımı eklendi; erişim hatalı boş okuma artık “kayıt bulunamadı” başlığı kullanmaz. Codex kota eksikliği Claude durum satırına yönlendirilmez.
- **Sınır:** Hiç okunmadan silinen kaydın varlığı/sayısı tespit edilemez; geri getirme sözü verilmez. Önbelleği yeniden kurma, arşivi silme veya tekrar okuma kayıp asılları onaramaz. Y04 öneri kuralları bu çalışmada değiştirilmedi; açıklamalar mevcut önerinin güvenli olduğunun kanıtı değildir.

- Mevcut kalite işaretleri, etkilenen oturumlar ve kaynak uyarıları korunur. Hangi kararın mevcut kapsamla yapılabileceğini, hangi karşılaştırmanın beklemesi gerektiğini anlaşılır kıl.
- Yeniden okunabilir/geçici hata ile artık geri getirilemeyen kaynağı ayır. Güvenli yeniden okuma veya yalnız yeniden kurulabilir önbelleği sıfırlama yönlendirmesi, arşivi yanlışlıkla sildirmesin.
- **Kapanış:** Geçici okuma hatası, durmuş WSL, eski parser arşivi ve hiç okunmadan silinmiş geçmiş örneklerinde farklı ve doğru sonraki adım verilir; ham yollar/özel içerik paylaşılan rapora eklenmez.

### Y06 — Doğrulanmış yedekleme ve geri yükleme

**Durum:** 0.2.25'te tamamlandı; aşağıdaki yeni klasör/aynı bilgisayar ve kaynak kökleri kapsamıyla kaynak, kurulu paket, portable ve arayüz kanıtı var. Y07'nin geniş dağıtım ve fiziksel platform kabulü bundan ayrı ve açık kalır.

- **Uygulanan kapsam:** `pler backup create`, `pler backup check` ve `pler backup restore ... --to YENİ_KLASÖR`. Yalnız PLER arşivi, saklama tercihi, oturum değerlendirmeleri ve kota örnekleri sürümlü, bütünlüğü doğrulanan yerel yedeğe alınır; yeniden kurulabilir önbellekler, ajan ayarları ve erişim anahtarları alınmaz.
- Arayüzde özel yedek indirme ve seçilen dosyayı denetleme var. Geri yükleme komut satırından yalnız yeni, henüz var olmayan yerel klasöre yapılır; mevcut veri klasörü üzerine yazılmaz. Arayüzden tek tıkla geri yükleme bu adayın kapsamı değildir.
- Geri yüklenen klasör her açılışta açıkça `pler --data-dir KLASÖR` ile seçilir; çalışan sayfa veya sonraki varsayılan açılış kendiliğinden değiştirilmez. Aynı bilgisayar ve özgün seçili kaynak kökleri için kurtarma sağlanır; başka bilgisayara taşıma kaynak yollarını yeniden eşleştirmez.
- Özgün okuyucu anahtarları, kota zamanları ve saklama açık/kapalı tercihi korunur. Eski okuyucunun arşivi yeni okuyucuyla doğrulanmış gibi yükseltilmez; eski kota örneği yeni ölçüm gibi sunulmaz. Yedek şifreli veya anonim değildir; özel yollar/kimlikler taşıyabilir. Sağlama toplamı kim tarafından üretildiğini kanıtlamaz.
- **Son aday doğrulaması:** Linux WSL 681/681; Node 47/47. Son kurulu wheel, Python 3.12'de 672 test, 0 hata, 5 atlama; 51 kaynak dosyası birebir. Modül çıkış kodu düzeltmesinden önce tam kaynak koşuları Python 3.9'da 667 geçti/13 atlandı, Windows Python 3.14'te 680 çalıştı/0 hata/4 atlandı. Son düzeltmeden sonra bu iki ortamda 22 CLI/yardım kontrolü ayrıca hatasız geçti; bunu yeni bir tam Windows takım koşusu diye sunma.
- **Kurtarma kanıtı:** Son wheel ve PATH'te Python olmadan paketlenmiş portable çalışma ortamında 2 arşiv kaynağı, 1 değerlendirme ve 1 kota örneği; kaynaklar silindikten sonra geri yüklemede toplamlar, tamlık işaretleri, değerlendirme ve zamanlar aynı. Hasarlı yedek ve var olan hedef reddedildi; mevcut veri korundu. Bozuk/uyumsuz/yarım yedek ve yayımlama öncesi kesinti senaryoları regresyonlarla sınandı.
- **Arayüz kanıtı:** Son kurulu adayda gerçek yedek indirmesi dosyaya kaydedildi ve indirilen dosya denetlendi: yalnız bu arayüz uydurma örneğinde 2 kaynak/0 değerlendirme/0 kota; ayrı güvenilir örnek 2/1/1 verdi. EN/TR, özel veri uyarısı ve mevcut verinin korunması doğrulandı. Kendi test süreci çıkış 0 ile kapandı, test sekmesi kapatıldı, geçici erişim dosyası silindi. Ayrıntılar [çalışma raporunda](../../reports/backup-v1/REPORT.md).
- **Kapanış sonucu:** Kaynakları silinmiş uydurma geçmiş, boş yalıtılmış yeni klasörde aynı sayım/kalite bilgileriyle kurtarıldı. Ajan kayıtları değişmedi. Bu yerel kurtarma kanıtı, başka bilgisayara yol eşleme, gerçek profesyonel pilot, temiz makine, imza veya bütün tarayıcıların kabulü değildir.

### Y07 — Dağıtım, güncelleme ve destek güvencesi

**Durum:** Kısmen doğrulandı; aşağıdaki kabul ve kararlar açık. **Öncelik:** Geniş dağıtımdan önce. Ayrıntı: [RELEASE.md](RELEASE.md), [ACCEPTANCE.md](ACCEPTANCE.md).

**2 Kasım güncelleme talebi:** Uygulama içi bildirim/indirme/kurma/yeniden açma R01 kapsamıyla önceliklendirildi. Önceki “otomatik güncelleme sona” yönlendirmesi bu iş için geçerli değildir. Y07'nin aşağıdaki veri geçişi ve imza/dağıtım kabulü R01'in de ön koşullarıdır; bu özellik 0.2.31'de yayımlandı, 0.2.30'da yoktur.

**0.2.29 yerel ilk kullanım kanıtı:** Canlı siteden tarayıcıyla indirilen .28 paketi ve son .29 ZIP, manifest bütünlüğüyle denetlendi. .29'un yerleşik runtime/native başlatıcısı PATH'te Python yokken, Türkçe/boşluk/`&` içeren yolda çalıştı. Demo, boş kaynak, dolu port, iki bağımsız örnek, EN/TR çevrimdışı yardım, iki ajanın oturumlarını tek işe bağlama ve temiz kapanış doğrulandı. Son wheel'in 53 dosyası kaynakla birebir; kurulu pakette 21 yardım/API kontrolü hatasız, Node 70/70. Kaynak Python takımı 731 test/5 atlama/0 hata verdi; son metin düzeltmeleri ayrıca kurulu paket/arayüzde kontrol edildi. Bu geliştirici bilgisayarındaki yalıtılmış provadır; yeni Windows hesabı, imza, fiziksel macOS, tam CI veya gerçek kullanıcı kabulü değildir. [Ayrıntılar](../../reports/first-use-v1/REPORT.md).

- [ ] **Güncel platform CI:** 0.2.25 için CI çalıştırılmadı. Önceki 0.2.24 `9891966` kaynağının [41056121858](https://github.com/OguzayYildiz/pler/actions/runs/41056121858) koşusu hesap ödeme/harcama limiti engeli nedeniyle 12 işte sıfır adım çalıştırmıştı; bu yeni adayın geçtiği veya testte kaldığı anlamına gelmez. Hesap engeli giderilince yayınlanacak tam adayın kaynak/kurulu paket/isteğe bağlı çözücü matrisi başarıyla çalışmalı. Hesap ayarları bu görevde değiştirilmez; engel sürerken boş koşu tekrarlanmaz.
- [ ] **Temiz makine:** Geliştirici checkout'u ve Python olmayan standart kullanıcıyla son paket; boş ve ASCII dışı yol, port çakışması, boş kayıt, kurulum/kaldırma, çevrimdışı yardım ve doğru erişim bağlantısı kabulü.
- [x] **Geliştirici makinesinde güncelleme ve geri dönüş:** 0.2.31→yalnız test için imzalı 0.2.32 geçişi; başarısız açılışta .31'e dönüş, iki örnek, Türkçe/boşluk/`&` yolu ve yarım seçim kurtarması. Kalıcı özel veriler değişmedi; yeni veri eski yedekle ezilmedi. Gerçek .31 paketi canlı imzalı kaynağı doğruladı. [Rapor](../../reports/updater-v1/REPORT.md). Temiz makine/güç kesintisi kabulü yukarıdaki açık satırlarda kalır.
- [ ] **Fiziksel tarayıcı/erişilebilirlik:** Seçilecek Windows/macOS/Linux tarayıcılarında indirme ve yeniden bağlanma; klavye, odak, gerçek dar dokunmatik cihaz, %200/%400 yakınlaştırma, yüksek karşıtlık ve NVDA/VoiceOver. Son .25 yedek indirme/denetleme ve önceki .24 demo kontrolü tam matris yerine geçmez.
- [ ] **Yayın kararları:** Desteklenen platform/sürüm listesi, ürün lisansı ve dağıtım hakları, kamuya açık ad/paket kimliği, yayıncı, destek/güvenlik kanalı, sürüm ve fiyatlandırma/lisans modeli. Abonelik veya tek seferlik ödeme kararı verilmeden ödeme altyapısı zorunlu geliştirme sayılmaz.
- [ ] **İmza ve dağıtım:** Onaylanan yayıncıyla son paket baytlarını imzalama/doğrulama, artifact hash'i, yayın kanalı ve geri çekme yolu; güvenlik uyarısını atlatma test yöntemi değildir.
- **Kapanış:** Seçilen hedefler için her satırda gerçek ortam, sürüm/hash, beklenen/görülen sonuç ve kanıt vardır. Kit hazırlamak, eski CI'ın geçmesi veya geliştirici bilgisayarındaki kurulum bu kabulün tamamlandığı anlamına gelmez.

## Bu yedi başlık dışında önceki çalışmalardan kalan altı iş

### E01 — Zor geçmişlerin sayım uzlaştırması

**Durum:** Sınırları görünür, genel çözüm açık. 2 Kasım'da ilk desteklenen örüntü eklendi: sıkıştırılmış ve çatallanmış Codex iş parçacıkları (ACCOUNTING.md "Compacted and forked Codex threads"). Bu bilgisayarda uzlaşmamış Codex oturumu 9 (%98,8 token) → 3 (%0,19), toplamlar aynı; sentetik regresyonlar `test_history_boundaries.py`. Aynı gün ikinci tur: birden fazla klasörde çalışan oturumlar tarihli kullanımda (Claude %2,4 → %100), canlı dosyanın tamamen kapsadığı eski sürüm arşiv kopyaları sayılmıyor (Codex %71'lik uyarı kalktı; tarihli Codex %28 → %99). Açık ve dürüstçe bilinmeyen: Codex token'larının %0,9'u yanıt başına tarihi olmayan eski birikimli kayıtlarda, %0,2'si çelişen sayaçlı 3 oturumda. **Tür:** Hesap motoru/doğruluk.

Keyfi fork/ebeveyn–çocuk/compaction geçmişleri, birikimli sayaçlar ve sabit kimliği olmayan olaylar her durumda tam uzlaştırılmış değil. Mevcut dar uzlaştırmaları ve alt ajan düzeltmelerini koru. Desteklenecek kanıtlanabilir örüntüleri bağımsız beklenen toplamlarla genişlet; dosya/olay sırası değişiminde sonucu ve tamlık işaretlerini karşılaştır. Kanıtı olmayan geçmiş bilinmiyor/eksik kalmalı; bütün geçmişlerin eksiksiz olacağı sözü verilmemeli. **Kapanış:** Her desteklenen örüntü için açık sözleşme ve regresyon; desteklenmeyen durumda sessiz çift sayım veya kesin toplam iddiası yok. Y05 yalnız bu sonucu anlaşılır kılar, motoru çözmez.

### E02 — Hesap değişimi ve çoklu hesap kapsamı

**Durum:** 2 Kasım'da hesap kimliği okunmadan kapanış ölçütüne getirildi; destek tablosu ACCOUNTING.md "Account scope without account identity (E02)". Birden fazla kaynak grubu: kota gizli (önceden vardı). Aynı kaynakta kayıtlı plan değişimi (Codex her örnekte planı yazar): tahmin ve plan kontrolü sınır sayımları son değişimden başlar, değişim zamanı sayfa/terminal/JSON'da. Eşzamanlı iki hesap: yalnız okumalar çelişirse yakalanır. Aynı planda başka hesaba geçiş: kayıtlardan anlaşılamaz, tek hesap iddiası da yok. Sentetik regresyonlar `test_account_scope.py`; bu bilgisayarda plan değişimi yok, çıktılar aynı. Hesap kimliği/harici bağlantı ayrı kullanıcı kararı. **Tür:** Veri kapsamı/kapsam kararı.

Uyumlu kota örnekleri tek hesabı kanıtlamaz. Hesap kimliği toplamadan doğrulanabilecek kapsamı ve ayrıştırma yöntemini belirle; doğrulanamayan metreleri tek hesap gibi tahmin etme. Yeni hesap verisi veya harici hesap bağlantısı ayrı seçim ve veri kapsamı gerektirir. **Kapanış:** Aynı klasörde hesap değişimi ve birden fazla kaynak senaryolarının hangi kısmının desteklendiği açık; belirsiz örnekler güvenilir tek hesap/fatura sonucuna dönüşmez. Kanıt yokluğu yalnız kodla giderilmiş sayılmaz.

### E03 — Claude masaüstü kota kapsamı

**Durum:** Terminal Claude Code durum satırı destekli; masaüstünden kota geldiği doğrulanmadı. **Tür:** Destek/kapsam kararı.

Onaylanmış, güvenilir masaüstü veri kaynağıyla gerçek destek doğrulanmalı veya ilgili sürüm için açıkça destek dışında bırakılmalı. Terminal kurulumunu tekrarlatmak masaüstü kotasını sağladığı anlamına gelmez. **Kapanış:** Kanıtlı destek veya ürün kapsamına işlenmiş açık destek dışı kararı; sıfır veya anlık sağlayıcı sorgusu izlenimi yok. Bu kayda eklemek gerçek özel kaynağı okumaya izin değildir.

### E04 — Güncel adayın ölçek ve performans kabulü

**Durum:** 3 Kasım’da güncel kaynak için prizde üç Python sürümü × üç koşu **9/9** geçti; önceden belirlenmiş hız/bellek/iptal sınırları değiştirilmedi. E04 tanımlı geliştirici Windows iş yükü kapsamında tamamlandı. [Güncel kanıt](../../reports/scale-refresh-v1/REPORT.md), [ham kabul](../../reports/scale-refresh-v1/acceptance.json). Önceki kaynak/pil sonuçları aşağıda tarihsel dayanak olarak korunur. Bağımsız ortam ve farklı iş yükleri R04/Y07 altında açık. **Tür:** Ölçüm ve kabul.

- **Neden ve düzeltme (2 Kasım, Claude):** Makine pilde (BatteryStatus 1, işlemci 1,88/3,2 GHz). E05'in değiştirmediği Git dal kodu ve modül yükleme de aynı oranda (~2,3 kat) yavaştı ([pil, eski kod](../../reports/scale-v1/audit-native-1/result.json)). Profil, değişmeyen yenilemede üç tekrar iş gösterdi: aynı dal uçları için her seferinde 1.073 commit nesnesini yeniden okuyan Git yürüyüşü, her istekte yeniden doğrulanan iş dosyası ve yanıt başına ayrı fonksiyon çağrısıyla yapılan tarihli kullanım/plan toplamları. Git cevabı aynı uçlar ve hedefler için yalnız bütün hedefler biliniyorsa saklanır; iş dosyası aynı baytlarda bir kez doğrulanır ve her okuma özel kopya alır; toplamlar satır içi yapılır ve zaten UTC olan zaman dönüştürülmez. Aynı pil koşullarında ([yeni kod](../../reports/scale-v1/audit-fast-1/result.json)): değişmeyen yenileme 5,53 → 2,38 sn, değişim aşamaları 10,5–10,9 → 7,3–8,1 sn, ilk Git toplamı 5,13 → 3,61 sn, HTTP 1,3–1,5 → 0,9–1,0 sn, ilk okuma 19,4 → 16,9 sn; önceden belirlenmiş bütün eşikler geçti. Sabit saatle tam sayfa görünümü eski/yeni kodda, ölçek verisinde ve bu bilgisayarın gerçek kayıtlarında, okuma zamanı ve arşiv bayt sayısı dışında aynı.
- **Önceki karşı örnek:** Güncel 3.14 native tek koşusunda ilk JSON 20,02 sn; değişmeyen yenileme 5,64 sn > 3 sn, ilk Git toplamı 5,52 sn > 5 sn, üç HTTP ölçümü 2,05–2,08 sn > 2 sn. Sayım/tarihli kanıt önbelleksiz okumayla eşit, arşiv ve fixture bütünlüğü korundu; tepe çalışma kümesi 212,57 MiB. Bu, hız kabulü veya değişikliğin nedeninin kanıtı değildir. Önce kontrollü tekrar/profil ile neden ayrılır; aynı eşikler korunur, sayım ve kapsam azaltılarak hedef geçirilmez.

- **Doğrulanan:** Sonuç görülmeden sabitlenen eşiklerle 102,61 MiB açılmış veri, 385 dosya/oturum, 36.992 yanıt, 16 Git deposu/1.024 commit, 200 iş/20.000 bağlantı/100 takip. Üçer koşuda Windows Python 3.14 native, 3.12 ve 3.9 saf-Python yolları bütün eşikleri karşıladı. İlk kullanılabilir JSON raporu ortancası 8,85 / 20,09 / 27,50 sn; değişmeyen yenileme 2,32 / 2,23 / 2,62 sn. Bütün yeni süreç ayrıca ölçüldü; Git/arşiv/rapor maliyeti dahil, görsel ilk boyama dahil değil. Tepe süreç çalışma kümesi en fazla 239,08 MiB.
- **Doğruluk/kapanış kanıtı:** Bağımsız önbelleksiz referansla metadata, kullanım, tarihli yanıt ve kalite eşitliği; büyüyen dosyada bütün eski öneğin doğrulanması ve önceki bölüm değişiminde yeniden okuma. Dokuz ek tüm-kaynak-kaybı koşusunda son saklanan 386 oturum aynı sayılarla ve arşiv olarak korundu. Üç çözücüde gerçek ilerlemeden sonra iptal yarım snapshot yayımlamadı. Kaynak/fixture/plan hash'leri, ham koşular ve yeniden çalıştırılabilir araçlar raporda. Python 3.12 kaynak takımı 786/5-atlama/0-hata, 3.14 795/4-atlama/0-hata. Gerçek ekranda sınırlı liste çizimi ve 390 px görünüm doğrulandı.
- **Açık sınır:** Bir geliştirici Windows makinesi ve tanımlı corpus. İşletim sistemi soğuk disk önbelleği, en büyük izinli tek dosya, başka iş yükleri veya fiziksel macOS/Linux/WSL ölçümü yapılmadı. Y07 temiz makine/platform kabulü ve bu kapsamlar açık. Bu tur ürün hızlandırması veya yeni paket yok; önceki geliştirmeler için tekrar üretilebilir kabul kanıtı eklendi.

İlk okuma, değişmeyen yenileme, eklenen kaynak, tam önek doğrulaması, Git ve arşiv maliyetini bütün hat üzerinde ölç. Büyük uydurma geçmiş, eski Python/fallback çözücü ve desteklenen çalışma ortamları için süre/bellek/iptal kanıtı tut; kabul eşiklerini ölçüm sonuçlarını görmeden seç. Eski parser-only oranını toplam açılış süresi diye sunma. Yeni gerçek veri ölçümü ancak uygun kullanıcı yetkisiyle yapılır. **Kapanış:** Tam aday ve fixture hash'leriyle tekrar üretilebilir ölçüm, önceden belirlenen hedefler ve sayım/kalite eşitliği; karşılanmayan ortam ya iyileştirilir ya belgelenmiş kapsam kararı alır.

### E05 — Kayıt biçimi ve fiyat tablosu uyumluluğunun bakımı

**Durum:** 1–2 Kasım'da ilk bakım/yayın kontrolü kaynakta tamamlandı; sonraki sürümlerde tekrarlanır. Yeni paket/yayın yok. [E05 çalışma kanıtı](../../reports/compatibility-v1/REPORT.md), [bakım sözleşmesi](COMPATIBILITY.md) ve [sürümlü inceleme kaydı](compatibility.json). **Tür:** Uyumluluk ve sürümleme.

- **Uygulanan:** 22 uydurma kayıt örneğinin bağımsız sayım/fiyat beklentileri ilk okuma, önbellek ve doğrulanmış arşivde sınanır. 26 model kimliği, fiyat/kota varsayımları, resmi kaynak/tarih, okuyucu kodu ve örnek sağlama toplamı çevrimdışı yayın kontrolüne bağlı. Yeni model/fiyat, incelenmemiş yorum değişimi, 30 günden eski fiyat veya 90 günden eski okuyucu incelemesi yayın kontrolünü durdurur. Bu süreler PLER bakım politikasıdır; aradaki fiyatın değişmediğinin kanıtı değildir. CI tüm arayüz test dosyalarını keşfeder; hesap engelli CI tetiklenmedi.
- **Kapanan kusurlar:** Codex'in saklama süresi bilinmeyen GPT-6 önbellek yazıları normal girdi fiyatına çevrilmez; incelenmemiş tarihli Codex kimlikleri fiyat devralmaz. Claude'un bozuk süre/hız/bölge/servis bilgisi geçerli sayıma zarar vermeden fiyatı belirsiz bırakır; aynı kullanımın kopyaları sıra bağımsız biçimde fiyat üzerinde anlaşmalıdır. Ekran/yardım EN/TR açıklamaları fiyatlanamayanı ücretsiz göstermez.
- **Geçiş sınırı:** Parser `accounting-2026-11-01.1`; değişen okuyucu anahtarları ilgili önbelleği yeniden kurar. Eski arşiv kanıtı yeni okuyucuda doğrulanmış sayılmaz; eski dışa aktarımlar sürüm bilgisini taşır, farklı parser başlangıçları haftalık karşılaştırmada çözümsüz kalır. Şema 2, iş bileşeni 3 ve yedek zarfı değişmedi. Gerçek istemci sürümlerinin bütün olaylarına veya tüm hesap geçmişine destek sözü yok.

Claude/Codex alan/olay–örnek eşlemesi ve resmi fiyat kaydı her yayında yeniden incelenir. Kaynak değişimi otomatik dış ağ sorgusu veya model çağrısı gerektirmez. **Kapanış:** İlk kontrol/regresyon/versiyonlama kapsamı tamamlandı; sürekli bakım ve yeni kayıt örüntülerinin incelenmesi devam eder.

### E06 — Gerçek profesyonel pilot ve tekrar kullanım

**Durum:** Kullanıcı 31 Ekim'de küçük ücretsiz yayın ve 10 kişilik pilotu sıraya aldı; yayın, lisans ve davet kararları kullanıcıdadır. 0.2.28 kiti ([yayın paketi raporu](../../reports/release-kit-v1/REPORT.md)) iki kurulum yolunda doğrulandı; görevler ve ölçütler değişmedi, gerçek katılımcı sonucu yok. **Tür:** Kullanıcı kanıtı. **Öncelik:** Kullanıcı ürünü hazır bulduktan sonra değer varsayımlarını sınama.

[PILOT.md](PILOT.md) ölçütleri değişmeden en az beş profesyonelle mevcut yönteme karşı görevleri karşılaştır; başarısız/yanlış yorumlanan durumları da kaydet. Sonraki hafta somut tekrar kullanım gerekçesini gözle. Kullanıcı ürünü hazır bulduğunu belirtmeden reklam ve katılımcı arama başlatılmaz. Katılımcı bulma, onay ve yürütme daha sonra kullanıcıyla koordine edilir; bu belge kişilere mesaj gönderme yetkisi değildir. **Kapanış:** Önceden belirlenen kritik anlama, bağımsız görev ve tekrar kullanım hedefleri gerçek sonuçlarla değerlendirilir. Başarısız sonuç da rapordur; ölçütler sonuç görüldükten sonra değiştirilmez. Y01–Y05'in tamamını önce yapmak pilot için otomatik ön koşul değildir; kullanıcı yönlendirmesi ve gerekli yayın/mahremiyet kabulü korunur.

## Tamamlanmış işleri yeniden açmama ve bilgi sınırları

- .24'te kaybolan okuma uyarısı, başka dosyaya eski önbellek isabeti, orta bölüm değişimi+ekleme ve yeniden açma yarışı, çalışmayan test kipleri, Git dolaşım sınırı ve sınırlı değerlendirme okuması düzeltildi. Kaynak/paket kanıtı [raporda](../../reports/integrity-v1/REPORT.md); bunlar yeni iş listesi değildir.
- Yerel API erişim anahtarı, ağ yolu korumaları, Python'suz Windows adayı, proje adı gizleme, çevrimdışı yardım, arşiv saklama, kullanıcı değerlendirmesi, test/Git sinyalleri ve API karşılığı zaten vardır. Eksik kabul veya kapsamı, özelliğin yokluğu diye yazma.
- PLER'in hiç okumadan silinen geçmişi geri getirmek; mevcut kayıttan gerçek faturayı, insanın kesintisiz çalışma süresini, kodun doğruluğunu veya nedensel tasarrufu kesin çıkarmak vaat edilmez. Bunlar yeni bir düğmeyle kapatılacak işler değildir.
- Ekip sunucusu, SSO, çalışan performans puanı, yeni ajanlar ve çoklu cihaz eşitleme bu bireysel yerel ürün için zorunlu iş olarak eklenmedi. Ayrı hedef kullanıcı/kapsam kararı gerekir.

## Önerilen yürütme sırası ve kapanış disiplini

1. Y06 belirtilen yerel kurtarma kapsamıyla, Y01 iş bağlama 0.2.26'da yerel kapsamla tamamlandı. Bu kayıt tek başına yeni özellik uygulama yetkisi değildir.
2. R01 uygulandı/yayımlandı; R07 zorunlu yayın kontrolü ve E04 güncel prizde Windows ölçek kabulü tamamlandı. R02/R04'ün bağımsız ortam/imza/CI kabulü ve R05'in gerçek anlama kontrolü açık. İmza/lisans/hesap ve gerçek katılımcı kararları kullanıcıyla ayrıca ele alınır; otomatik güncelleme artık sona ertelenmez. R03/R05/R06 için ek görevler, kapsam kartları ve ölçüm formu hazır; gerçek gözlem ve bulguya göre düzeltme bekliyor. Asıl pilot ölçütleri ve davet yasağı korunur.
3. Y05 → Y04 → Y03 → Y02 0.2.30'da yayımlandı; gerçek kullanıcı yararı/anlama pilotta açık. E05'in ilk bakım/yayın kontrolü tamamlandı. E04'ün güncel prizde 3×3 tekrarı 9/9 geçti. E01'in dar örüntüleri ve E02'nin kimliksiz kapsamı korunur; kalan E01 örüntüleri somut karşı örneklerle incelenir. Kanıtlanamayan kapsam kesin sonuca dönüşmez. Yeni uygulama paketi çıkarılmadı. Site yayın hazırlığı güçlendirildi; 28 herkese açık dosyanın baytları aynı kaldı.
4. Kullanıcının ürünü hazır bulmasına kadar reklam/katılımcı arama başlatma. E06 pilotu ancak kullanıcı bu aşamayı başlatınca ve gerekli kabul koşulları sağlanınca yürütülür; ölçütleri korunur ve sonraki gerçek kanıt önceliği değiştirebilir.
5. E01–E05 doğruluk, hesap/kota kapsamı, performans ve bakım işleri somut karşı örnek ve açık destek kararıyla sürdürülür; gerçek doğruluk hatası görülürse özelliklerden önce alınır.

Her kapanışta: iş kimliği, somut başarısızlık veya kabul görevi, uygulama commit/sürümü, kullanılan uydurma/izinli veri kapsamı, gözlenen sonuç ve kanıt bağlantısı kaydedilir. Yeni istek olmadan pilot ölçütleri veya mahremiyet sınırları değiştirilmez. Yalnız belge değişikliğinde uygulama sürümü/paket değiştirilmez ve hesap engelli CI yeniden çalıştırılmaz.
