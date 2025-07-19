// pages/_app.tsx
import "../app/globals.css";     // ← make sure this path matches your file
import type { AppProps } from "next/app";

export default function MyApp({ Component, pageProps }: AppProps) {
  return <Component {...pageProps} />;
}


