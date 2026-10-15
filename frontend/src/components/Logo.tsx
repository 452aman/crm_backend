export default function Logo({ className = 'h-7 w-7' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <defs><linearGradient id="logo-g" x1="2" y1="2" x2="30" y2="30" gradientUnits="userSpaceOnUse"><stop stopColor="#2dd4bf" /><stop offset="1" stopColor="#34d399" /></linearGradient></defs>
      <rect width="32" height="32" rx="9" fill="url(#logo-g)" />
      <path d="M16 6.5v6M13 9.5h6" stroke="#070a14" strokeWidth="2" strokeLinecap="round"/><path d="M5.5 19.5h5l2-4.2 3.4 8.2 2.6-5.3 1.4 1.3h6.1" stroke="#070a14" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  )
}
