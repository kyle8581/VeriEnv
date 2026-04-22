import Link from "next/link";

export function Logo() {
  return (
    <Link href="/" className="flex items-center gap-2">
      <svg
        width="26"
        height="26"
        viewBox="0 0 26 26"
        aria-hidden="true"
        className="text-apts-green"
      >
        <g fill="currentColor">
          <path d="M13 1.8c2.1 0 3.9 1.7 3.9 3.9 0 .9-.3 1.7-.8 2.4-1.2-.6-2.5-1-4.1-1-1.6 0-2.9.4-4.1 1-.5-.7-.8-1.5-.8-2.4 0-2.2 1.8-3.9 3.9-3.9Z" />
          <path d="M24.2 13c0 2.1-1.7 3.9-3.9 3.9-.9 0-1.7-.3-2.4-.8.6-1.2 1-2.5 1-4.1 0-1.6-.4-2.9-1-4.1.7-.5 1.5-.8 2.4-.8 2.2 0 3.9 1.8 3.9 3.9Z" />
          <path d="M13 24.2c-2.1 0-3.9-1.7-3.9-3.9 0-.9.3-1.7.8-2.4 1.2.6 2.5 1 4.1 1 1.6 0 2.9-.4 4.1-1 .5.7.8 1.5.8 2.4 0 2.2-1.8 3.9-3.9 3.9Z" />
          <path d="M1.8 13c0-2.1 1.7-3.9 3.9-3.9.9 0 1.7.3 2.4.8-.6 1.2-1 2.5-1 4.1 0 1.6.4 2.9 1 4.1-.7.5-1.5.8-2.4.8-2.2 0-3.9-1.8-3.9-3.9Z" />
        </g>
      </svg>
      <span className="text-[22px] font-semibold tracking-tight">
        Apartments.com
      </span>
    </Link>
  );
}

