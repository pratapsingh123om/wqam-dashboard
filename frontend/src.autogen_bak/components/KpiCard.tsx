import React from "react";
export default function KpiCard({title,value,trend,accent}:any){
  return (
    <div className={`p-4 rounded-xl glass ${accent ? "border-l-4 border-purple-500" : ""}`}>
      <div className="kpi-title">{title}</div>
      <div className="kpi-value">{value}</div>
      {trend && <div className="kpi-trend">{trend}</div>}
    </div>
  );
}
