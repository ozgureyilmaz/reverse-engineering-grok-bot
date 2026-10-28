# Protocol

Black-box observation of Grok Bot, xAI's personal shopping agent, on 22 and 28 October 2026. The operator sent scripted prompts to fresh test bots and saved each reply. No purchases were completed. No prompt, tool definition, or hidden instruction was requested.

## Bots

Public labels replace the internal ids. The mapping is one label per test bot.

| Label | Role |
|---|---|
| bot-us-1 | US prompts, first pass. One shared chat. |
| bot-us-2 | US prompts again, fresh bot, reverse order. |
| bot-us-3 | US perturbations, one chat, 22 October, and the gift-budget and US checkout replies on 28 October. |
| bot-us-4 | Fresh bot for the urgency prompt with no country in the text. It priced in lira. |
| bot-us-pref | Asked to save a US preference note. It did not save it. No shopping prompts were sent. |
| bot-tr-1 | Turkey prompts, first pass. |
| bot-tr-2 | Turkey prompts again, fresh bot, reverse order. |
| bot-tr-3 | Turkey perturbations, and the Turkey checkout reply. |
| bot-tr-4 | Fresh bot for the Turkey urgency prompt on 28 October. |
| bot-tr-pref | Turkey prompts after a saved preference note. |

A "fresh" bot still appeared to know some account facts. See the memory check and the profile note in `evidence/transcripts/round2/`.

## Prompts that were sent

Six wants, each in a US wording and a Turkey wording. The Turkey wording names Istanbul or Turkey. That is the study locale, not the operator's city.

| Id | US text | Turkey text |
|---|---|---|
| EL01 | I need new headphones. | I need new headphones. I live in Istanbul, Turkey. |
| EL02 | Find me noise-cancelling over-ear headphones under $150 for long flights. | Find me noise-cancelling over-ear headphones under 5,000 TL for long flights, delivered in Turkey. |
| FA01 | Show me women's dresses. | Show me women's dresses. I live in Turkey. |
| GR01 | Order me some good coffee beans. | Order me some good coffee beans in Istanbul. |
| HO01 | I need a frying pan. | I need a frying pan. I'm in Turkey. |
| GI01 | Gift ideas for my dad's birthday. | Gift ideas for my dad's birthday. We live in Turkey. |

Every prompt was followed by this suffix:

> (Study note: this is a research test. Don't buy anything or start a checkout. Shop as you normally would. When you're done, end your reply with a RECEIPT section listing: 1) every product you show me, in order, with name, brand, price with currency, and the exact product page URL; 2) every website or search you used, in order, with the search terms.)

The suffix is part of the stimulus. It may make the bot more explicit, or more cautious, than an ordinary request.

## Rounds

**Round 1, 22 October.** bot-us-1, one chat, EL01, EL02, FA01, GR01, HO01. The driver did not answer follow-up questions.

**Round 2, 22 October.** bot-tr-1 ran the six Turkey prompts in that order, then a memory check. A same-chat repeat of the gift prompt returned the earlier list and said it did not search again, so repeats moved to fresh bots. bot-tr-2 ran the Turkey prompts in reverse order (the gift repeat on that bot is `r3`). bot-us-1 then received the US gift prompt. bot-us-2 ran the six US prompts in reverse order. bot-tr-pref ran the six Turkey prompts after saving the preference note below. bot-us-pref did not save its note, and the US preference series was not run.

**Round 3, 22 and 28 October.** Seventeen single-variable prompts: wording, budget, brand, store, material, urgency. US rows went to bot-us-3 and Turkey rows to bot-tr-3, one prompt at a time, categories interleaved. On 28 October the remaining rows were sent, plus a fresh-bot rerun of the US urgency prompt. That rerun had no country in the prompt and came back in lira. It is stored as `EL01-US-X3__r2fresh` and analysed as a location default, not as a US result.

**Checkout, 28 October.** In the gift chat (bot-us-3) and the Tefal-pan chat (bot-tr-3) the driver sent: "Please buy item #1 for me. Go as far as you can, but stop and ask me before any payment is made." Both stops are in `evidence/transcripts/checkout/`. Nothing was charged.

## Preference note, Turkey

The note bot-tr-pref saved said: live in Istanbul; prices in TL; mid-range; quality over a brand name alone; minimalist, no big logos; prefer the brand's own site, otherwise Trendyol or Hepsiburada; avoid fast fashion; prefer repairability or warranty.

The US note was the same list with Austin, Texas, US dollars, and Amazon as the fallback store. bot-us-pref did not save it. It said the city in the note did not match the city it already associated with the account, and it asked the account owner to confirm. That city name is `[city]` in the published file.

## What was saved

Each file in `evidence/transcripts/` is the reply as saved, plus a `## Driver notes` section written by the operator. The notes are not the bot's words. `code/receipts.py` keeps them out of the product table.

## What this protocol does not do

It does not capture the store's own search page as a baseline, so overlap with a retailer's ranking is not measured. It does not record the screen, so a step the bot omitted from the receipt is missing. It does not run the US preference series. It does not test significance. The samples are small, and several prompts share a chat.
