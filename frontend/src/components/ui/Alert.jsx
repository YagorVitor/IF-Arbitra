import { Info, AlertTriangle, XCircle } from 'lucide-react';

export default function Alert({ variant = 'info', title, children }) {
  const variants = {
    info: { bg: 'bg-blue-50', text: 'text-blue-800', icon: Info },
    warning: { bg: 'bg-amber-50', text: 'text-amber-800', icon: AlertTriangle },
    error: { bg: 'bg-red-50', text: 'text-red-600', icon: XCircle }
  };
  
  const Icon = variants[variant].icon;

  return (
    <div className={`${variants[variant].bg} ${variants[variant].text} p-4 rounded-md flex items-start gap-3 text-sm`}>
      <Icon className="w-5 h-5 shrink-0 mt-0.5" />
      <div>
        {title && <p className="font-semibold mb-1">{title}</p>}
        <div>{children}</div>
      </div>
    </div>
  );
}