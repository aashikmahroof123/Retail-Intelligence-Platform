
"use client";

import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";

const navItems = [
  { label: "Dashboard", href: "/" },
  { label: "Customer Segmentation", href: "/segmentation" },
  { label: "Demand Forecasting", href: "/forecasting" },
  { label: "Inventory Analysis", href: "/inventory" },
  { label: "Pricing Analysis", href: "/pricing" },
  { label: "Market Basket Analysis", href: "/market-basket" },
  { label: "Recommendations", href: "/recommendations" },
  { label: "Overall-Inventory", href: "/overall-inventory" },
];

export default function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();

  function logout() {
    localStorage.removeItem("retail_token");
    localStorage.removeItem("retail_username");
    router.push("/login");
  }

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-icon">R</div>
        <div>
          <h2>Retail Intelligence</h2>
          <p>Management Platform</p>
        </div>
      </div>

      <p className="nav-heading">WORKSPACE</p>

      <nav className="nav-links">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={pathname === item.href ? "active" : ""}
          >
            {item.label}
          </Link>
        ))}
      </nav>

      <button className="logout-button" onClick={logout}>
        Log out
      </button>
    </aside>
  );
}
