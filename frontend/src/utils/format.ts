const currency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

export function formatSalary(value: string | number | null | undefined) {
  if (value === null || value === undefined) return "—";
  const num = Number(value);
  return Number.isFinite(num) ? currency.format(num) : "—";
}

export function formatStat(value: string | number | null | undefined, digits = 1) {
  if (value === null || value === undefined) return "—";
  const num = Number(value);
  return Number.isFinite(num) ? num.toFixed(digits) : "—";
}

export function formatDelta(value: string | number | null | undefined) {
  if (value === null || value === undefined) return "—";
  const num = Number(value);
  if (!Number.isFinite(num)) return "—";
  const sign = num > 0 ? "+" : "";
  return `${sign}${num.toFixed(1)}%`;
}

export function verdictColor(verdict: string | null | undefined) {
  switch (verdict) {
    case "Underpaid":
      return "#00C805";
    case "Overpaid":
      return "#FF5000";
    default:
      return "rgba(255,255,255,0.6)";
  }
}

export function deltaColor(value: string | number | null | undefined) {
  const num = Number(value);
  if (!Number.isFinite(num) || num === 0) return "text-white/60";
  return num < 0 ? "text-[#00C805]" : "text-[#FF5000]";
}
