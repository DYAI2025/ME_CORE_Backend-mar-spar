import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";

const inter = { className: "" };

export const metadata: Metadata = {
  title: "MarkerEngine",
  description: "Lean-Deep 3.1 kompatible Text-Analyse",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="de">
      <body className={inter.className}>
        {children}
        <Toaster />
        <div id="dock"></div>
        <Script 
          src="https://b0bfe21bd-8080.preview.abacusai.app/sdk/inputdock.js" 
          strategy="afterInteractive"
        />
        <Script 
          src="/inputdock-init.js" 
          strategy="afterInteractive" 
        />
      </body>
    </html>
  );
}