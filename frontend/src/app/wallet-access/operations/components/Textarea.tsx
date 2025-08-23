import React from "react";

const Textarea: React.FC<React.TextareaHTMLAttributes<HTMLTextAreaElement>> = ({ className, ...props }) => {
  return (
    <textarea
      className={`border p-2 mb-3 w-full rounded ${className || ""}`}
      {...props}
    />
  );
};

export default Textarea;
