# Website Description (Reference-Based)

This project is a production-quality clone of the **Apartments.com** public rental search experience as shown in the provided screenshots:

- `landingpage.png` / `screenshot_1.png`: marketing landing page with hero search + curated rental cards + informational/marketing sections + large footer.
- `screenshot_2.png` / `screenshot_3.png` / `screenshot_4.png`: search results page with **map + list** split layout, top filter bar with dropdowns, listing cards with actions (favorite, email), and map pins.

The goal is to implement a functionally and visually identical website (within reasonable differences such as images sourced from `https://images.unsplash.com/`).

---

## 1) Global Layout / Design System

### 1.1 Header (Global)
- **Left**:
  - Hamburger icon + “Menu”
  - Globe icon + “English”
- **Center**:
  - Brand mark + wordmark: “Apartments.com”
- **Right**:
  - Links: “Manage Rentals”, “Sign Up / Sign In”, “Add a Property”

### 1.2 Primary Color + Buttons
- Primary accent color is a **deep green** used for:
  - Main CTA buttons (“Search”, “Email”, “View More”)
  - Active filter pill states (“2+ Beds”)
  - Map pin markers (green map markers)

### 1.3 Typography / Spacing
- Large hero heading in bold, centered, white text.
- Secondary headings centered with generous vertical spacing.
- Cards have light shadows and clean, white background.

---

## 2) Landing Page (`/`)

### 2.1 Hero Section
- Full-width hero with a **city skyline photo** background.
- Centered content:
  - H1: “Discover Your New Home”
  - Subtitle: “Helping 100 million renters find their perfect fit.”
  - Search bar:
    - Location input (example shown: “Columbus, OH”)
    - Green “Search” button at the right

### 2.2 “Explore Rentals in {City}” Section
- Title: “Explore Rentals in Columbus, OH”
- A row/grid of **4 property cards**, each showing:
  - Image thumbnail
  - Property name (e.g., “College Park”)
  - Address line
  - Beds and price range line (e.g., “1-2 Beds | $1,075 - $1,695”)
- Centered green button: “View More”

### 2.3 “The Most Rental Listings” Section
- Center title: “The Most Rental Listings”
- Subtitle: “Choose from over 1 million apartments, houses, condos, and townhomes for rent.”
- Below, a set of informational panels:
  - **Renting Made Simple** (left block with heading + descriptive text + link “Find Out More”)
  - A large image to the right (laptop with map)
  - **Tips for Renters** (right/lower block with heading + text + link “Browse Articles”)
  - **Take Us With You** (left/lower block with heading + short copy referencing Apartments.com in pocket)

### 2.4 “The Perfect Place to Manage Your Property” Section
- Center heading and subheading:
  - “The Perfect Place to Manage Your Property”
  - “Work with the best suite of property management tools on the market.”
- Below, panels/cards for:
  - **Advertise Your Rental** + link “List Your Property”
  - **Lease 100% Online** + link “Manage Your Property”
  - **Property Manager Resources** + link “Stay Informed”

### 2.5 Large Footer Discovery Section + Footer Links
- A centered line with embedded links:
  - “Search over 1 million listings including apartments, houses, condos, and townhomes…”
- A dense multi-column link section (examples visible):
  - **Top Markets** (many city links)
  - **Popular Searches**
  - **Rental Manager Services**
- Bottommost footer:
  - Brand logo + copyright
  - Social icons row
  - Several columns of site links:
    - Advertisers / The Marketplace / Neighborhoods / Featured Cities / About Us (etc.)

---

## 3) Search Results Page (Map + List) (`/apartments` or `/search`)

### 3.1 Top Search/Filter Bar
Sticky horizontal controls across top:
- Location input with current query (example: “Boston, MA”)
- Dropdown filters:
  - **Price**
  - **Beds**
  - **Type**
  - **Move-In Date**
  - **More**
- Right side:
  - “Sort” control (with up/down icon)
  - “Save Search” link/button
  - Bell/notification icon

### 3.2 Map + List Split Layout
- **Left ~65–70%**: interactive map (Google-style in reference) with many green pin markers.
  - Map controls appear on the right side of the map:
    - Zoom + / -
    - Additional icons (layers/target-like, draw/edit tool)
- **Right ~30–35%**: vertically scrollable listing results column.

### 3.3 Listing Card (Search Results)
Each card shows:
- Header row:
  - Property name (e.g., “The Brynx”)
  - Address line under the name
  - Small management/company badge at top-right of the card area
  - Heart outline icon at far right for favorite/save
- Media:
  - Large image with left/right carousel arrows
  - Overlay badges on image bottom-left:
    - “Videos”
    - “Virtual Tour”
- Pricing and facts:
  - Price range (e.g., “$2,600 - 4,250”)
  - Bed range (e.g., “Studio - 2 Beds”)
  - “Specials” label sometimes visible
- Amenity snippet list (short comma-separated):
  - Examples: “Dog & Cat Friendly, Fitness Center, Pool, Dishwasher, Refrigerator, …”
- Contact:
  - Phone number displayed
  - Large green CTA button: “Email”

### 3.4 Filters: Beds Dropdown Behavior
The Beds dropdown expands into a panel showing:
- Two selectors for range:
  - “No Min” (min beds)
  - “No Max” (max beds)
- Quick options list:
  - “No Min”
  - “1 Bed”
  - “2 Beds”
  - “3 Beds”
  - “4+ Beds”
When a filter is applied, the filter control becomes a **green pill** (e.g., “2+ Beds”) with a small “x” to clear the filter.

---

## 4) Required Functional Scope (Production-Quality)

To be production-ready and not a static mock, the implementation must include:

### 4.1 Core User Flows
- **Search rentals** by location query (city/state/zip).
- **Filter** results (at minimum: price, beds; plus type, move-in date, “more” as structured filters).
- **View listing details** (click a result card -> details page).
- **Favorite/save listings** (requires authentication).
- **Save searches** (requires authentication).
- **Contact property** via “Email” CTA (should create a contact request record; can optionally send email via provider later).

### 4.2 Auth
- Sign up / sign in (email + password).
- Session/JWT-based authentication for API access.

### 4.3 Data Model (Realistic Seed Data)
Database must be pre-populated with realistic datasets, including:
- Cities/areas with coordinates (for map markers).
- Properties with addresses, geo coordinates, price ranges, bed ranges, amenities.
- Property images sourced from `images.unsplash.com`.
- Optional: agents/companies, reviews/ratings, specials, availability dates.

### 4.4 Developer/Operations Requirements
- Local run scripts:
  - `start_servers.sh` to start frontend + backend locally.
  - `reset_servers.sh` to reset DB back to initial seeded state.
- Python SDK:
  - Auth, API access wrappers, typed models where appropriate.
  - Should support search, listing retrieval, favorites, saved searches, contact requests.

