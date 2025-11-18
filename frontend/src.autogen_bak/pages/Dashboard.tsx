import React, { useEffect, useState } from "react";
import KpiCard from "../components/KpiCard";
import ChartCard from "../components/ChartCard";
import { fetchDemo } from "../services/api";

export default function Dashboard({demoMode, role}: any){
  const [data, setData] = useState<any>(null);
  useEffect(()=>{ fetchDemo().then(setData); }, [demoMode]);

  if(!data) return <div className="p-6">Loading...</div>;

  return (
    <div>
      <section className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <KpiCard title="pH (avg)" value={data.kpis.ph} trend="+0.1" accent/>
        <KpiCard title="Dissolved O (mg/L)" value={data.kpis.do} trend="+0.6"/>
        <KpiCard title="Temp (C)" value={data.kpis.temp} trend="-0.4"/>
        <KpiCard title="Turbidity (NTU)" value={data.kpis.turbidity} trend="-0.2"/>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ChartCard title="User Activity" data={data.timeseries}/>
        </div>

        <aside className="space-y-4">
          <div className="glass p-4 rounded-xl">
            <h4 className="font-semibold">Quick Stats</h4>
            <div className="mt-3 text-sm text-gray-600">
              <div className="flex justify-between"><span>Total uploads</span><strong>{data.meta.total_uploads}</strong></div>
              <div className="flex justify-between"><span>Validators queue</span><strong>{data.meta.validators}</strong></div>
              <div className="flex justify-between"><span>Active orgs</span><strong>{data.meta.orgs}</strong></div>
            </div>
          </div>

          {role === "admin" && (
            <div className="glass p-4 rounded-xl">
              <h4 className="font-semibold">Admin</h4>
              <button className="mt-2 bg-purple-600 text-white px-4 py-2 rounded">Validate Pending Reports</button>
            </div>
          )}
        </aside>
      </section>
    </div>
  );
}
