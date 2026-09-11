// frontend/src/components/ui/Input.jsx
export function Input({ label, id, ...props }) {
  return (
    <div className="flex flex-col gap-1 mb-4">
      <label htmlFor={id} className="text-sm font-semibold text-gray-700">
        {label}
      </label>
      <input
        id={id}
        className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-emerald-700 focus:border-transparent"
        {...props}
      />
    </div>
  );
}