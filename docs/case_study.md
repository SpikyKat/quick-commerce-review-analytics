# Quick commerce: what unhappy customers write about, and what the order data can and cannot say

A personal analytics project on three public Kaggle files about Blinkit, JioMart, Zepto and Swiggy Instamart. Not
affiliated with any of these companies. All numbers come from `outputs/results/*.json`, produced by `scripts/`.

## 1. Executive summary

I set out to answer "how can quick-commerce platforms improve delivery reliability, satisfaction and commercial
performance?" The first thing the data told me is that only one of the three files can support a real answer.

- **Real data (4,620 app reviews):** In 1-2 star reviews, the most common topics are about what happens after the order, not
  speed. 55% mention customer support, refunds or cancellations; 36% mention a delivery-experience problem such as
  lateness, missing or wrong items, quality or the delivery person; 7% mention fees.
- **Strongest associations with a low rating** (adjusted odds ratios): fraud or trust wording 11.1x, cancellation 5.7x,
  customer support 4.0x, quality or expiry 3.2x, refunds 2.9x. Mentions of speed and of good service go the other way (0.21x, 0.10x).
- **Platforms differ in the reviews, with caveats.** In Oct-Dec 2024 (the only window with all three), Blinkit reviews
  average 2.55 stars against 1.64 (JioMart) and 1.53 (Zepto). The gap holds in every month. JioMart reviewers mention
  cancellation far more (22.5% vs 8.7% for Blinkit); Zepto reviewers mention support (34.7%) and fraud or trust (15.8%) most.
- **The two other files are synthetic.** In the 100,000-order file the delay flag is exactly "over 40 minutes", every
  rating and refund request is fixed by the feedback phrase, and the platforms are statistically identical. In the
  5,000-row agent file the review text is random words and no column relates to any other. I use them to show how
  to detect that, and to build KPI mechanics, not to draw business conclusions.

## 2. Business background and question

Quick-commerce apps compete on speed, but their public reviews are dominated by what happens when something goes wrong.
For an operations or product team the practical question is: **which failure modes do unhappy customers talk about most,
how do platforms differ, and what should be measured to fix them?** Stakeholders: customer-support and operations leads,
product (checkout and fees), and category quality teams.

## 3. What the data can support

| Original ask | Verdict |
|---|---|
| Customer sentiment and complaints | Yes, from `reviews.csv` |
| Platform benchmarking | Reviews only, 3 platforms, with sampling caveats; no overall winner |
| Delivery performance, distance, peak hours | No: no distance column, no usable timestamp, synthetic minutes |
| Cancellation rate | No: no order status column |
| Discounts, payment methods, delivery charges, revenue | No such columns; order value only |
| Delay or dissatisfaction prediction | Not meaningful on synthetic files; a review-text check is done instead |

I did not invent a delivery SLA. The order file's own delay flag is "over 40 minutes"; I tested 25 to 50 minutes.

## 4. Data and cleaning

See `data_card.md`. In short: review whitespace and dates cleaned, platform names standardised, originals untouched.
The audit (`01_audit.py`) found:

- Reviews: 96.4% of reviews are from Jul-Dec 2024; platforms were collected in different months (Zepto and Blinkit
  almost entirely Oct-Dec, JioMart from July). 71.5% of reviews are 1-star. 13% look cut off at ~500 characters.
- Orders: no missing or duplicate rows, but `Order Date & Time` holds only minutes and seconds, so no trends or peak hours.
- Agent file: 5,000 unique review texts made of random words; 7% contain any common review word.

## 5. Method

1. **Complaint taxonomy.** Eleven complaint and two praise themes defined as transparent keyword patterns (`src/qcmod/themes.py`).
   I read eight random matches per theme, found two patterns too loose ("fee" matched "feel"; "instead of" matched
   unrelated text) and fixed them. A keyword means the topic is mentioned, not that it caused the rating, and the support
   theme also catches some praise.
2. **Fair platform comparison.** Platform contrasts use Oct-Dec 2024 only, with 95% Wilson intervals, chi-squared tests
   across the three platforms, Holm correction over the eleven themes, and a bootstrap for rating differences. The
   rating gap is also checked month by month.
3. **Associations.** Logistic regression of "1-2 stars" on all theme flags plus platform, bootstrap intervals.
4. **Text-model check.** A TF-IDF logistic regression predicts low stars with "1 star"-type phrases removed. Tested with
   random folds, with a whole platform held out, and trained on Jul-Nov to predict December.
5. **Order file.** KPIs with intervals, platform and category tests, a threshold sensitivity table, and checks of how
   the file is structured.

## 6. Findings

Each finding is marked **Observed** (in the data) or **Hypothesis** (my reading).

### 6.1 Post-order service dominates unhappy reviews

- **Observed:** Among 3,584 reviews with 1-2 stars, 34.6% mention customer support, 20.2% refunds, 19.7% cancellation;
  55.3% mention at least one of the three. Lateness is mentioned in 9.2%, missing items 7.8%, wrong items 3.6%.
  21.3% mention none of the 11 complaint themes.
- **Why it matters:** the platforms sell speed, but the complaints that go with the lowest ratings are about getting
  help after something went wrong.
- **Hypothesis:** a first failure becomes a 1-star review when support does not resolve it. These data cannot prove that:
  they have no order or ticket history.
- **Action to consider:** human escalation path, one owner per ticket, visible refund-to-source status.
- **Measure success by:** time to first human reply, ticket reopen rate, refund time to original payment method.

### 6.2 Cancellation and fraud/trust wording carry the strongest signal

- **Observed:** adjusted odds ratios for a low rating: fraud or trust 11.1 (5.8-26.3), cancellation 5.7 (3.8-9.4),
  support 4.0 (3.0-5.2), quality 3.2 (1.9-5.7), refunds 2.9 (2.1-4.7), wrong item 2.2 (1.1-4.2), fees 2.1 (1.5-3.1),
  lateness 2.0 (1.2-3.1). Missing item, app issues and delivery-person behaviour were not clearly different from 1.
- **Observed:** cancellation covers both the platform cancelling and customers unable to cancel.
- **Hypothesis:** order cancellations after payment are especially damaging; fraud wording often accompanies unrefunded money.
- **Action:** reason codes for cancellations, a short window for free customer cancellation, proactive refunds.
- **Measure:** post-payment cancellation rate and share refunded within 24 hours.

### 6.3 Platform differences in Oct-Dec 2024

| Share of reviews mentioning | Blinkit | JioMart | Zepto |
|---|---|---|---|
| customer support | 21.1% | 25.4% | 34.7% |
| cancellation | 8.7% | 22.5% | 12.2% |
| fees and pricing | 10.8% | 1.8% | 8.0% |
| missing item | 6.4% | 10.5% | 3.9% |
| fraud or trust | 7.2% | 9.5% | 15.8% |

Reviews: Blinkit 1,368, JioMart 927, Zepto 1,739. One-star share 51.8%, 78.1%, 79.1%. All differences above are
significant after Holm correction. Refund and delivery-person mentions are not (adjusted p 0.064).

- **Observed:** the Blinkit gap in mean stars is 0.91 vs JioMart (0.78-1.03) and 1.01 vs Zepto (0.91-1.13). JioMart vs
  Zepto is 0.11 (0.005-0.21). Blinkit is higher in October, November and December separately.
- **Caveat:** I do not know how reviews were selected. A rating gap this big may partly reflect how each platform's
  reviews were sampled. These are differences in this sample, not a ranking of the companies. I declare no winner.

### 6.4 The order file shows no platform effect

- **Observed:** delay rate 13.4%, 13.8%, 13.8% (p=0.17); refund request rate about 45.8% on every platform (p=0.84);
  mean rating 3.23-3.25 (p=0.58). Moving the delay threshold from 25 to 50 minutes never separates platforms by more than 0.8 points.
- **Observed:** only 13.8% of orders whose feedback says "very late delivery" are flagged delayed, about the overall
  base rate, and 46% of delayed orders have 4-5 stars. Feedback and delay are unrelated in this file.
- **Observed:** order value differs by category (Snacks Rs 273, Fruits & Vegetables 376, Dairy 451, Beverages 550,
  Grocery 848, Personal Care 1,052), the one structure that looks like pricing. Rs 27.1M of Rs 59.1M order value
  (45.9%) sits on orders with a refund request. That is order value at risk, not revenue lost; the file has no refund amounts.

### 6.5 Do the words predict a low rating?

Yes, mostly because they carry sentiment. AUC 0.94 with random folds; 0.90 to 0.95 when a whole platform is held out;
0.94 predicting December from earlier months. A model using only the 13 theme flags reaches 0.89 / 0.86-0.90 / 0.91.
A majority-class guess is 0.50. This is a check on the taxonomy, not a product: the leading words ("worst", "pathetic")
are sentiment, which is why the theme odds ratios in 6.2 are the more useful result.

## 7. Recommendations

1. **Fix support first.** Support is the most common topic in unhappy reviews and has a 4x odds ratio. Track first human reply time and reopen rate. (6.1)
2. **Treat post-payment cancellation as a defect.** Reason codes, instant refund and a visible cancel window. Track the cancellation rate and refund within 24 hours. (6.2)
3. **Make refunds visible and to source.** Many unhappy reviews mention refunds; track time to refund. (6.1, hypothesis on cause)
4. **Be clear on fees at checkout.** Fees feature in 10.8% of Blinkit and 8.0% of Zepto reviews but only 1.8% of JioMart's. Test fee display; track checkout drop-off. (6.3)
5. **Investigate trust signals on Zepto.** 15.8% of its reviews use fraud/trust wording versus 7.2% on Blinkit; read the underlying cases before acting. (6.3)
6. **Collect the data that would answer the delivery questions.** Order timestamps, promised vs actual time, distance, order status, ticket history. Without these, speed and cancellation-rate analysis is impossible.

## 8. Limitations

- Reviews are a self-selected, mostly 1-star sample; not a measure of overall satisfaction.
- Platform samples were collected in different months and by unknown means.
- Keyword themes are unvalidated; I read eight matches per theme and corrected two patterns. A labelled sample would give precision and recall.
- Associations are not causes.
- Two of the three files are synthetic; their numbers describe how the data was built.
- Review text is truncated for about 13% of reviews.
- Kaggle licences and provenance are not yet recorded.

## 9. Future scope

Hand-label 300 reviews to validate the themes; add a multilingual layer (some reviews are in Hinglish); get a real order
dataset with timestamps, then build the delivery and cancellation analysis the original brief asked for.

## 10. Reproduce

```
python -m venv .venv ; .venv\Scripts\pip install -r requirements.txt
.\run_all.ps1
```
