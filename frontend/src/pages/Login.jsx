import { useNavigate, Link } from "react-router-dom";
import AuthForm from "../components/Auth/AuthForm";
import { loginUser } from "../services/api";

export default function Login() {
  const navigate = useNavigate();

  const handleLogin = async (email, password) => {
    try {
      const data = await loginUser(email, password);
      localStorage.setItem("token", data.access_token);
      // Dispatch event so ConnectionContext picks up the new token
      window.dispatchEvent(new Event("auth-change"));
      navigate("/quick-start");
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
