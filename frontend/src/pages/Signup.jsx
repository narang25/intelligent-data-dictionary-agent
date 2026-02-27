import { useNavigate, Link } from "react-router-dom";
import AuthForm from "../components/Auth/AuthForm";
import { signupUser } from "../services/api";

export default function Signup() {
  const navigate = useNavigate();

  const handleSignup = async (email, password) => {
    try {
      await signupUser(email, password);
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

      <p className="text-center text-sm text-secondary mt-4">
        Already have an account?{" "}
        <Link to="/login" className="text-accent hover:underline">
          Login
        </Link>
      </p>
    </div>
  );
}
