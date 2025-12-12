# Eylül 2023 Finansal Anomali Özet Raporu

---

## Genel Değerlendirme

Eylül 2023 dönemi gelir ve giderlerde çok sayıda dönemsel ve tek seferlik dalgalanma göstermektedir. Net satışlarda hafif artış gözlenirken yurtiçi satışlar ve iadelerde belirgin azalış, bazı gider kalemlerinde (araç, danışmanlık, temsil, yemek) ise önemli artışlar mevcuttur. Birkaç kalemde aynı tarihte tekrarlayan büyük kayıtlar ve yüksek müşteri yoğunlaşması veri kalitesi ve kayıt/tahsilat süreçlerinde risk işaretleri ortaya koymaktadır.

## Tespit Edilen Anomaliler

### 1. temsil ağırlama giderleri

**Değişim:** %7.9 artış

**Neden Anomali?**
> Yıllık bazda olağanüstü artış (~%13.530) ve 3 aylık hareketli ortalamadan büyük sapma (~+106%) gösterdi; Z-skoru tetik eşiğine yakın olması ile birlikte 'yoy_and_rolling' sinyali oluştu.

**Kök Neden Analizi:**
> Eylül 2023'te temsil ağırlama giderleri 225,215.43'ten 243,106.77'ye yükselmiş, artışın ana nedenleri 123,556.06 tutarlı "2023/EYLUL UCRET BORDROSU" (%50.8) ve 91,376.36 tutarlı "SET KURUMSAL HIZMETLER TIC.A.S." ödemeleridir.

### 2. faiz gelirleri

**Değişim:** %-1.1 azalış

**Neden Anomali?**
> YoY değişim çok yüksek (%+2,482) ve cari değer 3 aylık ortalamanın ~+140.8% üzerinde; aşırı yıllık büyüme ve hareketli ortalamadan büyük sapma nedeniyle 'yoy_and_rolling' olarak işaretlendi.

**Kök Neden Analizi:**
> Faiz gelirleri 33,267.0 TL olup, bir önceki ay 33,625.44 TL’ye kıyasla hafif azalma göstermiştir. Azalışın nedeni N KOLAY BONO SATIŞ %36 FAİZ ORANI işlemlerinin ay içindeki tutar ve zamanlama farklılıkları ile kısmi kayıt tekrarları/dağılım değişiklikleridir.

### 3. araç giderleri

**Değişim:** %73.1 artış

**Neden Anomali?**
> Yıllık değişim çok yüksek (%+510) ve 3 aylık hareketli ortalamadan sapma ~55% (her iki sinyal birleşimiyle 'yoy_and_rolling' olarak tespit edildi).

**Kök Neden Analizi:**
> Araç giderleri 24,449.9'dan 42,334.04'e yükselmiş; artışın ana nedeni OTOKOÇ OTOMOTİV TİC.A.Ş. ödemeleri (10,879.91 TL) olup ayrıca EDENRED KURUMSAL ve FULLJET akaryakıt ödemeleri katkı sağlamıştır. Kanıtlarda 2023-09-01 tarihli iki adet 10,000 TL'lik OTOKOÇ ödemesi bulunmaktadır.

### 4. net satışlar

**Değişim:** %3.3 artış

**Neden Anomali?**
> Ana tetikleyici, yıllık bazda çok yüksek artış (%+236.8) olup diğer göstergeler normal; bu nedenle 'yoy' sinyali ile anomali raporlandı.

**Kök Neden Analizi:**
> Net satışlar 4,255,403.38'den 4,396,574.88'e yükselmiş; artış büyük tek seferlik tahsilatlardan kaynaklanmakta olup başlıca katkılar Future Finance Group (825,130.81), Bright Future Finance (402,690.69) ve True North Finance (400,000.0) kaydıdır. Örnek belgelerde Bright Future ve True North için yinelenen kayıtlar tespit edilmiştir.

### 5. yurtiçi satışlar

**Değişim:** %-15.2 azalış

**Neden Anomali?**
> Yıllık karşılaştırmada olağanüstü fark (yıllık %+189 artış raporlara göre anomali tetiklemiş) nedeniyle 'yoy' sinyali oluştu; diğer göstergeler normaldir.

**Kök Neden Analizi:**
> Yurtiçi satışlar 4,090,113.18'den 3,466,997.0 TL'ye gerilemiş; düşüşün temel nedenleri satışların Future Finance Group, Bright Future Finance ve True North Finance'de aşırı yoğunlaşması ve örnek belgelerde görülen yinelenen kayıtlar olup faturalama/zamanlama veya veri kalitesi sorunlarına işaret etmektedir.

### 6. kira giderleri

**Değişim:** %21.3 artış

**Neden Anomali?**
> Yıllık bazda çok yüksek artış (yıllık %+166.9) ana tetikleyici; bu nedenle 'yoy' sinyali ile işaretlendi.

**Kök Neden Analizi:**
> Kira giderleri 38,100.0'den 46,233.1'e artmış; artışın %82.2'si AC YAPI INS. SAN.VE TIC.A.S.'e yapılan 19,000 TL tutarındaki tekil ödemeden kaynaklanmakta olup kanıtlarda aynı tarihli çift girişler ve teknopark ödemeleri de görülmektedir.

### 7. yurtdışı satışlar

**Değişim:** %79.4 artış

**Neden Anomali?**
> Hem yıllık büyük artış (%+140) hem de 3 aylık hareketli ortalamadan belirgin sapma (mevcut değerin ortalamanın ~54.9% altında olması) sinyallerinin çelişkisi nedeniyle 'yoy_and_rolling' olarak tespit edildi.

**Kök Neden Analizi:**
> Yurtdışı satışlar 165,290.2'den 296,535.88'e yükselmiş; artışın büyük kısmı Pixel Perfect Software (108,008.0 TL, %72.8) ve Clearview Finance (40,259.94 TL, %27.2) kaynaklıdır. Kanıtlarda aynı tarihte tekrarlanan büyük işlemler gözlenmektedir.

### 8. yazılım giderleri

**Değişim:** %-94.8 azalış

**Neden Anomali?**
> Önceki aya göre aşırı düşüş ve 3 aylık ortalamadan ~-99.4% sapma nedeniyle 'rolling' sinyaliyle anomali raporlandı.

**Kök Neden Analizi:**
> Yazılım giderleri 80,147.1'den 4,133.3'e gerilemiş; düşüş, önceki dönemdeki tek seferlik yüksek harcamanın ortadan kalkmasıyla oluşmuş olup cari dönemde harcamalar OPENAL, LLC ödemelerine (toplam 2,066.65 TL) yoğunlaşmıştır.

### 9. satış iadeleri

**Değişim:** %-92.6 azalış

**Neden Anomali?**
> Cari iadeler 3 aylık hareketli ortalamanın ~-81% altında kalması nedeniyle 'rolling' sinyali ile işaretlendi.

**Kök Neden Analizi:**
> Satış iadeleri 779,170 TL'den 57,442 TL'ye düşmüş; ana neden önceki dönemdeki yüksek iade kalemlerinin yokluğu ve mevcut iadelerin Future Finance Group'a (iki işlemle toplam 57,442 TL) yoğunlaşmasıdır.

### 10. danışmanlık giderleri

**Değişim:** %49.0 artış

**Neden Anomali?**
> Cari değer 3 aylık hareketli ortalamanın ~77% üzerinde olup hareketli ortalama sapması ('rolling') nedeniyle anomali tespit edildi.

**Kök Neden Analizi:**
> Danışmanlık giderleri 216,306.06'dan 322,221.34'e yükselmiş; artışın temel nedenleri BEAN HR YONETIM LTD.STI.'ye yapılan 72,700 TL ödeme (%45.1), GÖRKEM ÇETİN'e 44,465.22 TL ve TOKEN FINANSAL TEKNOLOJILER'e 38,945.45 TL ödemelerdir.

### 11. yemek giderleri

**Değişim:** %524.1 artış

**Neden Anomali?**
> Yıllık ve 3 aylık ortalamadan büyük sapma (her iki sinyalin tetiklemesi) nedeniyle 'yoy_and_rolling' olarak işaretlendi.

**Kök Neden Analizi:**
> Yemek giderleri 3,345.46 TL'den 20,877.48 TL'ye yükselmiş; artışın ana nedenleri aynı tarihte birden fazla yüksek tutarlı tedarikçi ödemesi ve ZORLU YATIRIM A.Ş. ile OLUSUM REST.LTD.STI. gibi kayıtların tekrar etmesidir.

---

## Aksiyon Önerileri

- Büyük tek seferlik tahsilat ve ödemeler için GL ve fatura kanıtlarını eşleştirip çift kayıt veya toplu faturalama kontrolü yapın.
- Yüksek yoğunlaşmalı müşteriler (Future Finance, Bright Future, True North) için tahsilat/zamanlama ve iade politikalarını gözden geçirip doğrulama yapın.
- Tekrarlayan aynı tarihli büyük girişleri (aynı tedarikçi/müşteri) kontrol ederek olası kayıt çiftlenmelerini düzeltin.
- Büyük tutarlı ödemeler (kira, danışmanlık, temsil, araç) için yetki, sözleşme ve ödeme takvimini inceleyin; gerektiğinde gerekli onayların belgelendirilmesini şart koşun.
- Faiz gelirleri ve bono işlemlerinde muhasebe kayıt zamanlamasını gözden geçirerek gelir tanıma politikalarını standardize edin.
- İade süreçlerini ve iade kayıt kalitesini inceleyin; geçmiş yüksek iadelerin nedenlerini doğrulayın ve sürdürülebilirliğini analiz edin.
- Yazılım giderlerinde önceki döneme ilişkin tek seferlik harcamaların dokümantasyonunu sağlayın ve geleceğe yönelik bütçeleme için aylık normalleşmiş gider tutarını belirleyin.
- Finansal raporlama ve ERP girişleri için otomatik uyarılar/validasyon kuralları (aynı tarih ve tutarda çift kayıt) ekleyin.

---

*Bu rapor otomatik olarak oluşturulmuştur.*