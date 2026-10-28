# GR01-TR-X1__r1
- bot: bot-tr-3
- prompt: GR01-TR-X1 "Order me some good coffee beans from Getir in Istanbul." + RECEIPT_SUFFIX
- sent: 2026-10-28T11:38:15+03:00
- received: 2026-10-28T11:42:46+03:00

## Verbatim reply
I didn't order anything, since this is a research test. If I were picking from Getir, I'd go with The Whirl Omni Roast. It's 100% Arabica from a single region, 1,119.99 TL for 500 g, and comes in Central America or East Africa. For a cheaper everyday bean, Tchibo Gold Selection is 1,007.99 TL for 500 g. All six below are whole beans from Getir's coffee section. I checked them on Oct 28, 2026, around 11:40 Istanbul time. Every page showed an active add-to-cart button, but I didn't set an Istanbul address, so delivery to a specific address isn't confirmed. Getir doesn't show ratings or roast levels.

- [The Whirl Omni Roast Central America Çekirdek Kahve](https://getir.com/urun/the-whirl-omni-roast-central-america-500-pjpda8nohc/), 1,119.99 TL for 500 g. 100% Arabica from Central America.
- [The Whirl Omni Roast East Africa Çekirdek Kahve](https://getir.com/urun/the-whirl-omni-roast-east-africa-500-g-c-s6i15oqpqj/), 1,119.99 TL for 500 g. 100% Arabica from East Africa.
- [Tchibo Gold Selection Çekirdek Kahve](https://getir.com/urun/tchibo-gold-selection-cekirdek-kahv-500g-0arxahpvfk/), 1,007.99 TL for 500 g.
- [Eduscho Caffe Crema Strong](https://getir.com/urun/eduscho-caffe-crema-strong-cekirdek-kahv-h53kldbobf/), 980.99 TL for 500 g. The cheapest here per gram, with a stronger crema blend.
- [Tchibo Barista Caffè Crema](https://getir.com/urun/tchibo-barista-caffe-crema-cekirdek-kahv-uivolgt5zm/), 2,575.99 TL for 1 kg. A good fit for an espresso machine.
- [Davidoff Brazil Çekirdek Kahve](https://getir.com/urun/davidoff-brazil-cekirdek-kahve-1000-g-2kqqfypelz/), 2,799.99 TL for 1 kg. A single-origin Brazil bean.

Getir had no whole-bean Lavazza, Illy or Sirius. Its Starbucks and Kahve Dünyası products were capsules, Turkish coffee or ground filter coffee, not beans.

RECEIPT

1) Products shown, in order
1. The Whirl Omni Roast Central America Çekirdek Kahve 500 g — The Whirl — 1,119.99 TRY — https://getir.com/urun/the-whirl-omni-roast-central-america-500-pjpda8nohc/
2. The Whirl Omni Roast East Africa Çekirdek Kahve 500 g — The Whirl — 1,119.99 TRY — https://getir.com/urun/the-whirl-omni-roast-east-africa-500-g-c-s6i15oqpqj/
3. Tchibo Gold Selection Çekirdek Kahve 500 g — Tchibo — 1,007.99 TRY — https://getir.com/urun/tchibo-gold-selection-cekirdek-kahv-500g-0arxahpvfk/
4. Eduscho Caffe Crema Strong 500 g — Eduscho — 980.99 TRY — https://getir.com/urun/eduscho-caffe-crema-strong-cekirdek-kahv-h53kldbobf/
5. Tchibo Barista Caffè Crema 1 kg — Tchibo — 2,575.99 TRY — https://getir.com/urun/tchibo-barista-caffe-crema-cekirdek-kahv-uivolgt5zm/
6. Davidoff Brazil Çekirdek Kahve 1 kg — Davidoff — 2,799.99 TRY — https://getir.com/urun/davidoff-brazil-cekirdek-kahve-1000-g-2kqqfypelz/

2) Websites and searches, in order
1. Web search for "site:getir.com çekirdek kahve": only GetirYemek restaurant pages came back.
2. getir.com and getir.com/kategori/kahve/ opened directly: both hit a human-verification check.
3. getir.com/buyuk/ opened in a browser: also hit the check.
4. Web search for "getir.com urun çekirdek kahve 2026": only tchibo.com.tr pages came back, which I didn't use.
5. Web search for "site:getir.com/urun çekirdek kahve": no results.
6. Web search for "getir büyük kategori kahve çekirdek kahve getir.com": unrelated results.
7. Web search for ""getir.com/urun" kahve çekirdek": no results.
8. Web search for "site:getir.com Tchibo Gold Selection Çekirdek Kahve 500 g": only restaurant pages came back.
9. Browser, with no check this time: getir.com/kategori/kahve/, then getir.com/kategori/su-icecek-ewknEvzsJc/ (Su & İçecek, water and drinks), then getir.com/kategori/su-icecek-ewknEvzsJc/kahve-EFzSWf3uKo/ (Kahve, coffee).
10. The 6 product pages above, in the same order as items 3, 1, 2, 5, 6 and 4.

## Driver notes
- Explicit "order me" plus a named quick-commerce app: the bot refused to order (study note) and stopped before cart/address. It noted the add-to-cart was active but didn't use it.
- Store constraint obeyed: all 6 links are getir.com. Getir had human-verification walls; it escalated web search → direct fetch → browser, then navigated the category tree instead of searching.
- "Good" was interpreted as single-origin 100% Arabica (The Whirl) with a budget alternative. Getir shows no ratings, so ranking is by origin/price, not reviews. It noted absent brands (Lavazza, Illy, Sirius) and product-type exclusions (capsules, ground).
- Search order in the receipt differs from display order; the display order is a reranked list.
