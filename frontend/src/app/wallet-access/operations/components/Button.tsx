import React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  loading?: boolean;
}

const Button: React.FC<ButtonProps> = ({ children, loading, disabled, ...props }) => {
  return (
    <button
      disabled={disabled || loading}
      className={`w-full py-2 rounded text-white ${
        disabled || loading ? "bg-gray-400 cursor-not-allowed" : "bg-blue-500 hover:bg-blue-600"
      }`}
      {...props}
    >
      {loading ? "Loading..." : children}
    </button>
  );
};

export default Button;
