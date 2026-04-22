export type ListingImage = {
  id: number;
  url: string;
  sort_order: number;
};

export type Amenity = {
  id: number;
  name: string;
};

export type Listing = {
  id: number;
  name: string;
  street: string;
  city: string;
  state: string;
  postal_code: string;
  latitude: number;
  longitude: number;
  min_price: number;
  max_price: number;
  min_beds: number;
  max_beds: number;
  property_type: string;
  move_in_date: string | null;
  description: string;
  phone: string;
  management_name: string;
  specials: string | null;
  has_videos: boolean;
  has_virtual_tour: boolean;
  created_at: string;
  images: ListingImage[];
  amenities: Amenity[];
};

export type ListingSearchResponse = {
  total: number;
  items: Listing[];
};

export type UserPublic = {
  id: number;
  email: string;
  full_name: string | null;
  role: string;
  created_at: string;
};

export type Token = {
  access_token: string;
  token_type: "bearer";
};

export type Location = {
  id: number;
  name: string;
  state: string;
  kind: string;
  latitude: number;
  longitude: number;
};

