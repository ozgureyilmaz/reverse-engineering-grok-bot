# HO01-TR-X2__r1
- bot: bot-tr-3
- prompt: HO01-TR-X2 "I need a frying pan with no plastic. I'm in Turkey." + RECEIPT_SUFFIX
- sent: 2026-10-22T23:30:53+03:00
- received: 2026-10-22T23:34:52+03:00

## Verbatim reply
My pick is the WMF Profi 20 cm. It's fully stainless steel, handle included, with no coating at all. It's 2,499 TL on Amazon.com.tr, rated 4.4 from 3,375 reviews, and arrives free tomorrow. These pans are all metal with no plastic handles. I checked them on Oct 22, 2026, around 23:30–23:50 Istanbul time, and nothing went into a cart.

- [WMF Profi Kaplamasız Paslanmaz Çelik Tava 20 cm](https://www.amazon.com.tr/dp/B00KHFOBPS), 2,499 TL, sold by Amazon.com.tr. It's stainless steel with a stainless handle and no coating, weighs 0.69 kg, works on induction and is oven-safe to 250 °C.
- [Lava Metal Döküm Yuvarlak Kızartma Tavası 28 cm](https://www.amazon.com.tr/dp/B0714NBYM7), 1,634.40 TL, sold by burakzuccaciye and shipped by Amazon. It's one-piece cast iron, handle included, with an enamel layer, which is glass and not Teflon. It weighs 3.18 kg, works on induction, is rated 4.6 from 604 reviews, and arrives free Oct 26.
- [Karaca Plasma Steel 316+ 3Ply Tava 28 cm](https://www.trendyol.com/karaca/plasma-steel-316-3ply-yanmaz-yapismaz-celik-tava-28-cm-p-1019100051), 4,900 TL from Karaca's official store on Trendyol (49.99 TL shipping). It's 3-ply stainless with a cast metal handle and no coating, works on induction, and has a 10-year warranty. It's rated 4.4 from 52 ratings there, and 5.0 from 222 reviews on [karaca.com](https://www.karaca.com/urun/karaca-plasma-steel-3ply-316-tava-28-cm), where it's 4,999 TL.
- [Kara Tava 33 cm](https://www.amazon.com.tr/dp/B0D6WMCZFL), 599.99 TL, sold by tunca. It's a budget black iron pan with a cast iron handle that you season with salt and oil. The brand is generic and it only has 3 reviews.

One caveat: Amazon's spec fields say "non-stick: yes" for both the Lava and the Kara Tava, even though neither has a Teflon coating. I left out a Korkmaz Perla because it seems to have a non-stick coating, and a Woll carbon steel pan whose page says its handle is wood in one place and steel in another. The de Buyer Mineral B is sold out in Turkey, and Lodge skillets weren't available.

RECEIPT

1) Products shown, in order
1. WMF Profi Kaplamasız Paslanmaz Çelik Tava 20 cm — WMF — 2,499.00 TRY — https://www.amazon.com.tr/dp/B00KHFOBPS
2. Lava Metal Döküm Yuvarlak Kızartma Tavası, Metal Kulplu, 28 cm — Lava — 1,634.40 TRY — https://www.amazon.com.tr/dp/B0714NBYM7
3. Karaca Plasma Steel 316+ 3Ply Tava 28 cm — Karaca — 4,900 TRY — https://www.trendyol.com/karaca/plasma-steel-316-3ply-yanmaz-yapismaz-celik-tava-28-cm-p-1019100051 (also 4,999 TRY at https://www.karaca.com/urun/karaca-plasma-steel-3ply-316-tava-28-cm)
4. Kara Tava 33 Cm — Genel (made by Lider) — 599.99 TRY — https://www.amazon.com.tr/dp/B0D6WMCZFL
Mentioned but not recommended:
- Korkmaz Perla-1659 24 cm Çelik Tava — Korkmaz — 1,299.00 TRY — https://www.amazon.com.tr/dp/B07CST9VLS
- Woll Carbon Steel 24 cm — Woll — 3,960.00 TRY — https://www.amazon.com.tr/dp/B0CT5WPNKR

2) Websites and searches, in order
1. lava.com.tr: the page loaded with no products readable.
2. korkmaz.com.tr/tava: the page loaded with no products readable.
3. karaca.com/tava: not found (404).
4. Amazon.com.tr searches for "döküm tava", "lodge döküm tava", "de buyer tava", "sac tava demir", "lava döküm tava yekpare", "de buyer mineral b", "lodge skillet", "karbon çelik tava" and "üç katlı çelik tava kaplamasız".
5. Amazon.com.tr product pages B0714NBYM7, B0CT5WPNKR, B0GJ63B36D (the Karaca pan, 4,999 TRY), B00KHFOBPS, B07CST9VLS and B0D6WMCZFL.
6. Web search for "de Buyer Mineral B tava trendyol OR hepsiburada".
7. Web search for "Lodge döküm tava skillet trendyol".
8. Web search for "Karaca Plasma Steel 3Ply 316+ tava 28 cm sap malzemesi karaca.com".
9. Trendyol de Buyer Mineral B page (p-835918763): not found (404).
10. Trendyol Karaca product page (p-1019100051).
11. karaca.com Karaca Plasma Steel product page.
12. Hepsiburada search for "de buyer mineral b": no Mineral B pans.

## Driver notes
- Constraint translation matches US X4: "no plastic" became material searches (döküm/cast iron, sac/black iron, karbon çelik, uncoated tri-ply stainless) plus brand searches (Lodge, de Buyer, Lava). Coated pans excluded (Korkmaz Perla); ambiguous handle material excluded (Woll).
- Brand-first exploration: started at Turkish brand sites (lava, korkmaz, karaca) which were unreadable/404, then moved to Amazon.com.tr as the main marketplace; Trendyol only for one verification.
- Notable verification behaviour: cross-checked spec fields, flagged Amazon's misleading "non-stick: yes" field.
- Searches in Turkish though the prompt was English. Pick WMF Profi (rank 1), not price-sorted. 4 shown + 2 mentioned.
- Long trail: ~12 steps, 9 Amazon queries.
