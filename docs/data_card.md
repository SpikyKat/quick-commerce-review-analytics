# Data card

Three files, all downloaded from Kaggle by me. The Kaggle page, author and licence for each still need to be recorded
here before any public release; I have not verified them. Raw files are not in this repository.

| File | Rows | What it really is | Used for |
|---|---|---|---|
| `reviews.csv` | 4,620 | Public app reviews with rating, date, text, platform (Blinkit, JioMart, Zepto). Looks real. | main analysis |
| `Ecommerce_Delivery_Analytics_New.csv` | 100,000 | Orders for Blinkit, JioMart, Swiggy Instamart. Rule-generated (see audit). | KPIs, audit, sensitivity |
| `Fast Delivery Agent Reviews.csv` | 5,000 | Review text is random words and all numeric columns are unrelated. | validity check only |

## Handling

- Review whitespace collapsed, dates parsed (`%d %B %Y`), platform names standardised. Original files untouched.
- Review text is not copied into outputs or the Power BI tables, and no review is quoted verbatim in the write-up.
- The order file's `Order Date & Time` holds only minutes and seconds (60 distinct values), so it carries no date or hour.

## Known issues

- Review sample covers 2020-07 to 2024-12 but 96% is from Jul-Dec 2024; platforms were collected in different months.
- Ratings are heavily 1-star (71.5% of all reviews); the sample is not representative of all customers.
- About 13% of reviews appear cut off near 500 characters.
- No Swiggy Instamart reviews; no Zepto orders.
- How each Kaggle file was created is not documented to me.
