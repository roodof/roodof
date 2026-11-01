# PLER

[English](README.md) · **Türkçe**

Claude Code ve Codex'in ne kullandığını, bilgisayarındaki kendi kayıtlarından gösterir: hangi projede, hangi modelle, ne kadar token; kotanın nereye gittiği; harcamanın nerede biriktiği.

- **Model çağırmaz.** Ölçmek için tek bir token harcamaz.
- **Hiçbir şey göndermez.** İnternete bağlanmaz; sayfa yalnız bu bilgisayardan açılır (`127.0.0.1`).
- **Ajan kayıtlarını değiştirmez.** PLER üst bilgi önbelleği tutar; istek, yanıt, komut ve araç çıktısı ekrana ve önbelleğe girmez. İsteğe bağlı durum satırı, Claude Code ayarını onaydan sonra ve yedek alarak değiştirir.
- **Her dilde çalışır.** Ajan kayıtlarını inceler. Yerel Git satır gözlemi ayrıca commit'lerdeki dosya adlarını ve içeriklerini bellekte okur; yalnız sayılar saklanır veya gösterilir.

## Windows betasında ilk adımlar

[PLER sitesinden](https://pler-local-usage.oguzay5555.chatgpt.site/tr/) Windows x64 paketini indir, ZIP dosyasının tamamını klasöre çıkar ve `PLER.exe` dosyasını aç. Python pakete dahildir. `PLER-Demo.cmd` yalnız uydurma kayıtları açar; kendi seçili yerel kayıtların için demoyu kapatıp `PLER.exe` dosyasını aç. `PLER.cmd` terminal girişidir.

İlk iş grubunu oluşturmak, boş kayıt durumunu anlamak, gizlilik, kaldırma ve yerel veri saklama için uygulamadaki **Yardım** bölümünü aç. Destek: plersolutions1st@gmail.com. Beta imzasızdır; temiz makine kabulü açıktır. Otomatik güncelleme dağıtımı yoktur.

## Kurulum

Python 3.9 veya üstü yeter; başka bağımlılık yoktur.

Bu kaynak deponun kökünden (`pyproject.toml` dosyasının bulunduğu klasör):

```
pipx install .
```

`pipx` yoksa `pip install .` da olur. Bu depo daha büyük bir çalışma klasöründe `product/` adıyla duruyorsa dış klasörden `pipx install ./product` kullan. Genel PyPI paket adı henüz onaylanmadı; doğrulanmamış genel bir paket yerine verilen kaynağı veya tam aday wheel dosyasını kur.

## Kullanım

```
pler
```

Tarayıcıda **Kullanımım** sayfası açılır. Kapatmak için sayfadaki **Kapat** düğmesi ya da terminalde Ctrl+C.

Sekmeyi elle açarken başlangıçta yazılan tam adresi kullanın. Bu adres çalışan rapora erişim sağlar; yeniden başlatınca değişir, paylaşmayın. Sayfa erişim bölümünü görünen adresten kaldırır. Raporu okumak ve indirmek de bu erişim anahtarını gerektirir. Ürün kişisel ve yereldir; ekip hesapları ve paylaşımlı sunucu kurulumu desteklenmez.

**Dil:** Sayfa tarayıcının diliyle açılır; üstteki düğmeyle İngilizce ve Türkçe arasında geçilir. Terminal Türkçe bir sistemde Türkçe, diğerlerinde İngilizce konuşur; `PLER_LANG=tr` ya da `PLER_LANG=en` ile seçilebilir.

**Çevrimdışı yardım:** Sayfadaki Yardım bağlantısı, kurulu paketle birlikte gelen sürümlü Türkçe/İngilizce açıklamayı açar. Mahremiyet, güvenli önbellek sıfırlama, saklanan geçmiş, dönemler, kalite ve destek anlatılır. Sayım sözleşmesi de pakettedir; kaynak klasörü veya İnternet bağlantısı gerekmez.

```
pler report             # son 30 günde etkin oturumlar
pler report --days 0    # bütün kayıtlar
pler report --json      # makinenin okuyacağı biçim
pler demo               # uydurma kayıtlar ve uydurma bir Git deposuyla sayfa
```

**Kendi verin olmadan dene:** `pler demo`, uydurma Claude Code ve Codex kayıtlarıyla küçük bir Git deposunu PLER'in önbellek klasöründeki `demo` klasörüne yazar. Sayfa yalnız bu klasörü okur ve en üstte verilerin uydurma olduğunu söyler. Denemede şunlar görünür:
- iki ajan ve birkaç proje;
- kota tahmini;
- bir veri kalitesi uyarısı;
- dalda olan ve olmayan commit'ler.

Her **Kayıtları yeniden oku**, verileri şimdiki zamana göre yeniden kurar. Windows'un Python'suz paketinde aynı iş için `PLER-Demo.cmd` var.

## Oturumları yaptığın işe göre düzenle

**İşlerim** bölümünde gerçek bir işe ad verip o işte kullandığın Claude Code ve Codex oturumlarını bağlayabilirsin. İş oluşturduktan sonra oturum ayrıntısından bağlantı ekle; bir oturum birden fazla işe bağlanabilir. İşin adını değiştirmek veya bağlantıyı kaldırmak ajan kayıtlarını ve oturum değerlendirmelerini değiştirmez. İşi silmek yalnız o işi ve bağlantılarını kaldırır; eski özel yedeğinde kopyası kalabilir.

İş ara toplamları mevcut dönem/ajan/proje seçimini izler ve seçilen oturumların tamamını kapsar. İki işe bağlı oturum iki ara toplamda da görünür; işlere bağlanan ortak toplamda bir kez sayılır. İş ara toplamlarını birbirine ekleme. Bu gruplama bir oturumun tokenlarını farklı işlere dağıtmaz; tek işin maliyetini, tamamlanmasını veya kalitesini kanıtlamaz.

Seçimdeki oturumlar, filtre dışındaki bilinen oturumlar ve artık bulunamayan bağlantılar ayrı gösterilir. Kaynak taşınır veya oturum kimliği değişirse bağlantı kendiliğinden başka oturuma taşınmaz. Eksik bağlantılar incelemek veya kaldırmak için görünür kalır; bunlara kullanım uydurulmaz.

**Hedef ve sonuç:** isteğe bağlı hedeflenen sonucu, kendi tamamlanma değerlendirmeni ve sonuç/kalan iş notunu kaydedebilirsin. Bunlar filtrelerden bağımsız olarak işin tamamına aittir. Seçili bağlı oturumların test/derleme ve Git gözlemleri ayrı gösterilir; tamamlanma veya kalite puanı belirlemez. Taslaklar filtre ve dil değişiminde korunur; çakışan düzenleme, sonraki açık kayıttan önce inceleme gerektirir.

**Haftalık takip:** iş içindeki “Dene ve takip et” bölümünden bir değişiklik ve sabit yedi günlük başlangıç kaydı oluştur. Sonraki yedi gün bitince kayıtları yeniden oku, yeni oturumları bağla ve incelemeyi açıkça kaydet. Her araç/proje/model grubunda dönem başına en az üç oturum ve benzer görev değerlendirmesi gerekir. Eksik kaynak, değişmiş geçmiş, farklı model veya bilinmeyen görev koşulları sonucu açık bırakır. Token farkı tasarruf veya kalite artışı kanıtlamaz. Takipler özeldir, işle birlikte yedeklenir ve normal rapora girmez.

İş adları, hedefler, sonuç notları ve opak oturum bağlantıları yalnız bu bilgisayardaki `work-items.json` dosyasında saklanır, özel yedeğe girer. **Normal JSON raporuna, proje gizleme kapalı olsa da eklenmez.** Bunlar senin girdiğin özel üst bilgidir; gruplama için istek veya yanıt toplanmaz. Eski iş dosyaları değiştirilmeden okunur; gerçek düzenleme, eski sürümlerin okuyamadığı iş biçimi 3 ile kaydeder. Geri dönüş için denetlenmiş uyumlu yedeğini koru. Deneme modundaki işler bellekte kalır ve deneme kapanınca kaybolur.

## Doğrulanmış özel yedek ve kurtarma

**Yerel geçmiş ve okuma önbelleği** bölümünden özel yedek indirilebilir ve seçilen yedek bu bilgisayarda kontrol edilebilir. Yedek, rapor filtrelerinden bağımsız olarak saklanan geçmişi, oturum değerlendirmelerini, saklama tercihini, Claude kota örneklerini ve iş adlarınla bağlantılarını kapsar. Özgün ajan kayıtlarını okumaz; okuyucu/kod önbellekleri, deneme verisi, ajan ayarları ve erişim anahtarı alınmaz.

```text
pler backup create "gecmisim.pler-backup.zip"
pler backup check "gecmisim.pler-backup.zip"
pler backup restore "gecmisim.pler-backup.zip" --to "kurtarilan-gecmis"
pler --data-dir "kurtarilan-gecmis"
```

Taşınabilir paketin terminal komutlarında `pler` yerine `PLER.cmd` kullanılır. Geri yükleme yalnız üst klasörü var olan **yeni bir yerel klasör** oluşturur. Yedeği tamamen doğrulayıp tam klasörü hazırlar; var olan hedefi reddeder ve mevcut veriyi korur. Sonraki her açılışta bu klasörü `--data-dir` ile açıkça seç; yedek komutları da buna dahildir. Çalışan profil kendiliğinden değişmez. `--json` özel yol/kimlik yerine sayılar ve sabit hata kodları döndürür.

**Yedek özeldir ve şifreli değildir:** gizlenmiş JSON'dan farklı olarak özgün yolları ve saklanan kimlikleri içerir. Özel yerde tut; yalnız kendi güvendiğin yedeği kullan. SHA-256 hasarı bulur, kaynağın güvenilirliğini doğrulamaz. Bilinmeyen biçim, tutmayan sağlama toplamı, beklenmeyen dosya ve aşırı boyut reddedilir; kontrol için seçilen dosya yerel sunucunun belleğinde kalır. Kurtarma özgün kaynak köklerini, zamanları ve okuyucu anahtarlarını korur: aynı bilgisayarda aynı kökleri seç. Taşınmış kaynak veya başka bilgisayar otomatik eşlenmez; saklama sınırları geçerlidir, eski kota güncel hale gelmez ve eski okuyucu arşivi uygun durumlarda doğrulanamamış kalır. Tam yönergeler kurulu çevrimdışı yardımdadır.

## Windows'ta WSL kayıt klasörleri

PLER WSL dağıtımlarını otomatik aramaz. Dağıtımı kendiniz açıp kayıt kökünü `CLAUDE_CONFIG_DIR`, `CODEX_HOME`, `--claude-dir` veya `--codex-dir` ile açıkça seçin. Hem `\\wsl.localhost\Ubuntu\...` hem `\\wsl$\Ubuntu\...` desteklenir. Ortam değişkenleri ajanın ana/ayar klasörünü, komut seçenekleri projects/sessions klasörünü gösterir.

PLER okumadan önce yalnız Windows System32 içindeki sabit `wsl.exe --list --running --quiet` durum sorgusunu çalıştırır. Kapalı veya durumu öğrenilemeyen dağıtım açıklamayla atlanır; başlatma, kurulum veya otomatik bulma komutu kullanılmaz. Okuyucu aşamasından önce durum yeniden denetlenir. Durum kontrolü ile Windows dosya erişimi arasında dağıtımın başka bir işlem tarafından kapatılmasına karşı atomik yalıtım sağlanmaz.

Git/proje ve önbellek yolları ile kayıt klasörünün içindeki bağlantılar daha sıkı kurallarını korur. Yerel bir bağlantı taramayı sessizce WSL'ye ya da ağ paylaşımına yönlendiremez. Gerçek UNC, aygıt ve birim yolları sorgulanmadan reddedilir.

Alternatif olarak PLER'i WSL içinde çalıştırıp Windows kayıt klasörlerini `/mnt/c` üzerinden aynı seçeneklerle seçebilirsiniz. Önbelleği Linux ortamında tutun. Bu yol normal yerel bağlama yollarını kullanır; Windows WSL durum sorgusu gerekmez.

## Ne gösterir

- **Durumun:** Kayıtlardan çıkan, dayanağı yanında yazan gözlemler. Örneğin uzun oturumlarda her model çağrısının kısa oturumlara göre kaç kat token harcadığı, ya da harcamanın çoğunun tek bir oturumda toplanması.
- **Kota:** Codex'in ve Claude Code'un 5 saatlik ve haftalık kotasının en son nerede olduğu, mevcut hızla sıfırlanmadan dolup dolmayacağı. Claude Code için bir kez [durum satırını](#claude-code-kotası) açman gerekir.
- **Kota uyarısı:** Bir sınır dolduğunda ya da mevcut hızla sıfırlanmadan bir saat içinde (haftalık sınırda bir gün içinde) dolacaksa sayfanın üstünde uyarı çıkar. **Kotayı canlı izle** açık sayfanın kayıtları 5 dakikada bir yeniden okumasını sağlar; sen yazarken ya da bir pencere açıkken okumaz. Her okuma biraz işlemci zamanı kullanır (bu bilgisayarın büyük geçmişinde değişiklik yoksa yaklaşık 1 sn, bir ajan yazdıktan sonra 10–13 sn). **Masaüstü bildirimleri** tarayıcı izin verdikten sonra her yeni uyarıyı bir kez gösterir. İki seçim de yalnız bu tarayıcıda hatırlanır.
- **Toplamlar:** Token bileşimi: yeni girdi, önbellekten okunan, önbelleğe yazılan ve çıktı. Önbellek dışı miktar ayrıca yazılır, çünkü ajan tokenlarının büyük kısmı aynı bağlamın yeniden okunmasıdır.
- **Projeler, modeller, oturumlar:** Oturumlar git deposuna göre gruplanır. Geçici klasörlerdeki oturumlar tek bir grupta toplanır.
- **Oturumlarını bul:** Proje, model veya kısa oturum koduyla ara. En son etkinlik, başlangıç, token kullanımı ya da hata ve kesinti sayısına göre sırala. Her satırın kendine ait kodu, başlangıcı ve son etkinliği vardır.

![Uydurma örnek kayıtlarla oturum arama ve sıralama](docs/sessions.jpg)

Arama yalnız oturum listesini daraltır. Sayfanın üstündeki özet ve indirilen JSON, dönem / ajan / proje seçimini izler. İndirilen özette liste aramasının dışındaki oturumlar da bulunabilir.

**Kayıtlı kullanım ve plan fiyatları:** son 30 günün tarihli yanıtlarının API liste fiyatı karşılığı, seçilen/kayıtlı planın aylık liste fiyatıyla birlikte gösterilir. Sayfa filtrelerinden bağımsız olarak seçili kaynak klasörleri ve projelerin tamamı kullanılır. Gerçek ödeme ve eksiksiz hesap geçmişi doğrulanmaz. Eksik veya fiyatlanamayan kayıtlar ücretsiz kullanım ya da geçişte tasarruf anlamına gelmez. Koşullu küçük plan sınırı karşılaştırması için en az 14 güne yayılan 14 ayrı UTC gününde güncel ve tutarlı gözlem, en fazla iki günlük örnek aralığı gerekir; bu, küçük planın yeteceğini kanıtlamaz. Bilinen kaynak, fiyat, kullanım, plan değişimi veya hesap kapsamı sınırları dayanağı olmayan sonuçları engeller. Codex plan adı saklanan kayıtlardan gelir; Claude seçimi bu bilgisayarda kalır. Fatura hesabı sorgulanmaz.

**API liste fiyatıyla**, kayıtlı yanıtların sağlayıcıların yayımlanmış standart fiyatlarıyla ne tutacağını gösterir. Fiyatlar tarihleriyle birlikte pakete gömülüdür; her yanıt kendi modeli ve istem büyüklüğüyle fiyatlanır. Bunu aboneliğine ödediğin tutarla karşılaştır; fatura değildir. Eksik model fiyatı, bilinmeyen önbelleğe yazma süresi veya çelişen fiyat bilgisi bir yanıtı fiyatlama dışında bırakabilir; tokenları toplamda kalır ve fiyatlanan pay gösterilir. Bakım için [uyumluluk kaydı](docs/COMPATIBILITY.md), desteklenen örnekleri ve tarihli fiyat kontrollerini tutar.

**İşe yaradı mı?** Bir oturumu tek tıkla **İşe yaradı** ya da **Boşa gitti** diye işaretle (listede veya ayrıntısında). PLER seçimdeki tokenları ve liste fiyatı karşılığını değerlendirmeye göre toplar; böylece boşa giden oturumların neye mal olduğunu görürsün. Değerlendirmeler yalnız bu bilgisayarda saklanır; PLER hiçbirini tahmin etmez.

**Ajanların çalıştırdığı testler ve derlemeler.** PLER, ajan kayıtlarındaki test ve derleme komutlarını tanır ve her oturumda görünen son çalıştırmanın nasıl bittiğini gösterir. Komut metni yalnız bellekte okunur, hiçbir yerde saklanmaz. Ajan çıktıyı başka bir komuta aktardıysa (örneğin `| tail`) çıkış kodu testin kendisine ait olmaz; sonuç görünmüyor diye gösterilir.

**Dönem içindeki tarihli kullanım**, tam, belirsizliği giderilmiş ve zamanlı yanıt kayıtlarının ayrı, temkinli görünümüdür. Birikimli toplamlar ve çözülemeyen geçmiş tarihlere dağıtılamaz; kapsam sayılarıyla dışlanır. Aralık taramanın sabit gözlem zamanında biter. Seçilen etkin oturumların tam toplamının yerine geçmez ve hesabın eksiksiz kapsandığını kanıtlamaz. Sayfa ve terminal bunu yalnız seçilen her oturumun kullanımı tarihlenebildiğinde gösterir; aksi hâlde JSON dışa aktarımı kapsam sayılarıyla taşır.

Özet hazırlanırken indirme düğmesi durumu gösterir. Hazırlanan dosya için **Yeniden indir** bağlantısı görünür kalır. Kaydedildiğini tarayıcı indirmelerinden kontrol edin. Ana filtreleri değiştirmek veya kayıtları yeniden okumak eski bağlantıyı kaldırır. Dar ekranda diğer sütunlar için tablo alanına odaklanıp sol/sağ oklarını kullanabilirsiniz.

Oturum ayrıntısındaki **kayıt aralığı**, ilk ve son olay arasındaki zamandır; beklemeleri de içerir. **Çalışma süresi** yalnız ajan kaydettiyse gösterilir. Dosya düzenleme sayısı, değişikliklerin Git'te korunduğunu veya işin tamamlandığını kanıtlamaz.

**Veri kalitesi:** Kopya yanıtlar sayım öncesinde uzlaştırılır. Kanıtlanamayan model/proje atfı bilinmiyor gösterilir. Geçersiz kayıtlar ve uzlaştırılamayan birikimli/dallanmış/bağlamı özetlenmiş geçmiş açıkça işaretlenir; görünen toplam eksik olabilir. Bilinen toplam, hesabın tüm kullanımının kapsandığını kanıtlamaz. JSON, uygulama/okuyucu/şema sürümleriyle kalite işaretlerini içerir. Karar vermeden önce [sayım sözleşmesini](ACCOUNTING.md) inceleyin. Oturum uzunluğu karşılaştırmaları israfı veya tasarrufu kanıtlamaz.

## Sonraki düzenlemeler

Sayfa ve `pler report`, bir oturum bittikten sonraki yedi gün içinde başka bağımsız bir oturumun aynı düzenleme hedefini kaydettiğini gösterir. Gözlemi açınca en fazla beş çift görünür: ajanlar, kısa oturum kodları, oturum sınırları arasındaki süre ve her oturumun bütün kayıtlı tokenları. Bunlar tekrarlanan düzenlemenin maliyeti değildir. Hesaplama, önceden okunan üst bilgiyi kullanır; dosya ya da Git sorgusu yapmaz.

Dönem/ajan/proje filtreleri önceki oturumları seçer; sonraki oturum kanıtı, diğer ajanlar dahil seçilen kayıt klasörlerinin tamamından gelir. Gözlem sonu, kayıtlar yeniden okunana kadar sabittir. Yakın tarihli eşleşmeyen oturumların takibi beklemededir. Eksik hedefler, bağımsızlığı belirsiz geçmişler, çakışan zamanlar ve eski ya da doğrulanamayan arşiv kanıtı nedenleriyle birlikte dışlanır. Windows sürücü yollarında harf büyüklüğü ayrılmaz; POSIX yollarında ayrılır. Farklı yol adları, taşıma, başarısız düzenleme, silme ve yeniden oluşturma dosya kimliğini sınırlar. Bu gözlem israfı, tasarrufu, nedeni ya da kaliteyi kanıtlamaz. [Sabit tanım](ACCOUNTING.md#preregistered-subsequent-edit-observation-0212).

## Yerel Git hareketleri

Oturumu açınca, ilk ve son kaydı arasındaki yerel Git hareketleri de görünür: commit, commit düzeltmesi, checkout, reset, merge ve rebase. O sürede kaydedilen commit'lerin hâlâ bir dalda olup olmadığı da işaretlenir. Aynı anda başka kişiler ve ajanlar da çalışmış olabilir; bu kayıtlar yazarı kanıtlamaz. Bir hareket birden fazla oturumla eşleşebilir; oturum sayılarını toplayarak benzersiz commit sayısı çıkarılamaz.

**Kayıtları yenile** sırasında her oturumun bağlı olduğu depoların `.git/logs/HEAD` dosyası kontrol edilir. Bir depo şu durumlarda bağlı sayılır:
- oturumun çalışma klasörü o depodadır;
- oturum o deponun içindeki bir dosyayı düzenlemiştir. Claude Code'un düzenleme araçları ve Codex yamaları hedef dosyalarını kayda geçirir.

Böylece üst klasörde başlatılan bir ajan da değiştirdiği depoya bağlanır. Depo yolları yalnız bellekte tutulur; sayfada yalnız kaç depoya bakıldığı görünür.

Oturum sırasında kaydedilen her commit için PLER, commit'in hâlâ yerel ya da uzak izleme dalında durup durmadığını da kontrol eder. Commit düzeltilmiş (amend), yeniden sıralanmış (rebase), reset edilmiş ya da silinen bir dalda kalmış olabilir. Bunun için commit nesnelerinin yalnız ebeveyn bağları ve zamanları okunur; isim ve mesaj okunmaz. `gitdir` dosyası kullanan worktree ve alt depolar desteklenir. Filtre değiştirmek Git dosyalarını yeniden okutmaz.

Güncel HEAD geçmişinde duran bu commit'ler için PLER, ekledikleri satırların kaçının HEAD'de hâlâ yerinde olduğunu da sayar. Değişen dosyaları Git'in kendi nesnelerinden yalnız bellekte okur ve yalnız sayıları tutar. Birleştirmeler, ilk commit'ler, ikili ve çok büyük dosyalar dışarıda kalır. Yerinde yeniden yazılan satır ya da taşınan dosya yerinde sayılmaz. Ayrıntı [hesap kurallarında](ACCOUNTING.md#lines-still-in-place-0219).

Ekrana ve JSON'a yalnız olay zamanı, sabit işlem türü, commit'in hâlâ dalda olup olmadığı, satır sayıları ve hedef commit'in ilk sekiz karakteri gider. Yazar adı, e-posta, commit mesajı, dal adı, dosya adları, dosya içerikleri ve Git ayarları dahil edilmez. Git komutu çalıştırılmaz ve bu bilgiler kalıcı önbelleğe yazılmaz. Kalıcı önbellekteki tek Git kaynaklı veri, ölçülen her commit için dört satır sayısıdır (`git-survival.json`). Her biri depo klasörü, HEAD ve commit'in tek yönlü özetiyle saklanır; böylece yeniden başlatmada aynı dosyalar tekrar okunmaz. Bu dosyaya yol, commit kimliği, ad ya da metin yazılmaz.

Yerel günlük silinmiş, süresi dolmuş veya kapalı olabilir. Her projenin günlüğünden en fazla son 1 MiB okunur; eşleşen en yeni 20 hareket listelenir, sayaç okunan bölümdeki tüm eşleşmeleri kapsar. Eksik tarihler ve kısmi ya da okunamayan geçmiş açıkça gösterilir. Sıfır eşleşme, iş yapılmadığı anlamına gelmez. Ağ yolları, sembolik bağlantılar, Windows junction'ları ve ev klasöründeki depolar atlanır. Bare depolar ve başka worktree'lerin hareketleri dahil edilmez.

## Claude Code kotası

Claude Code kota yüzdesini kayıtlarına yazmaz, ama Pro ve Max aboneliklerde durum satırına verir. Bir kez şunu çalıştır:

```
pler statusline --install
```

- **Ne olur:** Claude Code'un `settings.json` dosyasına hangi satırın ekleneceği gösterilir ve onayın sorulur. Önce dosyanın bir yedeği alınır.
- **Mevcut durum satırın varsa:** Ona dokunulmaz. Kendi betiğinden PLER'e nasıl veri verebileceğin yazılır.
- **Sonrasında:** Claude Code'un alt satırında `bağlam %37 · 5 saat %24 · hafta %41` gibi bir satır görünür. PLER bu satırdan yalnız kota yüzdelerini ve sıfırlanma zamanlarını, değiştiklerinde önbellek klasörüne yazar; konuşma, klasör ve oturum bilgisi saklanmaz.
- **Ekranda:** Claude Code kotası Codex'inki gibi "ne zaman dolar" tahminiyle görünür.
- **Geri almak için:** `pler statusline --remove`

Yalnız mevcut PLER kurulumunun ürettiği, değiştirilmemiş satır kaldırılır. Özel betik, düzenlenmiş satır veya başka kurulum yoluna işaret eden komut korunur. Onay beklerken değişen ayarın üzerine yazılmaz; kontrol ettikten sonra yeniden dene.

## Neyi okur

| Ajan | Klasör | Değiştirmek için |
|---|---|---|
| Claude Code | `~/.claude/projects`, `~/.config/claude/projects` | `CLAUDE_CONFIG_DIR` |
| Codex | `~/.codex/sessions`, `~/.codex/archived_sessions` (sıkıştırılmış olanlar dahil) | `CODEX_HOME` |

Bu klasörlerden birini başka bir diske taşıyıp yerine bir bağlantı (sembolik bağlantı veya Windows junction'ı) bıraktıysan, PLER bu bağlantıyı izleyip asıl yerel klasörü okur. Kayıt klasörlerinin içindeki bağlantılar ve ağ konumuna giden bağlantılar izlenmez.

Codex'in sıkıştırılmış kayıtları ek kurulum gerektirmeden okunur. Python 3.14 ve üstünde standart kütüphane bunları hızlı açar. Daha eski Python'da isteğe bağlı `zstandard` çözücüsü bu kaynak kopyadan `pip install ".[fast]"` ile kurulabilir; bu ekin kurulması bağımlılık indirebilir. İkisi de yoksa yerleşik çözücü çalışır ama yavaştır: bir test bilgisayarında geçmiş bir adayın ilk okuması 7 yerine 23 saniye sürdü. Bu değerler güncel aday veya başka geçmiş için hız garantisi değildir. Sonraki okumalar önbellekten gelir.

Bağımlılıksız okuyucuda tekrarlanan sayaç karşılaştırmaları ve önbelleğin yazılması iyileştirildi. Büyük arşivlerin ilk okunması hâlâ zaman alır; [hız doğrulaması](../reports/cold-start-v1/REPORT.md), boş PLER önbelleğiyle okumayı sonraki okumalardan ayrı ölçer.

[Önceki kaynak ölçek kontrolü](../reports/scale-v1/REPORT.md), 102,61 MiB açılmış yapay kayıt, 385 oturum, Git, 200 iş ve 20.000 bağlantı kullanır. Bir Windows bilgisayarında tam taramadan ilk kullanılabilir JSON raporuna ortanca süre Python 3.14'te 8,85 sn, Python 3.12/3.9 uyumluluk çözücüsünde 20,09/27,50 sn; değişmeyen yenileme 2,23–2,62 sn oldu. Sürüm başına üç koşuda sayım korundu ve sabit hedefler karşılandı. [Daha sonraki güncel kaynak kontrolü](../reports/compatibility-v1/REPORT.md) tek koşuda sayımı korudu fakat yenileme/Git/HTTP hedeflerini aştı; güncel performans kabulü açık. Görsel ilk boyama ölçülmedi, işletim sistemi disk önbelleği temizlenmedi; başka geçmiş/platform için hız garantisi değildir. Kaynak kabulü yayımlanmış paketten ayrıdır.

Değişmeyen Claude Code ve Codex kayıtlarının üst bilgileri önbellekte tutulur; sonraki okumada özgün konuşma tekrar ayrıştırılmaz. Yalnızca sonuna ekleme yapılmış düz bir kayıt, örneğin hâlâ çalışan bir ajanın kaydı, son okumanın bittiği yerden okunmaya devam eder. Bunun için dosyanın aynı dosya olması, ilk baytlarının ve o noktaya kadarki baytlarının değişmemiş olması gerekir; aksi hâlde kayıt baştan okunur. Sıkıştırılmış Codex kayıtları her zaman baştan okunur. Sayfa açık kaldığı sürece, hiçbir kaydın, bulunan klasörlerin ve PLER'in önbellek, arşiv ve saklama dosyalarının değişmediği bir yenileme önceki sonucu en çok bir saat yeniden kullanır. Önbellek sayı, zaman, kimlik, proje yolu ve araç üst bilgisi içerir; istek, yanıt, komut ve araç çıktısı metni içermez. Özel yerel üst bilgidir, anonim dosya değildir. Yeri:
- Windows: `%LOCALAPPDATA%\pler`
- macOS: `~/Library/Caches/pler`
- Linux: `~/.cache/pler`

`PLER_CACHE_DIR` ile yeri değiştirilebilir. Yeniden kurulabilen okuyucu önbellekleri, saklanan arşiv geçmişi ve kota örnekleri şu anda bu klasörü paylaşır. **Önbellek onarımı için klasörün tamamını silme.** `pler cache reset` yalnız bilinen Claude/Codex okuyucu önbelleklerini ve kod sayımlarını (`git-survival.json`) kaldırır; arşivi, kota örneklerini ve saklama tercihini korur. Silinmiş kaynak kayıtlarının üst bilgisi yalnız `metadata-archive.json` içinde kalmış olabilir; bu dosya silinirse yeniden kurulamaz.
Bozulmuş veya eski biçimdeki önbellek girdileri özgün kayıttan yeniden okunur. Sağlama toplamı kazara değişiklikleri yakalar; önbelleği ve sağlama toplamını birlikte değiştirebilen birine karşı koruma değildir.
Okuyucuyu veya doğrulama yardımcılarını değiştiren güncellemeden sonra ilgili önbellek ilk okumada yeniden kurulur. Okunurken büyüyen ya da erişimi yarıda kesilen dosya sonraki okumada tekrar denenir. Önbellek değiştirilemezse önceki dosya korunur; izin verildiği sürece geçici dosya temizlenir.

### Kayıtlar silindikten sonra geçmiş

Claude Code varsayılan olarak 30 günden eski konuşmaları siler. Aylık karşılaştırmalar sessizce küçülmesin diye PLER, çıkardığı üst bilgiyi önbelleğin yanındaki bir arşivde (`metadata-archive.json`) tutar. Kayıt silinince oturumları sayılmaya devam eder. Sayfada ve dışa aktarmada "Kaynak silindi · PLER arşivinden" diye işaretlenirler.
- **Ne tutulur:** Önbellektekiyle aynı alanlar: sayılar, zamanlar, kimlikler, modeller, proje yolları, dal adları ve düzenlenen dosya yolları. İstek, yanıt, komut ve araç çıktısı tutulmaz.
- **Hangi klasörler:** Varsayılan klasörler ile `CLAUDE_CONFIG_DIR` ya da `CODEX_HOME` ile seçilenler. `--claude-dir`/`--codex-dir` ile verilen klasörler okunur ama arşivlenmez.
- **Sınırlar:** 365 gün görülmeyen dosya düşer. Arşiv en çok 2.048 dosya ve 64 MB tutar, önce en eskiler gider; kapsam kaybı sayfada söylenir.
- **Denetim:** Kaynak kayıtları hâlâ canlıyken de sayfada saklama durumu görünür. `pler archive off` saklanan geçmişi silmeden arşiv kullanımını ve yeni saklamayı durdurur; `pler archive on` yeniden açar. Canlı kaynaklar yine okunabilir. Saklamayı durdurmak ile kalıcı olarak silmek farklı işlemlerdir.
- **Kopyalar:** Arşivdeki yanıtları kopyalayan devam oturumu bir kez sayılır. Eski okuyucuyla çıkarılmış ya da kaynağı yerinde olduğu hâlde okunamayan arşiv verisi kalite uyarısıyla gösterilir.
- **Silmek:** Sayfadaki **PLER arşivini sil** düğmesi (önce onay ister) ya da `pler archive clear`. Ajan kayıtlarına ve kota örneklerine dokunulmaz. Silinmiş kayıtların kopyaları sonra geri getirilemez.

PLER'i kaldırmak özel veri klasörünü kendiliğinden silmez. Arşivin özel yedeğini almadan önce PLER'i kapat. Destek kaydına önbellek veya arşiv ekleme.

## Güven ve veri kalitesi

Ekran tarihli bir anlık görüntü gösterir. Kısa pencerelerde 30 dakikadan, günlük/haftalık pencerelerde 24 saatten eski ölçümlerden tahmin çıkarılmaz. Bunlar sağlayıcının kuralları değil, PLER'in temkinli güncellik sınırlarıdır. Sıfırlanma veya tahmini dolma zamanı geçtiyse güncel doluluk bilinmiyor diye gösterilir. Açık sayfa bu etiketleri kendi saatiyle günceller; hesabı sorgulamaz. Kayıtları yalnız **Kayıtları yeniden oku** ile ya da **Kotayı canlı izle** açıkken yeniden okur.

Tamamen okunamayan Claude Code ve Codex dosyaları sayılır. Bozuk JSON, geçersiz kayıt kimliği veya yarım kalmış son satır varsa sağlam satırlar korunur; toplamın eksik olabileceği belirtilir. Her iki ajanın dosyası önbellekten okunurken de uyarı korunur. Hiç kayıt olmaması ile eksik okuma ayrılır. Geçersiz kota sayıları reddedilir. Bulunan dosya sayısı, her konuşma satırının geçerli veya her ajan sürümünün desteklendiği anlamına gelmez.

Sıkıştırılmış Codex dosyalarının çerçeveleri tam olmalı ve belirtilen boyutlar tutmalıdır. Dosyada varsa zstd içerik sağlama toplamı yerleşik okuyucuyla doğrulanır. Açılan byte'lara güvenilemeyeceği için bozuk sıkıştırılmış dosya bütünüyle dışarıda bırakılır ve bildirilir. Sağlama toplamı olmayan dosyada her veri değişikliği yakalanamaz. Proje gruplarken ve Git üst bilgisi okurken UNC ağ yolları ve sembolik bağlantı/junction içeren üst klasörler izlenmez.

Claude kayıtları sabit kimlik veriyorsa kopyalanmış istek ve araç çağrıları bir kez sayılır. Bu kimlikler yoksa ayrı satırların kopya olduğu güvenle anlaşılamaz.

Token kullanımı fiyat veya ölçülmüş tasarruf değildir. Ekrandan indirilen özet ve `pler report --json --sessions`; kaynak dosya yolu, ham oturum kimliği, dal adı, düzenlenen dosyaların yolları ve kayıttaki serbest notları içermez. Kısaltılmış proje adları, zamanlar, model adları ve sayılar içerir; anonim paylaşım dosyası değildir. Ayrıntılı terminal JSON'u ekranla aynı oturum alanlarını kullanır. Günlük harcama çağrıştıran `days` dizisi kaldırılmıştır: dönem, etkin oturumları seçer ve bu oturumların tamamının toplamını içerir.

Bu deponun kökünden güncellerken PLER'i kapat, `pip install --upgrade .` çalıştır ve yeniden aç. Depo daha büyük bir çalışma klasöründe `product/` adıyla duruyorsa dış klasörden `pip install --upgrade ./product` kullan. `pler --version` kurulu sürümü gösterir. Açık sayfa başladığı sürümün dosyalarını kullanır; güncel kod için PLER'i yeniden başlat. Güncelleme ve geri dönüşte saklanan geçmiş korunmalıdır. Sürüm ve JSON değişiklikleri [değişiklik kaydında](CHANGELOG.md) listelenir.

[Kalite kaydı](QUALITY.md), düzeltilmiş hatalarla açık kullanıcı itirazlarını ayırır. Otomatik testler Windows, Linux ve macOS'ta Python 3.9–3.14 ile geçiyor. İmzalı ve Python gerektirmeyen kurulum, her sistemde gerçek tarayıcı kabulü ve profesyonellerin günlük işinde fayda kanıtı hâlâ açık.

## Sınırlar

- Birden fazla seçili kaynak grubu kota geçmişi sağlıyorsa birleşik yüzde ve tahmin gösterilmez. Aynı Codex ev klasöründeki `sessions` ve `archived_sessions` tek gruptur. Sayacı incelemek için tek yerel ajan evi/kaynak grubu seçin. Sağlayıcı hesap kimliği toplanmaz; aynı klasördeki uyumlu örnekler de tek hesabı kanıtlamaz. Aynı kayıt evinde hesap değiştirme doğrulanmış kapsamda değildir.

- Claude Code kota yüzdesini kayıtlarına yazmaz. Durum satırı açık değilse yalnız sınıra takılma sayısı gösterilir. Durum satırı açıksa da kota, Claude Code'un çalıştığı anlardaki değerlerdir; Claude'u başka yerlerde (web, masaüstü) kullanman aynı kotayı tüketir ve bir sonraki Claude Code yanıtında görünür.
- Durum satırı, terminaldeki Claude Code'un özelliğidir. Claude masaüstü uygulamasının bu komutu çalıştırdığı doğrulanmadı; denemede 15 dakika boyunca hiç örnek gelmedi.
- Hesap kotası proje ve ajan filtrelerinden bağımsızdır. Kayıtlı sınır olayı olmaması, kalan kotanın bilindiği anlamına gelmez.
- Para karşılığı gösterilmez; sayılar ajanların kendi kaydettiği tokenlardır.
- "Durumun" bölümündeki gözlemler kayıtlardan çıkar; kontrollü bir deneyin sonucu değildir.

## Söz verilenin denetimi

[tests/test_trust.py](tests/test_trust.py) şunları sınar:
- bağlantı ya da süreç modüllerini yalnız yerel HTTP/tarayıcı parçalarının ve açıkça seçilen WSL kökleri için sabit durum sorgusunun kullandığını;
- yerel kayıtlarla tam bir kullanım boyunca yalnız `127.0.0.1` ile konuşulduğunu ve hiçbir program başlatılmadığını; seçilen WSL köklerinde yalnız belgelenen çalışma durumu sorgusunun çalıştığını;
- ekrana ve önbelleğe kayıt metninin girmediğini.

```
python -m pytest
```
