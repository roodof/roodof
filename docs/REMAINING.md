# PLER — güncel kalan işler

30 Ekim 2026; güncel uygulama 0.2.25, son test edilen uygulama commit'i `a78f0b6` (önceki özellik commit'i `9a428d6`). Parser `accounting-2026-10-30.3` ve şema 2 değişmedi. Bu kayıt aktif iş listesidir. [QUALITY.md](../QUALITY.md) tarihsel bulguları ve kapanan kusurların kanıtlarını korur; eski bir notta “açık” yazması, sonraki sürümde kapanmış kusuru yeniden açmaz. [Yedekleme çalışması](../../reports/backup-v1/REPORT.md), [0.2.24 raporu](../../reports/integrity-v1/REPORT.md), [sayım sözleşmesi](../ACCOUNTING.md), [yayın koşulları](RELEASE.md), [kabul adımları](ACCEPTANCE.md) ve [pilot protokolü](PILOT.md) dayanaklardır.

Kullanıcının son satın alma değerlendirmesinden yedi başlık kayda alındı. Bunların dışında, önceki çalışmalardan kalan altı başlık aşağıda ayrı tutulur. Bunların hepsi kod hatası veya yayın engeli değildir: ürün geliştirmesi, doğrulama, kapsam kararı ve mevcut kayıttan çıkarılamayan bilgi ayrılır. Her başlığın tamamlanma durumu ayrıca yazılıdır; bir özelliğin uygulanması gerçek kullanıcı faydasının veya ödeme isteğinin kanıtı değildir.

**Son kullanıcı yönlendirmesi:** Aylık yaklaşık 3 dolar abonelik düşünülüyor; bu kesinleşmiş fiyat veya ödeme isteğinin kanıtı değildir. Kullanıcının içine sinmeden reklam veya deneyecek kişi arama başlatılmayacak. Önce somut ürün eksikleri giderilecek; ilk yetkilendirilen geliştirme Y06 yedekleme/geri yüklemedir. E06 pilotu ve katılımcı arama bu yeni yönlendirme nedeniyle ertelendi; önceden belirlenen pilot ölçütleri değişmedi.

## Son değerlendirmeden eklenen yedi başlık

### Y01 — Oturumları yapılan işe bağlama

**Durum:** Planlandı; ürün geliştirmesi. **Öncelik:** Y06 tamamlandıktan sonra önerilen ilk iş değeri geliştirmesi.

- Kullanıcı birkaç Claude/Codex oturumunu kendi seçtiği bir işe bağlayabilsin. Aynı oturum birkaç işle ilişkiliyse bu belirsizlik görülsün; tutarı kanıtsız oranlarla bölüştürme.
- Başlık/etiket gibi isteğe bağlı kullanıcı girdilerinin yerel saklama, silme, yedek ve dışa aktarma kapsamını açık tanımla. Ajan konuşmalarını toplamak gerekmesin.
- Ortak oturumlar birden fazla işte göründüğünde genel toplam ikinci kez artmasın. Kaynak taşınması veya oturum kimliğinin değişmesi, bağlantıyı sessizce başka oturuma taşımamalı.
- **Kapanış:** Uydurma çok ajanlı/çok oturumlu iş örneklerinde ilişkilendirme, kaldırma, örtüşme, yeniden açılış ve eksik kaynak davranışı doğrulanır; kullanıcı bu görünümden iş kapsamını açıklayabilir.

### Y02 — Gözlemden karara ve haftalık takibe geçiş

**Durum:** Planlandı; ürün geliştirmesi ve kullanıcı doğrulaması. **Bağımlılık:** Y01 ve kullanılabilir veri kapsamı.

- Mevcut kota, yoğunlaşma ve oturum karşılaştırmalarını temel alarak incelenecek durumun dayanağını ve sınırını birlikte sun.
- Kullanıcı bir çalışma değişikliği kaydedebilsin; sonraki dönemde gözlenen değişimi inceleyebilsin. Karşılaştırma aynı dönem/oturum tanımı, sabit gözlem zamanı ve uyumlu model/proje kapsamını kullansın.
- Aktif oturumun bütün toplamını takvim haftasının harcaması diye sunma. İş zorluğu veya veri kapsamı karşılaştırılamıyorsa sonucu açık bırak; nedensellik, otomatik tasarruf veya başarı iddiası üretme.
- **Kapanış:** Eksik/örtüşen dönem, değişen model ve küçük örnek senaryoları yanıltıcı karşılaştırma üretmez; pilotta kullanıcı bir gözlemden savunulabilir karar çıkarıp sonraki gözlemi yorumlayabilir.

### Y03 — İşin hedefi ve tamamlanma sonucunu ilişkilendirme

**Durum:** Planlandı; ürün geliştirmesi. **Bağımlılık:** Y01.

- İşin hedefi ile kullanıcının “tamamlandı/kısmen tamamlandı” sonucunu mevcut oturum değerlendirmelerinden ayrı tut.
- Mevcut test/derleme ve Git gözlemleri dayanak olarak birleşsin; bunlar kullanıcı sonucunun yerine geçmesin. İsteğe bağlı görev/PR referansı tasarlanabilir; harici hesap bağlama veya otomatik sorgulama bu kayıtla yetkilendirilmiş sayılmaz.
- **Kapanış:** Geçen test, kalan satır, kullanıcının yararlı değerlendirmesi ve işin tamamlanması birbirine dönüştürülmeden gösterilir; çelişen örneklerde otomatik kalite puanı üretilmez.

### Y04 — Gerçek ödeme, API fiyat karşılığı ve kotanın karar bağlamı

**Durum:** Planlandı; mevcut ayrımı geliştirme ve isteğe bağlı ödeme karşılaştırmasının kapsam kararı. Yeni bir fatura hatası saptanmadı.

- API karşılığı, tarih/fiyat kapsamı ve kota gözlemi zaten mevcut; bunları yokmuş gibi yeniden geliştirme.
- Kullanıcının gerçek ödeme bilgisini ayrıca eklemek yararlı mı, pilotta sına. Gerekirse yalnız açıkça seçilen veriye dayalı ayrı karşılaştırma tasarla; kayıtlardaki API karşılığını gerçek abonelik giderine çevirmeye çalışma.
- **Kapanış:** Kullanıcı örnekler üzerinde ödediği para, varsayımsal API karşılığı ve hesap kotasını ayırır. Sağlayıcı faturası veya tam hesap kanıtı olmadan “gerçek harcama/tasarruf/abonelik getirisi” sonucu çıkmaz.

### Y05 — Eksik kapsamı kullanılabilir karara ve giderme adımına bağlama

**Durum:** Planlandı; mevcut kalite açıklamalarını geliştirme. **Bağlantı:** E01/E02 hesap motoru ve kaynak kapsamı çalışmalarıdır; bu başlık kullanıcının açıklamayı kullanabilmesidir.

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

- [ ] **Güncel platform CI:** 0.2.25 için CI çalıştırılmadı. Önceki 0.2.24 `9891966` kaynağının [41056121858](https://github.com/OguzayYildiz/pler/actions/runs/41056121858) koşusu hesap ödeme/harcama limiti engeli nedeniyle 12 işte sıfır adım çalıştırmıştı; bu yeni adayın geçtiği veya testte kaldığı anlamına gelmez. Hesap engeli giderilince yayınlanacak tam adayın kaynak/kurulu paket/isteğe bağlı çözücü matrisi başarıyla çalışmalı. Hesap ayarları bu görevde değiştirilmez; engel sürerken boş koşu tekrarlanmaz.
- [ ] **Temiz makine:** Geliştirici checkout'u ve Python olmayan standart kullanıcıyla son paket; boş ve ASCII dışı yol, port çakışması, boş kayıt, kurulum/kaldırma, çevrimdışı yardım ve doğru erişim bağlantısı kabulü.
- [ ] **Güncelleme ve geri dönüş:** Önceki aday→son aday→geri alma; arşiv/tercih/değerlendirme korunması ve parser değişikliklerinin açık yorumlanması. Sürüm/şema geçişi bozuk dosyayı sessizce ezmemeli.
- [ ] **Fiziksel tarayıcı/erişilebilirlik:** Seçilecek Windows/macOS/Linux tarayıcılarında indirme ve yeniden bağlanma; klavye, odak, gerçek dar dokunmatik cihaz, %200/%400 yakınlaştırma, yüksek karşıtlık ve NVDA/VoiceOver. Son .25 yedek indirme/denetleme ve önceki .24 demo kontrolü tam matris yerine geçmez.
- [ ] **Yayın kararları:** Desteklenen platform/sürüm listesi, ürün lisansı ve dağıtım hakları, kamuya açık ad/paket kimliği, yayıncı, destek/güvenlik kanalı, sürüm ve fiyatlandırma/lisans modeli. Abonelik veya tek seferlik ödeme kararı verilmeden ödeme altyapısı zorunlu geliştirme sayılmaz.
- [ ] **İmza ve dağıtım:** Onaylanan yayıncıyla son paket baytlarını imzalama/doğrulama, artifact hash'i, yayın kanalı ve geri çekme yolu; güvenlik uyarısını atlatma test yöntemi değildir.
- **Kapanış:** Seçilen hedefler için her satırda gerçek ortam, sürüm/hash, beklenen/görülen sonuç ve kanıt vardır. Kit hazırlamak, eski CI'ın geçmesi veya geliştirici bilgisayarındaki kurulum bu kabulün tamamlandığı anlamına gelmez.

## Bu yedi başlık dışında önceki çalışmalardan kalan altı iş

### E01 — Zor geçmişlerin sayım uzlaştırması

**Durum:** Sınırları görünür, genel çözüm açık. **Tür:** Hesap motoru/doğruluk.

Keyfi fork/ebeveyn–çocuk/compaction geçmişleri, birikimli sayaçlar ve sabit kimliği olmayan olaylar her durumda tam uzlaştırılmış değil. Mevcut dar uzlaştırmaları ve alt ajan düzeltmelerini koru. Desteklenecek kanıtlanabilir örüntüleri bağımsız beklenen toplamlarla genişlet; dosya/olay sırası değişiminde sonucu ve tamlık işaretlerini karşılaştır. Kanıtı olmayan geçmiş bilinmiyor/eksik kalmalı; bütün geçmişlerin eksiksiz olacağı sözü verilmemeli. **Kapanış:** Her desteklenen örüntü için açık sözleşme ve regresyon; desteklenmeyen durumda sessiz çift sayım veya kesin toplam iddiası yok. Y05 yalnız bu sonucu anlaşılır kılar, motoru çözmez.

### E02 — Hesap değişimi ve çoklu hesap kapsamı

**Durum:** Çoklu yerel kaynak grubu koruması var; aynı kaynakta hesap değişimi doğrulanmış değil. **Tür:** Veri kapsamı/kapsam kararı.

Uyumlu kota örnekleri tek hesabı kanıtlamaz. Hesap kimliği toplamadan doğrulanabilecek kapsamı ve ayrıştırma yöntemini belirle; doğrulanamayan metreleri tek hesap gibi tahmin etme. Yeni hesap verisi veya harici hesap bağlantısı ayrı seçim ve veri kapsamı gerektirir. **Kapanış:** Aynı klasörde hesap değişimi ve birden fazla kaynak senaryolarının hangi kısmının desteklendiği açık; belirsiz örnekler güvenilir tek hesap/fatura sonucuna dönüşmez. Kanıt yokluğu yalnız kodla giderilmiş sayılmaz.

### E03 — Claude masaüstü kota kapsamı

**Durum:** Terminal Claude Code durum satırı destekli; masaüstünden kota geldiği doğrulanmadı. **Tür:** Destek/kapsam kararı.

Onaylanmış, güvenilir masaüstü veri kaynağıyla gerçek destek doğrulanmalı veya ilgili sürüm için açıkça destek dışında bırakılmalı. Terminal kurulumunu tekrarlatmak masaüstü kotasını sağladığı anlamına gelmez. **Kapanış:** Kanıtlı destek veya ürün kapsamına işlenmiş açık destek dışı kararı; sıfır veya anlık sağlayıcı sorgusu izlenimi yok. Bu kayda eklemek gerçek özel kaynağı okumaya izin değildir.

### E04 — Güncel adayın ölçek ve performans kabulü

**Durum:** Artımlı okuma/önbellek optimizasyonları ve sentetik hız korumaları var; genel kullanıcı hız garantisi yok. **Tür:** Ölçüm ve gerekirse optimizasyon.

İlk okuma, değişmeyen yenileme, eklenen kaynak, tam önek doğrulaması, Git ve arşiv maliyetini bütün hat üzerinde ölç. Büyük uydurma geçmiş, eski Python/fallback çözücü ve desteklenen çalışma ortamları için süre/bellek/iptal kanıtı tut; kabul eşiklerini ölçüm sonuçlarını görmeden seç. Eski parser-only oranını toplam açılış süresi diye sunma. Yeni gerçek veri ölçümü ancak uygun kullanıcı yetkisiyle yapılır. **Kapanış:** Tam aday ve fixture hash'leriyle tekrar üretilebilir ölçüm, önceden belirlenen hedefler ve sayım/kalite eşitliği; karşılanmayan ortam ya iyileştirilir ya belgelenmiş kapsam kararı alır.

### E05 — Kayıt biçimi ve fiyat tablosu uyumluluğunun bakımı

**Durum:** Desteklenen okuyucular ve tarihli sabit fiyatlar var; sürekli bakım işi. **Tür:** Uyumluluk ve sürümleme.

Claude/Codex kayıt sürümü–desteklenen olay/alan–fixture eşlemesini ve yeni/bozuk olay davranışını sürdür. Fiyat tablosunun tarih/kaynak/model kapsamını kontrol eden yayın adımı oluştur; bilinmeyen model sıfır fiyat sayılmasın. Parser değişikliği önbellek/arşiv ve eski JSON yorumuna bağlansın. Kaynak değişimi otomatik dış ağ sorgusu veya model çağrısı gerektirmez. **Kapanış:** Yayın başına destek matrisi, uydurma/izinli anonim fixture regresyonları, fiyat/sürüm kaydı ve bilinmeyeni güvenli sunan davranış; bundan sonraki sürümlerde bakım tekrar edilir. Bu, şu an yeni bir yanlış fiyat veya kayıt hatası bulunduğu iddiası değildir.

### E06 — Gerçek profesyonel pilot ve tekrar kullanım

**Durum:** Kullanıcının isteğiyle ertelendi; 0.2.24 kiti iki kurulum yolunda doğrulanmış, gerçek katılımcı sonucu yok. **Tür:** Kullanıcı kanıtı. **Öncelik:** Kullanıcı ürünü hazır bulduktan sonra değer varsayımlarını sınama.

[PILOT.md](PILOT.md) ölçütleri değişmeden en az beş profesyonelle mevcut yönteme karşı görevleri karşılaştır; başarısız/yanlış yorumlanan durumları da kaydet. Sonraki hafta somut tekrar kullanım gerekçesini gözle. Kullanıcı ürünü hazır bulduğunu belirtmeden reklam ve katılımcı arama başlatılmaz. Katılımcı bulma, onay ve yürütme daha sonra kullanıcıyla koordine edilir; bu belge kişilere mesaj gönderme yetkisi değildir. **Kapanış:** Önceden belirlenen kritik anlama, bağımsız görev ve tekrar kullanım hedefleri gerçek sonuçlarla değerlendirilir. Başarısız sonuç da rapordur; ölçütler sonuç görüldükten sonra değiştirilmez. Y01–Y05'in tamamını önce yapmak pilot için otomatik ön koşul değildir; kullanıcı yönlendirmesi ve gerekli yayın/mahremiyet kabulü korunur.

## Tamamlanmış işleri yeniden açmama ve bilgi sınırları

- .24'te kaybolan okuma uyarısı, başka dosyaya eski önbellek isabeti, orta bölüm değişimi+ekleme ve yeniden açma yarışı, çalışmayan test kipleri, Git dolaşım sınırı ve sınırlı değerlendirme okuması düzeltildi. Kaynak/paket kanıtı [raporda](../../reports/integrity-v1/REPORT.md); bunlar yeni iş listesi değildir.
- Yerel API erişim anahtarı, ağ yolu korumaları, Python'suz Windows adayı, proje adı gizleme, çevrimdışı yardım, arşiv saklama, kullanıcı değerlendirmesi, test/Git sinyalleri ve API karşılığı zaten vardır. Eksik kabul veya kapsamı, özelliğin yokluğu diye yazma.
- PLER'in hiç okumadan silinen geçmişi geri getirmek; mevcut kayıttan gerçek faturayı, insanın kesintisiz çalışma süresini, kodun doğruluğunu veya nedensel tasarrufu kesin çıkarmak vaat edilmez. Bunlar yeni bir düğmeyle kapatılacak işler değildir.
- Ekip sunucusu, SSO, çalışan performans puanı, yeni ajanlar ve çoklu cihaz eşitleme bu bireysel yerel ürün için zorunlu iş olarak eklenmedi. Ayrı hedef kullanıcı/kapsam kararı gerekir.

## Önerilen yürütme sırası ve kapanış disiplini

1. Y06 belirtilen yerel kurtarma kapsamıyla tamamlandı. Sonraki önerilen geliştirme Y01 iş bağlama; bu kayıt tek başına yeni özellik uygulama yetkisi değildir.
2. Y01'den sonra Y03 hedef/sonuç ve Y02 karar takibi; Y04/Y05 kullanıcı yanlış anlamalarını kapatacak kapsamda ilerler. Y07'nin tamamlanabilir yerel kabul hazırlığı sürdürülür; dış engel/kararlar ayrı görünür.
3. Kullanıcının ürünü hazır bulmasına kadar reklam/katılımcı arama başlatma. E06 pilotu ancak kullanıcı bu aşamayı başlatınca ve gerekli kabul koşulları sağlanınca yürütülür; ölçütleri korunur ve sonraki gerçek kanıt önceliği değiştirebilir.
4. E01–E05 doğruluk, hesap/kota kapsamı, performans ve bakım işleri somut karşı örnek ve açık destek kararıyla sürdürülür; gerçek doğruluk hatası görülürse özelliklerden önce alınır.

Her kapanışta: iş kimliği, somut başarısızlık veya kabul görevi, uygulama commit/sürümü, kullanılan uydurma/izinli veri kapsamı, gözlenen sonuç ve kanıt bağlantısı kaydedilir. Yeni istek olmadan pilot ölçütleri veya mahremiyet sınırları değiştirilmez. Yalnız belge değişikliğinde uygulama sürümü/paket değiştirilmez ve hesap engelli CI yeniden çalıştırılmaz.
