# Website Description (from `landingpage.png` + `screenshot_*.png`)

## Product summary
This project is a production-ready clone of a Weather.com-style website that combines:

- A **content-heavy weather/news homepage** (top stories, latest news, national weather map, curated modules)
- A **location (city) weather page** with current conditions, hourly forecast strip, multi-day forecast, radar, and “today details”
- A **global header** with search + primary navigation and account controls
- A **right sidebar** on content pages with subscription promo, editor picks, safety content, and ads-like blocks

The implementation must be functionally complete (no dead links/buttons) and visually very close to the screenshots.

---

## Global layout & navigation

### Header (global)
Observed elements across screenshots:

- **Top bar** (blue on homepage, purple/gray theme on city page):
  - Brand area on left
  - **Primary nav** items: `Today`, `Hourly`, `10 Day`, `Radar`, `Video`, `More Forecasts`
  - Right-side actions: search, settings/menu icons, **Sign In**, and a prominent **Subscribe**/plan button
- **Search input**: “Search City or Zip Code”
  - Shows a **typeahead dropdown** with suggested locations (e.g., “Atlanta, GA”, “Atlanta, TX”, etc.)
  - Selecting a suggestion navigates to that location’s weather page

### Page grid
- **Two-column** layout:
  - **Main content column** (left, wide)
  - **Sidebar** (right, narrow) containing stacked cards
- A top “ad banner” placeholder region appears above some pages/sections.

### Footer (global)
Footer includes:
- “Connect With Us” social icons row
- Standard informational links (Terms, Privacy, etc.)
- Brand/legal line and small partner logos

---

## Homepage (`/`) – content modules (from `landingpage.png`, `screenshot_1.png`, `screenshot_3.png`, `screenshot_4.png`)

### Hero / Top Stories module
Title: **Top Stories**

Layout:
- Left: a **large featured story** tile with:
  - Image/thumbnail with a **play** icon overlay (video-like)
  - Headline (example: “Huge Texas Sinkhole Suddenly Starting To Expand”)
  - Metadata row (time/source style)
  - A bulleted/stacked list of additional story links underneath the headline area
- Right: a grid/stack of **smaller story cards** with thumbnails and titles
- A **“See More”** button at module bottom-left

### Latest News module
Title: **Latest News**

Layout:
- A horizontal row of small cards with thumbnails + short titles
- **“See More”** button at module bottom-left

### National weather map module
Title: **Weather Today Across the Country**

Layout:
- A wide **USA map visualization** with colored temperature overlay and small labels
- Timestamp/updated indicator near the title area
- **“See More”** button

### Recommended module
Title: **Recommended**

Layout:
- A row of medium cards (thumbnail + title)
- **“See More”** button

### Photos module
Title: **Photos**

Layout:
- A row of photo cards (thumbnail + title/caption)
- **“See More”** button

### Sponsored Content section
Title: **Sponsored Content**

Layout:
- Large wide block near the bottom with:
  - Text link lists and/or ad-like content blocks
  - Empty/placeholder ad slots in the screenshot that must be implemented as real components (not broken)

### Sidebar modules on homepage
Stacked cards observed:
- **“New: Subscription Bundle”** promo card (with close “X” in screenshot)
- **Editor’s Picks**: vertical list of cards (some with video play icon)
- **Stay Safe**: safety-related content card(s)
- **Stunning Sights in Nature**: curated card
- **Featured Deal**: product/deal card with image + CTA
- Additional “ad slot” type rectangles interleaved

### Promotional banner (screenshot_3 / screenshot_4)
A large banner ad at the top of the homepage content area (e.g., “Your trip is waiting…”) appears in some variants.

---

## Location weather page (example: Los Angeles) – modules (from `screenshot_2.png`)

### Location header
- Page title: **“Los Angeles, CA Weather”**
- Current condition summary area:
  - Large current temperature (e.g., **60°**)
  - Condition text (e.g., “Mostly Cloudy”)
  - High/Low
  - Updated time

### Alerts strip
An inline alert-style banner appears under the header (severity/info style).

### Hourly forecast strip
Horizontal row of hourly items:
- Each item shows time, icon, and temperature
- Scrollable/overflow behavior

### “Today” details panel(s)
Below/near hourly strip:
- Metric tiles such as:
  - Wind, Humidity, Pressure, Visibility, Dew Point
  - UV Index, Air Quality
  - Sunrise/Sunset, Moon phase

### Radar / maps
A radar preview module with thumbnail/map imagery.

### Daily forecast & longer-range
Sections like:
- Daily forecast cards (multi-day)
- Monthly/seasonal summary blocks (as seen lower on the page)

### Right sidebar on location page
Similar stacked sidebar with:
- “Today’s Weather” summary card (sunrise/sunset style)
- Air quality / pollen / health-related cards
- Additional curated content cards and ad blocks

---

## Functional requirements (must be fully implemented)

### Content system
- Articles/stories with:
  - title, slug, deck/summary, body, hero image (Unsplash), published timestamp
  - category tags (Top Stories, Latest News, Editor’s Picks, Stay Safe, etc.)
  - optional “video” flag to show play overlay
- Photos gallery items (image + caption)
- “Featured deals” items (image + CTA link)

### Weather data
- Location search by city/zip with typeahead
- Location pages render:
  - current conditions
  - hourly forecast
  - multi-day forecast
  - radar/map preview (implemented as an interactive map component or a radar-like tile)
- Weather data should be **realistic and dynamic** (not hard-coded), with caching to avoid rate limits.

### Accounts & personalization
- Authentication (email/password):
  - sign up, sign in, sign out
  - token-based auth for API
- Saved locations:
  - add/remove a location to “My Locations”
  - list saved locations in account area

### Subscription
- A subscription promo module is visible in the sidebar/home.
- A subscription plan page and a functional subscribe/unsubscribe flow (mock payment, but real DB state).

### No dead UI
- All nav links and “See More” buttons must route to real pages that render real content from the DB/API.

---

## Pages to implement (minimum)
- `/` Homepage
- `/today` National highlights (can reuse homepage modules with different filtering)
- `/hourly` (location-aware; prompts to select/search a location if none)
- `/tenday` (location-aware)
- `/radar` (location-aware + national view)
- `/video` Video/story feed
- `/news` News feed
- `/photos` Photos gallery
- `/deals` Featured deals page
- `/account/sign-in`
- `/account/sign-up`
- `/account/saved-locations`
- `/subscribe` Plans + subscribe flow
- `/weather/:locationSlug` Location weather page (e.g., Los Angeles)

---

## Data requirements (DB seeding)
Seed the database with **realistic volume** (not a handful of rows):

- Locations: 200+ (US-focused; include major cities + many medium/small)
- Articles: 150+ across categories (Top Stories, Latest, Editor’s Picks, Stay Safe, etc.)
- Photos: 80+
- Deals: 20+
- Users: 5–10 test accounts (document credentials in dev-only docs)

All media uses `https://images.unsplash.com/…` URLs.

---

## API requirements
Provide a first-party REST API for:
- Auth (register/login/refresh/logout)
- Locations search + saved locations management
- Weather endpoints (current/hourly/daily) by location
- Content endpoints (articles/photos/deals) with category filters and pagination

Also provide a **Python SDK** that supports:
- authentication/token management
- calling all major API endpoints
- typed responses and helpful errors

