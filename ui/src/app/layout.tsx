import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "MASAT Portal (Prototype)",
  description: "UI prototype for MASAT",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
