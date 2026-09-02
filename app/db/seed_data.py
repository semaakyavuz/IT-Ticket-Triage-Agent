"""Mock geçmiş IT ticket verisi.

Gerçek bir ServiceNow/ITSM entegrasyonu yerine, RAG ve triage akışını
göstermek için elle yazılmış 28 kayıtlık örnek veri seti.
"""

TICKETS = [
    {
        "id": 1,
        "title": "VPN bağlantısı kurulamıyor",
        "description": "Kullanıcı ofis dışından VPN'e bağlanmaya çalışıyor ancak "
        "'bağlantı zaman aşımı' hatası alıyor.",
        "category": "ağ",
        "priority": "yüksek",
        "solution": "VPN istemcisi güncellendi ve kullanıcı profili yeniden "
        "oluşturuldu, sorun çözüldü.",
        "team": "Network Operasyon Ekibi",
    },
    {
        "id": 2,
        "title": "Wi-Fi sürekli kopuyor",
        "description": "Ofis 3. katta kablosuz bağlantı dakikada bir kopup "
        "tekrar bağlanıyor.",
        "category": "ağ",
        "priority": "orta",
        "solution": "Kat için ayrı access point tanımlandı, kanal çakışması "
        "giderildi.",
        "team": "Network Operasyon Ekibi",
    },
    {
        "id": 3,
        "title": "Yazıcıya çıktı gönderilemiyor",
        "description": "Muhasebe departmanındaki ağ yazıcısı 'offline' "
        "görünüyor, çıktı kuyrukta bekliyor.",
        "category": "donanım",
        "priority": "orta",
        "solution": "Yazıcının IP adresi değişmiş, sürücü ayarları "
        "güncellendi.",
        "team": "Donanım Destek Ekibi",
    },
    {
        "id": 4,
        "title": "Laptop açılmıyor, güç ışığı yanmıyor",
        "description": "Kullanıcının dizüstü bilgisayarı hiç açılmıyor, şarj "
        "göstergesi de yanmıyor.",
        "category": "donanım",
        "priority": "yüksek",
        "solution": "Adaptör arızalıydı, yenisiyle değiştirildi.",
        "team": "Donanım Destek Ekibi",
    },
    {
        "id": 5,
        "title": "Excel dosyası açılırken çöküyor",
        "description": "Büyük boyutlu bir Excel dosyası açılırken uygulama "
        "beklenmedik şekilde kapanıyor.",
        "category": "yazılım",
        "priority": "orta",
        "solution": "Office güncellemesi yapıldı ve eklenti devre dışı "
        "bırakıldı, sorun tekrarlamadı.",
        "team": "Uygulama Destek Ekibi",
    },
    {
        "id": 6,
        "title": "Şifremi unuttum, hesabıma giremiyorum",
        "description": "Kullanıcı Active Directory şifresini unuttu, giriş "
        "yapamıyor.",
        "category": "erişim",
        "priority": "orta",
        "solution": "Self servis şifre sıfırlama portalından yeni şifre "
        "oluşturuldu.",
        "team": "Erişim ve Kimlik Yönetimi Ekibi",
    },
    {
        "id": 7,
        "title": "Yeni işe başlayan için hesap açılması gerekiyor",
        "description": "Yeni personel için AD hesabı, e-posta ve gerekli "
        "klasör yetkileri talep ediliyor.",
        "category": "erişim",
        "priority": "düşük",
        "solution": "Standart onboarding şablonuna göre hesap oluşturuldu ve "
        "yetkiler tanımlandı.",
        "team": "Erişim ve Kimlik Yönetimi Ekibi",
    },
    {
        "id": 8,
        "title": "Üretim sunucusu erişilemez durumda",
        "description": "Üretim ortamındaki uygulama sunucusuna hem RDP hem de "
        "web arayüzünden erişilemiyor, tüm ekip etkilendi.",
        "category": "ağ",
        "priority": "yüksek",
        "solution": "Switch portu arızalıydı, yedek porta alınarak erişim "
        "geri sağlandı.",
        "team": "Network Operasyon Ekibi",
    },
    {
        "id": 9,
        "title": "Monitör görüntü vermiyor",
        "description": "Masaüstü bilgisayara bağlı ikinci monitör hiç görüntü "
        "vermiyor.",
        "category": "donanım",
        "priority": "düşük",
        "solution": "HDMI kablosu değiştirildi, sorun kablodan kaynaklanıyormuş.",
        "team": "Donanım Destek Ekibi",
    },
    {
        "id": 10,
        "title": "Outlook e-posta göndermiyor",
        "description": "Kullanıcı e-posta gönderdiğinde 'gönderilemedi' hatası "
        "alıyor, gelen kutusu normal çalışıyor.",
        "category": "yazılım",
        "priority": "orta",
        "solution": "Outlook profili yeniden oluşturuldu, önbellek temizlendi.",
        "team": "Uygulama Destek Ekibi",
    },
    {
        "id": 11,
        "title": "CRM uygulaması çok yavaş açılıyor",
        "description": "Şirket içi CRM uygulaması her gün sabah saatlerinde "
        "çok yavaş yükleniyor.",
        "category": "yazılım",
        "priority": "orta",
        "solution": "Uygulama sunucusundaki bellek kullanımı optimize edildi.",
        "team": "Uygulama Destek Ekibi",
    },
    {
        "id": 12,
        "title": "Klavye bazı tuşlara basılınca çalışmıyor",
        "description": "Dizüstü bilgisayarın dahili klavyesinde birkaç tuş "
        "tepki vermiyor.",
        "category": "donanım",
        "priority": "düşük",
        "solution": "Harici klavye verildi, dahili klavye değişimi için "
        "bakıma alındı.",
        "team": "Donanım Destek Ekibi",
    },
    {
        "id": 13,
        "title": "Paylaşımlı sürücüye erişim yetkisi yok",
        "description": "Kullanıcı departman paylaşım sürücüsündeki yeni "
        "klasöre erişemiyor, 'yetki yok' hatası alıyor.",
        "category": "erişim",
        "priority": "düşük",
        "solution": "Klasöre kullanıcı grubu için okuma/yazma yetkisi "
        "tanımlandı.",
        "team": "Erişim ve Kimlik Yönetimi Ekibi",
    },
    {
        "id": 14,
        "title": "İnternet bağlantısı tüm ofiste kesildi",
        "description": "Sabah saatlerinde tüm ofiste internet erişimi aniden "
        "kesildi, hiçbir kullanıcı çalışamıyor.",
        "category": "ağ",
        "priority": "yüksek",
        "solution": "ISP kaynaklı kesinti tespit edildi, yedek hat devreye "
        "alındı.",
        "team": "Network Operasyon Ekibi",
    },
    {
        "id": 15,
        "title": "Mouse bazen tepki vermiyor",
        "description": "Kablosuz mouse ara sıra donuyor, tıklamalar gecikmeli "
        "algılanıyor.",
        "category": "donanım",
        "priority": "düşük",
        "solution": "Pil değiştirildi ve alıcı farklı bir USB portuna takıldı.",
        "team": "Donanım Destek Ekibi",
    },
    {
        "id": 16,
        "title": "ERP sisteminde fatura kesilemiyor",
        "description": "Muhasebe ekibi ERP üzerinden fatura keserken "
        "'veritabanı hatası' alıyor, ay sonu kapanışı riske giriyor.",
        "category": "yazılım",
        "priority": "yüksek",
        "solution": "Veritabanı bağlantı havuzu yeniden başlatıldı, sorunlu "
        "oturumlar temizlendi.",
        "team": "Uygulama Destek Ekibi",
    },
    {
        "id": 17,
        "title": "Yeni yazılım kurulumu talebi",
        "description": "Kullanıcı departmanı için lisanslı bir tasarım "
        "yazılımının kurulmasını talep ediyor.",
        "category": "yazılım",
        "priority": "düşük",
        "solution": "Lisans temin edilip standart imaj üzerinden kurulum "
        "yapıldı.",
        "team": "Uygulama Destek Ekibi",
    },
    {
        "id": 18,
        "title": "Uzaktan masaüstü bağlantısı kopuyor",
        "description": "Kullanıcı uzak masaüstü ile şirket sunucusuna "
        "bağlanıyor ancak bağlantı sık sık kopuyor.",
        "category": "ağ",
        "priority": "orta",
        "solution": "VPN MTU ayarı düşürülerek paket parçalanması giderildi.",
        "team": "Network Operasyon Ekibi",
    },
    {
        "id": 19,
        "title": "Hesap kilitlendi, çok fazla yanlış deneme",
        "description": "Kullanıcı yanlış şifre denemeleri sonucu AD hesabı "
        "kilitlendi.",
        "category": "erişim",
        "priority": "orta",
        "solution": "Hesap kilidi kaldırıldı ve kullanıcıya güvenli şifre "
        "oluşturma rehberi iletildi.",
        "team": "Erişim ve Kimlik Yönetimi Ekibi",
    },
    {
        "id": 20,
        "title": "Sunucu odası klima arızası, sıcaklık yükseliyor",
        "description": "Sunucu odasındaki klima arızalandı, sıcaklık kritik "
        "seviyeye yaklaşıyor, donanımlar risk altında.",
        "category": "donanım",
        "priority": "yüksek",
        "solution": "Yedek klima devreye alındı ve teknik servis çağrıldı.",
        "team": "Donanım Destek Ekibi",
    },
    {
        "id": 21,
        "title": "Teams'te ekran paylaşımı çalışmıyor",
        "description": "Kullanıcı Microsoft Teams toplantısında ekranını "
        "paylaşamıyor, buton tepki vermiyor.",
        "category": "yazılım",
        "priority": "düşük",
        "solution": "Teams uygulaması güncellendi ve önbelleği temizlendi.",
        "team": "Uygulama Destek Ekibi",
    },
    {
        "id": 22,
        "title": "Yetki yükseltme talebi - yönetici hakları",
        "description": "Geliştirici kendi bilgisayarında yazılım "
        "kurabilmek için yerel yönetici hakkı talep ediyor.",
        "category": "erişim",
        "priority": "düşük",
        "solution": "Talep onaylandı, ilgili kullanıcı yerel admin grubuna "
        "eklendi.",
        "team": "Erişim ve Kimlik Yönetimi Ekibi",
    },
    {
        "id": 23,
        "title": "Switch arızası nedeniyle kat ağı çöktü",
        "description": "2. kattaki ana switch arızalandı, o kattaki tüm "
        "bilgisayarlar ağa bağlanamıyor.",
        "category": "ağ",
        "priority": "yüksek",
        "solution": "Switch yedeğiyle değiştirildi, port konfigürasyonları "
        "geri yüklendi.",
        "team": "Network Operasyon Ekibi",
    },
    {
        "id": 24,
        "title": "Harici disk tanınmıyor",
        "description": "Kullanıcının USB harici diski bilgisayara "
        "takıldığında tanınmıyor.",
        "category": "donanım",
        "priority": "düşük",
        "solution": "Farklı bir USB portu ve kabloyla test edildi, sorun "
        "çözüldü.",
        "team": "Donanım Destek Ekibi",
    },
    {
        "id": 25,
        "title": "Antivirüs yazılımı sürekli uyarı veriyor",
        "description": "Kullanıcının bilgisayarında antivirüs yazılımı "
        "zararsız bir uygulamayı sürekli tehdit olarak işaretliyor.",
        "category": "yazılım",
        "priority": "orta",
        "solution": "Uygulama güvenilir listesine eklendi, tarama ayarları "
        "güncellendi.",
        "team": "Uygulama Destek Ekibi",
    },
    {
        "id": 26,
        "title": "Ortak yazıcıdan renkli çıktı alınamıyor",
        "description": "Kat yazıcısından siyah beyaz çıktı alınabiliyor ama "
        "renkli çıktılar boş çıkıyor.",
        "category": "donanım",
        "priority": "düşük",
        "solution": "Renkli toner kartuşu değiştirildi.",
        "team": "Donanım Destek Ekibi",
    },
    {
        "id": 27,
        "title": "Şirket portalına giriş yapılamıyor - SSO hatası",
        "description": "Kullanıcı SSO ile şirket portalına giriş yapmaya "
        "çalıştığında 'oturum doğrulanamadı' hatası alıyor.",
        "category": "erişim",
        "priority": "orta",
        "solution": "Kimlik sağlayıcı önbelleği temizlendi, kullanıcı "
        "oturumu sıfırlandı.",
        "team": "Erişim ve Kimlik Yönetimi Ekibi",
    },
    {
        "id": 28,
        "title": "DNS çözümlemesi bazı sitelerde başarısız",
        "description": "Kullanıcılar bazı iç sistemlere alan adı ile "
        "erişemiyor, IP ile erişim çalışıyor.",
        "category": "ağ",
        "priority": "orta",
        "solution": "DNS sunucusundaki eksik kayıt eklendi ve önbellek "
        "temizlendi.",
        "team": "Network Operasyon Ekibi",
    },
]
