
# Mini Case Study – Product Attribute Pattern in MongoDB

**DBS302 – Practical 3 mini case study**       
**Student:** Pema Dolker       
**ID:** 02230294   
**Date:** April 23, 2026  


## Table of Contents

1. [Overview](#1-overview)
2. [What Is the Attribute Pattern?](#2-what-is-the-attribute-pattern)
3. [Querying the Attribute Pattern](#3-querying-the-attribute-pattern)
4. [Indexing Attribute Fields](#4-indexing-attribute-fields)
5. [Lab Exercises](#5-lab-exercises)
   - 5.1 [Reviews Collection – Average Rating per Product](#51-reviews-collection--average-rating-per-product)
   - 5.2 [Low Stock Products Query](#52-low-stock-products-query)
   - 5.3 [Customer Segmentation by Tier](#53-customer-segmentation-by-tier)
6. [Custom Index Experiments – explain() Analysis](#6-custom-index-experiments--explain-analysis)
7. [Text Search Enhancement](#7-text-search-enhancement)
8. [Trade-offs](#8-trade-offs)
9. [Summary](#9-summary)

---

## 1. Overview

Today's e-commerce sites offer products from all sorts of categories - electronics, apparel, furnishings, groceries. Each product type has relevant attributes:


| Category | Relevant Attributes |
|----------|-------------------|
| Headphones | brand, color, wireless, battery life (hours) |
| Clothing | size, color, material, fit |
| Laptop | RAM, storage, processor, screen size |
| Cable | brand, length, connector type, color |

In a **relational database**, this would be handled either through a table per product category (schema explosion) or perhaps 100 nullable columns for an individual product table. Neither scales well.

MongoDB's flexible schema solves this with the **Attribute Pattern** — storing variable attributes as a nested sub-document that only contains what each product actually needs.

---

## 2. What Is the Attribute Pattern?

The Attribute Pattern uses a nested key-value sub-document, named `attributes` to store variable product-specific values. The products only bring along the fields they need - no nulls, no empty columns.

This practical showcases this with the three products: the headphones, cable and keyboard each have a different shape of the `attributes` object stored within the same collection.

```js
// Headphones – audio-specific attributes
{
  name: "Wireless Bluetooth Headphones",
  price: 129.99,
  stock: 200,
  attributes: {
    brand: "Acme Audio",
    color: "black",
    wireless: true,
    batteryLifeHours: 24
  },
  tags: ["audio", "wireless", "headphones"]
}

// Cable – physical-specific attributes
{
  name: "USB-C Cable 1m",
  price: 9.99,
  stock: 500,
  attributes: {
    brand: "Acme Tech",
    color: "white",
    lengthMeters: 1
  },
  tags: ["cable", "usb-c"]
}

// Keyboard – input device attributes
{
  name: "Mechanical Keyboard",
  price: 79.99,
  stock: 150,
  attributes: {
    brand: "Acme Input",
    layout: "US",
    switchType: "blue",
    backlight: true
  },
  tags: ["keyboard", "mechanical", "backlit"]
}
```



## 3. Querying the Attribute Pattern

MongoDB uses **dot notation** to query into nested sub-documents. So, the fields `attributes.color` or `attributes.brand` can be queried like any other field.

### Query 1 – Filter by a single attribute

Find all products where `attributes.color` is black AND `attributes.brand` is Acme Audio:

```js
db.products.find({
  "attributes.brand": "Acme Audio",
  "attributes.color": "black"
})
```

This query has an AND combination of two attribute filters, only the Wireless Bluetooth Headphones match.

![Single and multi-attribute filter — only the black Acme Audio headphones returned](<Screenshot From 2026-04-22 10-46-27-1.png>)

---

### Query 2 – Combined attribute filter with index-friendly aggregation

The aggregation pipeline below runs on orders, then alongside it the attribute filter query demonstrates dot notation on nested fields:

```js
// Aggregation: recent PAID orders using index-friendly $match + $sort at start
db.orders.aggregate([
  {
    $match: {
      status: "PAID",
      createdAt: { $gte: new Date("2026-04-19") }
    }
  },
  { $sort: { createdAt: -1 } },
  {
    $project: {
      _id: 0,
      userId: 1,
      createdAt: 1,
      grandTotal: 1,
      itemCount: { $size: "$items" }
    }
  },
  { $limit: 20 }
])
```

With the `{ status: 1, createdAt: -1 }` index, the `$match` and `$sort` at the beginning of the aggregation pipeline are pushed down to the query engine and use the index - making this aggregation fast even with a high throughput.

![Index-friendly aggregation pipeline output and attribute filter result](<Screenshot From 2026-04-22 10-46-14-1.png>)
---

## 4. Indexing Attribute Fields

If there are attributes that are commonly filtered, you can index the attribute as a nested field in dot-notation. This is where the Attribute Pattern shines compared to other patterns - MongoDB supports indexing on nested fields.


```js
// Compound index on brand + color (common filter combination in a storefront)
db.products.createIndex(
  { "attributes.brand": 1, "attributes.color": 1 },
  { name: "idx_products_brand_color" }
)
```

![Index idx_products_brand_color created on nested attribute fields](<Screenshot From 2026-04-22 10-46-48.png>)



This index can be used for queries filtering by brand, or by brand and color (prefix rule). It cannot be used for filtering by color only - field order is important.


---

## 5. Lab Exercises

### 5.1 Reviews Collection – Average Rating per Product

**Goal:** Add a `reviews` collection with embedded comments and ratings, then compute average rating per product using an aggregation pipeline.

#### Insert Reviews

```js
db.createCollection("reviews")

const headphonesId = db.products.findOne({ name: "Wireless Bluetooth Headphones" })._id
const keyboardId   = db.products.findOne({ name: "Mechanical Keyboard" })._id
const tashi        = db.users.findOne({ email: "tashi@example.com" })
const sonam        = db.users.findOne({ email: "sonam@example.com" })

db.reviews.insertMany([
  {
    productId: headphonesId,
    userId:    tashi._id,
    rating:    5,
    comment:   "Excellent sound quality and battery life!",
    createdAt: new Date("2026-04-20T10:00:00Z")
  },
  {
    productId: headphonesId,
    userId:    sonam._id,
    rating:    4,
    comment:   "Very comfortable, slightly pricey.",
    createdAt: new Date("2026-04-20T11:00:00Z")
  },
  {
    productId: keyboardId,
    userId:    sonam._id,
    rating:    5,
    comment:   "Great tactile feedback. Love the blue switches!",
    createdAt: new Date("2026-04-21T09:00:00Z")
  },
  {
    productId: keyboardId,
    userId:    tashi._id,
    rating:    3,
    comment:   "A bit loud for office use.",
    createdAt: new Date("2026-04-21T10:30:00Z")
  }
])
```

![Reviews collection created and 4 reviews inserted successfully](<Screenshot From 2026-04-22 10-47-26.png>)

#### Aggregation – Average Rating per Product

```js
db.reviews.aggregate([
  {
    $group: {
      _id:           "$productId",
      averageRating: { $avg: "$rating" },
      totalReviews:  { $sum: 1 },
      minRating:     { $min: "$rating" },
      maxRating:     { $max: "$rating" }
    }
  },
  {
    $lookup: {
      from:         "products",
      localField:   "_id",
      foreignField: "_id",
      as:           "product"
    }
  },
  { $unwind: "$product" },
  {
    $project: {
      _id:           0,
      productName:   "$product.name",
      averageRating: { $round: ["$averageRating", 2] },
      totalReviews:  1,
      minRating:     1,
      maxRating:     1
    }
  },
  { $sort: { averageRating: -1 } }
])
```

**Pipeline explanation:**
- `$group` - Aggregates all reviews by its `productId`, calculating the average, count, minimum and maximum of the `rating` field.
- `$lookup` - Joins with `products` to get the product name from its `_id`.
- `$unwind` - Flattens single-item array returned by `$lookup` to plain object..
- `$project` - FFormats the result, rounding up `averageRating` to 2 decimal places.
- `$sort` - Sorts products by highest rating.

![Average rating per product: Headphones 4.5, Keyboard 4.0](<Screenshot From 2026-04-22 10-47-38.png>)  

**Result:** Wireless Bluetooth Headphones averaged **4.5** from 2 reviews; Mechanical Keyboard averaged **4.0** from 2 reviews.

---

### 5.2 Low Stock Products Query

**Goal:** Find products with low stock (stock < 10), enriched with category name.

First, the stock of the Mechanical Keyboard was set to 7 to create a low-stock product:


```js
db.products.updateOne(
  { name: "Mechanical Keyboard" },
  { $set: { stock: 7 } }
)
```

![Stock updated to 7 for Mechanical Keyboard (matchedCount: 1, modifiedCount: 1)](<Screenshot From 2026-04-22 10-48-40.png>)

#### Low Stock Aggregation Pipeline

```js
db.products.aggregate([
  { $match: { stock: { $lt: 10 } } },
  {
    $lookup: {
      from:         "categories",
      localField:   "categoryId",
      foreignField: "_id",
      as:           "category"
    }
  },
  { $unwind: "$category" },
  {
    $project: {
      _id:              0,
      name:             1,
      stock:            1,
      price:            1,
      categoryName:     "$category.name",
      "attributes.brand": 1
    }
  },
  { $sort: { stock: 1 } }
])
```

**Pipeline explanation:**
- `$match`  - Limits to products with stock under 10, filtering early.
- `$lookup` - Joins with `categories` to enrich each result with the category name.
- `$project` - Restrains the results to only those needed for a stock alert report.
- `$sort` -  Sorts by the most urgent (lowest stock first).

![Low stock result: Mechanical Keyboard, stock 7, category Electronics](<Screenshot From 2026-04-22 10-48-53.png>)

**Result:** Only the Mechanical Keyboard appeared with `stock: 7` under the Electronics category — exactly as expected.

---

### 5.3 Customer Segmentation by Tier

**Goal:** Group customers into Bronze / Silver / Gold tiers based on total amount spent, and write the tier back into the `users` collection using `$merge`.

**Tier thresholds:**
- **Gold** — total spent ≥ $200
- **Silver** — total spent ≥ $100
- **Bronze** — all others

#### Step 1 – Compute tiers and preview results

```js
db.orders.aggregate([
  { $match: { status: "PAID" } },
  {
    $group: {
      _id:        "$userId",
      totalSpent: { $sum: "$grandTotal" }
    }
  },
  {
    $addFields: {
      tier: {
        $switch: {
          branches: [
            { case: { $gte: ["$totalSpent", 200] }, then: "Gold"   },
            { case: { $gte: ["$totalSpent", 100] }, then: "Silver" }
          ],
          default: "Bronze"
        }
      }
    }
  },
  {
    $lookup: {
      from:         "users",
      localField:   "_id",
      foreignField: "_id",
      as:           "user"
    }
  },
  { $unwind: "$user" },
  {
    $project: {
      _id:        0,
      userName:   "$user.name",
      totalSpent: 1,
      tier:       1
    }
  },
  { $sort: { totalSpent: -1 } }
])
```

**Pipeline explanation:**
- `$group` - Sums all PAID order totals per user.
- `$addFields` with `$switch` - Checks the tier condition in the following order: first Gold (≥200), then Silver (≥100), then the default Bronze.
- `$lookup` - Joins with `users` to get user names for display.

![Customer tiers computed: Tashi Dorji = Gold ($269.97), Sonam Choden = Bronze ($79.99)](<Screenshot From 2026-04-22 10-49-11.png>)

#### Step 2 - Write tiers back to the users collection using $merge

```js
db.orders.aggregate([
  { $match: { status: "PAID" } },
  {
    $group: {
      _id:        "$userId",
      totalSpent: { $sum: "$grandTotal" }
    }
  },
  {
    $addFields: {
      tier: {
        $switch: {
          branches: [
            { case: { $gte: ["$totalSpent", 200] }, then: "Gold"   },
            { case: { $gte: ["$totalSpent", 100] }, then: "Silver" }
          ],
          default: "Bronze"
        }
      }
    }
  },
  {
    $merge: {
      into:           "users",
      on:             "_id",
      whenMatched:    [{ $addFields: { tier: "$$new.tier", totalSpent: "$$new.totalSpent" } }],
      whenNotMatched: "discard"
    }
  }
])
```

`$merge` inserts the results of the pipeline back into users. `whenMatched` adds or updates a user with the tier and totalSpent values. `whenNotMatched: "discard"` safely skips over any user IDs not in users.





![$merge pipeline writing tier and totalSpent back to users collection](<Screenshot From 2026-04-22 10-49-29.png>)

#### Step 3 – Verify tiers written to users

```js
db.users.find({}, { name: 1, tier: 1, totalSpent: 1 })
```

![Users now have tier and totalSpent fields: Tashi = Gold, Sonam = Bronze](<Screenshot From 2026-04-22 10-49-44.png>)

**Result:** The users now have their calculated tier and totalSpent included - Tashi Dorji is Gold ($269.97) and Sonam Choden is Bronze ($79.99).

---

## 6. Custom Index Experiments – explain() Analysis

**Goal:** Demonstrate how index choice affects query performance for the same query, comparing no index, a partial index, and a full compound index.

**Test query:** Find Electronics products priced ≤ $100, sorted by price ascending.

```js
db.products.find(
  { categoryId: electronicsId, price: { $lte: 100 } }
).sort({ price: 1 })
```

---

### Experiment 1 – No index (COLLSCAN)

The existing `idx_products_category_price` compound index was dropped first:

```js
db.products.dropIndex("idx_products_category_price")
const electronicsId = db.categories.findOne({ name: "Electronics" })._id

db.products.find(
  { categoryId: electronicsId, price: { $lte: 100 } }
).sort({ price: 1 }).explain("executionStats")
```

![explain() COLLSCAN: totalDocsExamined=3, totalKeysExamined=0, executionTimeMillis=7](<Screenshot From 2026-04-22 11-05-44.png>)

| Field | Value |
|-------|-------|
| `winningPlan.inputStage.stage` | `COLLSCAN` |
| `totalDocsExamined` | 3 (every product scanned) |
| `totalKeysExamined` | 0 |
| `executionTimeMillis` | 7 ms |

**Observation:** Without any index, MongoDB scans all 3 documents regardless of the filter. At scale (millions of products) this would be extremely slow.

---

### Experiment 2 – Single-field index on categoryId only (partial IXSCAN)

```js
db.products.createIndex(
  { categoryId: 1 },
  { name: "idx_products_category_only" }
)

db.products.find(
  { categoryId: electronicsId, price: { $lte: 100 } }
).sort({ price: 1 }).explain("executionStats")
```

![explain() IXSCAN with single-field index: uses index for categoryId but still fetches all matching docs for price filter](<Screenshot From 2026-04-22 11-06-15.png>)

**Observation:** The query uses IXSCAN on categoryId - it finds Electronics products using the index. But it needs to apply the price and sort after retrieving the documents (FETCH), because price isn't in the index. This is an improvement from COLLSCAN but not ideal.

---

### Experiment 3 – Compound index { categoryId, price } (full IXSCAN)

```js
db.products.createIndex(
  { categoryId: 1, price: 1 },
  { name: "idx_products_category_price" }
)

db.products.find(
  { categoryId: electronicsId, price: { $lte: 100 } }
).sort({ price: 1 }).explain("executionStats")
```

![explain() full IXSCAN with compound index: totalDocsExamined=1, totalKeysExamined=1, executionTimeMillis=4](<Screenshot From 2026-04-22 11-08-41.png>)


| Field | Value |
|-------|-------|
| `winningPlan.inputStage.stage` | `IXSCAN` |
| `indexName` | `idx_products_category_price` |
| `totalDocsExamined` | 1 (only matching doc) |
| `totalKeysExamined` | 1 |
| `executionTimeMillis` | 4 ms |

**Observation:** With this new compound index, MongoDB will skip straight to Electronics products for which the price is ≤ $100 - only 1 document. The output even shows the single-field index being considered, but rejected, in favour of the compound index.


### Comparison Summary

| Experiment | Index Used | Stage | Docs Examined | Time |
|------------|-----------|-------|---------------|------|
| No index | None | COLLSCAN | 3 | 7 ms |
| Single-field on `categoryId` | `idx_products_category_only` | IXSCAN + FETCH | >1 | — |
| Compound `{ categoryId, price }` | `idx_products_category_price` | IXSCAN | 1 | 4 ms |

The compound index follows the ESR principle: `categoryId` is the **Equality** field, `price` covers both the **Range** filter (≤100) and the **Sort**.

---

## 7. Text Search Enhancement

**Goal:** Extend the text index to include a `description` field and test searches with different terms.

#### Step 1 – Add descriptions to products

```js
db.products.dropIndex("idx_products_text")  // Drop the old text index first

db.products.updateOne(
  { name: "Wireless Bluetooth Headphones" },
  { $set: { description: "Premium wireless audio headphones with long battery life and noise cancellation." } }
)
db.products.updateOne(
  { name: "Mechanical Keyboard" },
  { $set: { description: "Durable mechanical keyboard with tactile blue switches and RGB backlight." } }
)
db.products.updateOne(
  { name: "USB-C Cable 1m" },
  { $set: { description: "Fast charging USB-C cable compatible with all modern devices." } }
)
```

#### Step 2 – Create extended text index

```js
db.products.createIndex(
  { name: "text", tags: "text", description: "text" },
  {
    name: "idx_products_text_extended",
    weights: { name: 10, tags: 5, description: 3 }
  }
)
```

The weights determine the relevance: 10 points for a match in the `name`, 5 points in  `tags` and 3 points in `description`. So a product with the search term in its name always scores more highly than one with just a description match.

#### Step 3 – Test searches

```js
// Search 1: "wireless"
db.products.find(
  { $text: { $search: "wireless" } },
  { score: { $meta: "textScore" }, name: 1, price: 1 }
).sort({ score: { $meta: "textScore" } })

// Search 2: "noise cancellation"
db.products.find(
  { $text: { $search: "noise cancellation" } },
  { score: { $meta: "textScore" }, name: 1, price: 1 }
).sort({ score: { $meta: "textScore" } })

// Search 3: "mechanical backlight"
db.products.find(
  { $text: { $search: "mechanical backlight" } },
  { score: { $meta: "textScore" }, name: 1, price: 1 }
).sort({ score: { $meta: "textScore" } })
```

![Extended text index created; three searches returning results ranked by relevance score](<Screenshot From 2026-04-22 11-08-53.png>)

**Observations:**
- **Search 1 ("wireless")** - Headphones returned with high score, as "wireless" is in the name (weight 10) and tags (weight 5).
- **Search 2 ("noise cancellation")** - Headphones returned with a match in description (weight 3), demonstrating the extended index can match terms not in name or tags.
- **Search 3 ("mechanical backlight")** - Mechanical Keyboard with score 15.875 via name (weight 10) and tags/description (weights 5 and 3).

---

## 8. Trade-offs

| Benefit | Trade-off |
|---------|-----------|
| No migrations when adding new attribute types | Can't enforce required attributes at database level - must be done in the application |
| No nulls - only relevant fields for each product | Attributes are untyped; batteryLifeHours: "24" (string) and 24 (number) are both valid |
| Adapts to different product catalogs | Querying on a seldomly-used attribute for many products is slow without an index
| New product attributes are backwards-compatible | Many attribute indexes leads to higher write costs and index size |
| $text index supports rich product search with query relevance | One text index per collection; fields can only be added by dropping and recreating the index |


---

## 9. Summary

This mini case study demonstrated the Attribute Pattern across five practical areas:

**Schema flexibility** — Three products with completely different `attributes` shapes coexist in the same collection, with no schema changes required between them. Dot-notation queries (`"attributes.brand"`, `"attributes.color"`) work exactly like top-level field queries.

**Indexing attribute fields** — A compound index on `{ "attributes.brand": 1, "attributes.color": 1 }` makes frequent storefront filter queries fast without any structural changes to the collection.

**Lab exercises** — Four additional aggregation pipelines were built: average product ratings from a reviews collection, a low-stock alert query with category enrichment, customer tier segmentation using `$switch` and `$addFields`, and writing computed data back to a collection using `$merge`.

**Index experiments** — Running `explain("executionStats")` across three index configurations (none, single-field, compound) proved that the compound `{ categoryId, price }` index reduces examined documents from 3 to 1 and halves execution time compared to no index.

**Text search** — Extending the text index to cover `name`, `tags`, and `description` with weighted scoring (10 / 5 / 3) enables rich product search that rewards matches in more important fields with higher relevance scores.

---
