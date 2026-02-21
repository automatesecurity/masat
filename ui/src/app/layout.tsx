import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "MASAT Portal",
  description: "MASAT UI portal",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <div id="__app">{children}</div>
      </body>
    </html>
  );
}
