
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest } from "../../components/api";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleLogin(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const result = await apiRequest("/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });

      if (!result.access_token) {
        throw new Error("The backend did not return an access token.");
      }

      localStorage.setItem("retail_token", result.access_token);
      localStorage.setItem("retail_username", result.username ?? username);

      // Success popup
      alert("Successfully logged in to the Retail Intelligence System!");

      // Redirect to dashboard
      router.push("/dashboard");

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-page">
      <form className="login-card" onSubmit={handleLogin}>
        <div className="brand-icon login-icon">R</div>

        <p className="eyebrow">RETAIL INTELLIGENCE PLATFORM</p>

        <h1>Admin login</h1>

        <p className="page-description">
          Sign in using the administrator account stored in your backend database.
        </p>

        <label htmlFor="username">Username</label>
        <input
          id="username"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          autoComplete="username"
          required
        />

        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="current-password"
          required
        />

        {error && <p className="error-message">{error}</p>}

        <button className="primary-button" type="submit" disabled={loading}>
          {loading ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </main>
  );
}
