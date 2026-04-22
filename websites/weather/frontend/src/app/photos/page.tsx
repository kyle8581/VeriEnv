import Image from "next/image";

import { serverGet } from "@/lib/serverApi";

type Photo = {
  id: string;
  title: string;
  image_url: string;
  caption: string | null;
  published_at: string;
};

export default async function PhotosPage() {
  const items = await serverGet<Photo[]>("/content/photos?limit=60&offset=0");

  return (
    <div className="twc-card p-4">
      <h1 className="text-lg font-semibold text-[#0b1f2a]">Photos</h1>
      <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        {items.map((p) => (
          <div
            key={p.id}
            className="overflow-hidden rounded-lg border border-black/10 bg-white"
          >
            <Image
              src={p.image_url}
              alt={p.title}
              width={900}
              height={650}
              className="h-[140px] w-full object-cover"
            />
            <div className="p-3">
              <div className="line-clamp-2 text-xs font-semibold text-[#0b1f2a]">
                {p.title}
              </div>
              {p.caption ? (
                <div className="mt-1 line-clamp-2 text-xs text-black/60">
                  {p.caption}
                </div>
              ) : null}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

