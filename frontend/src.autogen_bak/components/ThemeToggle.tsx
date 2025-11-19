
export default function ThemeToggle(){
  const [dark,setDark] = useState(false);
  useEffect(()=> document.documentElement.classList.toggle("dark", !!dark), [dark]);
  return <button onClick={()=>setDark(!dark)} className="p-2 rounded-lg bg-white/5 hover:bg-white/10">{dark ? "??":"??"}</button>;
}
