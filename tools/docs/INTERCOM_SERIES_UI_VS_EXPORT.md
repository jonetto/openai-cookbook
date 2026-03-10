# Intercom Series: UI definitions vs Content Data Export

This doc summarizes how the **Intercom UI** defines Series metrics (from official help) and how that maps to what we can compute from the **Content Data Export API** (receipt CSV). Use it to interpret our `get_intercom_series_metrics` / `run_series_metrics.mjs` output and to align with the UI when possible.

**Sources:** [View a Series Performance Summary Report](https://www.intercom.com/help/en/articles/6926571-view-a-series-performance-summary-report), [Measure how well your series performs](https://www.intercom.com/help/en/articles/4425234-measure-how-well-your-series-performs), [Series explained](https://www.intercom.com/help/en/articles/4425207-series-explained), [Series FAQs – Entering and leaving](https://www.intercom.com/help/en/articles/8780861-series-faqs).

---

## How the UI defines each metric

### Started

- **UI:** “The number of users that have **started** your Series” / “users who have **started the series by matching an entry rule block**”.
- **Intercom logic:** Users **enter** the series when they **match the filters in any entry rule block**. Entry rules are checked once per hour or on user ping (Messenger). So “Started” = **enrollment event** (first time they matched an entry rule), not “received first message”.
- **Time period in UI:** When you pick a date range, “Started” = users who **started (entered) in that period**.

### Finished

- **UI:** “Users who’ve **finished** your Series — they’ve **reached the end of a path** and have no further content to be delivered.”
- **Time period:** Users who **finished in the selected period** (first_series_completion timestamp in range).

### Disengaged

- **UI:** “Users who’ve **disengaged** — **reached a rule block they do not match**, or **didn’t come online to receive a message**.” Also: no email, invalid email, unsubscribe, spam, hard bounce, or (in-app) didn’t come online in time; (rule block) didn’t match filters in time.
- **Time period:** Users who **disengaged in the selected period** (first_series_disengagement timestamp in range).

### Exited

- **UI:** “Users who have **exited** the Series by **matching the exit rules**.”
- **Time period:** Users who **exited in the selected period** (first_series_exit timestamp in range).

### Goal

- **UI:** “Customers who **met the Series goal**” (the action defined as the goal for the series).
- **Time period:** Users who **hit the goal in the selected period** (first_goal_success timestamp in range).

---

## What the Content Data Export gives us

- **API:** `POST /export/content/data` with `created_at_after` / `created_at_before` (Unix). Export is **messages sent** in that range. Download is ZIP with `receipt_*.csv` (and optionally other CSVs).
- **Receipt CSV columns (relevant):**  
  `user_id`, `series_id`, `series_title`, `received_at`, `first_series_completion`, `first_series_disengagement`, `first_series_exit`, `first_goal_success`, etc.

So we have **per-message receipt** rows for messages **sent** in the date range, with timestamps for first completion/disengagement/exit/goal (when that event first happened for that user/series).

---

## How we align with the UI

| Metric     | UI definition (in period)        | What we can do from export                         | Match? |
|-----------|-----------------------------------|----------------------------------------------------|--------|
| **Started**   | Users who **entered** (matched entry rules) in the period | We only have **message receipts** in the period. We count **distinct users with ≥1 receipt** in the export. That includes users who entered **before** the period and got a message **in** the period, so our number is often **higher** than the UI “Started”. We do **not** have “enrollment date” or “first message in series” in this export. | **No** – export has no entry/enrollment event. |
| **Finished**  | Users who **finished** (reached end of path) in the period | Count distinct users where `first_series_completion` is **within** the report date range. | **Yes** (in-period filtering). |
| **Disengaged** | Users who **disengaged** in the period | Count distinct users where `first_series_disengagement` is **within** the report date range. | **Yes** (in-period filtering). |
| **Exited**    | Users who **exited** in the period | Count distinct users where `first_series_exit` is **within** the report date range. | **Yes** (in-period filtering). |
| **Goal**      | Users who **hit the series goal** in the period | Count distinct users where `first_goal_success` is **within** the report date range. | **Yes** (in-period filtering). |

---

## Why “Started” differs (e.g. 5,919 vs 3,688)

- **UI “Started” (e.g. 3,688):** Users who **entered** the series (matched an entry rule) **in** the selected period.
- **Our “started” (e.g. 5,919):** Distinct users who **received at least one message** from the series in the period (any receipt in the export). That includes users who entered earlier and got a message in the period.
- So our “started” is a **receipt-based** count, not an **enrollment-based** count. To match the UI we would need an API or export that exposes **when each user entered the series** (entry rule match time); the Content Data Export does not provide that.

---

## UI CSV export (different from Content Data Export API)

From [Measure how well your series performs](https://www.intercom.com/help/en/articles/4425234-measure-how-well-your-series-performs):  
“You can get an export of your **Series stats** through the **Series Overview page**” (date range, then email with link). That export includes separate files, e.g.:

- `checkpoint_*.csv`
- `receipt_*.csv`
- **`series_completion_*.csv`**
- **`series_disengagement_*.csv`**
- **`series_exit_*.csv`**
- **`goal_success_*.csv`**
- content-specific stats (opens, clicks, replies, etc.)

That **in-product Series export** may be built from the same backend as the UI and can therefore match the UI exactly. Our pipeline uses the **Content Data Export API** (single receipt CSV with `first_*` columns), which is the only one we have programmatic access to for now.

---

## Recommendations

1. **For “Finished”, “Disengaged”, “Exited”, “Goal”**  
   Use our in-period logic (timestamps within the report range). These should align with the UI for the same period, up to timestamp format/timezone.

2. **For “Started”**  
   Treat our value as “users who received at least one message in the series in the period”, not “users who entered in the period”. For true “Started” (entry-in-period), use the Intercom UI or the Series Overview CSV export until an API exposes enrollment/entry data.

3. **If numbers still differ**  
   Check: (a) timezone (UI may use workspace or user TZ), (b) exact date range (inclusive boundaries), (c) timestamp format in the receipt CSV (Unix seconds vs ms vs ISO).

4. **Compare with UI segment exports**  
   Run `tools/scripts/intercom/compare_series_segments.mjs [from_date] [to_date]`. The script:
   - Requests an export with a **31-day lookback** before `from_date` so the receipt CSV includes receipts referenced by segment events (disengagement/completion/goal) in the report period.
   - Joins segment CSVs (`series_completion_*.csv`, `series_disengagement_*.csv`, `series_exit_*.csv`, `goal_success_*.csv`) to the receipt CSV via `receipt_id` to filter by series and count distinct users in the report date range.
   - Reports **UI-aligned** metrics (started from receipts in period, finished/disengaged/exited/goal from segment files). Use the "UI-aligned" block to compare with the Intercom Performance Summary.
   - **Started** may still be slightly higher than the UI (we count "received a message in period"; the UI counts "entered the series in period"). **Finished / Disengaged / Exited / Goal** should be close; small differences can be timezone (UTC vs workspace) or boundary definitions.
