# Analysis readout

Working notes on what the counts support. The article is the version to cite. These notes keep the interpretations that are one step past the table.

## The pipeline is real, and it is not one pipeline

Every reply that shopped does the same visible things: rewrite the want, look somewhere, drop some options, show a short list, stop. That is as far as a receipt can take a stage model. It does not say the bot has seven modules.

The source stage splits by cohort, not by country alone.

- US first pass: one retailer search, generic words, one domain. Twenty of those products are the five-prompt pilot; the gift prompt later the same day stayed on Target.
- US fresh repeat, same calendar day: editorial web search first, then brand sites and Amazon, many steps, no shared URL with the first pass.
- Turkey, both no-preference bots: marketplace lists, long trails, queries that already contain a brand or a model. The first bot mostly published Amazon.com.tr links and said other stores blocked it. The second bot mostly published Trendyol links.
- Turkey with a saved preference note: brand sites and Cimri, almost no marketplace product URL, even though the note said Trendyol or Hepsiburada was acceptable.
- 28 October: three replies name a catalog search. Three other replies that day do not. The operator's note that the path "appears consistently" on 28 October is stronger than the receipts.

A single sentence of the form "Grok Bot shops at Target in the US and Trendyol in Turkey" does not survive the fresh repeats.

## Stability

Link Jaccard near zero is the main stability result, and it limits what a perturbation can be said to do. If two untouched runs already share no URL, a third run that also shares no URL is not evidence the edit worked. Brand overlap is higher, especially in Turkey (mean 0.378). Model keys sit in between: the WH-CH720N and the Soundcore A-codes recur when the URL does not.

The one perfectly stable repeat was a cache in the same chat. It is not a retrieval result. Treating it as one would have inflated stability.

## Constraints

Store and brand constraints in this sample are followed on the shown rows: Best Buy, Trendyol, Getir, Sony, Tefal. Budget caps are followed on the open and the store-constrained headphone prompts, the dress caps, the $30 pan, and the $50 gift. The two misses are both Sony-plus-budget. The US miss is labeled over budget in the receipt. The Turkey miss is stated as "I couldn't find any" and the shown prices are both over 5,000 TL. That is a different outcome from a silent substitution.

"No plastic" is visible as a change of query (cast iron, carbon steel, uncoated steel), not as a materials assay.

## Checkout

n=2, and the Turkey file is only the last message. Both endings say nothing was charged. The US bot never reached a payment control: a default ZIP and a bladed-item restriction greyed checkout out. The extra Leatherman Surge is the only ad-in-cart event. The bot named it and removed it. One event is enough to record and not enough to estimate a rate.

The ordinary runs saying "I didn't buy anything" are weak evidence of a safety boundary, because the prompt told them not to. The checkout prompts are the test of the boundary, and they are two chats.

## What I would not write

- That the US bot "is" a Target/Best Buy shopper. That is the first chat only.
- That Turkey "is" Trendyol. The first pass was Amazon.com.tr.
- That preferences made the Turkey bot obey "Trendyol or Hepsiburada". The primary URLs are brand sites and Cimri.
- That the catalog path replaced store search on 28 October. Half of that day's shopping replies do not name it.
- A p-value.

## Left undone

The US preference series. Store-page baselines, which would be required before any claim that the bot reranks a retailer's top N. A fresh US urgency prompt that actually says "United States", so urgency can be separated from the location default. A second ad-in-cart trial. The Turkey checkout screens that were not delivered.
