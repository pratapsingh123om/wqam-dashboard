type Props = { title: string; value: string | number; trend?: string };
export default function KpiCard({ title, value, trend }: Props) {
  return (
    <div className="p-4 rounded-2xl bg-white dark:bg-gray-800 shadow-sm hover:shadow-lg transition">
      <h3 className="text-sm text-gray-500 dark:text-gray-400">{title}</h3>
      <p className="text-2xl font-semibold text-gray-900 dark:text-white">{value}</p>
      {trend && <span className="text-xs text-green-500">{trend}</span>}
    </div>
  );
}
