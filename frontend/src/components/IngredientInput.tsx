import { KeyboardEvent, useRef, useState } from "react";

interface Props {
  ingredients: string[];
  onChange: (updated: string[]) => void;
  disabled?: boolean;
}

export function IngredientInput({ ingredients, onChange, disabled = false }: Props) {
  const [draft, setDraft] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  function commit(raw: string) {
    const parts = raw
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s.length > 0 && !ingredients.includes(s));
    if (parts.length > 0) onChange([...ingredients, ...parts]);
    setDraft("");
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      commit(draft);
    } else if (e.key === "Backspace" && draft === "" && ingredients.length > 0) {
      onChange(ingredients.slice(0, -1));
    }
  }

  return (
    // No outer border — the parent nav bar is the container
    <div
      className={`flex flex-wrap gap-2 items-center min-h-[2.5rem] ${
        disabled ? "opacity-60 cursor-not-allowed" : "cursor-text"
      }`}
      onClick={() => inputRef.current?.focus()}
    >
      {ingredients.map((ing, i) => (
        <span
          key={`${ing}-${i}`}
          className="inline-flex items-center gap-1.5 border-2 border-stone-900 rounded-[5px] px-2.5 py-1 text-sm font-medium text-stone-900 leading-none"
        >
          {ing}
          {!disabled && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onChange(ingredients.filter((_, idx) => idx !== i));
              }}
              className="opacity-35 hover:opacity-75 transition-opacity duration-100 leading-none focus:outline-none"
              aria-label={`Remove ${ing}`}
            >
              <svg className="w-3 h-3" viewBox="0 0 12 12" fill="currentColor" aria-hidden>
                <path d="M9.53 9.53a.75.75 0 0 1-1.06 0L6 7.06 3.53 9.53A.75.75 0 0 1 2.47 8.47L4.94 6 2.47 3.53A.75.75 0 0 1 3.53 2.47L6 4.94l2.47-2.47a.75.75 0 1 1 1.06 1.06L7.06 6l2.47 2.47a.75.75 0 0 1 0 1.06Z" />
              </svg>
            </button>
          )}
        </span>
      ))}

      <input
        ref={inputRef}
        type="text"
        value={draft}
        disabled={disabled}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={() => draft && commit(draft)}
        placeholder={ingredients.length === 0 ? "Type an ingredient and press Enter…" : "add more…"}
        className="flex-1 min-w-[140px] bg-transparent outline-none text-sm text-stone-900 placeholder:text-stone-400 disabled:cursor-not-allowed"
        aria-label="Ingredient input"
      />
    </div>
  );
}
