# Video Standartları — "Esnaf / İşletme" Dikey Serisi

Referans: Drive klasöründeki 2 örnek video (720x1280, 47 sn ve 56 sn, Türkçe voiceover + ekran yazısı).
Bu doküman, aynı seriden onlarca videoyu hızlı ve tutarlı üretmek için bağlayıcı kuralları tanımlar.

## 1. Format (teknik)
| Alan | Standart |
|---|---|
| Çözünürlük | 720 x 1280 (9:16), dikey |
| FPS | 30 |
| Süre | Hedef **33–55 sn** (ilk video 33 sn — test için kısa tutuldu) |
| Video codec | H.264 High, yuv420p, CRF 19, faststart |
| Ses | AAC 160 kbps, 44.1 kHz, **stereo** |
| Bitrate | ~1.5–1.8 Mbps (Reels/TikTok/Shorts için ideal) |
| Dosya adı | `NN_kisa_baslik.mp4` (ör. `01_uc_saat_kayip.mp4`) |

## 2. Senaryo yapısı (6 blok şablonu)
1. **HOOK (0–4 sn):** Acı/para/süre içeren somut cümle. "Günde 3 saat mesaja cevap veriyorsan, o saatler kârından gidiyor."
2. **KÖPRÜ (4–8 sn):** Yeni bir bilgi değil, çözümün iddiası. "Bir kere kuruyorsun, sonra o yazıyor."
3. **MADDE 1–3 (8–25 sn):** Her madde tek cümle + ekranda büyük numara (1/2/3).
4. **KAPANIŞ (25–30 sn):** Toplam fayda + düşük riskli ilk adım. "Toplam 15 dakika. Yarın dükkânı açmadan dene."
5. Her blok = 1 görsel = 1 voiceover cümlesi. Blok voiceover'ı **4–6 sn** (max ~18 kelime).
6. CTA ayrı uzun blok değil, kapanışın içinde tek cümle (reklam kokusu yok).

## 3. Dil ve ton
- Sen dili, samimi, esnafın günlük konuşması. "Siz" yok.
- Somut sayı zorunlu: saat, TL, adet, gün. ("hızlanın" değil, "3 saat")
- Tek cümle = tek fikir. Devrik/uzun cümle yok.
- Abartılı vaat yok ("zengin olursun" ❌), gözlemlenebilir fayda var ("sabah rapor masada" ✅).
- Türkçe karakterler korunur (â, î, ğ, ş, ı). Marka adı anılıyorsa kısaltma kullanılmaz.

## 4. Görsel dil
- **Tek karakter tutarlılığı:** aynı seride aynı esnaf tipi (40'lı yaşlar, bıyık, önlük) — seri kimliği.
- Palette: **teal + amber** sinematik grade, sıcak tungsten ışık, sığ alan derinliği, hafif film grain.
- Görseller dikey üretilir (asla yataydan kırpılmaz), 2 kat büyütülüp zoompan ile %2–14 arası yavaş hareket.
- Hareket çeşitliliği: sırayla `in → out → pan_r → pan_l → in → out` (tekrar hissi yok).
- Sahne geçişi: 0.40 sn crossfade. Sert kesme yok.

## 5. Yazı katmanı (en çok hata buradan çıkıyor)
- Konum: alt-orta bölge, alt kenardan 250 px yukarı (Reels/TikTok arayüzü için güvenli alan).
- Font: DejaVu Sans Bold. **Caption 42 px**, **Hook 46 px**, numara 140 px, üst etiket 30 px.
- Satır başına **max 20 karakter (hook) / 22 karakter (diğer)**, max **3 satır**.
- Kontrast: siyah outline 5 px + 2 px gölge. Renkli kutu yok.
- Hook'ta sadece **1 vurgu**: sarı (≈ #FFC733). Tüm cümleyi sarı yapmak yasak.
- Her sahne metni 180 ms fade + %92→100 scale ile girer.
- Üstte sabit seri etiketi (ör. "ESNAF İÇİN 3 OTOMASYON") — seri tanınırlığı.

## 6. Ses
- Tek erkek ses, sıcak/öğretici ton; seri boyunca **aynı voice_id**.
- Voiceover sahne başından 0.30 sn sonra girer; sahne sonunda 0.75 sn nefes payı.
- Müzik: ambient pad + 60 Hz nabız, **-20 dB** (voiceover'ın çok altında), giriş/çıkış 1.2 sn fade.
- Sonda 1.2 sn fade-out; ani kesme yok.

## 7. Üretim hattı
```
video/scenes/NN_slug.json   → senaryo + görsel + ses eşleşmesi
assets/img/                 → dikey görseller (941x1672 üretim, 720x1280 çıkış)
assets/vo/                  → cümle başına 1 ses dosyası (vo1.mp3, vo2.mp3…)
python3 video/build_video.py video/scenes/NN_slug.json
→ video/out/NN_slug.mp4
```
Render süresi: 6 sahne ≈ 85 sn. Yeni video için sadece JSON + görseller + sesler değişir, kod değişmez.

## 8. Yayın öncesi kontrol listesi
- [ ] Hook ilk 2 saniyede anlaşılıyor, sayı içeriyor
- [ ] Hiçbir yazı kenardan taşmıyor, 3 satırı geçmiyor
- [ ] Voiceover 0.3 sn'de başlıyor, cümle ortasında geçiş yok
- [ ] Sahne geçişleri 0.4 sn, hareket yönleri tekrar etmiyor
- [ ] Ses seviyesi: tepe ≤ -1 dB, stereo
- [ ] Süre 30–55 sn, dosya < 15 MB
- [ ] Dosya adı `NN_slug.mp4`, Drive klasörüne yüklendi
