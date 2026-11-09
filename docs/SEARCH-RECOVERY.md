# Sonuçsuz aramada sonraki adım — 0.9.16

Sonuçsuz yerel arama ve dönem/ajan/projeyle boşalan kapsam aynı kurtarma eylemlerini kullanır. Geçerli seçim özeti gösterilir; boş sanal tablo gizlenir ve sonuç gelince aynı tablo geri açılır. En fazla iki ana eylem görünür; diğerleri native details içindedir.

- Tüm dönemlerde/projelerde/iki ajanda ara yalnız ilgili alanı değiştirir. Mevcut sorgu, kalan filtreler ve sıralama korunur. Aynı mevcut controller üzerinden tek GET yapılır; log taraması veya yazma POST’u başlatılmaz.
- Kayıt durumu filtresini kaldır yerel filtreyi değiştirir, GET yapmaz. Aramayı temizle ve Escape yalnız sorguyu temizler; kalite filtresini korur. Tüm filtreleri temizle ayrı, açık bir toplu sıfırlamadır.
- Hiç kayıt kaynağı bulunmaması, okunamayan kayıtlar, dosya bulunup kullanılabilir oturum çıkmaması ve sonuç okuma hatası ayrı açıklanır. Sadece sorgu eşleşmedi diye kayıt kaynağı eksik denmez. Kaynak ekleme/tanılama mevcut güvenli Ayarlar kısayollarını açar.
- Okuma hatasında seçim korunur; yeniden dene aynı kapsamı GET ile okur. Yenileme/scanning sırasında eylemler kilitlenir. Önceki snapshot yanlış filtrede yeni sonuç diye sunulmaz.

Yeni module committed data/sessions olaylarını tüketir; yeni projection eski snapshot ile eşleşmiyorsa veri commit’ini bekler. Controller’ın yeniden yazdığı eski boş-durum metinleri güncel durumla yeniden eşitlenir. Controller-owned clear/reset ID’leri ilk snapshot öncesinden itibaren DOM’da kalır; olay bağları kopmaz. Yeni depolama alanı veya backend endpoint’i yok. Arama sadece bellektedir, API URL’sine/kalıcı tercihlere eklenmez.400/work-view.jsx ve iş bağlantıları aynı.

[Geliştirici kanıtı](../../reports/search-recovery-v1/REPORT.md). Public beta0.9.11; gerçek ajan/WSL/bağımsız kullanıcı/temiz Windows kabulü SON görevdir. İlk kullanım sadeleştirmesi ve diğer UX önerileri bu kapsamda yapılmış sayılmaz.
