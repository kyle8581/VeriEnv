import Link from "next/link";

import { Header } from "@/components/Header";

export function SimplePage({
  title,
  children,
}: {
  title: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto max-w-[900px] px-4 py-10">
        <h1 className="text-[28px] font-semibold text-[#2b2b2b]">{title}</h1>
        <div className="mt-4 text-[14px] leading-7 text-[#555]">
          {children}
        </div>
        <div className="mt-8 text-[13px] text-[#0b6fbf]">
          <Link className="hover:underline" href="/">
            Back to Home
          </Link>
        </div>
      </main>
    </div>
  );
}

