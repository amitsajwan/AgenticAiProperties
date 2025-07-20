// pages/_app.tsx
import '..//styles/globals.css'; // [MODIFIED] Corrected path assuming globals.css is in styles/
import type { AppProps } from 'next/app';

export default function MyApp({ Component, pageProps }: AppProps) {
  return <Component {...pageProps} />;
}
