import Image from "next/image";
import Link from "next/link";

export function ReleaseCard({
  release,
}: {
  release: {
    id: number;
    title: string;
    artist?: string | null;
    cover_image_url?: string | null;
    year?: number | null;
  };
}) {
  return (
    <Link
      href={`/release/${release.id}`}
      className="block w-full hover:underline"
    >
      <div className="w-full overflow-hidden rounded-sm bg-white">
        <div className="relative aspect-square w-full bg-neutral-100">
          {release.cover_image_url ? (
            <Image
              src={release.cover_image_url}
              alt={release.title}
              fill
              className="object-cover"
              sizes="(max-width: 768px) 50vw, 200px"
            />
          ) : null}
        </div>
        <div className="px-2 py-2">
          <div className="line-clamp-2 text-xs font-semibold text-neutral-900">
            {release.title}
          </div>
          {release.artist ? (
            <div className="mt-0.5 text-[11px] text-neutral-600">
              {release.artist}
            </div>
          ) : null}
        </div>
      </div>
    </Link>
  );
}

