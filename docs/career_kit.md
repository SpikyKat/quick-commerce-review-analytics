# Career kit

Use only what the case study supports. This is a personal project on public Kaggle data, not employer work, and it has
no business outcome to claim.

## Resume (project section)

**Quick-Commerce Review & Order Analytics (personal project, Python, Power BI)**
- Built a keyword taxonomy of 11 complaint themes for 4,620 public app reviews of Blinkit, JioMart and Zepto; found that 55% of 1-2 star reviews mention support, refunds or cancellation versus 36% mentioning delivery-experience problems.
- Compared platforms within the one window where all three were sampled (Oct-Dec 2024), using Wilson intervals, Holm-corrected chi-squared tests and a month-by-month check; Blinkit averaged 2.55 stars against 1.64 (JioMart) and 1.53 (Zepto).
- Estimated adjusted odds ratios linking each theme to a low rating (cancellation 5.7x, support 4.0x), and tested a text model on a held-out platform and held-out month (AUC 0.90 to 0.95).
- Audited a 100,000-order file and showed its delay flag, ratings and refunds are rule-generated; reported what cannot be concluded rather than building a delivery dashboard on it.

Skills line: Python, pandas, scikit-learn, SciPy, statistical testing, text analysis, Power BI (when built), data-quality auditing.

## LinkedIn post (draft)

I took three public quick-commerce datasets and expected a delivery-speed project. Two of the three turned out to be synthetic: one file's "delay" column was exactly "minutes over 40", and ratings were fixed by the feedback phrase. The third, 4,620 real app reviews, told a different story: among 1-2 star reviews, support, refunds and cancellations came up far more than lateness. I compared Blinkit, JioMart and Zepto only in the months all three were sampled, and I'm careful not to call a winner. Write-up and code: [link once public]. #DataAnalytics #BusinessAnalysis #QuickCommerce #Python

Screenshots worth sharing: `themes_low_star.png`, `themes_by_platform.png`, `theme_odds_ratios.png`, and the audit evidence `audit_synthetic_evidence.png`.

## Interview: two-minute walkthrough

"I wanted to understand what drives unhappy customers on quick-commerce apps. I started by auditing three Kaggle files
and found two were synthetic, so I used the real review file for conclusions and the synthetic ones to show how I
check data validity. I built a complaint taxonomy, compared platforms in a common time window so sampling dates did
not drive the result, and estimated which topics go with low ratings. The main finding is that service after the order
matters more in these reviews than speed. The limits are that reviews are self-selected and the themes are keyword-based."

## Likely questions

- **Why did you restrict the platform comparison to Oct-Dec?** Platforms were collected in different months, so an all-time comparison would confuse platform with period.
- **How do you know the taxonomy is right?** I don't fully. I read eight matches per theme, tightened two patterns and say it is unvalidated; next step is 300 hand labels.
- **Is this causal?** No. Odds ratios are adjusted associations in a self-selected sample.
- **Why not predict delivery delay?** The delay flag is a rule on delivery minutes, so a model would only rediscover it.
- **What is Holm correction and why use it?** It controls the chance of false positives across the 11 theme tests.
- **DAX:** the Wilson interval measure and the `CALCULATE` with a low-star filter for "share of low-star reviews mentioning a theme".
- **What would you do with real order data?** Promised vs actual time, cancellation by reason, ticket history joined to ratings.

## Do not say

That the project improved any business metric, that a platform "wins", or that these order files are real operations data.
