import { useEffect, useState } from "react";

export default function ThemeToggle() {
  const [dark, setDark] = useState(document.documentElement.classList.contains("dark"));
  useEffect(()=> { document.documentElement.classList.toggle("dark", dark); }, [dark]);
  return (
    <button onClick={()=> setDark(!dark)} className="p-2 rounded-lg glass">
      {dark ? " Light" : " Dark"}
    </button>
  );
}
