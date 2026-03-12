import type { ButtonHTMLAttributes } from 'react'
import styles from './Button.module.css'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost'
  size?: 'default' | 'lg'
}

export const Button = ({
  variant = 'primary',
  size = 'default',
  className,
  ...props
}: ButtonProps) => {
  const classes = [
    styles.button,
    styles[variant],
    size === 'lg' && styles.lg,
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return <button className={classes} {...props} />
}
