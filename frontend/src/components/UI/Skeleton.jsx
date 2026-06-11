export function SkeletonCard({ className = "", style = {} }) {
  return <div className={`skeleton skeleton-card ${className}`} style={style}></div>;
}

export function SkeletonLine({ width = "100%", className = "" }) {
  return <div className={`skeleton skeleton-line ${className}`} style={{ width }}></div>;
}

export function SkeletonGrid({ count = 4, className = "" }) {
  return (
    <div className={`grid grid-cols-4 gap-3 ${className}`}>
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} style={{ height: 80 }} />
      ))}
    </div>
  );
}

export function SkeletonList({ rows = 5, className = "" }) {
  return (
    <div className={`space-y-2 ${className}`}>
      {Array.from({ length: rows }).map((_, i) => (
        <SkeletonLine key={i} width={`${80 - i * 8}%`} />
      ))}
    </div>
  );
}

export function SkeletonPage() {
  return (
    <div className="space-y-5">
      <SkeletonLine width="30%" className="skeleton" style={{ height: 24 }} />
      <SkeletonGrid />
      <SkeletonCard style={{ height: 200 }} />
      <SkeletonList />
    </div>
  );
}
