import { Nutrition } from "../api/client";

const MACROS: { key: keyof Nutrition; label: string; unit: string; color: string }[] = [
  { key: "calories", label: "Calories", unit: "kcal", color: "bg-amber-50 text-amber-700 border-amber-200" },
  { key: "protein", label: "Protein", unit: "g", color: "bg-blue-50 text-blue-700 border-blue-200" },
  { key: "fat", label: "Fat", unit: "g", color: "bg-rose-50 text-rose-700 border-rose-200" },
  { key: "carbs", label: "Carbs", unit: "g", color: "bg-green-50 text-green-700 border-green-200" },
];

interface Props {
  nutrition: Nutrition;
}

export function NutritionGrid({ nutrition }: Props) {
  return (
    <dl className="grid grid-cols-4 gap-2">
      {MACROS.map(({ key, label, unit, color }) => (
        <div key={key} className={`flex flex-col items-center rounded-lg border px-2 py-2 ${color}`}>
          <dt className="text-[10px] font-semibold uppercase tracking-wide opacity-75">{label}</dt>
          <dd className="mt-0.5 text-base font-bold leading-tight">
            {nutrition[key].toFixed(0)}
            <span className="ml-0.5 text-[10px] font-medium opacity-60">{unit}</span>
          </dd>
        </div>
      ))}
    </dl>
  );
}
