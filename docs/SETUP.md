# Windows kurulumu — ücretsiz beta 0.9.30

Roodof-Setup-0.9.30.exe kullanıcı hesabına kurar; yönetici izni istemez. Paket dosyaları manifest hash değerleriyle doğrulanır. Normal kurulum bitince Roodof açılır; Başlat/masaüstü kısayolları ve Windows Uygulamalar kaydı oluşturulur. Genel indirme adresi: https://roodof.com/downloads/Roodof-Setup-0.9.30.exe. Taşınabilir ZIP ve isteğe bağlı Python sürümü de bulunur.

Program `%LOCALAPPDATA%\Programs\Roodof\program`, normal geçmiş `%LOCALAPPDATA%\pler` altındadır. Kurulum geçmişe dokunmaz. Aynı veya daha yeni kurulu sürüm korunur; daha eski program yalnız kapalıyken değiştirilir. Kurulum ve kaldırma aynı işlem kilidini kullanır. Çalışan program/güncelleyici çalışma kilidi yenilemeyi durdurur. Kurulum kökü bir klasör bağlantısıysa işlem durur; temizlik alt bağlantıların hedeflerini izlemez.

Windows Uygulamalar üzerinden kaldırma geçmişi varsayılan olarak saklar; geçmiş silme ayrı açık seçimdir. Kaldırıcı geçici kopyasının temizliği yalnız doğrulanan kendi dosyasına literal yol ile yapılır. Uygulama içi güncellemeler mevcut kurulum kaydının sürümünü günceller; taşınabilir ZIP klasörü yeni kurulum kaydı oluşturmaz.

Geliştirici doğrulaması yalıtılmış dosyalarla yapılır. Bu teslim kullanıcının gerçek kurulumuna uygulanmadı. [0.9.30 yayın kaydı](https://github.com/roodof/roodof/releases/tag/v0.9.30). Temiz Windows kurulum/güncelleme/kaldırma kabulü SON görevdir. Setup Authenticode ile imzalanmış değildir; yayıncı imzası kararı R02 açık. Mevcut özel geçmiş yedeğini koru.
