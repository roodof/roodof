# PLER — güncel kalan işler

1 Kasım 2026; güncel uygulama 0.2.29 (ilk kullanım, çevrimdışı yardım/destek ve Windows paket yönlendirmeleri). 0.2.28 kota uyarısını, 0.2.27 plan kontrolünü, 0.2.26 Y01 iş bağlamayı ekledi. Son yayımlanan paket .29'dur; Y02/Y03/Y04/Y05/E05 değişiklikleri yerel kaynakta, yeni paket/yayın yok. E05 ile kaynak parser'ı `accounting-2026-11-01.1` oldu; kullanım şeması 2, iş bileşeni 3. Bu kayıt aktif iş listesidir. [QUALITY.md](../QUALITY.md) tarihsel bulguları ve kapanan kusurların kanıtlarını korur; eski bir notta “açık” yazması, sonraki sürümde kapanmış kusuru yeniden açmaz. [İlk kullanım/paket kanıtı](../../reports/first-use-v1/REPORT.md), [yedekleme çalışması](../../reports/backup-v1/REPORT.md), [sayım sözleşmesi](../ACCOUNTING.md), [yayın koşulları](RELEASE.md), [kabul adımları](ACCEPTANCE.md) ve [pilot protokolü](PILOT.md) dayanaklardır.

Kullanıcının son satın alma değerlendirmesinden yedi başlık kayda alındı. Bunların dışında, önceki çalışmalardan kalan altı başlık aşağıda ayrı tutulur. Bunların hepsi kod hatası veya yayın engeli değildir: ürün geliştirmesi, doğrulama, kapsam kararı ve mevcut kayıttan çıkarılamayan bilgi ayrılır. Her başlığın tamamlanma durumu ayrıca yazılıdır; bir özelliğin uygulanması gerçek kullanıcı faydasının veya ödeme isteğinin kanıtı değildir.

**Son kullanıcı yönlendirmesi — 1 Kasım:** Kullanıcıya katılım/hesap/karar gerektiren işleri sona bırak; yapılabilen teknik yayın ve ilk kullanım işlerini tamamla. Site daha önce kullanıcı yetkisiyle herkese açıldı; yayıncı adı PLER, destek plersolutions1st@gmail.com. Otomatik güncelleme kullanıcı tarafından sonraki işe ertelendi; bu tur uygulanmadı. Gerçek katılımcı, hesap erişimi, imza/lisans ve ödeme kararları sona kalır; kimseye mesaj gönderme yetkisi yok. Yaklaşık 3 dolar aylık fikir kesin fiyat veya talep kanıtı değildir. Pilotun önceden belirlenmiş ölçütleri değiştirilmedi.

## Son değerlendirmeden eklenen yedi başlık

### Y01 — Oturumları yapılan işe bağlama

**Durum:** 0.2.26'da yerel kapsamla tamamlandı; gerçek kullanıcı değeri pilotta sınanmadı. Kanıt: [iş bağlama raporu](../../reports/work-items-v1/REPORT.md). Kaynak testleri Windows Python 3.9 717 geçti/13 atlandı, 3.12 721 çalıştı/0 hata, 3.14 730 çalıştı/0 hata; Linux WSL `/tmp` ve `/var` 730/730; Node 62/62; kurulu wheel ve portable pakette uydurma iş örnekleri, yedek/geri yükleme ve dışa aktarım sınırı doğrulandı. CI hesap ödeme/harcama limiti engeli nedeniyle çalıştırılmadı.

- Kullanıcı birkaç Claude/Codex oturumunu kendi seçtiği bir işe bağlayabilsin. Aynı oturum birkaç işle ilişkiliyse bu belirsizlik görülsün; tutarı kanıtsız oranlarla bölüştürme.
- Başlık/etiket gibi isteğe bağlı kullanıcı girdilerinin yerel saklama, silme, yedek ve dışa aktarma kapsamını açık tanımla. Ajan konuşmalarını toplamak gerekmesin.
- Ortak oturumlar birden fazla işte göründüğünde genel toplam ikinci kez artmasın. Kaynak taşınması veya oturum kimliğinin değişmesi, bağlantıyı sessizce başka oturuma taşımamalı.
- **Kapanış:** Uydurma çok ajanlı/çok oturumlu iş örneklerinde ilişkilendirme, kaldırma, örtüşme, yeniden açılış ve eksik kaynak davranışı doğrulanır; kullanıcı bu görünümden iş kapsamını açıklayabilir.

### Y02 — Gözlemden karara ve haftalık takibe geçiş

**Durum:** 1 Kasım'da kaynakta uygulandı; yeni paket/yayın yok. [Y02 çalışma kanıtı](../../reports/followups-v1/REPORT.md). Kaynak ve arayüz doğrulamaları üretilmiş veriler/simüle hafta ile yapıldı; gerçek bir haftalık kullanıcı kararı, fayda ve tekrar kullanım pilotta açık. **Bağımlılık:** Y01 ve kullanılabilir veri kapsamı.

- **Uygulanan:** Kullanıcı kota/yoğunlaşma/oturum örüntüsü/diğer gerekçesini, gözlemini ve deneyeceği değişikliği bir işe kaydeder. Kaynak okuma zamanı sabit başlangıçtır; önceki ve sonraki dönemler eşit, çakışmayan yedi gündür. Yalnızca tarihli ve uzlaştırılmış yanıtlar ölçülür. Yeni model/provider çağrısı veya zamanlanmış inceleme yok; bölüm açılınca yüklenir. Bir hafta sonrası güncel kaynak okuması ve açık kullanıcı incelemesi gerektirir.
- **Karşılaştırma sınırı:** Her aynı araç/proje/model grubunda iki dönemde de en az üç oturum, yeniden üretilebilen başlangıç ve kullanıcının benzer görev/koşul değerlendirmesi gerekir. Medyan, oturumların yanıt başına token ortalamalarından hesaplanır. Eksik kaynak, değişmiş geçmiş, ayrıştırıcı/model değişimi, dönem sınırını aşan yanıt veya bilinmeyen koşulda sayısal fark üretilmez; gerekçe gösterilir. Nedensellik, kalite, hesap kotası veya para tasarrufu iddiası yok.
- **Saklama/güvenlik:** İş başına 10, toplam 100, aynı işte bir açık takip; iş dosyası 2 MiB sınırı korunur. Özel takipler aynı atomik iş kaydında, normal JSON dışında ve özel yedekte tutulur. İptal başlangıcı korur; takip veya işi silme eski yedekleri silmez. Yeni bileşen biçimi 3 eski 1/2'yi düzenlemeden okur; gerçek yazma 3 kullanır. Eski uygulamalar 3 okuyamaz. İlk açılışa ölçüm eklenmez; ayrı yetkili okuma ve 16 KiB eylem yolu, içerik/kapsam revizyonları ve kaybolmayan taslaklar kullanılır.

- Mevcut kota, yoğunlaşma ve oturum karşılaştırmalarını temel alarak incelenecek durumun dayanağını ve sınırını birlikte sun.
- Kullanıcı bir çalışma değişikliği kaydedebilsin; sonraki dönemde gözlenen değişimi inceleyebilsin. Karşılaştırma aynı dönem/oturum tanımı, sabit gözlem zamanı ve uyumlu model/proje kapsamını kullansın.
- Aktif oturumun bütün toplamını takvim haftasının harcaması diye sunma. İş zorluğu veya veri kapsamı karşılaştırılamıyorsa sonucu açık bırak; nedensellik, otomatik tasarruf veya başarı iddiası üretme.
- **Kapanış:** Eksik/örtüşen dönem, değişen model ve küçük örnek senaryoları yanıltıcı karşılaştırma üretmez; pilotta kullanıcı bir gözlemden savunulabilir karar çıkarıp sonraki gözlemi yorumlayabilir.

### Y03 — İşin hedefi ve tamamlanma sonucunu ilişkilendirme

**Durum:** 1 Kasım'da kaynakta uygulandı; yeni paket/yayın yok. [Y03 çalışma kanıtı](../../reports/work-outcomes-v1/REPORT.md). Kullanıcının hedefi, kendi sonuç durumu ve kalan iş notu, mevcut oturum değerlendirmelerinden ayrı kaydedilir. Gerçek kullanıcı yararı/anlama pilotta açık. **Bağımlılık:** Y01.

- **Uygulanan:** Hedef ve sonuç notu ayrı ayrı en fazla 1.000 karakter; değerlendirilmedi/kısmen tamamlandı/tamamlandı/tamamlanmadı kullanıcı seçimi ve kayıt zamanı. İşin tamamına ait bu girdiler filtreler veya kayıp oturumlarla değişmez. Seçili oturumların son görünür test/derleme sonuçları ve zamansal Git gözlemleri ayrı gösterilir; otomatik tamamlanma/kalite puanı yok.
- **Saklama/güvenlik:** Eski iş biçimi 1 değişmeden okunur; Y03 aşaması biçim 2 ekledi; güncel gerçek düzenleme Y02 ile iş bileşeni biçimi 3 yazar. Uygulama sürümü, kullanım şeması ve parser değişmedi. Hedef/notlar normal JSON'dan çıkarılır, özel yedekte korunur. Çakışan düzenlemede taslak ve son kayıtlı sürüm ayrılır; açık inceleme ve sonraki kayıt olmadan üzerine yazılmaz. Filtre/dil değişimi taslağı kaybettirmez. Eski uygulamalar güncel biçim 3'ü okuyamayacağından geri dönüşte uyumlu yedek gerekir.

- İşin hedefi ile kullanıcının “tamamlandı/kısmen tamamlandı” sonucunu mevcut oturum değerlendirmelerinden ayrı tut.
- Mevcut test/derleme ve Git gözlemleri dayanak olarak birleşsin; bunlar kullanıcı sonucunun yerine geçmesin. İsteğe bağlı görev/PR referansı tasarlanabilir; harici hesap bağlama veya otomatik sorgulama bu kayıtla yetkilendirilmiş sayılmaz.
- **Kapanış:** Geçen test, kalan satır, kullanıcının yararlı değerlendirmesi ve işin tamamlanması birbirine dönüştürülmeden gösterilir; çelişen örneklerde otomatik kalite puanı üretilmez.

### Y04 — Gerçek ödeme, API fiyat karşılığı ve kotanın karar bağlamı

**Durum:** 0.2.27'deki plan kontrolünün güvenilirlik sınırları 1 Kasım'da kaynakta düzeltildi; yeni paket/yayın yok. [Y04 çalışma kanıtı](../../reports/plan-safety-v1/REPORT.md). Önceki [0.2.27 raporu](../../reports/plan-check-v1/REPORT.md) tarihsel uygulamayı anlatır; eski “API daha ucuz / küçük plan yeterdi” sonuçları artık üretilmez. Gerçek ödeme girişi yararlılığı ve profesyonel kullanıcı anlama doğrulaması pilotta açık.

- **Kapanan somut açıklar:** Fiyatlanamayan yanıta rağmen ucuzluk sonucu; seyrek veya eski ölçerden küçük plan sonucu; birden fazla kaynak grubunun tek abonelikle kıyaslanması; kaynak okuma/arşiv hatalarının plan kararından düşmesi. Tarihi/yanıt toplamı uzlaşmayan kullanım, plan değişimi ve çelişen ölçer de sınırlanır.
- **Yeni sınır:** Yalnız kayıtlı tutarın liste fiyatından düşük olduğu sayısal gözlem ile varsayılan plana bağlı gözlenen eşik karşılaştırması kalır. Ödenen tutar `null`, eksiksiz hesap geçmişi `false`; küçük plan yeterliliği veya geçişte tasarruf iddiası yok. En az 14 güne yayılan 14 ayrı UTC gününde örnek, en fazla iki günlük aralık ve güncellik gerekir; bunlar PLER'in gözlem kurallarıdır. Açık sayfada eskiyen eşik karşılaştırması kendiliğinden yeniden okuma mesajına döner.

- API karşılığı, tarih/fiyat kapsamı ve kota gözlemi zaten mevcut; bunları yokmuş gibi yeniden geliştirme.
- Kullanıcının gerçek ödeme bilgisini ayrıca eklemek yararlı mı, pilotta sına. Gerekirse yalnız açıkça seçilen veriye dayalı ayrı karşılaştırma tasarla; kayıtlardaki API karşılığını gerçek abonelik giderine çevirmeye çalışma.
- **Kapanış:** Kullanıcı örnekler üzerinde ödediği para, varsayımsal API karşılığı ve hesap kotasını ayırır. Sağlayıcı faturası veya tam hesap kanıtı olmadan “gerçek harcama/tasarruf/abonelik getirisi” sonucu çıkmaz.

### Y05 — Eksik kapsamı kullanılabilir karara ve giderme adımına bağlama

**Durum:** 1 Kasım'da kaynakta uygulandı ve yapay verilerle doğrulandı; henüz yeni paket veya canlı site yayını yapılmadı. Gerçek kullanıcıların açıklamaları doğru yorumlaması pilotta açık. [Y05 çalışma kanıtı](../../reports/coverage-v1/REPORT.md). **Bağlantı:** E01/E02 hesap motoru ve kaynak kapsamı çalışmalarıdır; bu başlık o sınırları açıklamayı geliştirir, motorun bütün belirsizliklerini çözmez.

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

**0.2.29 yerel ilk kullanım kanıtı:** Canlı siteden tarayıcıyla indirilen .28 paketi ve son .29 ZIP, manifest bütünlüğüyle denetlendi. .29'un yerleşik runtime/native başlatıcısı PATH'te Python yokken, Türkçe/boşluk/`&` içeren yolda çalıştı. Demo, boş kaynak, dolu port, iki bağımsız örnek, EN/TR çevrimdışı yardım, iki ajanın oturumlarını tek işe bağlama ve temiz kapanış doğrulandı. Son wheel'in 53 dosyası kaynakla birebir; kurulu pakette 21 yardım/API kontrolü hatasız, Node 70/70. Kaynak Python takımı 731 test/5 atlama/0 hata verdi; son metin düzeltmeleri ayrıca kurulu paket/arayüzde kontrol edildi. Bu geliştirici bilgisayarındaki yalıtılmış provadır; yeni Windows hesabı, imza, fiziksel macOS, tam CI veya gerçek kullanıcı kabulü değildir. [Ayrıntılar](../../reports/first-use-v1/REPORT.md).

- [ ] **Güncel platform CI:** 0.2.25 için CI çalıştırılmadı. Önceki 0.2.24 `9891966` kaynağının [41056121858](https://github.com/OguzayYildiz/pler/actions/runs/41056121858) koşusu hesap ödeme/harcama limiti engeli nedeniyle 12 işte sıfır adım çalıştırmıştı; bu yeni adayın geçtiği veya testte kaldığı anlamına gelmez. Hesap engeli giderilince yayınlanacak tam adayın kaynak/kurulu paket/isteğe bağlı çözücü matrisi başarıyla çalışmalı. Hesap ayarları bu görevde değiştirilmez; engel sürerken boş koşu tekrarlanmaz.
- [ ] **Temiz makine:** Geliştirici checkout'u ve Python olmayan standart kullanıcıyla son paket; boş ve ASCII dışı yol, port çakışması, boş kayıt, kurulum/kaldırma, çevrimdışı yardım ve doğru erişim bağlantısı kabulü.
- [ ] **Güncelleme ve geri dönüş:** Önceki aday→son aday→geri alma; arşiv/tercih/değerlendirme korunması ve parser değişikliklerinin açık yorumlanması. Sürüm/şema geçişi bozuk dosyayı sessizce ezmemeli.
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

**Durum:** Önceki kaynak hash'i 1 Kasım'da tanımlı Windows iş yükünü geçti. E05 sonrası güncel adayın tek ek koşusunda hız hedefleri aşıldı; 2 Kasım'da neden ayrıldı ve değişmeyen girdilerdeki tekrar işler kaldırıldı; tek pil koşusu bütün eşikleri geçti. Prizde 3 sürüm × 3 koşu kabulü yeniden yapılacak. [Önceki E04 kanıtı](../../reports/scale-v1/REPORT.md), [güncel E05 kontrolü ve ham sonuçlar](../../reports/compatibility-v1/REPORT.md). **Tür:** Ölçüm ve gerekirse optimizasyon.

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
2. Y05 → Y04 → Y03 → Y02 kaynakta yapay verilerle doğrulandı; gerçek kullanıcı yararı/anlama pilotta açık. E05'in ilk bakım/yayın kontrolü tamamlandı. E04'ün hedef aşan sürelerinin nedeni (pil + tekrar işler) ayrıldı ve tek pil koşusu eşikleri geçti (prizde 3×3 tekrar ertelendi). E01'in ilk örüntüsü (sıkıştırılmış/çatallanmış Codex) eklendi; E02 kimliksiz kapsamla kapandı; kalan E01 örüntülerini somut karşı örneklerle sına. Kanıtlanamayan kapsam kesin sonuca dönüşmez. Y07'nin kullanıcı gerektirmeyen kabul hazırlıkları sürdürülür; hesap/lisans/imza/katılımcı işleri ve otomatik güncelleme sona kalır. Yeni paket çıkarmak bu incelemelerin ön koşulu değil.
3. Kullanıcının ürünü hazır bulmasına kadar reklam/katılımcı arama başlatma. E06 pilotu ancak kullanıcı bu aşamayı başlatınca ve gerekli kabul koşulları sağlanınca yürütülür; ölçütleri korunur ve sonraki gerçek kanıt önceliği değiştirebilir.
4. E01–E05 doğruluk, hesap/kota kapsamı, performans ve bakım işleri somut karşı örnek ve açık destek kararıyla sürdürülür; gerçek doğruluk hatası görülürse özelliklerden önce alınır.

Her kapanışta: iş kimliği, somut başarısızlık veya kabul görevi, uygulama commit/sürümü, kullanılan uydurma/izinli veri kapsamı, gözlenen sonuç ve kanıt bağlantısı kaydedilir. Yeni istek olmadan pilot ölçütleri veya mahremiyet sınırları değiştirilmez. Yalnız belge değişikliğinde uygulama sürümü/paket değiştirilmez ve hesap engelli CI yeniden çalıştırılmaz.
