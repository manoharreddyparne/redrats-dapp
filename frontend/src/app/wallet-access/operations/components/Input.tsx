import React from "react";

const Input: React.FC<React.InputHTMLAttributes<HTMLInputElement>> = ({ className, ...props }) => {
  return (
    <input
      className={`border p-2 mb-3 w-full rounded ${className || ""}`}
      {...props}
    />
  );
};

export default Input;
