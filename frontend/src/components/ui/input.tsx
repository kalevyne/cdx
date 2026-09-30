import type * as React from "react"

import { cn } from "@/lib/utils"

const fieldClasses =
  "w-full min-w-0 rounded-lg border border-input bg-transparent px-2.5 text-sm shadow-xs transition-colors outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-destructive/20"

function Input({ className, ...props }: React.ComponentProps<"input">) {
  return <input data-slot="input" className={cn(fieldClasses, "h-8", className)} {...props} />
}

function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(fieldClasses, "min-h-20 py-2", className)}
      {...props}
    />
  )
}

function Label({ className, ...props }: React.ComponentProps<"label">) {
  return (
    <label
      data-slot="label"
      className={cn("text-sm leading-none font-medium select-none", className)}
      {...props}
    />
  )
}

export { Input, Label, Textarea }
