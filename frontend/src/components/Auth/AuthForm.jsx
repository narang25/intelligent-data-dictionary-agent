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
    <div className="min-h-screen flex items-center justify-center bg-primary text-primary">
      <form
        onSubmit={handleSubmit}
        className="bg-surface p-8 rounded-2xl w-[380px] h-[520px] flex flex-col justify-between shadow-xl border border-primary"
      >
        {/* Top Section */}
        <div>
          <h2 className="text-2xl font-semibold text-center mb-8">
            {title}
          </h2>

          <div className="space-y-5">

            {/* Email */}
            <input
              type="email"
              placeholder="Email"
              className="w-full p-3 bg-gray-100 dark:bg-neutral-700 text-primary rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            {/* Password with Eye Icon */}
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                placeholder="Password"
                className="w-full p-3 pr-12 bg-gray-100 dark:bg-neutral-700 text-primary rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />

              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-secondary hover:text-primary transition"
              >
                {showPassword ? (
                  /* Eye Off */
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="20"
                    height="20"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    viewBox="0 0 24 24"
                  >
                    <path d="M17.94 17.94A10.94 10.94 0 0112 19C7 19 2.73 15.11 1 12c.65-1.19 1.57-2.4 2.72-3.5M9.9 4.24A10.94 10.94 0 0112 5c5 0 9.27 3.89 11 7-1 1.73-2.5 3.61-4.31 5.07M1 1l22 22" />
                  </svg>
                ) : (
                  /* Eye */
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="20"
                    height="20"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    viewBox="0 0 24 24"
                  >
                    <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Bottom Section */}
        <div className="space-y-5">
          <button
            type="submit"
            className="w-full bg-blue-600 text-white p-3 rounded-lg hover:bg-blue-500 transition font-medium"
          >
            {buttonText}
          </button>

          {linkText && (
            <p className="text-center text-sm text-secondary">
              {linkText}{" "}
              <Link
                to={linkTo}
                className="text-accent hover:underline"
              >
                Click here
              </Link>
            </p>
          )}
        </div>
      </form>
    </div>
  );
}
