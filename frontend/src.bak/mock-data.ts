export default function mock() {
  const kpis = [
    { title: "Active Users", value: "4.2k", delta:"+4.2%" },
    { title: "Uploads", value: "1,024", delta:"+12.4%" },
    { title: "Alerts", value: "7", delta:"-2%" },
    { title: "Success Rate", value: "92.7%", delta:"+0.9%" }
  ];
  const timeseries = Array.from({length:30}).map((_,i)=> {
    const d = new Date();
    d.setDate(d.getDate()- (30-i));
    return { date: d.toISOString().slice(0,10), value: Math.round(300 + Math.random()*350) };
  });
  return { kpis, timeseries };
}
