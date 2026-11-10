# Roodof 0.9.29 — ürün adı değişikliği

PLER ürününün yeni adı Roodof. Görünen uygulama, masaüstü pencere/kurulum, yardım ve site adı güncellendi. Mevcut geçmiş, yedek biçimleri, imza güven kökü ve eski indirme/güncelleme adresleri uyumluluk için korunur. Önceki sürüm kayıtları tarihsel adlarını korur. 400 seçici değişmedi; gerçek ortam kabulü Q01 SON/açık.

---

# Changes

## 0.9.28 — Ücretsiz Windows beta yayını

-0.9.22–0.9.27oturum/grafik hareketi, doğru Token/Calls seçimi, dar ekran ve Windows detay kapatma düğmesi düzeltmeleri yayıma alındı.
- Dil/Yardım/Güncellemeler Ayarlar → Genel altında; üst Close kaldırıldı. Kapsam/gözlem/yöntem/grafik rehberi ayrı Kayıt incelemesi sayfasında; sticky gezinme ve responsive okuma düzeni. Sayaç toplam gözlem ve uyarıyı ayrı gösterir.
- Eski indirmeler,400seçici ve veri biçimleri korunur. Ücretsiz beta; gerçek Windows/ajan/WSL/kullanıcı kabulü ve lisans/Windows imzası kararı ayrı ve açık.

## 0.9.27 — Ayrı kayıt incelemesi (yerel aday)

- Kapsam/uyarılar, gözlemler, tarihli hesaplama, hesaplama açıklamaları ve grafik rehberi sol menüde ayrı Kayıt incelemesi sayfasında. Kullanım ekranındaki açılır bilgi kartları kaldırıldı; uyarı sayısı yeni sayfaya yönlendirir. Eski bilgi ve eylemler korunur.
- Sayfa seçimi saklanır.400 ve public0.9.21 aynı; gerçek ortam kabulü ayrı ve açık.
- Kayıt incelemesi görünümü: bölüm dizini yanda sabit durur, okunan bölümü işaretler ve uyarı sayısını gösterir (dar pencerede üstte yatay). İçeriği olmayan bölüm ve bağlantısı gizlenir. Kapsam uyarıları kart, hesaplama ve grafik notları terim–açıklama satırı. Kullanım ekranındaki giriş düğmesi küçük hap biçiminde. Metinler ve sayım kuralları aynı.

## 0.9.26 — Uygulama seçenekleri Ayarlar’da (yerel aday)

- Güncellemeler, Yardım ve dil seçimi Ayarlar → Genel sekmesine taşındı. Mevcut düğmeler, yardımın dil bağlantısı ve güncelleme davranışı korunur; taşıma internet kontrolü başlatmaz.
- Üstteki Close/Kapat düğmesi kaldırıldı. Windows pencere kontrolleri, oturum ayrıntısı ve güncelleme penceresinin kapatılması korunur. Tarayıcı CLI oturumu Ctrl+C ile durdurulur.
- Kayıt kaynakları, kullanım uyarıları ve yedek/destek sekmelerine erişim korunur.400/public0.9.21 aynı, gerçek ortam kabulü ayrı ve açık.

## 0.9.25 — Pencereye sığan oturum detayı (yerel aday)

- Detay paneli Windows başlık alanının altında, kalan pencere yüksekliğinde açılır. Uzun başlık iki satırla sınırlıdır; tam metin title açıklamasında korunur.32px kapatma düğmesi küçülmez.
- Başlık ve önceki/sonraki oturum kontrolleri sabit; yalnız detay içeriği kayar. Yeni oturumda içerik başa döner. Panel girişinde yatay taşma üreten hareket kaldırıldı; kısa opaklık geçişi korunur.
- Hesaplama/400 seçici ve public0.9.21 aynı. Gerçek Windows/ajan/WSL kabulü ayrı ve açık.

## 0.9.24 — Daha az okuma, aynı bilgi (yerel aday)

- Kullanım ekranında grafik açıklamaları ve hesaplama notları klavye/fareyle açılan bilgi alanlarında. Tarihli kullanım ve kayıt gözlemleri kapalı bölümlerden erişilir; mevcut metin/düğüm/işlevler korunur.
- Fiyat kapsamı ve fatura olmadığı bilgisi, kısmi çağrı sayısı ve veri sorunları görünür kalır. Yeni gözlem uyarısı otomatik açılır; açık hesaplama bilgisi yenilemede korunur.
- Sayım kuralları ve400 seçici değişmedi; public0.9.21 aynı. Gerçek ortam kabulü ayrı ve açık.

## 0.9.23 — Menü ve dar ekran düzeltmeleri (yerel aday)

- Claude'un yeni menü/grafik/görünüm ekleri korundu. Azaltılmış harekette genel :active transform sıfırlaması yalnız düğme, bağlantı ve summary öğelerine daraltıldı; menü konumlandırması fareye basınca değişmez.
- Bulgular 340px'ten dar alana sığar. Günlük grafik giriş gecikmesi en fazla140ms; geçmiş uzadıkça büyümez. Metrik/veri değişiminde eski sabit gün vurgusu kaldırılır.
-400 seçici ve hesaplama kuralları aynı. Public0.9.21 korunur; gerçek Windows/ajan/WSL kabulü ayrı ve açıktır.

## 0.9.22 — Kullanım geçişi ve grafik doğruluğu (yerel aday)

- Tokens/Calls seçimi veriyi ve seçili düğmeyi birlikte değiştirir. Günlük grafik ve ısı haritası aynı serileri günceller; her tıklamada sıfırlanmaz. Gün üzerinden ayrılmak grafiği yeniden kurmaz.
- Sayılar arada başka değerler göstermeden doğrudan son değere geçer, kısa ve iptal edilebilir yüzey hareketi kullanır. Azaltılmış hareket tercihi korunur. Çağrı ekseni tam sayılıdır; bilinmeyen ajan kullanımı da çizilir.
- Tablo yalnız sıralı oturum listesi değişince kısa opaklık girişi kullanır; sayı güncellemelerinde tüm satırlar yeniden oynamaz. Kaydırma ve yeni veri eski animasyonu iptal eder.
- Dar ekranda proje grafiği etiketlerine yer ayrılır. Kaynak sayım kuralları değişmedi. Public beta0.9.21 ve400 seçici korunur; gerçek ortam kabulü ayrı ve açık.
- Hesap kotaları: kart başlığı artık sınırın adı (5 saatlik sınır, Haftalık sınır); ajan küçük renkli etiket. Aynı ajanın iki penceresi aynı kart gibi okunmaz. Kartlar zaten tahmini taşıdığı için üstteki uyarı şeridi bu ekranda yinelenmez.
- Zaman grafiği: Çağrı görünümü kendi soğuk renklerini kullanır (çubuklar, gösterge, ısı haritası); Token görünümü aynı kalır. İkinci kutu üstteki kartı yinelemek yerine aktif gün ortalamasını, bir gün seçiliyken o günün dönemdeki payını gösterir.
- Bir güne tıklamak o günü sabitler; yeniden tıklamak bırakır. Değer değişimi, çubuklar, kota kartları ve zaman çizgisi kısa giriş hareketi kullanır; azaltılmış hareket tercihi korunur.
- Kullanım bileşimi çubuğunda dört alan ayırt edilebilir renkte; plan etiketi tek satırda. Sayım kuralları değişmedi.
- Görünüm katmanı (`frontend/premium.css`): Windows değişken yazı tipi, sayılarda okuma yazı tipi ve sabit genişlikli rakamlar, tek vurgu rengi (geçerli menü, işaretli kutu, klavye odağı), sade üst çubuk düğmeleri, çizimi yenilenen açılır kutular, onay kutuları ve açılır satır okları. Davranış ve metinler aynı.
- Hesap kotaları: kota kaynağı olmayan Claude Code kendi kartında "Bağlı değil" olarak görünür; gereken tek komut kopyalanabilir. Eski açıklama paragrafı bu durumda gizlenir.
- Kullanım: bulgular tek sütun paragraf yerine kartlarda; proje grafiğinde en büyük proje vurgu renginde, çubukların ucunda değerleri yazar. Metinler ve sayım aynı.
- Oturumlar: ajan adı noktalı alt çizgi yerine renkli noktayla, durum rozetleri yuvarlak, açık satır vurgu çizgisiyle. Ayrıntı panelinde büyük rakamlar ve bileşim çubuğuyla aynı parça renkleri.
- Proje ve sıralama kutuları tarayıcının listesi yerine çizilmiş menü açar (`frontend/select-menu.jsx`, Base UI). Sayfadaki `<select>` tek kaynak olarak kalır; klavye ile açma, gezme ve seçme çalışır. Boş İşlerim ekranı ilk adımı ortada sunar.

## 0.9.21 — Ücretsiz Windows betası, kurulum ve arayüz düzeltmeleri

- Tek dosyalık kullanıcı kurulumu, PLER kısayolları/bildirim kimliği ve güncellemeden sonra Windows sürüm kaydı korundu.
- Kurulum ve kaldırma aynı dosya kilidini kullanır. Çalışan uygulama/güncelleyici, program klasörü değiştirilmeden önce ortak çalışma kilidiyle denetlenir.
- Temizlik klasör bağlantılarını izlemez; hedef dosya içerikleri ve izinleri korunur. Bağlantılı kurulum kökü reddedilir. Geçici kaldırıcı temizliği sabit Windows PowerShell ve literal yol kullanır.
- Yerel Setup ve ZIP; mevcut kullanıcı kurulumu/geçmişi değiştirilmedi. Genel yayın0.9.11 aynı; gerçek ortam kabulü SON.

## Windows kurulum programı — 0.9.21 kapsamı

- `tools/build_windows_setup.py` paket ZIP'inden tek dosyalık `PLER-Setup-SÜRÜM.exe` üretir (paket değiştirilmeden gömülü; sonradan imzalanabilir). Kurulum soru sormaz, yönetici izni istemez: `%LOCALAPPDATA%\Programs\PLER\program`, Başlat ve masaüstü kısayolu, Uygulamalar kaydı; her dosya manifest hash'iyle denetlenir, sonra PLER açılır.
- Aynı veya uygulama içinden güncellenmiş daha yeni sürüm korunur ve açılır; eski sürüm PLER kapalıyken değiştirilir (açıksa kapatma istenir). Uygulama içi güncelleyici aynı yapıda çalışır.
- Ayarlar > Uygulamalar'dan kaldırma geçmişi varsayılan olarak korur; isteğe bağlı silinir. Ajan kayıtları değişmez.
- Electron 45 bildirimler için Başlat menüsüne exe ürün adıyla ("Electron") ve iç pencere dosyasını hedefleyen ikinci bir kısayol yazıyordu (portable paketlerde de). İç exe artık PLER adını taşır, sabit bildirim kimliği kullanılır ve iç pencere doğrudan açılırsa PLER.exe başlatıcısına devreder.
- Uygulama içi güncellemeden sonra Ayarlar > Uygulamalar'daki sürüm numarası eski kalıyordu. PLER.exe her açılışta, yalnız kendi kurulumunu gösteren mevcut kaydın sürümünü günceller; portable klasör kayıt yazmaz.

## 0.9.20 — Yükleme animasyonu düzeltmesi (yerel aday)

- İskelet satırlarında sürekli arka plan boyama yerine tek transform katmanı; native belirsiz ilerleme çizgisi yerine kontrollü kesintisiz hareket. Gerçek yüzde uydurulmaz; erişilebilir progress öğesi korunur.
- Hızlı sayfa geçişinde önceki giriş animasyonu iptal edilir; derin solma kaldırıldı. Azaltılmış hareket tercihi durağan gösterge kullanır. Yenilemede mevcut veriler korunur.
- Logo düzeltmesi ve400 seçici korunur. Public0.9.11 aynı; gerçek ortam kabulü SON.

## 0.9.19 — Logo ana ekran geçişi düzeltmesi (yerel aday)

- Sol üst PLER logosu belgeyi yeniden yüklemeden mevcut arayüzde Oturumlar’a döner. Dil, adres, kayıtlı toplamlar ve kaydedilmemiş alanlar korunur. Fare ve Enter aynı geçişi kullanır.
- Önceki0.9.18 özellikleri ve400 seçici korunur. Yayın yapılmadı; public beta0.9.11 aynı.

## 0.9.18 — Tutarlı kavramlar ve yardımcı ekran okunabilirliği (yerel aday)

- Hesap kotaları, Kullanım uyarıları ve API fiyat karşılığı menü, komut arama, ayrıntı, bildirim, rapor ve yardımda aynı anlamlarla kullanılır. Sağlayıcı sınırı, kişisel eşik ve hesaplanan fiyat birbirinden ayrılır.
- Yardımcı metinler en az 12 px, gövde 13 px ve bölüm başlıkları 15 px ortak ölçülere taşındı. Yedek/geçmiş, tanılama, yeniden bağlama, kota göstergeleri ve güncelleme penceresindeki boşluklar hizalandı.
- Çevrimdışı TR/EN yardım aynı koyu tasarımla ve üç kavramın kısa sözlüğüyle açılır. Küçük ekranlarda uzun metinler sarılır.
- 400 oturum seçici, hesaplama/izleme kuralları ve ücretsiz beta kapsamı korundu. Public beta0.9.11; gerçek kullanıcı ve temiz Windows kabulü SON.

## 0.9.17 — Tek ana eylemli ilk kullanım, UX3 korunarak (yerel aday)

- İlk açılış duruma göre tek ana eylem sunar: Oturumlarını gör, Kayıt klasörü ekle veya Sorunu incele. İlk okuma bitmeden kaynak yok sayılmaz; okuma sırasında ana eylem kilitlidir.
- Yeniden arama, yardım ve şimdilik geçme Diğer seçenekler altında; bazı kayıtlar okunamadığında bulunabilen oturumlar da burada erişilir. Tur isteğe bağlı ve Ayarlar’da kalır.
- Oturum girişi tüm dönemleri açar; tamamlama yalnız oturumları görme veya açık geçme ile hatırlanır. Klasör/sorun inceleme kendiliğinden tamamlandı işareti koymaz.
- UX3 arama çıkışları,400 sınırı, backend ve bildirim kuralları korundu. Public beta0.9.11; gerçek kullanıcı ve temiz Windows kabulü SON.

## 0.9.16 — Aramada çıkmazları kaldırma (yerel aday)

- Sonuç bulunamadığında geçerli dönem/ajan/proje/kayıt durumu gösterilir; uygun sonraki eylem öne çıkar. Boş tablo yerini eylem alanına bırakır.
- Tüm dönemlerde/projelerde/iki ajanda ara yalnız ilgili seçimi genişletir; sorgu ve diğer filtreler korunur. Aramayı temizle kayıt durumu filtresini artık kapatmaz.
- Kaynak yokluğu, okunamayan veya kullanılabilir oturum üretmeyen kayıt ve bağlantı hatası ayrı anlatılır. Kaynak ekleme, tanılama ve yeniden deneme doğru ekrana gider.
- Arama metni API’ye veya kalıcı tercihlere eklenmez.400 sınırı, backend, sayım ve bildirim kuralları aynı. Public beta0.9.11; gerçek kullanıcı/temiz Windows kabulü SON.

## 0.9.15 — Sade iş bağlantısı ve gruplu Ayarlar (yerel aday)

- Oturum ayrıntısında bağlı işler görünür; bağlama/oluşturma tek açılır akıştadır. Aynı anda yalnız seçilen form görünür; taslak ve seçimler korunur. İşlerim → Oturum ekle seçilen işi önceden doldurur.
- Ayarlar üç klavye erişimli gruba ayrıldı: Kayıt kaynakları, Kullanım uyarıları, Yedek ve destek. Yedek/kurtarma, geçmiş, yeniden bağlama, tanılama ve rapor araçları istek üzerine açılır.
- Kısayollar doğru grubu ve aracı açar; başlangıçta geçmiş seçimi sorunu kurtarma aracını görünür yapar. Gruplar arasında geçiş ayar kaydetmez veya formu yeniden oluşturmaz.
- Backend, bildirim kuralları, sayım ve400 oturumluk iş seçicisi değişmedi. Ücretsiz public beta0.9.11; temiz Windows ve gerçek kullanıcı kabulü SON görev.

## 0.9.14 — Oturumu bul, kullanımını anla, uyarını kur (yerel aday)

- Arama görünür etiket ve `/` kısayoluyla öne çıktı. Yeni görünümlerde üç temel sütun var; kullanıcının kaydettiği sütun seçimleri korunur.
- Oturum ayrıntısı kayıtlı token, girdi/önbellek/çıktı ve API fiyat kapsamıyla başlar. Eksik değerler tahmin edilmez; model ve yöntem ayrıntıları istek üzerine açılır.
- Uyarı düzenleyicisi tek tıkla açılır; hazır eşikler, aşılmış eşik açıklaması ve ayrı kaydedilmiş durum var. Reddedilen kayıtta taslak korunur. Ayarlar’dan oturum aramaya doğrudan geçilir.
- Uzun listede seçim güncellemesi yalnız oluşturulmuş satır öğelerine dokunur; görünmeyen binlerce satır için öğe oluşturmaz. Kaydırma ve klavye seçimi korunur.
- 400 oturumluk iş seçicisi değişmedi. Yerel ölçümler genel hız garantisi değildir; gerçek kullanıcı ve temiz Windows kabulü SON görevdir. Sitedeki beta 0.9.11.

## 0.9.13 — Uygulamadan güvenli geçmiş kurtarma (yerel aday)

- Ayarlar’dan güvenilir özel yedeği incele; sayıları ve yeni hedefi gör; açık onayla ayrı klasöre kurtar. Mevcut veri üzerine yazılmaz.
- Kurtarılan geçmişi masaüstünde aç; eski okuyucular kapandıktan sonra yeni geçmiş yüklenir. Normal masaüstü açılışı seçimi hatırlar; önceki geçmişe dönüş vardır. Açık veri klasörüyle başlayan çalıştırmalarda seçim yalnız o çalıştırmayı kapsar.
- Bozuk yedek, eski önizleme, mevcut hedef, ağ/yönlendirilmiş konum ve onaysız işlem reddedilir. Önizleme on dakika bellekte tutulur; asıl ajan kayıtları yedekte değildir.
- Önceki kaynak 0948eb4 / candidate/0.9.12 ile yerel kayda alındı. 400 aynı; sitedeki beta 0.9.11, temiz Windows kabulü SON.

## 0.9.12 — Kullanıcı kontrollü oturum ayarı aktarımı (yerel aday)

- Ayarlar’da eski/arşivdeki oturumun iş bağlantılarını, değerlendirmesini ve bütçesini seçilen canlı oturuma önizlemeyle taşı. Çakışan değerlendirme ve eşik için açık seçim gerekir.
- Hedefin diğer iş bağlantıları ve notları korunur. Oturum kimliği, hesaplama ve ajan kayıtları değişmez.
- Son aktarımı geri alma, sonraki bağımsız düzenlemeleri korur; çelişen değişiklikte durur. Kesilen yazılar metadata erişiminden önce tamamlanır. Özel geri alma kopyası temizlenebilir; rapora/yedeğe girmez.
- 400 seçicisi aynı. Sitedeki ücretsiz beta 0.9.11; temiz Windows/gerçek kayıt kabulü son görev olarak açık.


## 0.9.11 — Ücretsiz masaüstü beta anlatımı

- Türkçe/İngilizce ilk kullanım ve yardım, masaüstü açılışı, kayıt klasörü seçimi, iş bağlama ve oturum uyarı eşikleriyle eşitlendi.
- Site, indirme ve sürüm bilgisi için masaüstü beta dağıtımı hazırlanıyor. Sayım motoru ve 400 oturum seçicisi aynı; temiz Windows ve gerçek kullanıcı kabulü son görev olarak açık.

## 0.9.10 — Ortak filtre ve ekran durumu (yerel aday)

- Filtreler, görünüm hafızası, rapor kapsamı ve tablo aynı açık bildirimleri kullanır. Bu alanlardaki DOM gözlemcileri kaldırıldı; aynı değer yeniden kaydedilmez.
- Aynı turdaki filtre değişiklikleri tek GET’e birleşir. Geçersiz kalan eski GET iptal edilir ve geç gelen yanıt son seçimi ezmez; metadata yazıları iptal edilmez. Proje/dil geri yüklemesinde uygulanmamış ara veri yayınlanmaz.
- Tablo tek filtre/sıralama projection’ı kullanır; gizli legacy tabloda ikinci liste üretilmez. Gizli grafikler yeni veri yokken yeniden çizilmez. İş taslakları, klavye, değerlendirme ve ilk okuma hata yolları korunur.
- Aynı bölüme tekrar tıklama yeni animasyon/veri işlemi/tercih yazısı başlatmaz. 1.000/5.000 uydurma geçmiş için geliştirici ölçüm bütçesi belgelendi; gerçek büyük kayıt ve temiz Windows kabulü SON görevdir.
- 400 oturum sınırı ve work-view.jsx byte düzeyinde korundu. Public0.2.31 değişmedi; bu yerel adaydır.

## 0.9.9 — Başlık nedenleri ve okuma tanılaması (yerel aday)

- Oturum ayrıntısında ajan başlığı yerine neden alternatif ad gösterildiği açıklanır: başlık bulunmaması, arşiv, konum/erişim, bozuk/büyük indeks, toplam başlık bütçesi, sınırlı Claude baş/son penceresi ve okuma sırasında değişim ayrı durumdur. Kısmi bilgiyle bulunan başlık en güncel adlandırma gibi sunulmaz.
- Ayarlar’da filtrelerden bağımsız okuma durumu ve tanılama. Kayıt kaynakları, başlıklar, saklanan geçmiş, Git, kayıtlı tercihler ve görünüm hazırlama sabit kodlarla ayrılır; her açıklama sonraki adımı gösterir. Başarısız yeni okumada önceki başarılı görünüm olduğu belirtilir.
- İçeriksiz yerel tanılama JSON’u indirilebilir: yalnız sürüm/zaman/durum/sabit kod ve sayılar; konuşma, başlık, sağlayıcı/oturum kimliği, özel yol, ham hata veya erişim anahtarı yok. Otomatik gönderim yok; özel geçmiş yedeğiyle aynı dosya değildir.
- İlk okumada hiç görünüm oluşmasa da Ayarlar, kayıt klasörleri ve tanılama açılır. Başlık bilgisi/başlık durumları ve tanılama normal rapora, kayıt önbelleğine veya arşive eklenmez; kullanım hesap kuralları aynı.
- WSL başlık erişimi için seçili kök kapsamı genişletilmez; bazı başlıklar erişim kapsamında olmayabilir. 400 sınırı ve public0.2.31 değişmedi. Gerçek ajan/temiz Windows kabulü SON görev olarak açık.

## 0.9.8 — Uygulamadan kayıt klasörü yönetimi (yerel aday)

- Ayarlar ve ilk kullanım ekranından Claude Code/Codex kaynaklarını seçme, kontrol etme, ekleme ve kaldırma. Masaüstünde yerel klasör seçicisi, tarayıcıda tam yol girişi. Ajan ana klasörü seçilirse yalnız mevcut kayıt alt klasörleri eklenir.
- Standart ve ortam değişkeniyle seçilen kaynaklar korunur; ek klasörler bunlara katılır. En fazla 12 ek klasör, kalıcı bilgisayar tercihi, eşzamanlı değişiklik kontrolü ve bozuk tercih dosyasını koruma. Kaldırma kaynak dosyalarını veya saklanan geçmişi silmez.
- WSL yalnız açıkça seçilen ve zaten çalışan dağıtım kökleriyle okunur. Duran/erişilemeyen dağıtım ayrı açıklanır; ağ paylaşımları reddedilir. WSL’ye ait fiziksel dosya taşıma kimliği doğrulanmış sayılmaz. Kullanılamayan önbellekle yalnız WSL okumada kimlik tercihi yazmaya çalışma düzeltildi.
- Masaüstü köprüsü yalnız klasör seçme işlemini sunar; ana uygulama ve kendi üst çerçevesi doğrulanır. Mevcut süreç/izin sınırları korunur. Klasör seçim dosyası yedeğe dahil değildir; geri yükleme sonrası yeniden seçilir. Özel geçmiş yedeği kaynak yollarını içerebilir.
- 400 oturum sınırı değişmedi. Temiz Windows kabulü SON görev; bu sürüm yerel adaydır, public 0.2.31 yayını değişmedi.

## 0.9.7 — Doğrulanmış oturum kimliği (yerel aday)

- Aynı yerel dosyanın doğrulanmış yeniden adlandırma/taşınmasında ilk oturum kodu korunur; iş, değerlendirme ve bütçe dosyaları yeniden yazılmaz.
- Sağlayıcı kimliği, başlangıç zamanı ve dosyanın fiziksel kimliği birlikte kullanılır. Kopya/yeni dosya, çelişen sahiplik ve doğrulanamayan kaynaklar otomatik aktarılmaz.
- Doğrulanmış canlı dosyanın kapsadığı eski arşiv adı bütçe izlemesini durdurmaz; canlı sayaç eksikse uyarı bekler.
- Kimlik kaydı ve bütçe ayarları özel yedeğe eklenir. Bozuk kimlik dosyası korunur; varsa önceki görünüm tutulur.
- 400 oturum sınırı korunur. Temiz Windows kabulü SON görevdir.

## 0.9.6 — Filtre ve klavye davranışı (yerel aday)

- Programatik filtre değişiklikleri görünür dönem/ajan seçimleri, rapor kapsamı ve görünüm hafızasıyla tek sorgu üzerinden eşitlenir.
- Tablo içindeki ajan düğmesinde Enter, ajanı filtreler; oturum başlığı doğal olarak açılır, yukarı/aşağı gezinme korunur.
- Panel açılışındaki tablo çizimi klavye odağını korur; gecikmiş kapanış olayı yeni açılmış panelin seçimini temizlemez.
- Kullanıcı isteğiyle toplu bağlamadaki 400 oturum sınırı aynen korunur. Temiz Windows kabulü SON görevdir.

## 0.9.5 — Oturum bütçe uyarıları (yerel aday)

- Oturum ayrıntısından token veya API fiyat karşılığı dolar eşiği; %80/%100 uyarıları ve Ayarlar’da izleme listesi.
- PLER açıkken filtrelerden bağımsız, bilinen ilgili canlı kaynakların sınırlı izlemesi; değişmeyen kayıtlar yeniden ayrıştırılmaz.
- Küçültülmüş pencerede ana süreçten yerel bildirim; gösterilmiş uyarılar normal yeniden açılışta tekrarlanmaz. Tarayıcı izinleri açılmaz.
- Eksik fiyat/kullanım, saklanan geçmiş, eski gözlem veya kaynak hatasında izleme durumu açık gösterilir. Oturum durdurulmaz; dolar gerçek fatura değildir.
- Yeni frontend/backend/girişimci gözlemleri kalan işlere işlendi. Temiz Windows kabulü SON görevdir; genel yayın değişmedi.

## 0.9.4 — İlk kullanım

- İlk açılışta Claude Code ve Codex kayıtlarının durumu ve filtreden bağımsız oturum sayıları görünür.
- Boş, kısmen okunabilen, yalnız saklanan geçmiş ve okuma hatası durumları ayrı anlatılır; yeniden arama ve kaynak yardımı sunulur.
- Oturumları incele bütün ajan/dönem/proje filtrelerini açar. Tamamlanan başlangıç mevcut yerel görünüm tercihlerinde hatırlanır, Ayarlar'dan tekrar açılabilir.
- Otomatik arayüz turu yerine Ayarlar'dan isteğe bağlı tur kullanılır.


## 0.9.3 — Oturum başlıkları

- Claude Code kayıtlı özel başlığı/indeks özeti ve Codex yerel sohbet başlığı listede ve ayrıntıda gösterilir.
- Başlık araması ve işlere oturum bağlama seçicisi aynı isimleri kullanır; başlık yoksa proje/tarih gösterilir.
- Başlıklar yalnız canlı görünümde tutulur; muhasebe önbelleği, arşiv ve standart JSON raporuna eklenmez. Kaynak yenilenince ad değişiklikleri tekrar okunur.
- PLER ikonu: PLER.exe, masaüstü penceresi ve görev çubuğu aynı ikonu kullanır; sabitlenen görev çubuğu düğmesi kararlı PLER.exe başlatıcısını açar. Kaynak assets/icon/*.svg, üretici tools/build_icon.py.


## 0.9.2 — Remember the working view (local candidate)

- Keep column order, visibility and user widths; agent/period/project, sort and quality filters; and the last open section across normal desktop restarts.
- Extend the existing local window-state file with a bounded view record. Only known field names, enum filters and opaque project IDs are accepted; damaged state falls back to defaults.
- Restore view choices into each fresh renderer profile. Preserve the preferred identity-column width while temporarily adapting it to smaller windows; update explicit resized widths before layout redraws.
- Verify native close/reopen in fresh profiles, language retention, resetting columns and corrupt-file fallback. Public releases and data formats are unchanged.


## 0.9.1 — Review fixes (local candidate)

- Quota gauges prioritize reset/stale/conflicting states, withhold old percentages and refresh their state as time passes or the page reopens.
- Daily charts include both partial boundary dates of rolling intervals; the first included day is no longer dropped from totals or sparklines.
- Multi-session linking blocks Escape/backdrop dismissal while writes run, guards repeat submission, and stops remaining writes on programmatic shutdown.


## 0.9.0 — Visual upgrade: time, limits, work and window (local candidate)

- Usage: a usage-over-time card with daily Claude Code/Codex bars, a weekday × hour rhythm map, a sliding-digit stat row that follows the pointed day, and a trend line in the total card. The engine adds UTC-hour buckets of the same dated responses (usage/timeline.py), so the chart always equals the dated total; whole-session totals are never spread over time.
- Limits: one gauge per quota window with a time track to the reset, the forecast fill time and pace; explanatory notes move into Base UI popovers.
- My work: work items as cards (FormKit auto-animate), several sessions linked at once through a cmdk picker (each link is the same checked write), sonner toasts for confirmations.
- Desktop window: on Windows the title bar blends into the app; window size, position, maximized state, language and the first-run tour are remembered in the PLER cache folder (no address, key or record).
- First-run tour (driver.js), five steps, shown once; never shown to automated checks.
- Data colors: agent-claude/agent-codex and a heat ramp from Radix Colors bronze dark. Bundled licenses are now collected from what esbuild actually bundles; sonner's injected style and cmdk's unused Radix dialog are kept out so the strict style-src policy holds.
- No new public release or clean-Windows acceptance.

## 0.8.0 — Monochrome design foundation (local candidate)

- DESIGN.md records product-specific surface, typography, density, motion and state contracts, with the six requested repository references archived by URL and SHA256.
- Replace stacked workbench styles with a token-generated monochrome foundation shared by all five screens. Standard panels use16px padding, controls32px and record rows64px; native desktop follows the dark theme.
- Real React/Motion islands provide spring/layoutId navigation and filter indicators. Existing controller and Tabulator retain data order, permissions and writes.
- Add tactile control feedback, bounded row entry, drawer/dialog/disclosure entry, keyboard palette navigation and a refresh-safe initial skeleton. Reduced motion is respected.
- The design contract runs during every frontend build: token/document consistency, allowed colors, density, motion and normal-text contrast. No new public release or clean-Windows acceptance.


## 0.7.0 — Sessions UX, first priority pass (local candidate)

- Recognizable rows keep agent/date visible and use a linked work title when available; work titles are searchable. Prompts and replies are still excluded.
- One controller sort applies to the full snapshot before paging. Grid headers only move/resize columns. Language changes retain the selected sort.
- Larger type, stronger contrast, compact list controls, stable essential columns, a single empty result and a visible horizontal-scroll cue.
- Inspector shows identity and metrics first; work-to-session navigation preselects the work. Corrected obsolete navigation copy and success styling.
- Report download now lives in Settings with its own explicit scope; technical notes remain in disclosures. No publication or clean-Windows acceptance in this pass.


## 0.6.0 — local Tabulator sessions, not published

- Replace the visible sessions table with bundled Tabulator 6.7.1; configurable/resizable/movable columns.
- Existing controller retains filter/export scope and verdict writes; failed saves keep prior values.
- Localized columns, responsive inspector view and existing session keyboard actions.

## 0.5.0 — local session workbench, not published

- Session-first compact desktop view, one-click agent/date filters and real row selection.
- Nonmodal right inspector keeps the session list interactive; previous/next and arrow navigation.
- Actual saved verdict and work-link actions retained; detailed fields disclosed on demand.

## 0.4.0 — local workspace redesign, not published

- Dedicated Overview, Sessions, My work, Quota and Data sections; bilingual sidebar and keyboard section search.
- Interactive recorded-project distribution with ECharts, Lucide icons and reduced-motion-aware Motion transitions.
- Progressive disclosure of export controls and coverage limits; original accounting and action controls preserved.
- Everything is bundled locally; no CDN or new data service. Clean Windows acceptance remains the final task.

## 0.3.0 — local desktop candidate, not published

- PLER.exe/demo open a dedicated Electron window; closing it stops the local backend.
- Access keys use a private process environment; isolated rendering, permission and navigation boundaries.
- Desktop updater 2 preserves window mode and gates health on document load. Initial upgrade
  from 0.2.31 is manual. Clean Windows acceptance remains the final pending task.

## Unreleased

- Require the launch Site’s offline signature/package/wheel/EN/TR consistency gate in the normal build before publication; current .31 artifacts remain unchanged. Prepare preregistered work/follow-up pilot tasks and comprehension/effort forms without claiming participant results.

- Clarify English/Turkish offline Help: usage missing from retained records cannot be counted, and no general error margin is established. Remove the unsupported claim that the figure may be only a few percent low. Published 0.2.31 artifacts are unchanged.

## 0.2.31 — 2026-11-02 (published early beta)

- Add Windows portable Updates: explicit checks, optional launch checks (off by default), verified download, private backup and restart. The first upgrade from .30 or earlier remains manual; Python wheels update manually.
- Verify pinned-key signed release metadata, entire ZIP and all files; refuse incompatible data formats. Keep the stable launcher and baseline runtime, select prepared versions atomically and recover an interrupted selection on launch. Failed startup reopens the old version without overwriting newer user data.
- Preserve unsaved work/follow-up drafts by refusing the UI install action; freeze edits during preparation. Stage private recovery data under protected per-user Windows permissions; retain backups and old versions for recovery. No agent data is sent.
- Publish matching .31 ZIP/wheel and signed feed; verify live bytes, EN/TR versions and the unchanged .30 URL. Tests use invented records; Windows Authenticode, clean-machine acceptance and full CI remain open.

## 0.2.30 — 2026-11-02 (published early beta)

- Add an offline reader/price release review gate, independently expected cold/cache/archive record cases, official price-source review dates and automatic discovery of all browser test suites. No provider fetch or workflow dispatch.
- Correct price confidence: GPT-6 writes without a lifetime split and unlisted Codex dated IDs stay unpriced; invalid Claude split/modifier metadata preserves counts without being clamped or sanitized into a standard price. Copies carrying the selected usage must agree on price in either order. Parser provenance becomes `accounting-2026-11-01.1`; API/plan review date is 2026-11-01; usage schema and work/backup formats stay unchanged.
- Real-data review: Claude Code logged region `not_available` for every response before it reported regions (until 8 October 2026 on this computer). Only US-only `us` has a published higher price, so such responses are priced like an absent region again; otherwise 37% of this computer's Claude tokens would have become unpriced. A contradictory quota episode now leaves only its own window period out of the plan's period counts instead of the whole 30-day window, which had hidden Codex's 5-hour count here; any contradiction still blocks a lower-plan comparison.

- E01, remaining patterns: a session whose attribution is incomplete only because it worked in several project folders keeps its dated responses (each is its own, counted once); records shared between sessions stay excluded. An older reader's Codex archive copy that one live file fully carries (a moved or renamed file) is no longer counted, reported or allowed to mark its session, and the session keeps its page identity. On this computer Claude Code's dated coverage rose from 2.4% to 100%, Codex's from 28% to 99%, and the old-reader archive warning on 71% of Codex tokens disappeared. Totals are unchanged. The rest stays explicit: 0.9% of Codex tokens are cumulative-only older logs without per-response dates, 0.2% are in sessions with conflicting checkpoints.
- E02, account scope without account identity: each Codex meter sample keeps the plan Codex logged with it. After a plan change (an upgrade, a downgrade or another account on another plan) quota forecasts and the plan check's limit counts use only samples since the latest change, and the page, terminal report and JSON say when it changed. The accounting contract now lists what is and is not detectable: several source groups are withheld, simultaneous accounts only when their readings conflict, and a switch to another account on the same plan cannot be seen in the logs, so PLER never claims one account. This computer's logs show no plan change; their results are unchanged.
- E01, compacted and forked Codex threads: a Codex session is now counted completely by its response records when every file's records move exactly with its cumulative meter between compactions (the meter omits compaction requests, which only add records), and forked threads that start from an inherited counter have no records before it. Anything else keeps the earlier warnings. On this computer every one of 226 compacted thread files followed the pattern; Codex sessions marked unreconciled fell from 9 (98.8% of Codex tokens) to 3 (0.19%) and Codex's dated usage grew from 2.8 million to 317 million tokens. Totals are unchanged.
- Speed: an unchanged refresh no longer repeats work. A Git branch walk is reused for the same branch tips and commits once every answer is known, the work file is validated once per unchanged content (each read gets its own copy), and dated-usage and plan sums no longer call a function per response or convert times already in UTC. On the scale workload, on battery power, an unchanged refresh fell from 5.53 s to 2.38 s and each change phase from about 10.7 s to 7.8 s; the page view is identical apart from its reading time. The earlier failed run was largely the machine running on battery: unchanged Git code was 2.3 times slower too.
- Validate the current source against a predeclared Windows scale workload: 102.61 MiB expanded invented logs, 385 sessions, Git, 200 work items and 20,000 memberships. Three rounds per runtime pass fixed latency/memory budgets on CPython 3.14 native and 3.9/3.12 fallback, with uncached accounting equality, archive-only recovery and cooperative cancellation evidence. This is source acceptance on one machine, not a new package or a general speed guarantee; physical platform acceptance remains open.

- Add private work follow-ups: frozen equal seven-day response windows, explicit review, cancellation/deletion and guarded agent/project/model comparisons. Unknown context, small samples, changed history or incomplete evidence produce reasons rather than a numeric gain. No scheduled action, provider query or causal savings claim.
- Follow-ups load only on opening their section. Preserve drafts across selection/language changes and failed/conflicting saves; confirm individual deletion. Atomic component format 3 reads legacy 1/2 without a no-op migration, remains in private backup/recovery and is omitted from ordinary reports.
- Add optional work goals, user-declared outcomes and result/remaining-work notes. Keep the whole-work entry separate from filter-scoped test/build/Git observations, session verdicts and usage. No automatic completion, quality score or task-cost inference.
- Read legacy work format 1 without rewriting it; real edits now use component format 3 (format 2 introduced the goal fields). New details remain local, omitted from normal reports and included in private backup/recovery. Earlier builds cannot read the new component format; keep a compatible backup for rollback.
- Guard goal/outcome edits with content revisions under the existing writer lock. Stale windows preserve their draft and review the latest saved entry before a later explicit save. Drafts survive work/filter/language changes; cancelling writes nothing. Existing work routes keep their 1 KiB bound; the authenticated details route has a 16 KiB UTF-8 bound.

- Withhold unsupported plan conclusions for unpriced responses, source/archive losses, unreconciled or unchecked usage, conflicting/unusable quota history, plan changes and multiple source groups. Unknown API equivalents no longer display as zero dollars.
- Replace switching-savings and "smaller plan fits" findings with bounded recorded-price observations and conditional observed-threshold comparisons. Actual payment remains unknown; retained history never proves a complete billing month. The plan interval is explicit and independent of page/report filters.
- Require fresh, consistent lower-plan evidence on 14 distinct UTC dates spanning 14 days, without gaps over two days. Comparisons expire with required sample freshness/reset deadlines; the page ages the message without rebuilding the selector. These are observation thresholds, not provider guarantees.
- Align terminal output, public JSON fields, English/Turkish UI, offline Help and the accounting contract. No new billing data store, price-table update, provider-account access, package or publication.

- Explain missing records with separate effects and safe next steps for source access, stopped WSL, malformed records, reading/path limits, old or unchecked archives, retained/deleted originals, incomplete counts, uncertain attribution and unpriced usage. File warnings cover selected source folders; session explanations follow the main filters.
- Link the English/Turkish panel to offline recovery help. Preserve the existing affected-session filter and technical reasons. Explain that successful reading cannot establish full account history and a cache rebuild cannot recreate missing originals; archive deletion is not a repair action.
- An empty failed read no longer uses the "no logs found" heading. Missing Codex quota samples no longer suggest installing the Claude Code status line; terminal and desktop Claude support are distinguished.
- Source changes only: no new package, release, update mechanism, price table, accounting, reader identity or schema change. Financial recommendation rules remain a separate Y04 audit.

## 0.2.29 — 2026-11-01 (early beta)

- Add a practical English/Turkish first-use walkthrough to offline Help: try the demo, close it, open your own selected records, identify a session and link it to named work. Include empty-record guidance, removal/data retention and the public support address.
- The demo banner explains how to return to normal use; demo work remains temporary and is not copied into personal work.
- The closed-page message points Windows portable users to `PLER.exe` instead of an unavailable globally installed `pler` command.
- Align Windows early-beta package instructions with the download page: `PLER.exe` starts the app, `PLER-Demo.cmd` starts invented data, and `PLER.cmd` remains the terminal entry point. The packager has an explicit early-beta channel; private candidates retain their previous default.
- This release changes guidance and packaging, not accounting, parser/schema, quota rules or update delivery. It remains unsigned; clean-machine and physical platform acceptance remain separate open checks.

## 0.2.28 — 2026-10-31 (private candidate)

- Quota warning: the page shows a warning at the top when a 5-hour or weekly limit is reached, or at the current pace fills before its reset within an hour (a weekly limit: within a day). It comes from the existing forecast and the page clock, so it also appears or clears between reads.
- **Watch the quota live** (off by default) makes the open page read the logs again every 5 minutes; a timed read waits while the user types, a dialog is open or another action runs. **Desktop notifications** (off by default) ask the browser once and then show each new warning once, also across reloads. Both choices are kept in this browser only; nothing is sent anywhere.
- A hidden page still checks the warning every 30 seconds so a notification can arrive; it skips redrawing.

## 0.2.27 — 2026-10-31 (private candidate)

- Plan check: per agent, the last 30 days of agent work at API list prices next to the plan's published price, and how many 5-hour windows and weeks reached the limit, on the page, in the terminal report and in JSON. Codex's plan comes from its log; for Claude Code the user chooses Pro, Max, Ultra or an API key once, saved only on this computer (`plan-choice.json`; the demo keeps it in memory).
- Only published figures are used (31 October 2026): Claude Pro $20, Max $100 (5x Pro every 5 hours and week), Ultra $200 (10x Pro weekly, no 5-hour limit); ChatGPT Go $8, Plus $20, Pro $100/$200/$500. A smaller Claude plan is named only with 14 days of meter history and 20% headroom; OpenAI publishes no ratio between Plus and Pro, so no Codex plan is named. "An API key would cost less" needs a full, fully dated period and no reached limit.
- Each accepted response now keeps its own list-price equivalent with its time, so the period sum counts every session of the account, including those with an unknown project. On this computer: Claude Code $464 and Codex $215 in the last 30 days; Codex Plus reached its 5-hour limit in 9 of 41 windows and its weekly limit in 1 of 12 weeks.
- The readers rebuild their cache once (the dated record gained the price).

## 0.2.26 — 2026-10-30 (private candidate)

- Add user-named local work items and explicit links to Claude Code/Codex sessions. Create, rename, link, unlink and delete work without changing logs, verdicts or usage totals. Demo work stays in memory.
- Show selected, outside-filter and unavailable linked sessions. Overlapping work subtotals are not additive; the assigned-work summary uses their session union once. Missing or changed identities are never rebound by names or inferred native IDs.
- Bound and validate the local work store; preserve damaged/newer files instead of overwriting. Work titles render as text and ordinary JSON exports omit titles and memberships, even when project masking is off.
- Include validated work items and links in private backup/recovery. Older 0.2.25 backups without a work file remain usable; saved titles are private and unencrypted like other backup metadata.
- Application version advances; token/pricing accounting, parser `accounting-2026-10-30.3` and schema 2 stay unchanged. Grouping does not infer task completion, cost allocation, code quality or savings.

## 0.2.25 — 2026-10-30 (private candidate)

- Add a versioned, verified private backup of retained metadata, session verdicts, retention preference and Claude quota samples. Snapshot only saved allowlisted files under the archive/quota writers' locks; never rescan original logs for backup.
- Validate manifests, per-file checksums, schemas and metadata before restoring. Reject unknown/duplicate/compressed/oversized members, private extra fields and damaged data. Stage and flush fixed files, then publish only a new local folder; refuse existing targets and preserve the current history.
- Add `pler backup create/check/restore`, fixed public JSON summaries and explicit `--data-dir` selection. Restore preserves source paths, timestamps and original reader keys; it neither switches the active profile nor remaps sources to another machine.
- Propagate command failure and argument exit codes from `python -m pler`, so a rejected restore cannot appear successful to calling scripts. The portable terminal entry point already propagates these codes.
- Add private-backup download and local file checking to history controls, with separate privacy wording and versioned EN/TR recovery help. Backup files are unencrypted and contain private paths/identifiers; a checksum is not an authenticity guarantee. Demo and unauthenticated requests cannot access saved private data.
- Application 0.2.25; accounting parser and schema stay unchanged. No subscription, advertisement, participant outreach or model call is introduced.

## 0.2.24 — 2026-10-30 (private candidate)

- Preserve reader/decompression/budget warnings when reusing a page result; retry error snapshots after five seconds instead of retaining them for an hour.
- Require device/file identity on exact cache hits. Verify the entire old prefix before continuing a grown log, and recheck the reopened descriptor before seeking; rotation falls back to a full read. Legacy cache entries rebuild. Prefix hashing adds bounded I/O; unchanged exact hits remain metadata-only checks.
- Exclude explicit informational, collection, listing, dry-run and compile-only invocations from test/build outcomes. Commands beyond the inspected word budget cannot claim a pass. Token and pricing rules stay unchanged.
- Bound and cancel Git tree traversal before collecting changed-file lists. Cutoff commits remain unknown and are not cached. Bound saved-count reads and validate kept lines do not exceed added lines; update verdicts from one bounded validated snapshot.
- Add seeded malformed-input and incremental/full differential regressions. Keep the original parser speed guard and additionally time verification and cache persistence in the continued-read pipeline.
- Parser `accounting-2026-10-30.3`, schema 2. Preserve Claude's 0.2.16–0.2.23 features and optimizations.

## 0.2.23 — 2026-10-30 (private candidate)

- A speed guard in the test suite, so large slowdowns fail CI before a release. CI machines differ in speed, so it never compares with a fixed number of seconds. On invented logs shaped like real ones (about 13 MB), it compares timings taken in the same process: a first read against plain JSON parsing of the same bytes (limit 10, seen 2.8–4.3), a later read against parsing the reader caches (limit 60, seen 12–28) and a continued read of a grown log against a full read (limit 0.25, seen 0.02–0.03). These were measured on Windows with Python 3.9, 3.12 and 3.14 and on Linux with Python 3.14. The guard caught each injected regression: a tenfold slower reader, a tenfold slower merge and a lost continued read. Slowdowns below about twofold are left to the recorded measurements.

## 0.2.22 — 2026-10-30 (private candidate)

- Keep the code-in-place counts across restarts. The page saves the four counts of each measured commit (added, kept, files, skipped) in `git-survival.json` in PLER's cache folder, each under a one-way digest of repository folder, HEAD and commit. No path, commit id, name or text is written. Counts from other counting code, damaged entries and counts cut short by the byte budget are never reused; `pler cache reset` removes the file. The demo keeps its counts in its own folder.
- On this computer's real repositories, the code count of the first refresh after a restart fell from 2.9 s to 0.14 s.

## 0.2.21 — 2026-10-30 (private candidate)

- While the page stays open, a refresh whose inputs are all unchanged returns the previous result without merging the logs again. The inputs are the found log files (path, size, modification time, file identity), the discovery issues, the reader versions and PLER's own cache, archive and retention files as the previous read left them. Any change, a cache reset, an archive clear or a retention switch means a full read, and a result is reused for at most an hour. `pler report` always reads.
- Claude Code rows of one session in a file now record their source once instead of once per row, and the archive encodes each entry once to check its checksum and measure its size (sizes are kept for the life of the process).
- On this computer's real logs: a page refresh with nothing changed fell from about 12 s to 0.94 s (0.1 s of it the log scan, the rest Git and the view). A scan after the running session's transcript grew fell from 18.9 s (0.2.19) and 14.2 s (0.2.20) to 10.4 s, with identical sessions and totals.

## 0.2.20 — 2026-10-30 (private candidate)

- Read a growing log only from where the last read ended. The reader cache now keeps, per plain log, the byte position of its last complete line, the file's identity, a digest of its first 4 KiB and of the 4 KiB before that position, and the small state the reader needs to continue (the Codex rollout's first and last times, whether a malformed line was seen, which Claude Code calls were test or build commands). A different file, changed bytes, a shorter file or a half-written last line mean a read from the start, as before. Compressed rollouts are always read whole.
- On copies of this computer's 13 real logs grown in steps, the continued reads gave exactly the rows of full reads. Reading the 121 MB transcript of a running Claude Code session again took 7.1 s and now takes about 0.01 s. A refresh after that transcript grew went from 20.4 s to 14.2 s with identical sessions and totals; the rest of a refresh is work done on every read (next item in the plan).

## 0.2.19 — 2026-10-30 (private candidate)

- Show how much of the code a session committed is still in place. For each commit made during a session that is still in the current HEAD's history, PLER counts the lines it added and how many HEAD still has, by content. The session list, the session's Git details and the commits observation show the share. Merges, first commits, binary and very large files are left out and counted.
- File names and contents are read only in memory through PLER's own Git object reader (loose objects and packs); only counts leave it. No Git program runs.
- Git objects are found with one listing per object folder, which also makes the existing branch check faster. Counts for an unchanged HEAD are reused while PLER runs.
- The demo repository now has invented files, so the share is visible there.

## 0.2.18 — 2026-10-30 (private candidate)

- Show whether the agents' own tests and builds passed. Each shell command is classified in memory as a test or build (many languages and tools); its text is never stored. Claude Code's failed-call flag and Codex's exit code give the outcome. A run whose output was piped on, that ran in the background or that was followed by another step is counted with no visible result.
- Each session shows its last visible test and build result next to the verdict buttons, and its counts in the details. A new observation says how the selected sessions' tests ended and how many tokens the sessions ending on a failing test used. The terminal report and JSON carry the same sums. The demo includes invented test runs.
- The readers rebuild their cache once; the first read takes about 7% longer, later reads about 2%.

## 0.2.17 — 2026-10-30 (private candidate)

- Judge a session with one click: **Useful** or **Wasted**, in a new "Did it pay off?" column and in the session details. The verdict is saved only on this computer, under the page's session code (no path, name or text), and survives cache reset and archive clear. Click the pressed button again to remove it.
- Above the list, the selection's verdicts are summed: sessions, tokens and API list-price equivalent for useful, wasted and not-judged sessions. The terminal report and JSON carry the same sums; a damaged or newer verdict file is reported and never overwritten. Demo verdicts stay in memory.
- `pler report --json` now always writes UTF-8, also when Windows redirects it to a file.

## 0.2.16 — 2026-10-30 (private candidate)

- Show what the recorded usage would cost at the providers' public API list prices (standard tier, prices of 30 October 2026), on the page, in the terminal report, in JSON and per session. Each response is priced once with its own model and prompt size; Claude cache writes use the logged 1-hour/5-minute split. Responses whose model has no published price, whose prompt exceeds a covered tier, or that ran at another speed or region price stay in the token totals but are left unpriced, and the priced share is shown. It is a comparison point for a subscription, never a bill.
- The Claude reader now keeps the 1-hour share of cache writes and the logged speed and region words, so the cache rebuilds once after the update.

On this computer's real logs: Claude Code $812 with 100% of its tokens priced, Codex $204 with 87% priced (one Codex model has no published price). Claude Code's own figure for a session's latest process was 3–4% above PLER's, because agents also send requests they do not record.

## 0.2.15 — 2026-10-30 (private candidate)

- Stream raw JSONL and native zstd input with explicit file, expanded-output, line, projection and scan budgets. Preserve complete good rows and report incomplete coverage at a limit. Reject excessive JSON nesting without stopping other sources.
- Bound rebuildable cache reads; keep timestamp-only Codex rows to their two endpoints instead of a growing list. Keep decoding checks for every compressed frame, including checksums and truncated tails; the plain-Python fallback remains bounded whole-buffer decoding.
- Coalesce scans through one cancellable worker and close it with a bounded wait. Limit local HTTP handlers, idle reads and total connection time without adding one timer thread per connection.
- Serialize quota journal writers across append/prune and bound journal/stdin reads. Flush and synchronize archive files before replacement, and POSIX directory changes after replacement/deletion. Post-replacement failures do not imply rollback.
- Source accounting parser: `accounting-2026-10-30.1`; schema remains 2. Ordinary usage rules, metadata-only persistence and access boundaries remain in effect.
- Keep the bounded reader nearly as fast as before. The first draft made a first read on this computer's real logs 37% slower (Python 3.14: 12.6 → 17.3 s). The nesting check now skips string bodies with a C-level regex instead of a per-character loop, row sizes use one shared encoder, and the archive's control-character check is a C-level search. Result: first read 12.8 s against 12.2 s for 0.2.14, later reads 3.35 s against 3.25 s, with identical sessions, tokens, calls, quality flags and quota states.
- Give the optional `zstandard` decoder its window limit in bytes. The first 0.2.15 commit passed kibibytes, which allowed only 128 KiB windows; the optional-decoder CI jobs rejected ordinary test logs on all three systems. A fake-module test now checks the value without installing the package.

## 0.2.14 — 2026-10-29 (candidate)

- Keep the newest session investigation when asynchronous replies finish out of order; an old request or failure cannot replace a newer selection. Preserve the selected project across a language reload while a scan is still in progress.
- Deny malformed/non-ASCII access tokens with an ordinary authentication response. Use the same strict language-query validation for individual session reads as for report reads.
- Bound metadata reads to the file size observed before opening and reject a changing file; keep the generation marker to 4 KiB. The archive's size limit remains enforced during a concurrent file growth.
- Treat excessively nested cache/archive/preference JSON as invalid metadata instead of aborting the scan. Disposable caches can rebuild; an invalid retention preference stays off until an explicit choice repairs it.
- Withhold combined quota values from more than one contributing selected local source group, including legacy samples without reset dates. Conventional active/archived Codex roots under one home stay one group. No account identity is collected or inferred.

## 0.2.13 — 2026-10-29 (candidate)

- Open versioned English/Turkish Help and the exact accounting contract from the page, offline, from the installed package.
- Pause and resume retained history with `pler archive off`/`on` or the page's collapsed "Local history and reader cache" section; pausing never deletes it. `pler cache reset` removes only the rebuildable Claude/Codex reader caches and keeps the archive, quota samples and preferences.
- Hide project names in the downloaded JSON by default (consistent aliases). Times, models and session codes remain; the file is reduced, not anonymous.
- Give distinct projects with the same short name stable opaque suffixes instead of merging them; separate repositories in the temporary folder stay separate.
- Link the data-quality warning to the affected sessions, with a list-only filter. Open a later re-edit session that lies outside the current filters by its opaque code.
- Report dated usage within the period from complete, unambiguous per-response records. JSON always carries it with coverage counts; the page and terminal show it only when every selected session could be dated.
- Compare session lengths only within one agent, known project and single model, with at least three sessions on each side.
- Withhold the current percentage and forecast when meter histories contradict each other (a reset moving back, a fall of more than 25 points within a window, different readings at one instant).
- Faster later reads: an intact reader cache is verified with one file digest instead of re-encoding every entry, and response ownership no longer re-merges a session's own source evidence. On this computer's real logs with Python 3.14 a later read fell from 4.1 to 3.3 s, with identical results.

The rules were fixed before measurement (`2f0689c`). The first real-data check hid both real Codex meters and left 75% of Claude responses undated, so the meter and dating rules and the display rule were corrected; see the correction note in [ACCOUNTING.md](ACCOUNTING.md). After the correction, the real meters match 0.2.12.

## 0.2.12 — 2026-10-29

- Observe when an independent, nonoverlapping session starts within seven days after another session ended and names the same edited target. The definition was committed before real measurement (`8917914`). Counts describe recorded edit intentions; they do not measure waste, savings, authorship or code quality.
- Show coverage, pending follow-up, exclusions and up to five earliest later-session matches, with opaque session codes, agents and whole-session recorded tokens/completeness. Filters select origins; the full selected-root timeline supplies later evidence. Page, terminal and JSON share the observation and fixed scan cutoff.
- Resolve edit paths at each record's working folder using the logged operating-system spelling. Windows drive paths compare without case on every viewing OS; POSIX paths preserve case. No source file, file-existence or Git query is used by the observation. Ambiguous targets, uncertain family history, overlapping spans and unverified/old-reader archive evidence are excluded.
- Preserve main-source evidence across all Claude native-session copies; filename order cannot turn a merged main/subagent session into an independent child.

Fixed real metadata produced identical per-session usage accounting in 0.2.11 and 0.2.12 (29 sessions, 9,371 recorded calls). See [aggregate evidence and limits](../reports/reedit-v1/REPORT.md).

## 0.2.11 — 2026-10-29

- Keep usage metadata after an agent deletes its logs. Claude Code deletes transcripts older than 30 days by default, so period totals used to shrink silently. Default and environment-selected roots now keep each file's allowlisted metadata in a bounded local archive (365 days unseen, 2,048 files, 64 MB). Deleted sources still count and are marked on the page, in the terminal report and in JSON. Existing cache entries are imported once, without reopening any log.
- Count a resumed session that copies archived replies once. Withhold anonymous archived quantities that cannot be proven disjoint, and mark old-reader, unreadable-source, evicted and unreadable-archive cases as incomplete.
- Clear the archive from the page, after confirmation, or with `pler archive clear`. Agent logs and quota samples are unchanged.
- Never archive folders named with `--claude-dir`/`--codex-dir`; they are one-off selections.
- An unchanged read neither rebuilds nor rewrites the archive. Session source evidence is merged in linear time. On this computer's real logs a warm read takes 4.1 s with a 24.5 MB archive, against 2.3 s without one; an earlier draft took 21 s.

See [evidence and limits](../reports/source-archive-v1/REPORT.md).

## 0.2.10 — 2026-10-28

- Read explicitly selected WSL log roots on Windows through either standard WSL host spelling. A per-scan capability covers only that subtree and requires a fresh running-distribution status before discovery and reader access. Ordinary UNC/device paths remain refused before probing; Git/project/cache paths stay strict.
- Use only the fixed, bounded System32 WSL status command, with no shell or distribution launch. Explain stopped/unavailable distributions in both languages. No automatic WSL discovery is performed.
- Preserve case-sensitive WSL file identities during discovery and reconciliation. Resolve a selected local link before its following parent-directory component instead of choosing another folder by early normalization.
- Keep root-owned operating-system links such as macOS `/var` → `/private/var` in their original spelling unless a later `..` needs the real parent. The first 0.2.10 commit resolved them always, which changed every reported macOS temporary path and failed five tests on macOS CI.

Real invented WSL records changed from zero sessions in 0.2.9 to two sessions and 350 tokens; both host spellings and both selection methods matched. Windows-from-Linux mount reading and case-only file names were verified separately. See [evidence and limits](../reports/wsl-roots-v1/REPORT.md).

## 0.2.9 — 2026-10-28 (local candidate)

- Follow the user's own link or junction to a log folder: `~/.claude`, `~/.codex`, their `projects`/`sessions` folders, `CLAUDE_CONFIG_DIR`, `CODEX_HOME`, `--claude-dir` and `--codex-dir`. Someone who moved these folders to another disk and left a link behind previously saw no records and an "UnsafePath" skip. Each link is read without being followed, so a target with network, volume or device syntax is refused before anything there is touched; loops stop after 32 links. Links inside a log folder, other Windows reparse points, project paths read from logs, Git metadata and the cache folder keep the previous rules.

## 0.2.8 — 2026-10-28 (local candidate)

- `pler demo` opens the page with invented Claude Code and Codex logs and an invented Git repository. The data is written into a `demo` folder inside PLER's cache folder; the agents' own folders and quota samples are never read. A banner on the page says the data is invented. The demo has two agents, four projects, a Codex quota forecast, an older-format Codex log with a data-quality warning, a session started in a parent folder, and commits on and off a branch. Each read recreates it relative to the current time. A folder that is not a PLER demo is never replaced.
- The Windows portable package adds `PLER-Demo.cmd`.
- The Git observations read "No longer on any branch: n" and "Could not be checked: n" in English, so a single commit reads correctly.

The demo is what the [pilot kit](../reports/pilot-kit-v1/REPORT.md) uses, so that participants can do every pilot task before deciding whether to look at their own records.

## 0.2.7 — 2026-10-28 (local candidate)

- For commits recorded during a session, show whether each is still on a local or remote-tracking branch, or was amended, rebased, reset or left on a deleted branch. Commit objects are read directly: loose files and version-2 packs, including offset and reference deltas, SHA-1 and SHA-256. Only parent ids and committer time are used; names, email addresses, messages, trees and files are never kept or opened. Missing or shallow history, borrowed objects, refused links and the 20,000-commit bound give `unknown`, never a guess.
- The period summary adds an observation: how many sessions recorded how many commits, each counted once, and how many are still on a branch. The token share of those sessions is shown only when usage is complete.
- Session JSON adds `commits` counts and a per-event `on_branch`. The view adds `git_outcome`. Accounting and export schema 2 are unchanged.

The branch answers matched git's own on invented repositories with amend, reset, rebase and a deleted branch, for loose objects, a pack and an aggressive delta pack, in SHA-1 and SHA-256. On a 30,000-commit pack, a recent commit was found in 0.07 s; a dropped one was confirmed in 0.56 s; the worst case stopped at the bound after 3.3 s. On this computer's logs, 4 sessions recorded 68 commits and all 68 are still on a branch. Tests: 248 on Windows with Python 3.9 and 3.12, 257 with Python 3.14 on Windows and Linux, plus 18 browser-logic tests. See the [evidence](../reports/git-outcome-v1/REPORT.md).

## 0.2.6 — 2026-10-28 (local candidate)

- Link each session to the Git repositories holding the files it edited, not only to its working folder. An agent started in a parent folder, or a session whose project is unknown, now shows the commits recorded in the repository it changed. Events of several linked repositories are merged. The page names how many repositories were checked, never their paths.
- Read the target files of Codex patches (`*** Add/Update/Delete File`, `*** Move to`), also when the patch sits inside a code or JSON string. Only paths are kept, never the patch body. Codex sessions now report edited files like Claude Code sessions.
- Advance the parser version to `accounting-2026-10-28.4`; token and call totals are unchanged and export schema 2 is unchanged. The Codex metadata cache rebuilds once.

On this computer's real logs, sessions with readable Git history went from 1 to 6 and sessions with Git events during their time from 0 to 4. Those 4 sessions hold 69% of the tokens. This session's view shows exactly the 4 commits made in the product repository during it. The source passes 237 tests on Windows with Python 3.9 and 3.12, 246 with Python 3.14 on Windows and Linux, plus 18 browser-logic tests. See the [Git link evidence](../reports/git-links-v1/REPORT.md).

## 0.2.5 — 2026-10-28 (local candidate)

- Disable the metadata and Claude quota caches when `PLER_CACHE_DIR` or the default cache base names a network location, or a user link or junction leads to it, instead of reading or writing there. Revalidate the cache and quota file paths before every write, and remove failed temporary files only at a validated location.
- Mark retained Codex parent/child cumulative histories, cumulative children with a missing parent, contradictory, self-referential or cyclic outside parents and compaction-only files as incomplete or unknown instead of complete. Keep sessions whose only activity is an abort, tool call, quota sample or completion. Subagent threads inside one merged session are not parent evidence, so ordinary multi-agent sessions are not flagged.
- On macOS and Linux, follow root-owned operating-system links such as macOS `/var` → `/private/var`; user-owned links and every Windows link or junction remain refused. Treat two leading slashes or backslashes in any mix as a network path on every platform.
- Advance the parser version to `accounting-2026-10-28.3`; export schema 2 is unchanged. Affected metadata caches rebuild once.
- The Windows candidate builder also accepts the official CPython embeddable package and bundles the 3.14 zstd module. It checks for an existing archive before building, and names a versioned folder's ZIP correctly. With CPython 3.14.10 the Python-free candidate's first read on the test computer fell from 23.1 to 7.2 seconds, with identical totals.
- Add a prepared, manually dispatched CI workflow for Windows, macOS and Linux on Python 3.9, 3.12 and 3.14, release/acceptance/pilot/support procedures, and an offline builder for a private, unsigned Windows x64 candidate that bundles an existing CPython 3.12 runtime.

The source passes 227 tests on Windows with Python 3.9 and 3.12 (the nine Python 3.14 decoder tests are skipped there), 236 on Linux (WSL2 Ubuntu, Python 3.14.4, standard-library zstd decoder), including a macOS-style system-link temporary folder, plus 18 browser-logic tests. The installed wheel passes 227 tests. On 128 fixed real Codex files sessions, tokens and calls are unchanged from 0.2.4. The portable candidate ran without any Python on `PATH`; it is unsigned and has not been tried on a clean machine. In the CI workflow all 12 jobs pass: source and installed-wheel suites on Windows Server 2025, Ubuntu 24.04 and macOS 26 arm64 with Python 3.9, 3.12, 3.14 and the optional `zstandard` reader. See the [completion evidence](../reports/completion-v1/REPORT.md).

## 0.2.4 — 2026-10-28 (local candidate)

- Collect all valid nonempty Codex session/context working folders before deciding project attribution. Conflicting projects remain unknown with incomplete attribution instead of the first file choosing a project. Empty metadata folders cannot hide valid context evidence.
- Compare safely observed Git roots and host-equivalent path spellings as project evidence; do not use the UI's shared temporary-folder bucket as proof of common ownership. Preserve one count for repeated response usage and reapply the rule to cached metadata.
- Generalize the existing attribution explanation to cover context conflicts as well as copied records. Advance the parser version to `accounting-2026-10-28.2`; export schema 2 is unchanged. Affected metadata caches rebuild once.

The source passes 188 tests on each of Python 3.9 and 3.12, plus 18 browser-logic tests. Package and local runtime checks are recorded separately in the [project attribution evidence](../reports/project-attribution-v1/REPORT.md). Arbitrary history reconciliation, first-read performance, native distribution and professional acceptance remain open. A separately observed explicitly configured network cache target remains an open follow-up.

## 0.2.3 — 2026-10-28 (local candidate)

- Select a real dominating usage snapshot with a linear verification pass instead of comparing every pair of unique checkpoints. Crossing snapshots remain unresolved; duplicate and iterable behavior is preserved.
- Use the standard JSON encoder's fast whole-document path for metadata cache writes, followed by the same temporary-file replacement. A serialization memory failure preserves the previous cache and extracted metadata.
- Bound the batched Huffman literal lookup at 12 bits instead of 14. The largest auxiliary table has one quarter as many entries; stream, frame-size and checksum validation remain enabled. All 128 fixed compressed archives decoded to identical bytes in a paired comparison.

Accounting schema and interpretation are unchanged. Affected caches rebuild once. Large dependency-free first reads remain slow; measured gains are specific to the recorded datasets, not a universal startup guarantee. See [performance evidence](../reports/cold-start-v1/REPORT.md).

## 0.2.2 — 2026-10-28 (local candidate)

- Reconcile a narrow Claude zeroed-copy shape only with an exact witness in the selected valid usage snapshot of the same reply and model. Count the verified reply once and retain a fixed explanation. Unmatched candidates and unrelated corruption remain incomplete; cached candidates are checked again against the current source set.
- Validate only the Codex identity fields actually consumed by each record type. Unused identity-shaped fields cannot reject otherwise valid usage; consumed invalid identities and broken JSON still warn.
- Advance the parser version to `accounting-2026-10-28.1`. Schema 2 is unchanged; `reconciled_copies` is an additional quality explanation, and unresolved zeroed copies have a specific source reason.

The diagnosed local file's calls and tokens remain identical; its repeated copies are now reconciled instead of marking the whole file unreadable. This does not resolve arbitrary fork/compaction history or establish account-wide completeness. Affected metadata caches rebuild once; no original log is changed.

## 0.2.1 — 2026-10-28 (local candidate)

- Show download preparation, prevent duplicate pending exports and retain a visible retry link to the prepared JSON. Clear outdated links when filters change or logs are explicitly refreshed; discard a pending result if its selection changed. Do not label a prepared download as saved to disk.
- Keep keyboard focus on newly revealed sessions after Show more, and restore action focus after refresh/export when the user has not moved elsewhere. Return focus to a persistent control when a project/empty-filter action replaces its origin.
- Make the session table a named keyboard-focusable scroll region with instructions. Use a single filter column on the narrowest screens and larger mobile form text.
- Reload when a valid startup access fragment is opened in an already loaded tab, so a restarted process's new credential is consumed.

Accounting schema and parser rules are unchanged from 0.2.0. These are local usage-flow corrections; real-device accessibility certification and professional acceptance are not established.

## 0.2.0 — 2026-10-27 (local candidate)

- Merge files with the same Codex session ID and reconcile compatible cumulative checkpoints with per-response usage. Retain the largest compatible actual response snapshot for both agents. Never assign legacy cumulative usage to the last model.
- Deduplicate identified Codex turns and tool calls alongside responses. Conflicting copied ownership uses explicit uncertainty and unknown project attribution. Validate numeric usage types, ranges and cache/reasoning relationships; invalid rows produce coverage warnings.
- Show data-quality warnings in both languages; export the app, parser and schema versions. Suppress comparisons with incomplete usage/ownership and remove the invalid error/abort percentage. Describe session-length differences as uncontrolled observations.
- Require the per-process startup access link for report reads and JSON exports, as well as mutations. Remove its fragment from the visible address; retain it in tab session storage. Public HTML no longer supplies the credential.
- Discover regular local logs without following network paths, symlinks or junctions. Report unsupported locations instead of probing them.

**Data contract change:** schema 2 can change session counts, model/project buckets and totals relative to older reports. See [ACCOUNTING.md](ACCOUNTING.md). Ambiguous fork/compaction history remains explicitly incomplete. This candidate is not a public release or proof of professional acceptance.

## 0.1.2 — 2026-10-26

- Cache Claude Code metadata as well as Codex metadata. Unchanged conversations are not parsed again; copied response deduplication and partial-file warnings persist. Prompt, reply, command and tool output text are discarded before caching.
- Require complete compressed frames and matching declared content sizes; verify optional zstd content checksums in the built-in decoder. Reject truncated checksum/skippable data and invalid frame flags. The optional zstandard adapter requires each frame's end and reads subsequent frames too.
- Use larger literal decoding lookups only when a block is large enough to amortize their construction. The first read of a large archive remains slow; improved warm reads do not establish a fast cold start.
- Invalidate caches when decoding/validation helpers change. Do not save a growing log under an old signature or cache a temporary access failure. Remove failed cache-write temporary files when allowed.
- Reject UNC project paths before filesystem probes and refuse symlink/junction ancestors or Git markers during project grouping.

No new dependencies or product controls. The update rebuilds affected caches once. The native installer, other operating systems, desktop Claude quota and professional usefulness remain unverified.

## 0.1.1 — 2026-10-26

Reliability and privacy corrections for local pilot use. This release does not establish company-wide readiness.

- Rebuild damaged or legacy Codex cache entries from the original logs. A checksum detects accidental changes to cached numbers; it is not an authentication mechanism.
- Retain valid records from partially read files and count each affected file once. Broken JSON, truncated rows and invalid response identities are reported instead of crashing or silently omitting the warning. Codex cache hits retain that warning.
- Deduplicate Claude prompts and tool calls that have stable IDs across copied logs; assign tool metadata to the same owner as its response. Records without stable IDs retain their previous counting behavior.
- Accept sessions with unknown dates alongside dated sessions without inventing visible dates.
- Keep a running server's HTML, JavaScript and CSS fixed until restart, so editing the installation does not mix a new page with an old backend.
- Keep the desktop local-only label readable; its text no longer receives the status dot's dimensions.
- Distinguish displayed rows from different source logs even when copied provider session IDs match. Opaque row codes include the source identity in their hash, without exporting the source path; moving a log can change its code.

### Terminal JSON compatibility

`pler report --json --sessions` now uses the page's explicit session projection. Source paths, raw session IDs, parent IDs, branch names, edited file paths, tool names and arbitrary notes are no longer exposed. Session and project IDs are opaque hashes; edited files and tools are counts. The source list contains failure reasons without local file paths. Project names are shortened, not anonymized.

The top-level `days` array was removed because its whole-session buckets could be mistaken for daily spending. `period.mode` is `active_sessions_full_totals`. Adapt scripts that consumed the removed fields. Existing period, agent, project and session totals continue to cover the selected whole sessions. As in 0.1.0, partial running dollar figures are excluded.

### Update

Close PLER, reinstall from the checkout with `pip install --upgrade ./product`, then reopen it. Check `pler --version`. No remote distribution was published as part of this release.
