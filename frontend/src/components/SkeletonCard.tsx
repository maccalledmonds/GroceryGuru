export function SkeletonCard() {
  return (
    <div aria-hidden="true" className="bg-white border border-black/[0.07] border-l-4 border-l-black/[0.08] rounded-r-xl p-5">
      <div className="flex justify-between items-start gap-3 mb-3">
        <div>
          <div className="h-4 w-36 rounded skeleton-shimmer mb-2" />
          <div className="h-3 w-24 rounded skeleton-shimmer" />
        </div>
        <div className="h-6 w-11 rounded-[5px] skeleton-shimmer" />
      </div>
      <div className="flex gap-1.5 mb-3">
        <div className="h-6 w-16 rounded skeleton-shimmer" />
        <div className="h-6 w-14 rounded skeleton-shimmer" />
        <div className="h-6 w-20 rounded skeleton-shimmer" />
      </div>
      <div className="h-3 w-28 rounded skeleton-shimmer" />
    </div>
  );
}
