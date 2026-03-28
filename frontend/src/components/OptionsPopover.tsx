import { useEffect } from "react";

const MAX_RESULTS = 20;

const FILTER_LABELS: Record<string, string> = {
  vegetarian: "Vegetarian",
  vegan: "Vegan",
  gluten_free: "Gluten-free",
  high_protein: "High-protein",
};

interface Props {
  availableFilters: string[];
  selectedFilters: string[];
  onFiltersChange: (filters: string[]) => void;
  spiceOptions: string[];
  selectedSpices: string[];
  onSpicesChange: (spices: string[]) => void;
  topK: number;
  onTopKChange: (k: number) => void;
  onClose: () => void;
  disabled?: boolean;
}

export function OptionsPopover({
  availableFilters,
  selectedFilters,
  onFiltersChange,
  spiceOptions,
  selectedSpices,
  onSpicesChange,
  topK,
  onTopKChange,
  onClose,
  disabled = false,
}: Props) {
  function toggleFilter(f: string) {
    onFiltersChange(
      selectedFilters.includes(f)
        ? selectedFilters.filter((x) => x !== f)
        : [...selectedFilters, f],
    );
  }

  function toggleSpice(s: string) {
    onSpicesChange(
      selectedSpices.includes(s)
        ? selectedSpices.filter((x) => x !== s)
        : [...selectedSpices, s],
    );
  }

  // Close on Escape key
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  // Percentage of slider filled for CSS gradient
  const sliderPct = ((topK - 1) / (MAX_RESULTS - 1)) * 100;

  return (
    <>
      {/* Backdrop — clicking outside closes the popover */}
      <div
        className="fixed inset-0 z-30"
        aria-hidden
        onClick={onClose}
      />

      {/* Popover panel */}
      <div
        className="relative z-40 bg-white border-t-[3px] border-t-brand-500 border-b border-x border-black/[0.08] shadow-popover"
        role="dialog"
        aria-modal="true"
        aria-label="Search options"
      >
        <div className="mx-auto max-w-7xl px-6 sm:px-8 py-5 flex flex-wrap gap-8 items-start">

          {/* Dietary filters */}
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-stone-400 mb-3">
              Dietary
            </p>
            <div className="flex flex-wrap gap-2">
              {availableFilters.map((f) => {
                const active = selectedFilters.includes(f);
                return (
                  <button
                    key={f}
                    type="button"
                    disabled={disabled}
                    aria-pressed={active}
                    onClick={() => toggleFilter(f)}
                    className={`border rounded-[5px] px-3.5 py-1.5 text-sm font-medium transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed ${
                      active
                        ? "bg-stone-900 text-white border-stone-900"
                        : "border-black/[0.12] text-stone-500 hover:border-black/[0.22] hover:text-stone-900"
                    }`}
                  >
                    {FILTER_LABELS[f] ?? f}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Spice toggles */}
          <div className="flex-1 min-w-[220px]">
            <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-stone-400 mb-3">
              Pantry Spices
            </p>
            <div className="flex flex-wrap gap-2">
              {spiceOptions.map((s) => {
                const active = selectedSpices.includes(s);
                return (
                  <button
                    key={s}
                    type="button"
                    disabled={disabled}
                    aria-pressed={active}
                    onClick={() => toggleSpice(s)}
                    className={`border rounded-[5px] px-3 py-1.5 text-sm font-medium transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed ${
                      active
                        ? "bg-stone-900 text-white border-stone-900"
                        : "border-black/[0.12] text-stone-500 hover:border-black/[0.22] hover:text-stone-900"
                    }`}
                  >
                    {s}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Results slider */}
          <div className="min-w-[160px]">
            <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-stone-400 mb-3">
              Number of Results
            </p>
            <div className="flex items-baseline gap-2 mb-2.5">
              <span className="text-3xl font-bold text-stone-900 tabular-nums leading-none" style={{ letterSpacing: "-0.04em" }}>
                {topK}
              </span>
              <span className="text-sm text-stone-400">recipes</span>
            </div>
            <input
              type="range"
              min={1}
              max={MAX_RESULTS}
              value={topK}
              disabled={disabled}
              onChange={(e) => onTopKChange(Number(e.target.value))}
              aria-label="Number of results"
              style={{
                appearance: "none",
                WebkitAppearance: "none",
                width: "100%",
                height: "4px",
                borderRadius: "2px",
                outline: "none",
                cursor: disabled ? "not-allowed" : "pointer",
                background: `linear-gradient(to right, #d97706 0%, #d97706 ${sliderPct}%, #e7e5e4 ${sliderPct}%, #e7e5e4 100%)`,
              }}
            />
            <div className="flex justify-between text-[11px] text-stone-300 mt-1.5">
              <span>1</span>
              <span>20</span>
            </div>
          </div>

        </div>
      </div>
    </>
  );
}
