
export default function DemoPanel({demoMode, onToggle, role, setRole}: any){
  return (
    <div className="flex items-center gap-3">
      <label className="flex items-center gap-2">
        <input type="checkbox" checked={demoMode} onChange={onToggle} /> Demo
      </label>
      <select value={role} onChange={(e)=>setRole(e.target.value)} className="rounded px-2 py-1">
        <option value="user">User</option>
        <option value="validator">Validator</option>
        <option value="admin">Admin</option>
      </select>
    </div>
  );
}
