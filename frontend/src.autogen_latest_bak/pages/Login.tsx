
export default function Login({ onLogin }) {
  const [pass, setPass] = useState("");

  return (
    <div className="h-screen flex items-center justify-center">
      <div className="glass p-8 w-96 space-y-6">
        <h1 className="text-2xl font-bold text-center mb-3">WQAM Login</h1>

        <input
          type="password"
          placeholder="Enter password"
          className="w-full p-3 bg-white/10 rounded-xl outline-none"
          value={pass}
          onChange={(e) => setPass(e.target.value)}
        />

        <button
          onClick={() => pass === "1234" && onLogin()}
          className="w-full py-3 rounded-xl bg-blue-500 hover:bg-blue-600 transition"
        >
          Login
        </button>
      </div>
    </div>
  );
}
