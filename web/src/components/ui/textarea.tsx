import * as React from "react";

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={
        "border border-neutral-200 rounded-lg px-4 py-2 text-base focus:ring-2 ring-blue-600 resize-none " +
        (className || "")
      }
      {...props}
    />
  )
);
Textarea.displayName = "Textarea";
