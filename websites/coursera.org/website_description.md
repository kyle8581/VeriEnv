# Website Description (Reference-Based Spec)

This project must replicate the reference website provided by:

- `landingpage.png` (long scroll capture)
- `screenshot_1.png` and `screenshot_2.png` (Coursera for Campus marketing landing page)
- `screenshot_3.png` and `screenshot_4.png` (Ebook lead-capture page: “Job Skills of 2023 Report”)

The goal is **functionally and visually identical** to the reference pages, while also being a production-deployable, fully functional web app with API, authentication, database, realistic seeded data, and a Python SDK.

---

## 1) Global Layout, Style, and UX

### 1.1 Typography & Spacing
- **Overall feel**: enterprise marketing site; clean, spacious, high readability.
- **Headings**: large, bold, modern sans-serif.
- **Body**: mid-gray text with generous line-height.
- **Grid**: fixed-width centered content with wide margins on desktop; consistent vertical rhythm between sections.

### 1.2 Color System (Observed)
- **Primary blue**: used for main CTA buttons and accents (e.g., “Contact Us”, “Learn more” link).
- **Neutrals**: white background, light gray section backgrounds, medium gray text.
- **Dark highlight**: black/dark-gray feature/stat card area on the homepage hero.

### 1.3 Common Components
- **Top navigation bar** (sticky-looking, white background)
  - Left: `coursera for campus` logo/wordmark.
  - Center nav items (desktop): `Why Coursera`, `Solutions`, `Resources`, `Compare Plans`
    - `Why Coursera`, `Solutions`, `Resources` show a dropdown indicator (caret).
  - Right: blue button `Contact Us`.
- **Footer**
  - Column headings: `Coursera`, `Community`, `More`, `Mobile App`
  - Mobile app area shows two store badges/images.
  - Bottom small-print: copyright line (e.g., “© 2023 Coursera Inc. All rights reserved.”)
  - Social icons aligned bottom-right (small square icons).

### 1.4 Responsiveness
- Desktop-first reference; implement fully responsive:
  - Nav collapses to hamburger on small screens.
  - Hero image stacks below text on mobile.
  - Multi-column feature blocks become stacked.

---

## 2) Page: Coursera for Campus Marketing Homepage
Source: `screenshot_1.png` + `screenshot_2.png`

### 2.1 Hero Section
- **Left column**
  - Large headline: “Strengthen employability to attract more students”
  - Supporting paragraph: mentions helping students with in-demand skills and preparing them for job success.
  - Primary CTA button: blue `Contact us`
  - Secondary link: `Learn more` (text link)
- **Right column**
  - Large photo: two people smiling/working on laptop (marketing image)
- **Below hero**: dark stats strip/card spanning width
  - 3 statistics in a row (each block separated visually):
    - Example: “76% …” (employment-related outcome)
    - Example: “85% …” (confidence/skill development)
    - Example: “90% …” (impact/satisfaction)
  - White text on dark background, concise descriptors under each percentage.

### 2.2 Partner Logos Section
- Headline: “Offer students 5,400 courses from 275+ leading universities and industry partners”
- Right side: grid/mosaic of university/partner logos (multi-color logos on white).

### 2.3 “Prepare your students…” Feature Section
- Two-column layout:
  - Left: photo (students / workplace scene)
  - Right:
    - Eyebrow label: “COURSE CATALOG”
    - Heading: “Prepare your students for in-demand jobs”
    - Bullet list describing benefits (career readiness, professional certificates, job-relevant content).
    - Link: “Explore course catalog and credentials” (or similar) in blue.

### 2.4 “Expand your curriculum…” Blue Band Section
- Full-width blue band with:
  - Left: heading “Expand your curriculum and empower your faculty”
  - Right: three feature columns/cards with small icons and headings, such as:
    - “Hands-on content and tools”
    - “Enable insights” (analytics / reporting)
    - “Global insights” or similar
  - Each column has 1–2 lines of supporting copy.

### 2.5 Trust/Institution Logos Strip
- Thin strip with small partner logos and a line like:
  - “Join colleges and universities worldwide that choose Coursera for Campus”

### 2.6 Testimonial/Proof Section
- Heading: “Here’s how innovative universities are using Coursera for Campus”
- Short paragraph describing outcomes and adoption.
- Embedded testimonial quote block (small, centered).

### 2.7 Large Dark CTA Banner
- Dark full-width panel with heading:
  - “Help prepare career-ready graduates”
- Short supporting sentence.
- Two CTA buttons:
  - Blue: “Contact us”
  - Secondary: “Compare plans” (outlined/light).

### 2.8 Two Resource Cards
- Two side-by-side cards near bottom:
  - Left: “Coursera Conference 2023” with small illustration background and `Explore` link.
  - Right: “Advancing Higher Education with Industry Micro-Credentials” with `Explore` link.

### 2.9 Footer
As described in Global components.

---

## 3) Page: Ebook Lead Form (“Job Skills of 2023 Report”)
Source: `screenshot_3.png` + `screenshot_4.png`

### 3.1 Hero / Header Block
- Eyebrow: `EBOOK`
- Large title: “Job Skills of 2023 Report”
- Subtitle: “Discover the fastest-growing job skills for businesses, governments, and higher education institutions.”
- Light gray background for header band.

### 3.2 Body: Two Column Layout
- **Left column** (copy)
  - Explains the report:
    - Explore fastest-growing human and digital skills for 2023.
    - Mentions Coursera learner dataset (4 million enterprise learners, 3,000 businesses, 3,600 higher ed institutions, governments in 100+ countries).
  - Line: “Download your report.”
- **Right column** (form in a bordered card)
  - Fields with red asterisk labels (required):
    - First Name
    - Last Name
    - Job Title
    - Work Email Address
    - Work Phone Number (with placeholder “Country Code + Phone Number”)
    - Institution Name
    - Primary Discipline (select)
    - Country (select)
  - Consent/legal copy: references `Terms of Use` and `Privacy Notice` links.
  - CTA button: blue `Submit`

### 3.3 Form Behavior (Functional Requirements)
- Client-side validation:
  - All required fields must validate before submit.
  - Email must be valid format.
  - Phone accepts “+countrycode number” and stores normalized value.
- On submit:
  - Persist lead in the database.
  - Show success state (inline message) and optionally offer download link.
  - Prevent duplicate submissions (idempotency by email + ebook id).

---

## 4) Content and Data Requirements (DB-backed)

The final product must not be a static mock. It must include a database and realistic seeded data.

### 4.1 Entities (Minimum)
- **Users** (authentication, roles)
- **Institutions** (universities/colleges)
- **Partners** (logo/name, type: university/company)
- **Courses** (title, description, skills, level, language, duration, partner)
- **Programs / Collections** (e.g., certificates, curated lists)
- **Resources** (ebooks, conferences, articles)
- **Leads** (ebook form submissions, contact-us submissions)
- **Enrollments** (optional but recommended for “platform-ness”)

### 4.2 Seed Data Expectations
- At least:
  - 50+ courses
  - 20+ partners
  - 10+ institutions
  - 10+ resources (including the “Job Skills of 2023 Report” resource)
- Images must use `https://images.unsplash.com/` URLs.

---

## 5) API + Python SDK Requirements

### 5.1 API
- REST API with OpenAPI docs.
- Authentication (JWT) and role-based access controls.
- Endpoints to:
  - Browse/search courses, partners, resources
  - Submit leads (ebook form, contact-us)
  - Manage user profile, enrollments (if implemented)

### 5.2 Python SDK
- Installable package that can:
  - Authenticate (login/register)
  - Call course/resource endpoints
  - Submit lead forms
  - Handle token refresh / persistence (where applicable)

---

## 6) Operational Requirements

- Provide `start_servers.sh` to start all services locally (frontend + backend).
- Provide `reset_servers.sh` to reset the DB back to seeded initial state.
- The implementation process must be documented in markdown (detailed, step-by-step).
- Progress must be tracked in `todo.md` using a Linear-style workflow.

