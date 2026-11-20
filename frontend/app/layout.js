
import "./globals.css";

export const metadata = {
  title: "Retail Intelligence Platform",
  description: "Administrator retail analytics dashboard",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
