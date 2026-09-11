// fontend/src/components/ui/Button.jsx
export function Button({ children, isLoading, ...props }) {
  return (
    <button
      className="w-full bg-emerald-700 hover:bg-emerald-800 text-white font-medium py-2.5 px-4 rounded-md transition-colors disabled:opacity-70 disabled:cursor-not-allowed flex justify-center items-center"
      disabled={isLoading}
      {...props}
    >
      {isLoading ? "Aguarde..." : children}
    </button>
  );
}