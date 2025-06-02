import React, { ReactNode } from 'react';

interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

export function Alert({ children, className = '', ...props }: AlertProps) {
  return (
    <div className={`alert ${className}`} {...props}>
      {children}
    </div>
  );
}

interface AlertTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  children: ReactNode;
}

export function AlertTitle({ children, className = '', ...props }: AlertTitleProps) {
  return (
    <h3 className={`font-semibold text-lg ${className}`} {...props}>
      {children}
    </h3>
  );
}

interface AlertDescriptionProps extends React.HTMLAttributes<HTMLParagraphElement> {
  children: ReactNode;
}

export function AlertDescription({ children, className = '', ...props }: AlertDescriptionProps) {
  return (
    <p className={`text-sm ${className}`} {...props}>
      {children}
    </p>
  );
} 