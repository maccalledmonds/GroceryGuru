const FILTER_LABELS: Record<string, string> = {
  vegetarian: "Vegetarian",
  vegan: "Vegan",
  gluten_free: "Gluten-free",
  high_protein: "High-protein",
};

interface Props {
  availableFilters: string[];
  selectedFilters: string[];
  spiceOptions: string[];
  selectedSpices: string[];
  topK: number;
  onFiltersChange: (filters: string[]) => void;
  onSpicesChange: (spices: string[]) => void;
  onTopKChange: (k: number) => void;
  disabled?: boolean;
}

export function FilterPanel({
  availableFilters,
  selectedFilters,
  spiceOptions,
  selectedSpices,
  topK,
  onFiltersChange,
  onSpicesChange,
  onTopKChange,
  disabled = false,
}: Props) {
  function toggleFilter(filter: string) {
    if (selectedFilters.includes(filter)) {
      onFiltersChange(selectedFilters.filter((f) => f !== filter));
    } else {
      onFiltersChange([...selectedFilters, filter]);
    }
  }

  function toggleSpice(spice: string) {
    if (selectedSpices.includes(spice)) {
      onSpicesChange(selectedSpices.filter((s) => s !== spice));
    } else {
      onSpicesChange([...selectedSpices, spice]);
    }
  }

  return (
    <aside className="flex flex-col gap-6">
      <div>
        <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">Dietary filters</h2>
        <ul className="space-y-2">
          {availableFilters.map((filter) => {
            const checked = selectedFilters.includes(filter);
            return (
              <li key={filter}>
                <label
                  className={`flex items-center gap-2.5 cursor-pointer select-none ${
                    disabled ? "opacity-60 cursor-not-allowed" : ""
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    disabled={disabled}
                    onChange={() => toggleFilter(filter)}
                    className="h-4 w-4 rounded border-gray-300 text-brand-500 focus:ring-brand-400 accent-brand-500"
                  />
                  <span className="text-sm text-gray-700">
                    {FILTER_LABELS[filter] ?? filter}
                  </span>
                </label>
              </li>
            );
          })}
        </ul>
      </div>

      <div>
        <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">Optional spices</h2>
        <ul className="max-h-56 space-y-2 overflow-y-auto pr-1">
          {spiceOptions.map((spice) => {
            const checked = selectedSpices.includes(spice);
            return (
              <li key={spice}>
                <label
                  className={`flex items-center gap-2.5 cursor-pointer select-none ${
                    disabled ? "opacity-60 cursor-not-allowed" : ""
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    disabled={disabled}
                    onChange={() => toggleSpice(spice)}
                    className="h-4 w-4 rounded border-gray-300 text-brand-500 focus:ring-brand-400 accent-brand-500"
                  />
                  <span className="text-sm text-gray-700">{spice}</span>
                </label>
              </li>
            );
          })}
        </ul>
      </div>

      <div>
        <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
          Results — <span className="text-brand-600">{topK}</span>
        </h2>
        <input
          type="range"
          min={1}
          max={20}
          value={topK}
          disabled={disabled}
          onChange={(e) => onTopKChange(Number(e.target.value))}
          className="w-full accent-brand-500 disabled:opacity-60 disabled:cursor-not-allowed"
          aria-label="Number of results"
        />
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>1</span>
          <span>20</span>
        </div>
      </div>
    </aside>
  );
}
