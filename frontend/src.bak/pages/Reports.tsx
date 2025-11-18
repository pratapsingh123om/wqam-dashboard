export default function Reports() {
  return (
    <div className="space-y-4">
      <div className="p-4 rounded-2xl glass">
        <h3 className="font-medium">Reports</h3>
        <div className="text-sm text-gray-400">Generate PDFs / CSVs</div>
      </div>
      <div className="p-4 rounded-2xl glass">
        <button className="px-4 py-2 rounded-lg">Download CSV</button>
      </div>
    </div>
  );
}
