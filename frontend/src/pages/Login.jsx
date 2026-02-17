import { useNavigate, Link } from "react-router-dom";
import AuthForm from "../components/Auth/AuthForm";

export default function Login() {
  const navigate = useNavigate();

  const handleLogin = async (email, password) => {
    try {
      const response = await fetch("http://localhost:8000/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Login failed");
      }

      localStorage.setItem("token", data.access_token);

      navigate("/chat");
    } catch (err) {
      alert(err.message);
    }
  };

 return (
  <AuthForm
    title="Login"
    buttonText="Login"
    onSubmit={handleLogin}
    linkText="Don't have an account?"
    linkTo="/signup"
  />
);

}
