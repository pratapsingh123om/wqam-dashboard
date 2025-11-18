export default function Login() {
  return (
    <div className="flex items-center justify-center h-screen bg-gray-50 dark:bg-gray-900">
      <form className="bg-white dark:bg-gray-800 p-8 rounded-2xl shadow-lg w-80">
        <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-100">Login</h2>
        <input type="text" placeholder="Email" className="w-full p-2 mb-3 rounded bg-gray-100 dark:bg-gray-700"/>
        <input type="password" placeholder="Password" className="w-full p-2 mb-4 rounded bg-gray-100 dark:bg-gray-700"/>
        <button className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700">Sign In</button>
      </form>
    </div>
  );
}
