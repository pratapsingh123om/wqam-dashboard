import React from "react";
export default function Login({onLogin}: any){
  return (
    <div className="flex items-center justify-center h-96">
      <div className="glass p-6 rounded-lg">
        <h3 className="font-semibold mb-3">Login (demo)</h3>
        <div className="flex gap-2">
          <button onClick={()=>onLogin("user")} className="px-3 py-2 bg-blue-600 text-white rounded">User</button>
          <button onClick={()=>onLogin("validator")} className="px-3 py-2 bg-yellow-600 text-white rounded">Validator</button>
          <button onClick={()=>onLogin("admin")} className="px-3 py-2 bg-purple-600 text-white rounded">Admin</button>
        </div>
      </div>
    </div>
  );
}
