# Discogs Clone — Website Description (from provided screenshots)

This document describes the target website UI/UX and functional requirements inferred from the reference images:

- `landingpage.png` / `screenshot_1.png`: Homepage
- `screenshot_2.png`: Genre overview (Rock)
- `screenshot_3.png`: Release detail page
- `screenshot_4.png`: Marketplace listings for a release

The goal is to implement a functionally and visually identical website to these references (production-ready), including a realistic database, an API, and a Python SDK.

---

## 1) Global layout & design system

### 1.1 Header (global)

- **Top bar**: dark/black background, full width.
- **Left**: Discogs wordmark/logo.
- **Center**: search box with placeholder similar to “Search artists, albums and more…” and a search icon button.
- **Primary nav**: text links with dropdowns:
  - **Explore** (dropdown mega-menu with categories)
  - **Marketplace** (dropdown)
  - **Community** (dropdown)
- **Right icons**:
  - notification / inbox
  - cart
  - user/account (auth state changes: login/register vs avatar/menu)

### 1.2 Footer (global)

Large multi-column footer on dark background:

- **Columns**:
  - Discogs (About, Careers, Discogs Digs, etc.)
  - Help Is Here (Help & Support, Shipping, Guides, etc.)
  - Join In (Get Started, Forum, etc.)
  - Follow Us (Facebook, X/Twitter, YouTube, Instagram, etc.)
  - On The Go (App Store + Google Play badges)
- **Bottom bar**: copyright, links (Terms, Privacy, Cookies), language selector.

### 1.3 Cards & grids

- Album/release cards with:
  - square cover image
  - title (release)
  - artist (sometimes)
  - optional subtitle/meta
- Grids are typically **6–8 columns** on desktop, responsive to fewer columns on smaller widths.
- Sections have clear headings and “See more …” links aligned to the right.

### 1.4 Cookie consent banner

Cookie/privacy banner appears above content sections with:
- short explanatory text
- buttons: **Cookie Settings**, **Accept All Cookies**

---

## 2) Homepage (`/`)

### 2.1 Hero module

Large hero area with:
- **Left**: editorial title like “10 Essential Synth-Pop Albums”
- **Background image**: a wide hero image (synth keyboard / music imagery)
- **Right column**: stacked promo tiles/cards (3) with:
  - thumbnail image
  - title (e.g., “Explore new releases on Discogs”)
  - subtitle (e.g., “Weekly…”)
  - CTA feel (clickable)

### 2.2 Banner ad / featured promo

Full-width banner (e.g., Pink Floyd “Dark Side of the Moon”) between hero and content.

### 2.3 “Trending Releases”

Section title: **Trending Releases**
- Horizontal row of 4–6 release cards.
- Each card: cover + title + artist; short subtitle for “New Trending Releases” or similar.

### 2.4 “Most Expensive Releases Sold This Month”

Dark-background section:
- Heading
- A row of release cards with sparse metadata
- “See how these expensive items sold” style link on the right.

### 2.5 Newsletter

Inline form on dark background:
- label “Email”
- email input
- green **Subscribe** button

### 2.6 “Explore Newly Added”

Section title: **Explore Newly Added**
- Grid of release cards (covers + title + artist).

### 2.7 Mobile app promo

Two phone mockups image (left) + text (right):
- headline like “It’s everywhere!”
- app store buttons (Apple + Google)

---

## 3) Genre overview page (`/genre/:slug`)

Reference is **Rock Genre Overview**.

### 3.1 Sub-navigation bar

Below header, a dark horizontal menu with multiple items:
- Rock Overview
- Rock Releases
- Rock Artists
- Rock (other subpages)

### 3.2 Genre header / intro

- Page title: “Rock Genre Overview”
- A “Rock Music Description” block with multiple paragraphs (Wikipedia-like).

### 3.3 “Most Collected Rock Music”

Row of album covers (carousel-like), with a link:
- “Explore the Popular Rock Music” (or similar)

### 3.4 “Rock Artists”

A grid/row of artist cards (images or placeholders).

### 3.5 “Early Rock Releases”

Row of cover thumbnails with a link:
- “Explore Early Rock Music”

### 3.6 Analytics charts (key visual requirement)

Two chart panels side-by-side:

- **Left**: “Rock Music Releases by Decade”
  - bar chart per decade
  - table underneath listing decade and number of releases

- **Right**: “Top Submitters of Rock Music”
  - bar chart per contributor/user
  - table underneath listing contributor and number of releases

### 3.7 “Most Sold Rock Releases This Month”

Grid of release cards with “Explore more Trending Rock Music” link.

### 3.8 Related styles/tags

Tag list under “Related Styles of Music” with pills:
- Pop Rock, Hard Rock, Indie Rock, Alternative Rock, etc.

---

## 4) Release detail page (`/release/:id`)

This is a long, content-heavy page (Discogs-style).

### 4.1 Above-the-fold

Two-column layout:

- **Left column**:
  - cover image
  - basic metadata table (label, catalog #, format, country, released, genre/style)
  - action buttons: **Add to Wantlist**, **Add to Collection**, and links to marketplace

- **Right column**:
  - marketplace summary (e.g., “For Sale” count + starting price)
  - short stats: have/want counts, average rating, rating count
  - potentially a small “Buy” module or “Sell on Discogs” CTA

### 4.2 Main content sections (scroll)

- Tracklist table (position, title, duration)
- Credits (performers, producers)
- Notes (long text)
- Identifiers (barcodes, matrix/runout, etc.)
- Versions / “Other versions” list (table)
- Recommendations / “You may also like”
- Activity/comments section near bottom

### 4.3 Right rail (sticky-ish feel)

May include:
- quick marketplace links
- “Add to cart” for best listing
- seller/price highlights

---

## 5) Marketplace listings for a release (`/sell/release/:id` or `/marketplace/release/:id`)

Long page with:

### 5.1 Title + seller tools

- Release title and “For Sale” context.
- Buttons like “Start Selling” / “Sell a copy” (depending on auth).

### 5.2 Filters panel

A filter form with multiple selects:
- **Media Condition**
- **Sleeve Condition**
- **Ships From**
- **Seller Rating** / “Minimum rating”
- **Price range**
- **Currency**

### 5.3 Listings table (core feature)

A tall table with rows. Columns commonly include:
- Seller
- Ships From
- Condition (media/sleeve)
- Price
- Quantity
- Add to Cart / Buy button

Rows show:
- seller name + rating badge
- shipping origin
- condition text
- price
- a button (cart icon)

### 5.4 Thread / discussion area

Below listings there is a comment-like thread with replies (community content).

---

## 6) Core functional requirements (MVP-to-production for this clone)

### 6.1 Accounts & auth

- Register/login/logout
- Session/JWT-based auth for API and SDK
- User profile: username, avatar, location, rating

### 6.2 Catalog

- Entities:
  - Genres & styles
  - Artists
  - Labels
  - Releases (with formats and tracklist)
- Search:
  - by artist, release title, label
  - filters (genre/style)

### 6.3 Marketplace

- Listings for a release
- Filters & sorting
- Cart
- Checkout (simulate purchase; create an order record)
- “Sell” flow:
  - authenticated user can create/edit listings

### 6.4 Collection & wantlist

- Add/remove releases from collection
- Add/remove releases from wantlist
- Show counts (have/want) on release pages

### 6.5 Analytics for genre page

- Releases by decade
- Top submitters/contributors (seeded as users who “submitted” releases)

---

## 7) Data requirements

- Database must be populated with **realistic** data (not a handful of dummy rows):
  - dozens of artists, labels, genres/styles
  - hundreds of releases (enough to power trending/newly added, genre stats, marketplace listings)
  - tracklists, durations, countries, years/decades
  - marketplace listings across many releases with varied conditions and prices
  - multiple users with ratings, orders, collection/wantlist items
- Images must come from `https://images.unsplash.com/` (use deterministic URLs to keep seeds stable).

---

## 8) Non-functional requirements

- Production deployable:
  - environment variable config
  - DB migrations
  - health checks
  - Docker support
- API documented (OpenAPI) and consumable from a Python SDK.

