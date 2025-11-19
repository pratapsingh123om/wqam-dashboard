import { useState } from "react";

export default function ThemeToggle(){
  const [dark, setDark] = useState(false);
  return <button onClick={()=>setDark(!dark)} className="px-3 py-1 rounded-md glass">{dark ? "🌙" : "☀️"}</button>;
}
