export function InfoPage({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="twc-card p-5">
      <h1 className="text-lg font-semibold text-[#0b1f2a]">{title}</h1>
      <div className="prose prose-slate mt-4 max-w-none text-sm text-black/70">
        {children}
      </div>
    </div>
  );
}

