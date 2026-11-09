# Sade iş bağlantısı ve gruplu Ayarlar — 0.9.15

Oturum ayrıntısında bağlı işler ve ayırma kontrolleri görünür. Bir işe bağla/başka bir işe bağla açılır bölümü, seçilen mevcut/yeni iş formunu gösterir. Bağlanabilecek iş yoksa yeni iş formu tek seçenektir. Açılma, mod, başlık taslağı ve seçilen iş çalışma belleğinde oturum bazındadır; gruplama yeni kalıcı veri biçimi üretmez. Katlama ve yeniden çizim taslağı korur. Başarısız kayıtta mevcut bağlantı değişmez. İşlerim → Oturum ekle, seçilen işi doldurup düzenleyiciyi açar. İş seçicisi ve400 sınırı aynı dosya/baytlardadır.

Ayarlar, mevcut form düğümlerini bir kez üç tab paneline taşır:

- **Kayıt kaynakları:** klasörler ve başlangıç/tur yardımı.
- **Kullanım uyarıları:** mevcut izleme listesi ve oturum aramaya dönüş.
- **Yedek ve destek:** özel yedek/kurtarma, yerel geçmiş/önbellek, taşınan oturum ayarları, okuma tanılaması ve kullanım raporu. Araçlar bağımsız açılır; birini açmak diğer taslağı kapatmaz.

Sekmeler role=tablist/tab/tabpanel, aria-selected/controls/labelledby, tek etkin tabIndex ve Left/Right/Home/End gezinmesini kullanır. Grup değişimi formu yeniden oluşturmaz, backend yazısı veya kaynak taraması başlatmaz. Seçili grup bu çalışma boyunca hatırlanır; yeni kalıcı tercih alanı eklenmedi. Kaynak/tanılama/yeniden bağlama kısayolları doğru grubu ve üst açılır bölümü açtıktan sonra hedefe odaklanır. Başlangıçtaki geçmiş seçimi sorunu da kurtarmayı görünür yapar. Snapshot olmadan Ayarlar ve kurtarma erişimi korunur; işlem izinleri mevcut denetimlerde kalır.

Yedek paneli, eski metadata details bölümünden destek satırına taşınır. Bekleyen yedek/aktarım onayı, eski inceleme süresi, açık geçmişi koruma, kontrol kilitleri ve indirme davranışları aynı kalır. Sayım, oturum kimliği, backend endpoint’leri ve masaüstü izinleri değişmez.

[Geliştirici kanıtı](../../reports/settings-work-v1/REPORT.md). Public beta0.9.11; gerçek kullanıcı, gerçek ajan/WSL, fiziksel erişilebilirlik ve temiz Windows kabulü SON görevdir. Önceki0.9.14 çalışma ağacı korunur; kaynaklar bu görevde commit/push edilmez.
