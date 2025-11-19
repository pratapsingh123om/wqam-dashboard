
export default function ActiveUsersWidget() {
  const [count, setCount] = useState(0);
  useEffect(() => {
    const ws = new WebSocket((import.meta.env.VITE_API_WS || "ws://localhost:8000") + "/ws/presence");
    ws.onopen = () => {
      // send fake ping (in real app, include user id)
      ws.send(JSON.stringify({ user_id: Math.floor(Math.random()*10000) }));
    };
    ws.onmessage = (ev) => {
      const data = JSON.parse(ev.data);
      if (data.active_users) setCount(data.active_users);
    };
    return () => ws.close();
  }, []);
  return (
    <div className="bg-white/5 rounded-lg p-4 shadow">
      <div className="text-sm text-slate-400">Active users</div>
      <div className="text-2xl font-semibold">{count}</div>
    </div>
  );
}
