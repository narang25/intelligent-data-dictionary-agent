import { useState } from "react";
import { Link } from "react-router-dom";

export default function AuthForm({
  title,
  onSubmit,
  buttonText,
  linkText,
  linkTo,
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(email, password);
  };

  return (
    <div className="auth-page">
      <form onSubmit={handleSubmit} className="auth-card rise">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4 float"
               style={{ background: "linear-gradient(135deg, var(--accent), var(--accent-dim))", boxShadow: "0 8px 32px var(--accent-glow)" }}>
            <span className="text-xl font-bold" style={{ color: "#0d0d0f" }}>J</span>
          </div>
          <h2 className="text-2xl font-bold" style={{ color: "var(--text-bright)" }}>{title}</h2>
          <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>Intelligent Data Dictionary</p>
        </div>

        {/* Inputs */}
        <div className="space-y-4 mb-6">
          <div>
            <label className="text-[10px] font-bold uppercase tracking-wider mb-1.5 block" style={{ color: "var(--text-muted)" }}>Email</label>
            <input
              type="email"
              placeholder="you@example.com"
              className="auth-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div>
            <label className="text-[10px] font-bold uppercase tracking-wider mb-1.5 block" style={{ color: "var(--text-muted)" }}>Password</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                placeholder="••••••••"
                className="auth-input"
                style={{ paddingRight: 48 }}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 transition-colors"
                style={{ color: "var(--text-muted)" }}
                onMouseEnter={e => e.currentTarget.style.color = "var(--accent)"}
                onMouseLeave={e => e.currentTarget.style.color = "var(--text-muted)"}
              >
                {showPassword ? (
                  <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path d="M17.94 17.94A10.94 10.94 0 0112 19C7 19 2.73 15.11 1 12c.65-1.19 1.57-2.4 2.72-3.5M9.9 4.24A10.94 10.94 0 0112 5c5 0 9.27 3.89 11 7-1 1.73-2.5 3.61-4.31 5.07M1 1l22 22" />
                  </svg>
                ) : (
                  <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Submit */}
        <button type="submit" className="auth-btn">{buttonText}</button>

        {/* Link */}
        {linkText && (
          <p className="text-center text-sm mt-6" style={{ color: "var(--text-muted)" }}>
            {linkText}{" "}
            <Link to={linkTo} className="font-semibold transition-colors" style={{ color: "var(--accent)" }}>
              Click here
            </Link>
          </p>
        )}
      </form>
    </div>
  );
}
