# Profesyonel neden kullanmaz?

## 2 Kasım: 0.2.30 yayın paketi ve pilot kiti (Claude)

Yerel olarak hazırlandı; yayımlanmadı, imzalanmadı. Kaynak `ac263ea`, kanal early-beta (0.2.29'daki yayıncı ve destek adresi). Ağsız derlenen wheel (54 kaynak dosyası birebir), Python'suz Windows x64 paketi (74 dosya, gömülü CPython 3.14.10, uygulama dosyaları kaynakla birebir) ve pilot kiti. Kurulu wheel'e karşı 810 test geçti (5 atlandı). Kit denetimi iki yolda geçti: PATH'te Python olmadan Windows paketi ve Python 3.9 wheel kurulumu; demo sayıları, yardım sürümü, gizli proje adlı JSON, 401, değerlendirme, plan seçimi ve kota uyarısı doğrulandı. Görev formları 0.2.24 ve 0.2.28 ile bayt bayt aynı. Sürüm notları, iş bileşeni biçimi 3 nedeniyle 0.2.29'a dönmeden önce yedek alınmasını söylüyor. Paket gerçek kayıtlarla açılmadı (gerçek önbelleğe dokunmamak için); temiz makine, macOS ve CI açık. [Rapor](../reports/release-0.2.30-v1/REPORT.md).

## 2 Kasım: E01 — kalan örüntüler (Claude)

Somut karşı örnekler (gerçek kayıtlar, yalnız sayılar): Claude'un tarihli kullanımı token'larının yalnız %2,4'ünü kapsıyordu; %97,5'i taşıyan 3 oturum 21, 4 ve 3 klasörde çalıştığı için "sahiplik doğrulanmadı" sayılıp dışlanıyordu. Bu oturumlar başka oturumla tek kayıt paylaşmıyor; yalnız proje bilinmiyor. Artık tarihli kullanıma giriyorlar; oturumlar arası paylaşılan kayıtlar dışlanmaya devam ediyor. İkinci örnek: Codex token'larının %71'i "eski sürüm arşivi" yüzünden eksik sayılıyordu. Üç eski arşiv kopyasının üçü de diskteki tek bir canlı dosyada eksiksiz bulunuyor (aynı kimlikler, aynı sayılarla her yanıt, her sayaç değeri): yer değiştirmiş dosyaların bayat kopyaları. Böyle bir kopya artık sayılmıyor, oturumu işaretlemiyor ve oturumun sayfa kimliğini değiştirmiyor. Sonuç: tarihli kapsam Claude %2,4 → %100, Codex %28 → %99; toplamlar ve oturum kimlikleri birebir aynı. Açık kalan, dürüstçe bilinmeyen: Codex token'larının %0,9'u yanıt başına tarihi olmayan eski birikimli kayıtlarda, %0,2'si çelişen sayaçlı oturumlarda.

## 2 Kasım: E02 — hesap kimliği okumadan hesap kapsamı (Claude)

Somut karşı örnek (sentetik): Codex'te Plus'tan Pro'ya geçen birinin haftalık tahmini, son 14 günün Plus yüzdelerini (günde 20 puan) Pro sayacına uyguluyordu; plan kontrolü de Plus'ta dolan pencereleri Pro'nun sınır sayımına katıyordu. Codex her kota örneğinde planı yazıyor; örnek artık planını taşıyor ve son plan değişiminden önceki örnekler tahmine ve sınır sayımına girmiyor (aynı örnekte tahmin günde 2 puan). Değişim zamanı sayfada, terminalde ve JSON'da. Destek tablosu ACCOUNTING.md'de: birden fazla kaynak grubu gizli; eşzamanlı iki hesap yalnız okumalar çelişirse yakalanır; aynı planda başka hesaba geçiş kayıtlardan anlaşılamaz, tek hesap iddiası yapılmaz; Claude Code planı kullanıcının seçimi. Bu bilgisayarda plan hiç değişmemiş; sayfa çıktısı birebir aynı.

## 2 Kasım: E01 — sıkıştırılmış ve çatallanmış Codex iş parçacıkları (Claude)

Somut karşı örnek: bu bilgisayarda Codex token'larının %98,8'i "uzlaşmamış toplam" uyarılı 9 oturumdaydı; 6'sı yalnız bağlam sıkıştırması yüzünden. Bu 6 oturum 226 dosyadan (kök + alt ajan iş parçacıkları) oluşuyor. Ölçüm, yalnız sayılarla: sıkıştırmasız 122 bölümün hepsinde dosyanın kendi yanıt kayıtları ile birikimli sayaç birebir aynı artıyor; fark yalnız sıkıştırmada ve yalnız kayıtlar lehine değişiyor (sayaç sıkıştırma isteğini saymıyor). Devralınan sayaçla başlayan 32 çatallanmış dosyanın hiçbirinde o değerden önce kayıt yok; değer adı geçen ana iş parçacığının hiçbir sayaç değerine eşit değil, bu yüzden toplam olarak kullanılmıyor, kayıtlar sayılıyor. Bu örüntü dosya bazında doğrulanırsa oturum kayıtlarla eksiksiz sayılır; kayıp kayıt, sayaç sıçraması, açıklanamayan başlangıç veya eski birikimli iş parçacığı eski uyarıyı korur. Sonuç: uzlaşmamış oturum 9 → 3 (%0,19), tarihli Codex kullanımı 2,8 M → 317 M token; toplam token ve dolar birebir aynı. Kalan büyük sınır: Codex token'larının %71'i eski sürümün yazdığı arşiv dosyalarında (asılları diskte artık yok), doğrulanmış sayılmıyor.

## 2 Kasım: E04 hız sorunu — neden ve düzeltme (Claude)

E05 koşusundaki hız aşımının büyük kısmı makineden: bilgisayar pilde, işlemci 1,88/3,2 GHz; E05'in hiç değiştirmediği Git dal kodu bile ~2,3 kat yavaştı. Yine de değişmeyen yenilemede üç tekrar iş vardı ve kaldırıldı: aynı dal uçları için Git yürüyüşü (yalnız bütün hedefler biliniyorsa saklanır), her istekte yeniden doğrulanan iş dosyası (aynı baytlar bir kez, her okuma özel kopya) ve yanıt başına fonksiyon çağrılı tarihli kullanım/plan toplamları. Aynı pil koşullarında değişmeyen yenileme 5,53 → 2,38 sn, değişim aşamaları ~10,7 → ~7,8 sn, HTTP ~1,4 → ~1,0 sn; önceden belirlenmiş bütün eşikler geçti. Sabit saatle tam sayfa görünümü eski/yeni kodda (ölçek verisi ve gerçek kayıtlar) okuma zamanı ve arşiv bayt sayısı dışında birebir aynı. Prizde 3×3 kabul koşusu yeniden yapılacak.

## 2 Kasım: Y02–Y05/E05 gerçek veri denetimi (Claude)

Bu bilgisayarın gerçek kayıtlarında, yalnız sayılarla, önbelleğin geçici kopyasında HEAD (0.2.29) ile kaynak karşılaştırıldı. İki gerileme bulundu ve düzeltildi. (1) Claude Code, bölge bilgisini raporlamaya başlamadan önce (burada 8 Ekim'e kadar) her yanıtta `inference_geo: not_available` yazmış; yeni kural bunu fiyatlanamaz saydığı için Claude geçmişinin %37'si fiyatsız kalıyor, toplam API karşılığı $893'ten $484'e düşüyordu. Yayımlanmış fiyatta yalnız `us` 1,1 kat; `not_available` artık yokmuş gibi fiyatlanır ve toplamlar HEAD ile aynıdır. (2) Plan ölçeri, 30 günde tek bir eski çelişki görünce 5 saatlik pencerenin tamamını atıyor, Codex'in "9/41 pencerede sınıra dayandı" bilgisi kayboluyordu. Artık yalnız çelişkinin olduğu pencere dönemi çıkarılır (burada 8/39). Herhangi bir çelişki küçük plan karşılaştırmasını yine engeller. Codex GPT-6 önbellek yazma kuralı burada etkisiz: Codex kayıtlarında yazma sayısı yok, Codex toplamı aynı ($280). Sıcak okuma 10,2 sn → 11,2 sn. Demo sayfasında yeni hedef/sonuç ve takip denetimleri stilli, 375 px'te taşma yok.

## 1–2 Kasım: E05 — kayıt/fiyat uyumluluğu yayın kontrolü

22 bağımsız beklenen uydurma kayıt ilk okuma, önbellek ve arşivde doğrulandı. Resmi kaynaklarla 1 Kasım tarihli 26 model/plan incelemesi, 30 günlük fiyat ve 90 günlük okuyucu inceleme süresi, kod/örnek değişimi denetimi ve tüm Node testlerini keşfeden yayın iş akışı eklendi. GPT-6 bilinmeyen önbellek yazma süresi, Codex'in incelenmemiş tarihli model kimliği ve Claude'un bozuk/çelişen fiyat kanıtı artık yanlış standart fiyat üretmez. Sayımlar korunur; sıfır fiyat kapsamı EN/TR ekranda bilinmiyor kalır. Parser `accounting-2026-11-01.1`, şema 2; eski arşiv ve takipler otomatik olarak yeni yorumla doğrulanmaz. [Rapor, test sonuçları ve sınırlar](../reports/compatibility-v1/REPORT.md). Yeni paket/site yayını veya CI koşusu yok. Aşağıdaki E04 kabulü önceki kaynak hash'ine aittir. Güncel tek büyük-küme koşusu sayımı korudu fakat yenileme/Git/HTTP süre hedeflerini aştı; güncel adayın performans kabulü açık ve sıradaki teknik inceleme budur.

## 1 Kasım: E04 — güncel kaynağın Windows ölçek kabulü

Önceden sabit eşiklerle 102,61 MiB yapay kayıt, 385 oturum/36.992 yanıt, 16 Git deposu, 200 iş/20.000 bağlantı/100 takip üç Python sürümünde üçer kez sınandı. Tam tarama + Git + ilk kullanılabilir JSON raporu ortancası 3.14 native'de 8,85 sn, 3.12 fallback'te 20,09 sn, 3.9 fallback'te 27,50 sn; değişmeyen yenileme 2,23–2,62 sn. Her tekil koşu kabul sınırlarını geçti, en yüksek süreç çalışma kümesi 239,08 MiB. Bağımsız önbelleksiz referans, tam eski önek, değişen kaynak, tüm kaynakların kaybolduğu dokuz arşiv koşusu, gerçek çözücü ilerlemesinde iptal ve yoğun arayüz doğrulandı. Python 3.12: 786/5-atlama/0-hata; 3.14: 795/4-atlama/0-hata. Bu bir geliştirici Windows kaynak provasının kanıtıdır; görsel ilk boyama, fiziksel platform/temiz makine veya genel hız garantisi değildir. Yeni paket/yayın/ürün hızlandırması yapılmadı. [Rapor ve ham ölçümler](../reports/scale-v1/REPORT.md).

**Güncel kalan işler:** [docs/REMAINING.md](docs/REMAINING.md). 30 Ekim 2026 satın alma değerlendirmesindeki yedi başlık, önceki altı ayrı iş, kapanış ölçütleri ve önerilen sıra burada tutulur. Dağıtım/CI/temiz makine/imza/tarayıcı kabulü tek başlık altında; ürün geliştirmesi, gerçek kullanıcı kanıtı ve kayıttan bilinemez sınırlar ayrı. Aşağıdaki tarihsel “açık” notlar sonraki sürümlerin kapanış kanıtlarıyla birlikte okunur; giderilmiş kusurlar tekrar iş sayılmaz.

## 31 Ekim: 0.2.28 yayın paketi ve pilot kiti

Yerel olarak hazırlandı, yayımlanmadı ve imzalanmadı: ağsız kurulan wheel (53 kaynak dosyası birebir), Python'suz Windows x64 paketi (73 dosya) ve kit (rehberler, görev formları, iki paket). Kit denetimi iki yolda geçti: PATH'te Python olmadan Windows paketi ve Python 3.9 wheel kurulumu; demo sayıları, yardım sürümü, gizli proje adlı JSON, değerlendirme, plan seçimi gidiş-dönüşü, bilinmeyen planın reddi ve kota uyarısı kodu doğrulandı. Kurulu wheel'e karşı 731 test geçti (5 atlandı). Görev formları 0.2.24 ile bayt bayt aynı; yeni özellikler pilot görevine eklenmedi. Sürüm notu taslakları (EN/TR) ve SHA256SUMS hazır. Lisans, yayıncı, imza, yayın kanalı ve katılımcı daveti kullanıcının kararıdır. Kanıt: [yayın paketi raporu](../reports/release-kit-v1/REPORT.md).

## 31 Ekim: 0.2.28 — anlık kota uyarısı

Bir 5 saatlik veya haftalık sınır dolduğunda ya da mevcut hızla sıfırlanmadan bir saat (haftalıkta bir gün) içinde dolacaksa sayfanın üstünde uyarı çıkar; kaynak mevcut tahmin ve sayfa saatidir, eski örnekler uyarı üretmez. İsteğe bağlı "Kotayı canlı izle" açık sayfayı 5 dakikada bir yeniden okutur (kullanıcı yazarken, pencere açıkken veya başka işlem sürerken atlar); isteğe bağlı masaüstü bildirimleri her yeni uyarıyı bir kez gösterir. Seçimler yalnız bu tarayıcıda tutulur. Windows 3.9 727/13 atlandı, 3.12 731/0 hata, 3.14 740/0 hata; Linux WSL `/tmp` ve `/var` 740/740; Node 70/70. Demo sayfasında şerit, canlı izleme ve engelli bildirim açıklaması gerçek tarayıcıda denendi; bildirim izni verilmedi, izin akışı birim testlerinde. CI hesap ödeme/harcama limiti engeli nedeniyle çalıştırılmadı. Kanıt: [kota uyarısı raporu](../reports/quota-alert-v1/REPORT.md).

## 31 Ekim: 0.2.27 — plan kontrolü (Y04'ün bir kısmı)

Her ajan için plan, yayımlanmış liste fiyatı (31 Ekim 2026), son 30 günün ajan işinin API liste fiyatı karşılığı ve sınıra dayanılan beş saatlik pencere/hafta sayısı gösterilir. Codex planı kayıttan, Claude planı kullanıcının bir kez yaptığı yerel seçimden gelir. Yalnız yayımlanmış oranlar kullanılır: Claude Max = 5x Pro (5 saat ve hafta), Ultra = haftalık 10x Pro, 5 saat sınırı yok. OpenAI Plus ile Pro arasındaki oranı yayımlamadığı için Codex için plan adı önerilmez. Küçük plan önerisi en az 14 günlük ölçer geçmişi ve %20 pay ister; "API daha ucuz" tam ve tarihli bir dönem ister, sınıra dayanılmışsa gösterilmez.

İlk sürümde dönem toplamı tarihli kullanım görünümünden alındı ve projesi belirsiz oturumları dışarıda bıraktı: gerçek veride Codex 215 $ yerine 2 $ çıktı ve yanlış "API daha ucuz" önerisi üretti. Toplam artık yanıtların kendi zaman ve fiyatından, hesabın bütün oturumlarıyla hesaplanıyor; bu durum için regresyon testi var. Gerçek veri: Claude Code son 30 gün 464 $, Codex 215 $; Codex Plus beş saatlik sınıra 41 pencerenin 9'unda, haftalık sınıra 12 haftanın 1'inde dayandı. Oturum, token, çağrı ve kalite işaretleri HEAD ile birebir aynı; okuma süresi aynı.

Testler: Windows Python 3.9 727 geçti/13 atlandı, 3.12 731/0 hata, 3.14 740/0 hata; Linux WSL `/tmp` ve `/var` 740/740; Node hepsi geçti. CI hesap ödeme/harcama limiti engeli nedeniyle çalıştırılmadı. Kanıt: [plan kontrolü raporu](../reports/plan-check-v1/REPORT.md).

## 30 Ekim: 0.2.26 — oturumları yapılan işe bağlama (Y01)

Kullanıcı kendi adlandırdığı işler oluşturup Claude Code/Codex oturumlarını bağlayabilir; ad değiştirme, bağlantı kaldırma ve silme kayıtları, değerlendirmeleri ve kullanım toplamlarını değiştirmez. Ortak oturumlar iş ara toplamlarında tekrar görünür ama atanmış iş özeti her oturumu bir kez sayar; filtre dışı ve bulunamayan bağlantılar ayrı gösterilir, taşınan oturum başka kimliğe bağlanmaz. `work-items.json` yalnız iş adı, zamanlar ve 24 karakterlik sayfa oturum kodlarını tutar; sınırlı ve doğrulanır, bozuk/yeni dosyanın üzerine yazılmaz. Olağan JSON dışa aktarımı iş adlarını ve bağlantıları içermez; özel yedek/geri yükleme içerir, 0.2.25 yedekleri iş dosyası olmadan kullanılabilir. Demo işleri bellekte kalır.

Codex özelliği, kurulu paket/portable/arayüz kanıtlarını tamamladı ve rapor/commit'ten önce durdu. Claude denetledi: Windows Python 3.9 717 geçti/13 atlandı, Python 3.14 730/0 hata; Linux WSL `/tmp` ve `/var` 730/730; Node 62/62. Codex'in tek Linux hatası (yedek dosyası izni 0777) geçici klasörün Windows diskinde (`/mnt/c`) açılmasından geldi; Linux dosya sisteminde test geçiyor. Gerçek veride 19 depoda kod sayımı 0.2.22 ile aynı sonucu ve süreyi verdi (97 commit, 28.763 eklenen / 27.558 yerinde satır, ~1,4 s). Parser ve şema değişmedi. CI hesap ödeme/harcama limiti engeli nedeniyle çalıştırılmadı. Kanıt: [iş bağlama raporu](../reports/work-items-v1/REPORT.md).

## 30 Ekim: 0.2.25 — doğrulanmış yerel yedekleme ve yeni klasöre kurtarma

Kullanıcı aylık yaklaşık 3 dolar abonelik düşündüğünü, ürün içine sinmeden reklam veya deneyecek kişi arama başlatılmamasını söyledi. Bu fiyat kesinleşmiş değildir; ücretli talep veya düzenli fayda kanıtı yoktur. İlk yetkilendirilen geliştirme Y06 olarak uygulandı. Profesyonel pilot ve katılımcı arama kullanıcı ürünü hazır bulana kadar ertelendi; pilot ölçütleri değişmedi.

`pler backup create/check/restore` ile yalnız kalıcı PLER üst bilgisi yedeklenir ve doğrulanır. Arşiv, saklama tercihi, değerlendirmeler ve kota örnekleri kapsanır; okuyucu/Git önbellekleri, demo, ajan ayarları ve erişim anahtarları kapsanmaz. Arayüz özel yedek indirme ve dosya denetimi sunar; geri yükleme komut satırından yalnız yeni, henüz var olmayan yerel klasöre yapılır. Mevcut klasörün üzerine yazma ve arayüzden tek tıkla geri yükleme bu adayda yoktur.

Geri yükleme, aynı bilgisayar/özgün seçili kaynak kökleri için kurtarmadır; kaynak yolları başka bilgisayara yeniden eşleştirilmez. Her açılışta `pler --data-dir KLASÖR` ile seçim gerekir. Özgün okuyucu anahtarı, zamanlar ve saklama tercihi korunur; çalışan sayfa ve varsayılan açılış kendiliğinden değiştirilmez. Yedek özel yollar/kimlikler taşır, şifreli veya anonim değildir; sağlama toplamı kazara hasarı kontrol eder, kaynağın güvenilirliğini kanıtlamaz.

Y06, bu açıkça sınırlanan yerel kurtarma kapsamıyla tamamlandı. Son uygulama commit'i `a78f0b6` (özellik commit'i `9a428d6`); sürüm 0.2.25, parser ve şema değişmedi. Son Linux WSL 681/681 ve Node 47/47 geçti. Son kurulu wheel Python 3.12'de 672 test, 0 hata, 5 atlama verdi; 51 kaynak dosyası birebir eşleşti. Modül çıkış kodu düzeltmesinden önce Python 3.9'da tam kaynak koşusu 667 geçti/13 atlandı; Windows Python 3.14'te 680 test, 0 hata, 4 atlama. Son düzeltmeden sonra her iki ortamda 22 CLI/yardım kontrolü hatasız tekrarlandı; yeni bir tam Windows takım koşusu iddia edilmiyor.

Son wheel ve PATH'te Python olmadan çalışan portable paket uçtan uca doğrulandı: 2 arşiv kaynağı, 1 değerlendirme, 1 kota örneği. Kaynaklar silindikten sonra yeni klasöre kurtarılan toplamlar, kalite işaretleri, değerlendirmeler ve zamanlar aynı kaldı. Hasarlı yedek ve var olan hedef reddedildi; mevcut veriler korundu. Son kurulu adayın tarayıcısında gerçek yedek indirmesi kaydedilip indirilen dosya denetlendi: bu ayrı uydurma arayüz örneği 2 kaynak/0 değerlendirme/0 kota verdi; güvenilir denetim örneği 2/1/1 verdi. EN/TR, özel veri uyarısı ve mevcut verinin korunması doğrulandı. Kendi test süreci çıkış 0 ile kapandı; test sekmesi kapatıldı ve geçici erişim dosyası silindi.

Nihai kanıtlar [yedekleme raporunda](../reports/backup-v1/REPORT.md). 0.2.25 CI çalıştırılmadı; önceki 0.2.24 koşusundaki hesap ödeme/harcama limiti engeli nedeniyle yeni boş koşu başlatılmadı. Bu aday için CI geçti/kaldı iddiası yoktur. Y07'nin temiz makine, fiziksel tam tarayıcı/ekran okuyucu matrisi, imza ve yayın koşulları açık kalır. Bu çalışma gerçek kayıt/önbellek okumadı, model çağrısı, reklam veya katılımcı iletişimi yapmadı. Sonraki iş değeri geliştirmesi Y01 iş bağlamadır; profesyonel pilot kullanıcı ürünü hazır bulana kadar ertelenmiş durumda kalır. Diğer kalan işler açık durumlarını korur.

## 30 Ekim: 0.2.24 — doğruluk ve sınır denetimleri

Claude'un 0.2.16–0.2.23 geliştirmeleri korundu. Yenilemede kaybolan okuma uyarıları, aynı boyut/tarihle değiştirilen dosyada eski cache isabeti, eski bölümün ortasındaki değişimi kaçıran artımlı okuma ve doğrulama/yeniden açma arasında dosya döndürülmesi düzeltildi. Hatalı görüntüler beş saniye sonra yeniden denenir. Yardım/listeleme/toplama/dry-run/yalnız derleme kipleri artık çalışmış test veya derleme olarak sayılmaz.

Git ağaçları ve değişen dosyalar toplandıktan sonra değil, dolaşım sırasında sınırlandırılır ve iptal kontrolü yapılır. Sınıra takılan commit bilinmiyor kalır; kısmi sayım eksiksiz diye saklanmaz. Git sayımı ve kullanıcı değerlendirmesi dosyaları tek, sınırlı okumadan geçer; kalan satır sayısı eklenen satırı aşamaz.

Yerel son kaynak testleri: Windows Python 3.9 pytest 618 geçti / 11 atlandı; Python 3.12 unittest 620 çalıştı / 3 atlandı; Python 3.14.10 unittest 629 çalıştı / 2 atlandı. Linux WSL Python 3.14.4 629/629; Node 39/39. Kurulu wheel'in 49 kaynak dosyası birebir aynı; 620 test hatasız çalıştı / 3 atlandı. 0.2.24 pilot kiti Python'suz Windows ve Python 3.9 wheel yolunda doğrulandı. Kurulu demo tarayıcıda EN/TR, değerlendirme ekleme/kaldırma, test/Git göstergeleri ve temiz kapanışla sınandı. Önce/sonra kanıtı ve paket durumu [güncel raporda](../reports/integrity-v1/REPORT.md). `9891966` kaynak commit'inin [GitHub denetimi](https://github.com/OguzayYildiz/pler/actions/runs/41056121858), hesap ödeme/harcama limiti engeliyle 12 işte sıfır adım çalıştırdı; başarılı kabul sayılmaz. Gerçek pilot, temiz makine, tam erişilebilirlik/tarayıcı matrisi ve imzalı dağıtım açık kabul kapılarıdır.

---

26 Ekim 2026. Aktif çalışma yönü: yeni özellik eklemek yerine kullanmama nedenlerini somut kanıtla azaltmak. Eski raporlardaki “kapandı” ifadeleri müşteri kabulü kanıtı olarak alınmaz. Bir testin geçmesi, yalnız sınadığı kusurun düzeldiğini gösterir.

## 30 Ekim: 0.2.15 — büyük ve bozuk kayıtlar okumayı durduramıyor

Kayıtlar artık parça parça okunuyor; dosya, satır, açılmış veri, iç içe JSON ve tarama başına üst sınırlar var. Sınıra takılan dosya bozuk değil "eksik kapsam" olarak bildiriliyor. Tarama tek bir iptal edilebilir işçide çalışıyor, yerel sunucu bağlantıları süreyle sınırlı, arşiv diske güvenli yazılıyor.

- **Kanıt (uydurma dosyalar):** 26 MB'lık bir Codex dosyasında okuma sırasındaki bellek tepesi 80 MB'tan 0,3 MB'a indi. 0.2.14'te aşırı iç içe bir Claude satırı okumayı `RecursionError` ile durduruyordu; artık yalnız o satır atlanıyor.
- **Gerçek veri:** 0.2.14 ile aynı oturum, token, çağrı, kalite işareti ve kota durumu; sınıra takılan dosya yok. Kota tek kaynak grubundan geliyor ve 0.2.14'teki "birden fazla kaynak grubu" kuralı onu gizlemiyor.
- **Hız:** İlk taslak gerçek veride ilk okumayı %37 yavaşlatmıştı (Python 3.14: 12,6 → 17,3 sn). İç içe derinlik kontrolü, satır boyutu ölçümü ve arşivin kontrol karakteri denetimi C hızına çekildi. Sonuç: ilk okuma 12,8 sn (0.2.14'te 12,2), sonraki okuma 3,35 sn (3,25).
- **Doğrulama:** Windows'ta Python 3.9'da 528 test geçti, 11'i atlandı; 3.12'de 530; 3.14.10'da 539. Linux'ta düz `/tmp` ve `/var` varyantında 539'ar test geçti. Node 32/32. Yeni testler gerçek önbelleğe yazmıyor. Demo sayfasında yenileme ve kapatma çalıştı.

## 29 Ekim: 0.2.14 — düşük seviyeli dayanıklılık düzeltmeleri

Claude'un 0.2.13 geliştirmeleri ve sıcak okuma optimizasyonları korundu. Bu turda gerçek kayıtlar okunmadan, uydurma dosya ve yerel bağlantılarla şu kusurlar giderildi:

- Geç gelen oturum yanıtı daha yeni seçimi değiştirebiliyordu; yalnız güncel istek açılır. Dil değişimi sırasında tarama sürüyorsa proje seçimi korunur.
- ASCII dışı erişim anahtarı bağlantıyı düşürüyordu; normal 401/403 yanıtı döner. Tek oturum sorgusu da dil değerini doğrular.
- Dosya boyutu kontrolünden sonra büyüyen arşiv sınırsız okunabiliyordu; gözlenen boyut + 1 bayt okunur, değişim reddedilir. Küçük nesil ve tercih dosyalarının ayrı 4 KiB sınırı vardır.
- Aşırı iç içe JSON eski Python'da okumayı kesebiliyordu; bozuk önbellek yeniden oluşturulur, geçersiz saklama tercihi kapalı kalır ve açık seçimle onarılır.
- Ayrı yerel kaynak grupları uyumlu görünen kota kayıtları sağlayınca tek hesap gibi tahmin üretilebiliyordu. Ortak hesap doğrulanamadığında yüzde ve tahmin gizlenir; sıfırlama tarihi olmayan eski sayaç yolu da buna dahildir. Tek kaynak grubu da tek hesabı kanıtlamaz.

Yerel doğrulama: Windows Python 3.9: 477 geçti / 10 atlandı; 3.12: 478 çalıştı / 2 atlandı; 3.14.10: 487 çalıştı / 1 POSIX testi atlandı. Linux WSL Python 3.14.4: 487/487; Node: 32/32. `6f10365` uygulama commit'inin Windows/macOS/Linux [12 platform denetimi](https://github.com/OguzayYildiz/pler/actions/runs/40959556534) geçti. Son pilot kiti iki kurulum yolunda; kurulu aday tarayıcıda ve gerçek JSON indirmesinde doğrulandı. Atlamalar ve dağıtım sınırları [raporda](../reports/lowlevel-v1/REPORT.md) kaydedilir. Gerçek profesyonel pilot, temiz makine, fiziksel macOS/Linux tarayıcı ve imzalı dağıtım tamamlanmış sayılmaz.

## 29 Ekim: 0.2.13 — günlük kullanıma engel olan küçük sorunlar

Çevrimdışı yardım, arşivi silmeden durdurma, yalnız okuma önbelleğini sıfırlama, JSON'da proje adlarını gizleme, aynı adlı projeleri ayırma ve kalite uyarısından etkilenen oturumlara geçiş eklendi. Kurallar ölçümden önce `2f0689c`'de sabitlendi.

- **Gerçek veride iki kural çöktü, yayından önce düzeltildi:**
  - *Kota:* Codex sayacı aynı pencere içinde sık sık 1 puan geri düşüyor (5 saatlik pencerede 622 kez, en çok 11 puan); sağlayıcı pencereyi bazen erken sıfırlıyor. İlk kural ikisini de "çelişki" sayıp iki gerçek Codex penceresini de gizledi. Düzeltmeden sonra gerçek sonuç 0.2.12 ile aynı.
  - *Dönem içi kullanım:* Claude yanıtlarının %75'i saniyeler arayla birkaç satıra yazılıyor; "tek zaman" kuralı bunları tarihsiz bıraktı (174 yanıt). Yanıt artık ilk ve son satırının zamanıyla tarihleniyor; dönem başlangıcına denk gelirse tarihsiz kalıyor.
- **Görünüm kararı:** Düzeltmeden sonra da gerçek 29 oturumun 23'ü eksik kullanım veya belirsiz sahiplik yüzünden dışlanıyor. Son 7 günde 1,5 milyar token kullanılmışken tarihli toplam 0. Bu yüzden sayfa ve terminal tarihli kullanımı yalnız seçilen her oturum tarihlenebildiğinde gösteriyor; JSON her zaman kapsam sayılarıyla taşıyor.
- **Hız:** Gerçek veri büyüdü (29 oturum, yaklaşık 9.700 çağrı). Python'suz Windows paketindeki Python 3.14.10 ile boş önbellekten ilk okuma 13,7 sn sürüyor; 28 Ekim'deki daha küçük veride 7,2 sn'ydi. Sonraki okumalar 4,1 sn'ydi; önbellek tek özetle doğrulanınca ve yanıt sahipliği kendi kanıtını yeniden işlemeyince 3,3 sn'ye indi, sonuçlar aynı. En yavaş yol, `zstandard` olmadan Python 3.9: ilk okuma 78 sn, sonraki okumalar 9–17 sn. Bu sürüm 0.2.12'ye göre yavaşlatmadı. Eski Python kullanan kaynak kurulumları için hız hâlâ açık sorun.
- **Doğrulama:** Windows'ta Python 3.9'da 459 test geçti, 10'u atlandı; 3.12'de 460; 3.14.10'da 469. Linux WSL'de Python 3.14.4 ile düz `/tmp` ve sistem bağlantısı arkasındaki `TMPDIR` için ayrı ayrı 469'ar test geçti. Node 24/24. Yeni testler gerçek önbellek klasörüne hiçbir şey yazmıyor.

## 29 Ekim: 0.2.12 — aynı hedefe sonraki oturumda dönüldü mü?

Profesyonel, yalnız token toplamından hangi oturumları inceleyeceğini bulamıyordu. Artık aynı düzenleme hedefini yedi gün içinde kaydeden bağımsız sonraki oturumlar gösteriliyor. Tanım gerçek sonuçlar görülmeden `8917914` commit'inde sabitlendi.

- **Sınırları görünür:** Süre, önceki oturumun sonuyla sonraki oturumun başlangıcı arasındadır. Alt ajanlar ve ortak yanıt geçmişleri bağımsız sayılmaz. Çakışmalar, belirsiz hedefler, eski/doğrulanamayan arşivler dışlanır; yakın tarihli eşleşmeyenlerin takibi beklenir. Ekran ve JSON, nedenleri ve sabit gözlem sonunu gösterir.
- **Yorum:** En fazla beş oturum çifti ve bütün oturumun kayıtlı tokenları inceleme başlangıcı sağlar. Düzenlemenin maliyeti, israf, kalite veya tasarruf çıkarılmaz; oran üretilmez. Taşıma/silme/yol adları gerçek dosya sürekliliğini kanıtlamaz.
- **Gerçek sabit üst bilgi:** 0.2.11 ve 0.2.12'de 29 oturum, 9.371 çağrı ve 2.378.361.325 token aynı; oturum başına sayım ve tamlık işaretleri de aynı. 13 oturum değerlendirilebilir, 1 eşleşir (167,42 sn), 4'ü takip bekler, 8'inde eşleşme gözlenmez. 15'inde hedef yok; 1'i tarama başlangıcından sonraki zaman nedeniyle dışlanır. Bu karşılaştırma yalnız o anda yerinde duran onaylı kayıtları kapsar.
- **Farklı kanıt:** Aynı üst bilgide Git gözlemi 75/75 commit'i dalda buldu. Bu, sonraki hedef düzenlemesinin olmadığını söylemez; sonraki düzenleme de commit'in kalitesini söylemez. İki gözlem farklı soruları yanıtlar.
- **Doğrulama:** Windows 3.9'da 353 geçti / 9 yerel zstd testi atlandı; 3.12'de normal paket geçti. Windows 3.14.10 ve Linux WSL 3.14.4'te 362/362; Node 24/24. Pilot kiti iki kurulum yolunda baştan sona doğrulandı. Ayrıntı ve paket kanıtı [raporda](../reports/reedit-v1/REPORT.md).

Yeni özellik profesyonel kullanıcı kabulünü kanıtlamaz. Gerçek pilot, temiz makine, imzalı dağıtım ve günlük kullanımda fayda açık kabul kapılarıdır.

## 29 Ekim: 0.2.11 — kayıtlar silinince geçmiş artık kaybolmuyor

Claude Code varsayılan olarak 30 günden eski konuşmaları siliyor. PLER'in önbelleği de yalnız son okumada görülen dosyaları sakladığından, oturumlar sessizce kayboluyor ve aylık toplamlar küçülüyordu. Kullanıcı bunu fark edemiyordu.

- **Düzeltme:** PLER, varsayılan ve ortam değişkeniyle seçilen klasörlerdeki her dosyanın izinli üst bilgisini sınırlı bir yerel arşivde tutuyor. Silinen kaynağın oturumları sayılmaya devam ediyor ve "kaynak silindi, PLER arşivinden" diye işaretleniyor. Metin tutulmuyor.
- **Önce ve sonra (uydurma kayıtlar):**
  - Kaynak silinince 0.2.10'da 350 token 0'a düşüyor, 0.2.11'de 350 kalıyor.
  - Arşivdeki yanıtları kopyalayan devam oturumu iki kez sayılmıyor (410 token, 3 çağrı).
  - Arşiv silinince yalnız yerinde duran kayıt kalıyor (290 token).
- **Gerçek kayıtlar:** Hiçbir şey silinmemişken toplamlar 0.2.10 ile birebir aynı: 29 oturum, 9.186 çağrı.
- **Codex'in yarım bıraktığı taslakta düzeltilenler:**
  - **Hız:** Her okuma arşivi baştan temizleyip yeniden yazıyor, oturum kaynak kanıtı da karesel büyüyordu. Gerçek kayıtlarda yeniden okuma 2,3 sn'den 21 sn'ye çıkmıştı; şimdi 4,1 sn.
  - **Komut satırı klasörleri:** `pler report --claude-dir` ile bir kez bakılan klasörler bir yıl saklanıyordu. Testler de bu yüzden gerçek kullanıcı önbelleğine uydurma kayıt yazıyordu. Artık bu klasörler arşivlenmiyor.
  - **Onaysız silme:** Sayfadaki silme düğmesi bir yıllık, geri getirilemez geçmişi onay sormadan siliyordu. Artık önce onay istiyor.
- **0.2.10 düzeltmesi:** Seçilen klasördeki macOS `/var` gibi sistem bağlantıları her zaman çözülüyor, bu yüzden macOS CI'ında 5 test düşüyordu. Düzeltildi; CI 12/12.
- **Testler:**
  - Windows'ta Python 3.9 ve 3.12 ile 310, Python 3.14 ile 319 test geçti.
  - Linux'ta normal ve macOS benzeri geçici klasörle 319/319 geçti.
  - Tarayıcı mantığında 19/19 geçti.

[Kanıt](../reports/source-archive-v1/REPORT.md).

**Sınır:**
- **Arşivin yükü:** Arşiv önbellek kadar özel bir üst bilgi dosyası; proje ve dosya yolları da içinde. Yük sınırlı ama sıfır değil: 24,5 MB ve sıcak okumada yaklaşık 1,8 sn.
- **Kaybolan geçmiş:** Silinmeden önce PLER'in hiç okumadığı kayıtlar geri gelmez.

## 28 Ekim: 0.2.10 — açıkça seçilen WSL kayıtları

Windows'ta açıkça seçilen iki WSL yol yazımı artık çalışır. Aynı uydurma gerçek WSL dosyalarında 0.2.9 sıfır oturum gösterirken 0.2.10 iki oturum ve 350 tokenı okudu. Hem ortam değişkeni hem açık klasör seçenekleri doğrulandı. Linux'tan Windows'a `/mnt/c` okuması aynı sonucu verdi. Harf büyüklüğüyle ayrılan iki WSL dosyası da korunuyor.

Kapalı dağıtımın gerçek durum sorgusunda dosya sorgusu yapılmadı ve dağıtım kapalı kaldı. Ürün yalnız sabit durum sorgusunu çalıştırır; dağıtım başlatmaz veya otomatik kayıt aramaz. Gerçek ağ, aygıt ve birim yolları ile Git/proje/önbellek sınırları korunur. Durum kontrolü ile dosya erişimi arasında dışarıdan kapatılmaya karşı atomik garanti yoktur.

Windows 3.9 ve 3.12'de 278 test geçti; yerleşik çözücü isteyen dokuz test bu sürümlerde yoktur. Windows 3.14 ve Linux'ta 287/287, tarayıcı mantığında 18/18 geçti. Kurulmuş pakette de 278 kabul testi geçti; 31 kaynak/arayüz dosyası birebir eşleşti. Bütün sonuçlar [çalışma raporunda](../reports/wsl-roots-v1/REPORT.md). Kaybolan kaynakların arşivi ve yeniden düzenleme gözlemi sonraki iki aşamadır; bu sürümde tamamlanmış sayılmaz.

## 28 Ekim: 0.2.9 — taşınmış kayıt klasörü artık "kayıt yok" göstermiyor

Kayıt klasörünü (`~/.claude`, `~/.codex` ya da içindeki `projects`/`sessions`) başka bir diske taşıyıp yerine sembolik bağlantı veya Windows junction'ı bırakan biri, PLER'de hiç kayıt görmüyordu. PLER bu bağlantıyı güvensiz yol sayıp atlıyordu. Pilotta böyle bir katılımcı, ürünü bozuk sanıp yanlış bir "veri yok" sonucu verirdi.

- **Düzeltme:** Kullanıcının seçtiği kayıt klasörüne giden kendi bağlantısı artık izleniyor: varsayılan klasör, `CLAUDE_CONFIG_DIR`, `CODEX_HOME`, `--claude-dir` ve `--codex-dir`.
  - Bağlantının hedefi açılmadan önce okunuyor. Ağ, birim ya da aygıt yazımına giden hedef, oraya hiç dokunulmadan reddediliyor.
  - Döngü 32 bağlantıda duruyor.
- **Değişmeyenler:** Kayıt klasörünün içindeki bağlantılar, bağlantı olmayan Windows ayrıştırma noktaları, kayıtlardan okunan proje yolları, Git üst bilgisi ve önbellek klasörü eski kurallarla çalışıyor.
- **Önce ve sonra:** Bağlantılı uydurma bir ev klasöründe 0.2.8 hiç oturum göstermiyor ve iki "UnsafePath" atlaması bildiriyordu. 0.2.9, 2 oturumu ve 2.320 tokenı eksiksiz okuyor. Sonuç Windows'ta junction'la ve Linux'ta sembolik bağlantıyla aynı.
- **Testler:**
  - Windows'ta Python 3.9 ve 3.12 ile 262 geçti. Python 3.14'ün yerleşik zstd çözücüsünü isteyen 9 test bu sürümlerde her zamanki gibi atlandı. Bu bilgisayarda sembolik bağlantı yetkisi olmadığından yeni testler Windows'ta junction'la çalıştı.
  - Python 3.14 ile Windows ve Linux'ta 271/271; Linux'ta ayrıca geçici klasör macOS'taki gibi bir sistem bağlantısının arkasındayken de 271/271.
  - 9'u yeni. Uçtan uca iki yeni test eski kodda düşüyor.

[Kanıt](../reports/linked-roots-v1/REPORT.md).

## 28 Ekim: 0.2.8 — pilot başlatılabilir durumda

Kalan en büyük açık, gerçek bir profesyonelin PLER'le farklı bir karar verip vermediği. Bunu yalnız bir pilot gösterebilir. Pilot için hazırlananlar:
- **Deneme modu:** `pler demo`, uydurma kayıtlar ve uydurma bir Git deposuyla sayfayı açıyor. Ajan klasörlerine dokunmuyor, sayfada açık bir "uydurma veri" uyarısı var. Protokoldeki 8 görevin her biri bu veriyle yapılabiliyor.
- **Pilot kiti:**
  - Python'suz Windows paketi (Python 3.14) ve wheel;
  - iki dilde katılımcı rehberi ve görev formu;
  - yürütücü için ölçülerek yazılmış cevap anahtarı, önceden belirlenmiş geçme ölçütleri ve kayıt şablonu.
- **Doğrulama:** Kit, katılımcı gibi açılıp hem Python'suz Windows paketiyle hem Python 3.9 wheel'iyle sınandı. [Rapor](../reports/pilot-kit-v1/REPORT.md).

**Açık:** Pilotun kendisi. Katılımcı bulma ve oturumları yürütme kullanıcının işi; sonuçlar gelince ölçütler değiştirilmeden yazılacak.

## 28 Ekim: 0.2.7 — “Harcanan tokenlar işe yaradı mı?”: commit'ler hâlâ dalda mı?

Kullanıcının izniyle Git okuma sınırı genişletildi. Artık commit nesnelerinin de ebeveyn bağları ve zamanları okunuyor. İsim, e-posta, mesaj, ağaç ve dosya okunmuyor; Git programı çalışmıyor.

Oturum sırasında kaydedilen her commit için şu soru cevaplanıyor: hâlâ yerel ya da uzak izleme dalında mı, yoksa amend, rebase, reset ya da silinen dal yüzünden dalın dışında mı? Okunamayan durumlar tahmin edilmeden "bilinmiyor" olarak bırakılıyor. Dönem özetine bir gözlem eklendi: kaç oturumda kaç commit kaydedildi ve kaçı hâlâ dalda. Her commit, oturumlar çakışsa da bir kez sayılıyor.

- **Doğruluk:** Uydurma depolarda (amend, reset, rebase, silinen dal) sonuçlar Git'in kendi cevabıyla 12 denetimde birebir aynı. Denetimler SHA-1 ve SHA-256 depolarda, tek tek nesne dosyaları, paket ve delta sıkıştırmalı paket biçimlerinde yapıldı.
- **Hız:** 30.000 commit'lik pakette yeni bir commit 0,07 sn, dalın dışına çıkmış bir commit 0,56 sn sürüyor. En kötü durum 3,3 sn'de sınıra gelip "bilinmiyor" diyor.
- **Gerçek kayıtlar:** 4 oturum sırasında 68 commit kaydedilmiş, 68'i de hâlâ dalda. Bu oturumlar tokenların yaklaşık %70'ini kullanmış. Kullanım eksiksiz olmadığı için bu pay ekranda gösterilmiyor.
- **Testler:** Windows'ta 248, Python 3.14 ile Windows ve Linux'ta 257, tarayıcı mantığında 18 test geçti. 11'i yeni.

[Kanıt](../reports/git-outcome-v1/REPORT.md).

**Sınır:**
- "Dalda" demek değişikliğin hâlâ kodda durduğu anlamına gelmez; sonraki bir commit onu geri almış olabilir.
- "Dalda değil" de değişikliğin kaybolduğu anlamına gelmez; yeniden yazılan bir commit aynı değişikliği taşıyabilir.
- Geri alma (revert) commit'lerini tanımak için mesaj okumak gerekir; bu bilerek yapılmıyor.
- Zaman eşleşmesi yazarlığı kanıtlamaz.

## 28 Ekim: 0.2.6 — “ccusage'dan farkı ne?”: oturumlar değiştirdikleri depoya bağlanıyor

PLER'in token saymanın ötesindeki asıl farkı, oturumu Git'teki sonucuyla yan yana koymak. Codex'in 26 Ekim'deki ilk sürümü yalnız oturumun açıldığı klasöre bakıyordu. Bu bilgisayarda bu yaklaşım hiçbir şey göstermedi.

**Nedeni:** Ajan çoğu zaman bir üst klasörde başlatılıyor ve içerideki bir depoyu değiştiriyor. Bazı oturumların proje bilgisi de belirsiz.

**Çözüm:** Oturum artık düzenlediği dosyaların bulunduğu depolara da bağlanıyor. Codex yamalarının hedef dosyaları da okunuyor; yamanın içeriği tutulmuyor.

| Bu bilgisayarın gerçek kayıtları (29 oturum) | Önce | Sonra |
|---|---:|---:|
| Okunabilir Git geçmişine bağlanan oturum | 1 | 6 |
| Oturum sırasında Git hareketi görülen oturum | 0 | 4 |
| Bu oturumlardaki hareketler | 0 | 70 (67 commit) |
| Bu oturumların tokenlardaki payı | %0 | %69 |

- **Gerçek kontrol:** Bu oturumun ekranı, `product/` deposunda oturum sırasında yapılan 4 commit'i tam olarak gösteriyor. Oturumun proje bilgisi belirsiz olduğu hâlde bağlantı düzenlenen dosyalardan kuruldu.
- **Sayım değişmedi:** 128 sabit gerçek dosyada 0.2.5 ile 0.2.6'nın token, çağrı ve kalite bayrakları aynı. Yalnız 8 Codex oturumu artık düzenlediği dosyaları bildiriyor.
- **Testler:** Windows'ta 237, Python 3.14 ile Windows ve Linux'ta 246, tarayıcı mantığında 18 test geçti. Yeni 10 test şunları sınıyor: yama hedefleri, bağlantı kuralı, birden çok depo, ağ yolu güvenliği ve gizlilik.

[Kanıt ve sınırlar](../reports/git-links-v1/REPORT.md).

**Sınır:**
- Bu hâlâ "oturum sırasında yerel Git'te ne oldu" sorusunun cevabı. Commit'in korunup korunmadığı ya da geri alınıp alınmadığı henüz yok.
- Aynı anda başka kişiler veya ajanlar da çalışmış olabilir.
- Düzenleme sayısı, kayda geçen düzenleme girişimidir.
- Sonraki adım: oturumun commit'lerinin bugün dalda durup durmadığı. Bu, Git nesnelerini okumayı gerektirir; okuma sınırı genişleyeceği için ayrı bir karar konusudur.

## 28 Ekim: “İlk açılışta çok bekliyorum” — Python'suz pakette 3 kat hız

Boş önbellekle ilk okumanın yaklaşık %80'i sıkıştırılmış Codex kayıtlarını saf Python ile açmaya gidiyordu (Windows'ta 19,2 saniyelik Codex okumasının 15,3 saniyesi). Python 3.14'ün yerleşik zstd çözücüsü aynı baytları 40 kat hızlı üretiyor.

Kullanıcının izniyle resmî Windows CPython 3.14.10 gömülü paketi python.org'dan indirildi:
- **Doğrulama:** SHA-256 değeri sürüm sayfasındakiyle aynı; içindeki bütün programlar geçerli PSF/Microsoft imzalı.
- **Derleme:** Derleme aracı bu yapıyı da kabul edecek biçimde uyarlandı ve Python'suz aday yeniden derlendi (7,8 MB ZIP).

| Python'suz aday, bu bilgisayarın gerçek kayıtları, boş önbellek | İlk okuma (3 ölçüm) | Önbellekli okuma |
|---|---:|---:|
| CPython 3.12 (önceki) | 23,0–23,1 sn | 2,6 sn |
| CPython 3.14.10 | **7,2 sn** | 2,1 sn |

- **Sonuçların tutarlılığı:** Altı koşunun hepsinde toplamlar birebir aynı.
- **Testler:** Resmî Windows 3.14.10 ile 236/236 geçti.
- **Paket akışı:** Paketteki küçültülmüş çalışma ortamıyla sayfa, okuma, dışa aktarma ve kapatma akışı geçti.

[Ölçüm ve kanıtlar](../reports/first-read-v1/REPORT.md).

**Sınır:**
- Tek bilgisayarın ölçümü.
- Python 3.13 ve eskisini `zstandard` olmadan kullananlar için ilk okuma hâlâ yavaş.
- Codex ayrıştırması (~4 sn) ve Claude okuması (~2,4 sn) değişmedi.
- Temiz makine ve imza işleri açık.

## 28 Ekim: 0.2.5 — kalan açıklar, Linux ve Python'suz Windows adayı

Codex'in yarıda kalan turu Claude tarafından tamamlandı. [Kanıt, yöntem ve sınırlar](../reports/completion-v1/REPORT.md).

- **Ağ biçimli önbellek hedefi kapandı.** `PLER_CACHE_DIR` ya da varsayılan önbellek tabanı ağ yolu ise veya kullanıcı bağlantısı/junction üzerinden geçiyorsa, önbellek ve kota dosyası kapatılıyor; orada okuma/yazma denenmiyor. Taklitli probda dört ağ yazımında deneme sayısı 8'den 0'a indi. Gerçek ağ erişimi yapılmadı.
- **Geçmiş sınırları dürüst.** Ebeveyn/çocuk birikimli sayaçlar, kayıtsız ebeveyn, çelişkili, kendini gösteren ya da döngülü ebeveyn ve yalnız özetleme işareti taşıyan dosya artık eksiksiz sayılmıyor. Yalnız iptal, araç, kota ya da tamamlama içeren oturumlar kaybolmuyor. Genel fork/compaction uzlaştırması hâlâ açık.
- **Yanlış alarm düzeltildi.** Codex'in ilk kuralı, gerçek kayıtlarda alt ajanların aynı oturumdaki ana iş parçacığını ebeveyn göstermesini "çelişki" sayıyordu. Sabit 128 gerçek dosyada 4 oturum yanlışlıkla atıf belirsiz, 2'si token eksik görünüyordu. Bu 4 oturumun hiçbirinde oturum dışını gösteren ebeveyn yoktu. Oturum içi bağlar artık ebeveyn kanıtı sayılmıyor. Düzeltmeden sonra 0.2.4'e göre oturum, token, çağrı ve kalite bayrakları aynı.
- **"Benim sistemimde denenmemiş" kısmen azaldı.** Linux'ta (WSL2 Ubuntu, Python 3.14.4, standart kütüphane zstd çözücüsü) tam takım 236/236 geçti. İlk koşuda iki kusur çıktı ve düzeltildi:
  - Windows'a özgü `/\sunucu` yazımı Linux'ta ağ yolu sayılmıyordu.
  - Geçici klasör macOS'taki gibi işletim sisteminin kısayolu arkasındayken 236 testin 176'sı düşüyordu. PLER, macOS'ta `/var` ve `/tmp`, bazı Linux'larda `/home` gibi root'a ait sistem bağlantılarını reddediyordu. Bu bilgisayarlarda kayıtlar ve önbellek kullanılamaz kalırdı.
  - Artık macOS/Linux'ta root'a ait bağlantılar izleniyor; kullanıcı bağlantıları ve Windows'taki tüm bağlantılar eskisi gibi reddediliyor.
- **İlk gerçek macOS çalıştırması.** Kod özel bir GitHub deposuna yüklendi ve hazırlanan CI çalıştırıldı. Her iş testleri kaynaktan ve yeni ortama kurulmuş wheel'den koşturdu, sürümü denetledi ve paketi kaldırdı.
  - Windows Server 2025, Ubuntu 24.04 ve macOS 26 arm64'te Python 3.9, 3.12, 3.14 ve isteğe bağlı `zstandard`: 12 işin 12'si geçti.
  - macOS işleri GitHub'ın makine kapasitesi yüzünden ancak dördüncü denemede başlayabildi.
  - İlk koşuda Windows'ta tek bir test sürücü farkından düştü (kod D:, geçici klasör C:). Bu test hatasıydı; düzeltildi.
- **"Python kurmam gerekiyor" kısmen azaldı.** İmzasız, özel bir Windows x64 adayı derlendi: 6,0 MB ZIP, içinde CPython 3.12 ve `PLER.exe`. Bu bilgisayarda `PATH` üzerinde hiç Python yokken kendini denetledi, terminal raporunu verdi ve sunucuyu açtı. Temiz bilgisayar, imza ve dağıtım onayı açık.

Testler: Windows'ta Python 3.9 ve 3.12 ile 227/227, Linux'ta 236/236, tarayıcı mantığında 18/18, kurulmuş wheel'de 227/227. 0.2.5 yerel uygulamaya geçirildi.

**Hâlâ açık:** macOS ve Linux masaüstünde gerçek tarayıcı kabulü, Python'suz paketin temiz makinede denenmesi ve imzası, ilk okuma hızı, genel geçmiş tamlığı, kullanıcının kendi kısayolu arkasındaki kayıt klasörü (örneğin dotfiles ile bağlanmış `~/.claude`), Claude masaüstü kotası, gerçek profesyonel pilot, lisans ve dağıtım.

Claude masaüstü kotası: Durum satırı 26 Ekim'de kuruldu, ama iki günde hiç kota örneği oluşmadı. Masaüstü uygulaması bu komutu çalıştırmıyor görünüyor.

## 28 Ekim: 0.2.4 — proje kanıtı çelişkileri

Aynı Codex oturumunda yalnız ilk bağlam klasörü tutulunca dosya adı/sırası hangi projenin kesin doğru göründüğünü seçebiliyordu. Tüm geçerli oturum ve bağlam klasörü kanıtlarını değerlendiren düzeltme; aynı yerel Git kökü/yol eşdeğerliğini korurken farklı proje kanıtını bilinmiyor ve eksik atıf olarak ele alır. Kullanım projelere tahminen bölünmez. Son kaynakta iki Python sürümünde 188/188, tarayıcı mantığında 18/18 test geçti; kurulum ve yerel çalışma sonucu [karşı örnek, kapsam ve doğrulama kaydında](../reports/project-attribution-v1/REPORT.md) izlenir.

Kurulmuş pakette 63/63 kabul testi geçti; 0.2.4 yerel ekranda doğrulandı. Sabit 128 gerçek Codex dosyasının metadata karşılaştırmasında 22 oturumun token/çağrı sayıları ve atıf dışındaki alanları aynı kaldı; altı oturumun çelişkili proje atfı bilinmeyene döndü. Bu, genel geçmiş uzlaştırmasının tamamlandığı anlamına gelmez.

**Yeni ayrı açık:** Kayıt kökü UNC/junction koruması mevcut, fakat `PLER_CACHE_DIR` ağ hedefi olarak açıkça ayarlanırsa önbellek ve kota metadata'sı için o hedefte I/O deneniyor. Çevrimdışı taklitlerle kanıtlandı; gerçek ağ erişimi yapılmadı. Bu ortam ayarına bağlı yerellik açığı henüz düzeltilmedi. [Kanıt ve kapanış ölçütü](../reports/remaining-audit-v1/cache-path-review.md).

## 28 Ekim: 0.2.3 — ilk okuma iyileşti, hız işi açık

Sabit 131 dosyada ilk okuma 51,45 → 46,33 saniye (%9,96), önbellekli okuma 2,22 → 1,82 saniye (%17,84). Bütün oturum metadata'sı ve sorun listesi birebir aynı kaldı. Gerçek kullanım kaydını seçme ve önbellek yazımı hızlandı; sıkıştırma yardımcı tablosu küçültüldü. 128 sıkıştırılmış dosyanın açılmış baytları önceki sürümle aynı. İki Python sürümünde 177/177, tarayıcı mantığında 18/18 ve kurulmuş pakette 52/52 test geçti. [Ölçüm, testler ve sınırlar](../reports/cold-start-v1/REPORT.md).

Bu ölçüm boş PLER metadata önbelleğiyle, işletim sistemi disk önbelleği temizlenmeden yapıldı. Tek bilgisayarın ölçümüdür; genel açılış garantisi değildir. İlk okumanın yaklaşık 46 saniye sürmesi hâlâ kabul engelidir. Sayımın kalan geçmiş sınırları, kurulum, platformlar ve profesyonel pilot açık kalır.

## 28 Ekim: 0.2.2 — tek dosya uyarısı çözüldü

Gerçek uyarı dosyanın okunamamasından değil, iki yanıtın sıfırlanmış sayaçlı sekiz kopyasından kaynaklanıyordu. Aynı yanıtların tam eşleşen sağlam kayıtlarıyla dar uzlaştırma yapıldı: aynı dosyanın 2.120 çağrı ve 784.546.981 tokenı aynen kaldı; kaynak uyarısı 1'den 0'a indi. Eşleşmeyen/bozuk kullanımın uyarısı sürer, önbellek sağlam tanığın güncel varlığına göre yeniden değerlendirilir. Bağımsız Codex ilgisiz kimlik doğrulama kusuru da düzeltildi. [Kanıt ve sınırlar](../reports/log-warning-v1/REPORT.md).

Kalan zor sayım durumları, hız, kurulum, platformlar ve profesyonel pilot bu düzeltmeyle kapanmış sayılmaz. Eski raporlardaki tek dosya uyarısı, o tarihteki durumun tarihsel kaydıdır.

## 28 Ekim: 0.2.1 kullanım düzeltmeleri

En kolay kalan kabul işleri ele alındı: diske alınan uydurma JSON özeti doğrulandı; indirme hazırlığı/yeniden indirme ve seçim tutarlılığı düzenlendi. Daha fazla gösterme ve yenileme/indirme sonrası klavye odağı düzeltildi. Dar ekranda tablo oklarla kaydırılıyor, filtreler tek sütuna iniyor. Yeniden başlatma bağlantısı aynı sekmede yeni erişimi tanıyor. [Kanıtlar ve sınırlar](../reports/usability-v1/REPORT.md).

Fiziksel telefon, ekran okuyucu, her tarayıcıda otomatik indirme ve genel erişilebilirlik uygunluğu doğrulanmış değildir. Aşağıdaki büyük kabul engelleri açık kalır.

## 27 Ekim: 0.2.0 düzeltme adayı

Aşağıdaki 0.1.2 bulguları tarihsel kanıt olarak korunmuştur. Bu turda kopya/birikimli/karma kayıt sayımı, güncellenen yanıtlar, belirsiz proje/model atfı, kopya istek/araç sayıları, geçersiz sayılar ve hatalı hata yüzdesi için regresyonlar eklendi. Somut karşı örneklerin sonuçları [çalışma raporunda](../reports/accounting-v1/REPORT.md). Yerel okuma erişimi ve rapor sürüm bilgisi de değişti. [Sayım ve erişim sözleşmesi](ACCOUNTING.md) yeni sınırları açıklar.

**Kapanmayan sınırlar:** Keyfi ebeveyn/çocuk, compaction ve eski geçmişin tam uzlaştırılması; sabit kimliği olmayan olayların güvenilir sayımı; hesap/çoklu hesap kapsamı; ilk okuma hızı; Python'suz imzalı kurulum; macOS/Linux'ta gerçek çalıştırma; gerçek profesyonel pilotta karar faydası; lisans, dağıtım ve destek. Belirsizlik görünür hale getirildi; bunlar çözülmüş sayılmaz.

## 0.1.2 değerlendirmesinde bulunan yeni açıklar

Bu önceki değerlendirmede ürün kodu değiştirilmedi. Mevcut 124 test yeniden geçti; aşağıdaki yeni karşı örnekleri kapsamıyor. 0.1.2 için açık bulgulardı; 0.2.0 adayı yukarıdaki durumu ilerletir. Frekansları gerçek müşteri kayıtlarında ölçülmedi; geçici sentetik kayıtlarla tekrar üretildi. [Kanıt](../reports/professional-audit-v1/observations.json), [betik](../reports/professional-audit-v1/probe.py), [inceleme sınırları](../reports/professional-audit-v1/REPORT.md).

| Öncelik | Yeni açık bulgu | Kapanış ölçütü |
|---|---|---|
| Yayın engeli | Aynı kimlikli, kopyalanmış eski Codex birikimli oturumu 100 yerine 200 token sayılıyor; uyarı yok. | Oturum kimliği, aktif/arşiv kopyası ve ebeveyn/çocuk geçmişi için açık sayım kuralları ve bağımsız beklenen toplamlar. |
| Yayın engeli | Birikimli toplamla çağrı kaydı aynı dosyada varsa örnekteki 150 yerine 50 sayılıyor; kapsam uyarısı yok. | Sürüm ve kayıt türüne göre uzlaştırma; açıklanamayan farkı eksiksiz toplam gibi göstermeme. |
| Yayın engeli | Aynı yanıtın 100 ve 150 tokenlık kopyalarında ilk değer tutuluyor. | Gerçek kaynak sözleşmesiyle yinelenen/güncellenen yanıt kuralı; tutarsızlığı işaretleme. |
| Yayın engeli | Codex ve Claude kopya yanıtının proje sahibi okuma sırasıyla değişebiliyor. | Dosya adından/sırasından bağımsız, belirsizlikte açıkça bilinmeyen atıf. |
| Yayın engeli | Çok modelli eski Codex oturumunun 150 tokenının tamamı son modele yazılabiliyor. | Kanıtlanabilen model dağılımı; kanıt yoksa model atfını bilinmiyor gösterme. |
| Yayın engeli | Kopyalanmış bir Codex isteği ve araç çağrısı iki kez sayılırken token bir kez sayılıyor. | İstek/araç kimlikleri ve miras alınan geçmiş için aynı kapsamda tutarlı sayım. |
| Yayın engeli | JSON geçerli olsa da hatalı türde/negatif token değerleri sessizce sıfıra çevrilebiliyor; dosya uyarısı yok. | Tür, aralık ve alanlar arası tutarlılık doğrulaması; bilinmeyeni sıfır göstermeme. |
| Karar kalitesi | Bir istek, iki hata ve bir kesinti örneği “isteklerin %300'ü” diye sunuluyor. | Hata olayı ile benzersiz başarısız istek paydasını ayırma; uygun adlandırma. |
| Kurumsal kapsam | Yerel kullanım API'si aynı makinedeki süreçlere kullanıcı kimlik doğrulaması olmadan veri veriyor. Proje/Git yol koruması, özel yapılandırılmış ağ kayıt klasörlerini kapsamıyor. | Kişisel makine ve paylaşımlı makine için ayrı tehdit modeli; ağ kaynaklarının destek/kapsam kararı. İnternetten veri sızıntısı gerçekleştiği iddia edilmiyor. |
| Rapor güveni | Dışa aktarılan görünümde tarama zamanı var; uygulama, okuyucu veya şema sürümü yok. | Geçmiş raporun hangi kuralla üretildiğinin izlenebilmesi; sürümlü veri sözleşmesi. |

Önceki turlarda giderilen belirli kusurlar aşağıda korunuyor; bu yeni bulgular, bütün hesaplamaların doğrulanmış olduğu anlamına gelmediğini gösteriyor.

| Öncelik | İtiraz | Bu turdaki bulgu ve karşılık | Durum / kapanış ölçütü |
|---|---|---|---|
| P0 | “Ayarlarımı bozabilir.” | Komutunda `pler` ve `statusline` geçen başka bir durum satırı PLER'in sanılıp silinebiliyordu. Yalnız üretilen ayarın tam eşleşmesi kabul ediliyor. Onay beklerken değişen ayar korunuyor; yazma hatası anlaşılır biçimde dönüyor. | Somut kusurlar regresyonla giderildi. Taşınmış/eski kurulumun ayarı otomatik silinmez; belirsizlikte koruma tercih edilir. |
| P0 | “Eski sayıyı güncel kota gibi gösteriyor.” | Bir saat eski ölçümden dolma tahmini çıkabiliyordu. 30 dakika / 24 saat güncellik sınırı, geçmiş dolma zamanı denetimi ve açık sayfada saatten güncelleme eklendi. Eski yüzde tarihli bilgi olarak kalır, güncel çubuk ve uyarı kaldırılır. | Somut kusur giderildi. Anlık hesap verisi sağlandığı iddia edilmez. |
| P0 | “Rakamlarım eksik; haberim yok.” | Açma ve okuma ortası hataları, bozuk/yarım JSON ve geçersiz yanıt kimlikleri tek dosya uyarısına giriyor. Sağlam satırlar korunuyor; Codex önbelleğinde de uyarı sürüyor. Sabit kimlikli kopya Claude istekleri ve araç çağrıları bir kez sayılıyor. | Yeniden üretilen kusurlar giderildi. Her ajan sürümünün şeması için tamlık garantisi yok; kimliksiz kayıtları güvenle tekilleştirme açık. |
| P0 | “Bir bozuk sayı uygulamayı çökertebilir.” | NaN bağlam yüzdesi durum satırını çökertiyor; negatif/sonsuz kota kabul ediliyordu. Yüzde ve zaman doğrulaması, bozuk önbellek satırını atlama ve budama düzeltildi. | Yeniden üretilen durumlar giderildi. Her olası dosya bozulması için genel garanti verilmez. |
| P0 | “Önbellek bozulunca yanlış rakam gösterir veya açılmaz.” | Hatalı önbellek biçimi okumayı durdurabiliyordu. Biçim ve sağlama toplamı tutmayan girdiler özgün kayıttan yeniden kuruluyor; yazma hatası sağlam toplamı gizlemiyor. Tarihsiz ve tarihli oturumlar birlikte özeti çökertmiyor. | Somut kusurlar giderildi. Sağlama toplamı kazara bozulmayı yakalar; kötü niyetli yerel değişikliğe karşı güvenlik sınırı değildir. |
| P0 | “Bozuk sıkıştırılmış arşivi sağlam sanıyor.” | Eksik/yanlış sağlama toplamı, tutmayan içerik boyutu, yarım atlanabilir çerçeve ve boş sıkıştırılmış dosya kabul ediliyordu. Çerçeve sınırları, boyut ve varsa içerik sağlama toplamı doğrulanıyor. İsteğe bağlı hızlı okuyucu da her çerçevenin sonunu arıyor ve sonrakileri okuyor. | Tekrar üretilen beş durum giderildi. Kontrol toplamı olmayan kayıtta her değişikliği yakalama iddiası yok. Bu bilgisayarda hızlı eklenti ve Python 3.14 yok; gerçek bu yolların çalıştırılması açık. |
| P0 | “Kayıttaki klasör yolu ağ paylaşımını sorgulatabilir.” | Proje gruplaması UNC proje yolu için dosya sistemi sorgusu deniyordu. Ağ yolu hiç sorgulanmadan reddediliyor; sembolik bağlantı/junction üst klasörü ve Git işareti izlenmiyor. | Somut sorgu girişimi sentetik olarak tekrar üretildi ve sıfıra indi. Gerçek ağ bağlantısı denenmedi; düşmanca eşzamanlı dosya değişikliğine karşı tam güvenlik sınırı iddiası yok. |
| P1 | “Veri yerine işe yarar karar istiyorum.” | Token başına para çağrıştıran başlık netleştirildi; kısmi dolar sayacı ve günlük harcama sanılabilen `days` dizisi terminal JSON'undan çıkarıldı. Dönemin tüm oturum toplamını seçtiği metinde ve JSON'da belirtiliyor. | Gerçek tasarruf / karar faydası kanıtı açık. Yüksek token doğrudan israf sayılmaz. |
| P1 | “Ekran gereksiz ayrıntılarla dolu.” | Git kartı temel sayılardan sonra, kapalı bir ayrıntı oldu. Git olmayan oturumlarda gösterilmiyor. Kullanılmayan ajanın kurulum ipucu kaldırıldı. Boş ekranda sıfır kartları gizleniyor; mevcut kota verisi boş filtrede de görülebiliyor. | Düzenleme yapıldı; profesyonel kullanıcıyla görev tamamlama / anlaşılabilirlik doğrulaması açık. |
| P1 | “Aynı kısa kodu taşıyan satırları ayıramıyorum.” | Gerçek ekranda farklı kaynak kayıtlarının aynı ajan kimliğini taşıyabildiği görüldü. Görünen satır kodu kaynak kimliğini de tek yönlü özetine katıyor; yerel yol dışa aktarılmıyor. | Tekrarlanan ajan kimliği senaryosu giderildi. Kayıt taşınırsa kod değişebilir; sekiz karakterlik gösterim matematiksel benzersizlik garantisi değildir. |
| P1 | “Claude masaüstü kotamı göstermiyor.” | Durum satırı bağlantısı terminaldeki Claude Code içindir. Masaüstünde veri geldiği doğrulanmadı; ekrandaki kurulum metni bu sınırı söylüyor. | Açık. Gerçek masaüstü örneği veya açıkça desteklenmeyen ürün kapsamı gerekir. |
| P1 | “Python kurmam gerekiyor; uygulamayı açamıyorum.” | Kaynak kurulumunun hangi klasörden yapılacağı düzeltildi; bağımlılıksız wheel denetleniyor. | Açık. Python'suz dağıtım ve temiz bilgisayarda kurulum/kaldırma kabulü gerekir. |
| P1 | “Benim sistemimde denenmemiş.” | Bu bilgisayarda Windows, Python 3.9 ve 3.12 var. **28 Ekim:** CI'da Windows, Ubuntu ve macOS 26 üzerinde Python 3.9, 3.12 ve 3.14 ile kaynak ve kurulmuş paket testleri geçti. | Büyük ölçüde kapandı. Kalan: her sistemde gerçek tarayıcı kabulü. |
| P1 | “İlk açılışta çok bekliyorum.” **28 Ekim:** Python'suz aday CPython 3.14 ile 23,1 → 7,2 sn; Python 3.14+ veya `pler[fast]` kullananlar zaten hızlı. | Aynı 133 sabit dosyada tam okuyucu ölçümü: ilk okuma 31,52 → 31,02 sn; önbellekli okuma 2,73 → 1,14 sn. Claude da metin içermeyen önbelleğe geçti. Oturum metadata özeti birebir aynı. Güncellemeden sonra doğrulama yardımcıları değişince önbellek bir kez yenilenir. | Yenileme iyileşti. İlk okuma hâlâ açık; tek bilgisayardaki bu koşu genel hız garantisi veya anlamlı ilk açılış kazancı değildir. Gerçek sunucunun tamamı ayrıca denetlenir. |
| P1 | “Geçici okuma hatası önbellekte takılı kalır.” | Erişimi yarıda kesilen Claude dosyası önbelleğe alınmaz; bozuk satır ile erişim hatası aynı dosyada olsa da sonraki okuma tekrar dener. Okunurken büyüyen dosya eski imzayla kaydedilmez. Hatalı önbellek yazımının geçici dosyası temizlenir. | Senaryolar regresyonla giderildi. Tüm dosya sistemlerinde atomik işlem veya eşzamanlı mutasyona tam garanti verilmez. |
| P1 | “Paylaştığım özet özel bilgiler taşır mı?” | Terminal JSON'u da ekranın açık alan listesine geçti: kaynak yolları, ham kimlikler, dal ve düzenlenen dosya yolları çıkarıldı. Kaynak hataları yol içermez. İstek, yanıt ve komutlar özetlere alınmaz. | Yeniden üretilen sızıntı giderildi. Kısa proje adları, zaman, model ve sayılar hâlâ özel olabilir; anonim paylaşım iddiası yok. |
| P1 | “Hangi sürümü kullanıyorum; güncellemede ekran karışır mı?” | Sürüm 0.1.2'ye ilerledi; JSON ve önbellek değişiklikleri değişiklik kaydında. Açık sunucu başladıktan sonra değişen sayfa dosyalarını karıştırmıyor; yeni sürüm için yeniden başlatılıyor. | Aynı sunucuda eski/yeni dosyaların karışması sınandı. Otomatik güncelleme veya imzalı dağıtım sağlanmış sayılmaz. |
| P1 | “ccusage yerine neden bunu kullanayım?” | İki ajanın görünümü mevcut; Git'in ilk eşleştirmesinde gerçek örneklerde eşleşen olay çıkmadı. **28 Ekim (0.2.6–0.2.7):** Oturumlar düzenledikleri depoya bağlanıyor ve oturumdaki commit'lerin hâlâ dalda olup olmadığı görünüyor. Gerçek kayıtlarda 68 commit'in 68'i dalda; bu oturumlar tokenların yaklaşık %70'ini kullanmış. Kalan: gerçek bir profesyonelin bu bilgiyle karar verip vermediği. | Açık. Profesyonelin kendi işiyle, mevcut alternatife karşı tekrar kullanılma nedeni gösterilmeli. Yeni özellik sayısı bu soruyu kapatmaz. |
| P2 | “Yayın ve destek şartları belli değil.” | PyPI yayını, lisans ve imzalı kurulum henüz yok. | Açık. Yayın lisansı/adı, sürümleme ve destek kapsamı belirlenmeden “dağıtıma hazır” denmez. |

Bu tur gerçek Claude ayarı değiştirilmedi; model deneyi, ücretli ajan çağrısı, harici kota sorgusu veya yayın yapılmadı. Kanıtlar: [0.1.2 güvenilirlik ve hız raporu](../reports/reliability-v2/REPORT.md), [bozuk arşiv önce](../reports/reliability-v2/corrupt-before.json), [sonra](../reports/reliability-v2/corrupt-after.json), [sabit arşiv ölçümü](../reports/reliability-v2/final-benchmark.json). Önceki tur: [0.1.1 raporu](../reports/company-readiness-v1/REPORT.md).

Sonraki çalışma da bu listeyi izler: bir itiraz seç, somut başarısızlık kur, düzelt, tekrar dene, kalan sınırı yaz. Kullanıcı yön değiştirmedikçe yeni özellik planı açılmaz.
