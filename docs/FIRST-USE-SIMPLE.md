# Tek ana eylemli ilk kullanım — 0.9.17

UX3 arama çıkışları korunur. UX4, mevcut ilk kullanım panelinde tek bir sabit ana düğme kullanır:

| Durum | Ana eylem |
|---|---|
| İlk okuma henüz tamamlanmadı veya sürüyor | Okunuyor, düğme kilitli |
| Başarılı snapshot’ta oturum var ve okuma sorunu yok | Oturumlarını gör |
| Başarılı snapshot’ta oturum/dosya yok | Kayıt klasörü ekle |
| Okuma hatası, okunamayan kaynak veya dosya bulunup kullanılabilir oturum çıkmaması | Sorunu incele |

Sayılar ekran filtrelerinden bağımsız setup özetinden gelir. Saklanan geçmiş, canlı kayıt gibi adlandırılmaz. Sorun öne çıktığında bulunabilen veya önceki snapshot’taki oturumlar Diğer seçenekler altında erişilir. Yeniden arama, yardım ve şimdilik geçme de ikincil bölümde kalır. Tur Ayarlar’da, yalnız açık kullanıcı eylemiyle başlar.

Ana düğme yeniden oluşturulmaz; güncel duruma göre etiketi ve eylemi değişir. Okuma sırasında kilitlenir; kaynağın eksik olduğu erken varsayılmaz. Kaynak/tanılama mevcut güvenli Ayarlar yollarına gider. Bu yollara gitmek setupDone yazmaz. Oturumları görme veya açık geçme mevcut sınırlı görünüm tercihine setupDone yazar; normal masaüstü yeniden açılışında hatırlanır. Oturum girişi mevcut tüm-dönem seçimini kullanır. Backend, kaynak tarama izinleri ve400 iş seçicisi aynı.

[Geliştirici kanıtı](../../reports/first-use-simple-v1/REPORT.md). Public beta0.9.11; gerçek kullanıcı/ajan/WSL/ekran okuyucu/temiz Windows kabulü SON görevdir. UX5 kavram adları ve UX6 yardımcı tipografi bu teslimde uygulanmış sayılmaz.
