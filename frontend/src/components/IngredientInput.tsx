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
    if (parts.length > 0) {
      onChange([...ingredients, ...parts]);
    }
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

  function removeIngredient(index: number) {
    onChange(ingredients.filter((_, i) => i !== index));
  }

  return (
    <div
      className={`flex flex-wrap gap-2 items-center min-h-[3rem] w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm shadow-sm transition-colors focus-within:border-brand-500 focus-within:ring-2 focus-within:ring-brand-200 ${
        disabled ? "opacity-60 cursor-not-allowed" : ""
      }`}
      onClick={() => inputRef.current?.focus()}
    >
      {ingredients.map((ing, i) => (
        <span
          key={`${ing}-${i}`}
          className="inline-flex items-center gap-1 rounded-full bg-brand-100 px-3 py-1 text-sm font-medium text-brand-800"
        >
          {ing}
          {!disabled && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                removeIngredient(i);
              }}
              className="ml-0.5 rounded-full hover:bg-brand-200 p-0.5 leading-none focus:outline-none focus:ring-1 focus:ring-brand-400"
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
        placeholder={ingredients.length === 0 ? "Type an ingredient and press Enter…" : "Add more…"}
        className="flex-1 min-w-[160px] bg-transparent outline-none placeholder:text-gray-400 disabled:cursor-not-allowed"
        aria-label="Ingredient input"
      />
    </div>
  );
}
