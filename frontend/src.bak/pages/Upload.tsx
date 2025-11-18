export default function Upload() {
  return (
    <div>
      <div className="p-4 rounded-2xl glass mb-4">
        <h3 className="font-medium">Upload Data</h3>
        <p className="text-xs text-gray-400">CSV or manual entry</p>
      </div>
      <div className="p-6 rounded-2xl glass">
        <input type="file" className="mb-4" />
        <button className="px-4 py-2 rounded-lg metric-pill bg-clip-text">Upload</button>
        <div className="mt-3 text-sm text-gray-500">If you get 404 on upload, your backend upload endpoint isn't configured. Use /api/upload on backend or disable docker engine reverse proxy if needed.</div>
      </div>
    </div>
  );
}
