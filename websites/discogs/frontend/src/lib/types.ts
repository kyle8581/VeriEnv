export type ReleaseCard = {
  id: number;
  title: string;
  artist?: string | null;
  cover_image_url?: string | null;
  year?: number | null;
};

export type HomeData = {
  hero_title: string;
  hero_image_url: string;
  hero_tiles: { title: string; subtitle: string; image_url: string }[];
  banner: {
    title: string;
    subtitle: string;
    image_url: string;
    release_id: number | null;
  };
  trending_releases: ReleaseCard[];
  most_expensive_sold: { release: ReleaseCard; price_cents: number; currency: string }[];
  newly_added: ReleaseCard[];
};

export type GenreOverviewData = {
  genre: { name: string; slug: string; description: string | null };
  styles: string[];
  most_collected: ReleaseCard[];
  early_releases: ReleaseCard[];
  stats: {
    releases_by_decade: { label: string; value: number }[];
    top_submitters: { label: string; value: number }[];
  };
  most_sold_this_month: ReleaseCard[];
  related_styles: string[];
};

