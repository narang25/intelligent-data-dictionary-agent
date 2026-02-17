import { useNavigate, Link } from "react-router-dom";
import AuthForm from "../components/Auth/AuthForm";

export default function Signup() {
  const navigate = useNavigate();

  const handleSignup = async (email, password) => {
    try {
      const response = await fetch("http://localhost:8000/auth/signup", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Signup failed");
      }

      alert("Signup successful. Please login.");
      navigate("/login");

    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div>
      <AuthForm
        title="Create Account"
        buttonText="Sign Up"
        onSubmit={handleSignup}
      />

      <p className="text-center text-sm text-gray-400 mt-4">
        Already have an account?{" "}
        <Link to="/login" className="text-blue-400 hover:underline">
          Login
        </Link>
      </p>
    </div>
  );
}
