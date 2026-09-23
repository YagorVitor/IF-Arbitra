import { useState } from 'react';
import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';

export default function PasswordInput({ className = '', ...props }) {
  const [showPassword, setShowPassword] = useState(false);

  function toggleVisibility() {
    setShowPassword((current) => !current);
  }

  return (
    <div className="relative w-full">
      <input
        {...props}
        type={showPassword ? 'text' : 'password'}
        className={`${className} pr-10`}
      />

      <button
        type="button"
        onClick={toggleVisibility}
        tabIndex="-1"
        className="absolute right-2.5 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-[#0A3D2A] transition-colors focus:outline-none"
        title={showPassword ? 'Esconder senha' : 'Mostrar senha'}
      >
        {showPassword ? (
          <EyeSlashIcon className="w-5 h-5" />
        ) : (
          <EyeIcon className="w-5 h-5" />
        )}
      </button>
    </div>
  );
}