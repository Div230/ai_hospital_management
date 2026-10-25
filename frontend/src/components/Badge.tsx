import clsx from "clsx";

const tones: Record<string, string> = {
  vital: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
  alert: "bg-red-500/10 text-red-600 dark:text-red-400",
  warn: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
  accent: "bg-cyan-500/10 text-cyan-700 dark:text-cyan-400",
  neutral: "bg-slate-500/10 text-slate-600 dark:text-slate-300",
};

export default function Badge({ children, tone = "neutral" }: { children: React.ReactNode; tone?: keyof typeof tones }) {
  return (
    <span className={clsx("rounded-full px-3 py-1 text-xs font-semibold", tones[tone])}>
      {children}
    </span>
  );
}
