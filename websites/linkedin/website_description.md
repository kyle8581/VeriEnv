# Website description (from screenshots)

This document describes the target website’s **visual layout and functional behavior** based on:

- `landingpage.png`
- `screenshot_1.png`
- `screenshot_2.png`
- `screenshot_3.png`
- `screenshot_4.png`

Goal: implement a **functionally and visually identical** site to these references.

## 1) Global layout and design language

### 1.1 Page grid (desktop)

Across feed/search pages, the UI uses a LinkedIn-style 3-column layout:

- **Top fixed header**: full-width, white background, subtle bottom border.
- **Content area**: centered with max width similar to ~1128px (LinkedIn-like), divided into:
  - **Left rail**: narrow column (profile shortcuts / filters).
  - **Main column**: feed or search results content.
  - **Right rail**: news/promotions or suggestions.

Background is a very light gray/off-white. Cards are white with soft borders and subtle shadows.

### 1.2 Typography and spacing

- Sans-serif system-like font; medium-weight headings.
- Dense but readable spacing; consistent card paddings.
- Icons are small, monochrome/gray; badges are red circles with numbers.

## 2) Top header / navigation

### 2.1 Elements (left → right)

- **LinkedIn logo**: “in” mark on the far left.
- **Global search bar**:
  - Input placeholder changes per context (e.g., jobs keyword).
  - Shows **typeahead autosuggest dropdown** (see section 3).
- **Primary nav icons** (icons only, with optional badges):
  - Home
  - My Network
  - Jobs
  - Messaging (badge visible in screenshots)
  - Notifications (badge visible in screenshots)
  - “Me” avatar menu (not expanded in screenshots)
- **Apps grid icon** (9-dot)
- **“Try Premium for free”** text link at far right

Header remains consistent across feed/search/jobs pages.

## 3) Global search typeahead (screenshot_1)

When the search input is focused and user types:

- A dropdown appears under the search input.
- It includes multiple suggestions such as:
  - the typed query itself (e.g., “bioinformatician”)
  - related queries (e.g., “bioinformatician jobs”, “bioinformatician salary”)
  - related keywords (e.g., “bioinformatics”)
- A clear CTA at bottom: **“See all results”**

Keyboard behavior (expected):

- Arrow up/down changes highlighted suggestion.
- Enter selects suggestion or submits search.
- Clicking a suggestion navigates to search results for that query.

## 4) Feed page (landingpage.png)

### 4.1 Left rail (profile + shortcuts)

At top, a profile card shows:

- User avatar
- Greeting line: “Welcome, {FirstName}!”
- “Add a photo” style action (in LinkedIn it’s often a prompt; implement as link/button)
- Shortcuts list:
  - Connections count (or “Grow your network”)
  - “Recent”
  - “Groups”
  - “Events” (with a plus icon on the right)
  - “Followed Hashtags”
- Bottom of card: **“Discover more”**

### 4.2 Main column

#### Post composer (“Start a post”)

Card at top of feed:

- Input-like button: **“Start a post”**
- Quick actions row with icons + labels:
  - Photo
  - Video
  - Event
  - Write article

#### Feed items

Scrolling feed with:

- News-style posts (e.g., “LinkedIn News”)
- Sponsored/promotional content (e.g., WGU banner)
- Regular user posts with:
  - Author + title line
  - Timestamp
  - Body text
  - Optional image
  - Reaction count line
  - Action row: Like, Comment, Repost, Send

### 4.3 Right rail

Right sidebar cards include:

- **“LinkedIn News”** card
  - “Top stories” list items with bullet-like rows
  - A “Show more” interaction
- A promotional card (e.g., profile views / premium upsell)

### 4.4 Messaging floating UI

Bottom-right floating element indicates messaging availability (collapsed bar).

## 5) Search results page (screenshot_2)

### 5.1 Search tabs row

Under the header, a horizontal list of tabs:

- Jobs
- People
- Posts
- Groups
- Courses
- Events
- Products
- Companies
- Services

Tab selection changes the primary content view; screenshot shows a blended view that surfaces Jobs and Posts sections (implement a default “All” style results page, plus tab-filtered pages).

### 5.2 Results content (main column)

Sections visible:

- **Jobs** section:
  - multiple job cards with company, title, location, and “Save” button
  - “See all job results in United States” style link
- **Posts** section:
  - post cards with author and “Follow” button
- **More jobs** section:
  - compact list of additional jobs with “Save”
- Feedback module:
  - “Are these results helpful?” with yes/no (or thumb) controls

### 5.3 Right rail suggestions

A card inviting the user to get job/industry news (email subscription style) and/or follow suggestions.

## 6) Jobs search split-view (screenshot_3)

### 6.1 Top search controls

At the top (below header), two inputs:

- **Keyword** input (e.g., “bioinformatician jobs”)
- **Location** input (e.g., “United States”)
- **Search** button

### 6.2 Filter pill bar

Directly below search inputs, pill dropdowns:

- Date posted
- Experience level
- Company
- Job type
- On-site/remote
- All filters

Pills open menus/modals; “On-site/remote” opens the modal in screenshot_4.

### 6.3 Left column: job list

Contains:

- Header: “Bioinformatician jobs in United States” + result count (e.g., 3,381 results)
- **Set alert** toggle switch
- List of job cards:
  - some labeled “Promoted”
  - each card shows title, company, location, work mode (On-site/Hybrid), and recruiting status

Selecting a job updates the right detail panel.

### 6.4 Right column: job details

Job detail header includes:

- Job title (large)
- Company name
- Location and work mode
- Posted time and applicant count
- Salary range line (e.g., “$78,400/yr - $133,100/yr”)
- Employment type (Full-time)
- Company size line (e.g., “10,001+ employees”)
- Skills list line (e.g., “Skills: Bioinformatics, Sequence Alignment, +8 more”)

Primary actions:

- **Apply** (primary blue)
- **Save** (secondary)

Below: “About the job” with long paragraphs.

## 7) On-site/remote filter modal (screenshot_4)

When “On-site/remote” is opened:

- A centered modal/popup appears with:
  - Title implied by the pill
  - Checkboxes:
    - On-site
    - Hybrid
    - Remote
  - Buttons:
    - Cancel
    - Show results (primary)

Selecting checkboxes updates filters; “Show results” applies and closes.

## 8) Functional requirements (minimum complete set)

### 8.1 Authentication

- Register / login / logout
- Persist session (JWT + refresh)
- Auth-gated pages: feed, jobs, search results

### 8.2 Feed

- Fetch feed posts (paged)
- Create post (text + optional image URL)
- Like/unlike
- Comment (create + list)

### 8.3 Search

- Typeahead suggestions for global search
- Search results pages:
  - All (blended sections Jobs + Posts + More jobs)
  - Jobs tab (routes to jobs search)
  - Posts tab
  - People tab (basic list sufficient but not placeholder)

### 8.4 Jobs

- Job search with keyword + location
- Filters:
  - on-site/hybrid/remote
  - job type
  - date posted
  - experience level
- Split-view list + detail
- Save job / unsave job
- Apply (records an application; can be “external apply” link but must persist state)
- Job alert toggle (records preference)

## 9) Data requirements (seeded realistic DB)

Seed data should be realistic and plentiful (not a handful of dummy rows), including:

- Users with avatars, names, headlines, locations
- Companies with logos (use `https://images.unsplash.com/` for placeholders), industries, sizes
- Jobs with salary ranges, descriptions, skills, locations, work modes, promoted flags
- Posts across multiple users, with timestamps, images, reactions, comments
- Connections/follows (basic graph), saved jobs, applications, job alerts

## 10) Non-functional requirements

- Production-grade project structure
- Input validation and error handling (API + UI)
- Pagination for feed and search
- Reasonable performance (indexed search where applicable)
- Security basics: password hashing, JWT expiry, refresh rotation, CORS, rate-limits (where feasible)

