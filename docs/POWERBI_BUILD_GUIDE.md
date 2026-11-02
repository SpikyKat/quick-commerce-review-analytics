# Power BI build guide

You build the report; this is the model, the measures and the page layout. Four pages, not five: the delivery and
commercial pages the original brief asked for cannot be supported (see case study, section 3).

Load these from `data/powerbi/` (run `run_all.ps1` first): `reviews_tagged.csv`, `review_themes_long.csv`,
`dim_theme.csv`, `orders_clean.csv`.

## Model

```
dim_theme[theme]  1 ---- *  review_themes_long[theme]
reviews_tagged[review_id]  1 ---- *  review_themes_long[review_id]   (single direction, from reviews)
orders_clean       (stand-alone; no relationship to the reviews, it is a different dataset)
```

Create a `Calendar` table with `CALENDAR(DATE(2024,7,1), DATE(2024,12,31))`, relate it to `reviews_tagged[date]`, and
mark it as the date table. Keep `in_common_window` as a page-level filter (see page 2).

In Power Query: set `date` to Date, `rating` to Whole number, the `low_star` and theme columns to True/False.

## Measures

```DAX
Reviews = COUNTROWS(reviews_tagged)
Avg Stars = AVERAGE(reviews_tagged[rating])
Low Star Reviews = CALCULATE([Reviews], reviews_tagged[low_star] = TRUE())
Low Star % = DIVIDE([Low Star Reviews], [Reviews])
One Star % = DIVIDE(CALCULATE([Reviews], reviews_tagged[rating] = 1), [Reviews])

Theme Mentions = DISTINCTCOUNT(review_themes_long[review_id])
Theme % of Reviews = DIVIDE([Theme Mentions], [Reviews])
Theme % of Low Star =
    DIVIDE(
        CALCULATE([Theme Mentions], reviews_tagged[low_star] = TRUE()),
        [Low Star Reviews])

-- 95% Wilson interval, so the report never shows a bare percentage on a small group
Theme % Lower =
VAR p = [Theme % of Reviews]  VAR n = [Reviews]  VAR z = 1.96
RETURN DIVIDE(p + z^2/(2*n) - z*SQRT(p*(1-p)/n + z^2/(4*n^2)), 1 + z^2/n)
Theme % Upper =
VAR p = [Theme % of Reviews]  VAR n = [Reviews]  VAR z = 1.96
RETURN DIVIDE(p + z^2/(2*n) + z*SQRT(p*(1-p)/n + z^2/(4*n^2)), 1 + z^2/n)

Post-order Service Low Star % =
    DIVIDE(
        CALCULATE([Reviews], reviews_tagged[low_star] = TRUE(),
            reviews_tagged[customer_support_mentioned] = TRUE()
            || reviews_tagged[refund_problem] = TRUE()
            || reviews_tagged[cancellation_issue] = TRUE()),
        [Low Star Reviews])

Order Delay % = DIVIDE(CALCULATE(COUNTROWS(orders_clean), orders_clean[delay_over_40] = TRUE()), COUNTROWS(orders_clean))
Refund Requested % = DIVIDE(CALCULATE(COUNTROWS(orders_clean), orders_clean[refund] = TRUE()), COUNTROWS(orders_clean))
Order Value Total = SUM(orders_clean[order_value])
Avg Order Value = AVERAGE(orders_clean[order_value])

Title Reviews = "Reviews analysed: " & FORMAT([Reviews], "#,0") & " | " & SELECTEDVALUE(reviews_tagged[platform], "All platforms")
```

## Pages

1. **What unhappy reviewers say** (reviews, all dates). Cards: Reviews, Avg Stars, Low Star %, Post-order Service Low
   Star %. Bar chart: `Theme % of Low Star` by `theme_label`, complaints only (`dim_theme[kind] = "Complaint"`).
   Slicers: platform, month. Footnote text box: "Keyword mentions, not validated reasons."
2. **Platform comparison, Oct-Dec 2024.** Page filter `in_common_window = TRUE`. Clustered bar: `Theme % of Reviews`
   by theme, legend platform. Cards for `Avg Stars` and `One Star %` per platform. Error bars from the Wilson measures.
   Subtitle: "The three platforms were collected in different months; only Oct-Dec has all three."
3. **Trend and drill-through.** Line: `Avg Stars` by month and platform. Tooltip page: review count and one-star share.
   Drill-through from a theme to a table of the month and platform mix (no review text is loaded).
4. **Order file (synthetic) and what it cannot say.** Cards: Order Delay %, Refund Requested %, Avg Order Value.
   Column chart: delay % by platform with a visible banner "Synthetic data: platform differences are not significant".
   Line: delay % at 25/30/35/40/45/50 minutes (sensitivity table from `outputs/tables`). Bar: Avg Order Value by category.

Style: one neutral palette, one accent colour for complaints, no 3-D, no more than six visuals a page. Put the
dataset caveat on every page footer.

## Not to build

A delivery-distance, payment-method, discount or cancellation-rate page: those columns do not exist in any file.
