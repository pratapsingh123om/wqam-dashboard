export async function fetchDemo(){
  try {
    const res = await fetch("/api/demo");
    if (!res.ok) throw new Error("no backend");
    return await res.json();
  } catch(e){
    const now = new Date();
    const d:any[] = [];
    for(let i=29;i>=0;i--){
      const dt = new Date(now); dt.setDate(now.getDate()-i);
      d.push({ date: dt.toISOString().slice(0,10), value: Math.round(300 + 200*Math.sin(i/3) + Math.random()*90) });
    }
    return { timeseries: d, kpis: { ph: 7.2, do: 8.6, temp:15.4, turbidity:3.2 }, meta:{ total_uploads:1024, validators:12, orgs:23 } };
  }
}
