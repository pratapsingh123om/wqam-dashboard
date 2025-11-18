import MetricCard from "../components/MetricCard";
import ChartCard from "../components/ChartCard";
import mock from "../mock-data";

export default function Dashboard() {
  const { kpis, timeseries } = mock();
  return (
    <div className="space-y-6">
      <section className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {kpis.map(k => <MetricCard key={k.title} {...k} />)}
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <ChartCard title="User Activity" data={timeseries} />
        </div>
        <div>
          <div className="p-4 rounded-2xl glass">
            <h4 className="font-medium mb-2">Quick Stats</h4>
            <div className="text-sm text-gray-400">Total uploads: <strong>1,024</strong></div>
            <div className="text-sm text-gray-400 mt-1">Validators queue: <strong>12</strong></div>
            <div className="text-sm text-gray-400 mt-1">Active orgs: <strong>23</strong></div>
          </div>
        </div>
      </section>
    </div>
  );
}
