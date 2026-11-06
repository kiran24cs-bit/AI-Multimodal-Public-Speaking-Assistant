import { useState } from "react";
import { useNavigate } from "react-router-dom";
import BannerVideo from "../assets/Banner3.webm";
import {
  Activity,
  BrainCircuit,
  TrendingUp,
  Mail,
  LockKeyhole,
  Eye,
  EyeOff,
  ArrowRight,
  RotateCcw,
  UserRound,
  Sparkles,
} from "lucide-react";
import "../index.css";
import { useData } from "../context/DataContext";
function PresenterScene() {
  return (
    <div className="scene-container video-scene">
      <video
        className="presenter-video"
        src={BannerVideo}
        autoPlay
        loop
        muted
        playsInline
        preload="auto"
        aria-hidden="true"
      />
    </div>
  );
}

const features = [
  {
    Icon: Activity,
    title: "Speech analytics",
    description: "Track pace, pauses and filler words.",
  },
  {
    Icon: BrainCircuit,
    title: "AI-powered feedback",
    description: "Discover strengths and areas to improve.",
  },
  {
    Icon: TrendingUp,
    title: "Build confidence",
    description: "Practice consistently and measure progress.",
  },
];

export default function Login() {
  const [mode, setMode] = useState("login");
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [message, setMessage] = useState("");
  const [remember, setRemember] = useState(false);
  const navigate = useNavigate();
  const { users, setUsers, setCurrentUser } = useData();
  const handleLogin = () => {
    const user = users.find(
      (u) => u.gmail === email && u.password === password
    );

    if (user) {
      setCurrentUser(user);
      navigate("/dashboard");
    } else {
      setMessage("Invalid email or password");
    }
  };
  const handleSignup = () => {
  if (!name || !email || !password) {
    setMessage("Please fill in all fields");
    return;
  }

  const existingUser = users.find((u) => u.gmail === email);

  if (existingUser) {
    setMessage("Email already registered");
    return;
  }

  const newUser = {
    name: name,
    gmail: email,
    password: password,
  };

  setUsers((prevUsers) => [...prevUsers, newUser]);
  setCurrentUser(newUser);
  navigate("/dashboard");
};

  function switchMode(next) {
    setMode(next);
    setMessage("");
  }

  function handleSubmit(event) {
    event.preventDefault();

    if (mode === "forgot") {
      setMessage(
        "Password recovery UI is ready. Connect an authentication service to send a reset email."
      );
      return;
    }

    if (mode === "signup" && !name.trim()) {
      setMessage("Please enter your name.");
      return;
    }

    if (password.length < 8) {
      setMessage("Your password must contain at least 8 characters.");
      return;
    }

    setMessage(
      "Form validation successful. Connect your backend to create an account or sign in."
    );
  }

  return (
    <main className="voxa-page">
      <header className="brand">
        Speak<span>Karo.AI</span>
      </header>

      <section className="showcase">
        <div className="hero-copy">
          <div className="eyebrow">
            <span className="live-dot" />
            YOUR PERSONAL AI SPEAKING COACH
          </div>

          <h1>
            Better speaking.
            <br />
            <span>Bigger opportunities.</span>
          </h1>

          <p className="hero-description">
            Transform the way you communicate. Practice your presentation,
            understand your delivery and speak with confidence.
          </p>

          <div className="feature-list">
            {features.map(({ Icon, title, description }) => (
              <article className="feature" key={title}>
                <div className="feature-icon">
                  <Icon size={21} />
                </div>
                <div>
                  <h3>{title}</h3>
                  <p>{description}</p>
                </div>
              </article>
            ))}
          </div>
        </div>

        <div className="presenter">
          <PresenterScene />
        </div>
      </section>

      <section className="auth-side">
        <div className="auth-card" key={mode}>
          <div className="auth-heading">
            <div className="auth-eyebrow">
              {mode === "signup"
                ? "START YOUR JOURNEY"
                : mode === "forgot"
                  ? "ACCOUNT RECOVERY"
                  : "WELCOME BACK"}
            </div>

            <h2>
              {mode === "login" ? (
                <>Sign in to <span>SpeakKaro.AI</span></>
              ) : mode === "signup" ? (
                "Create your account"
              ) : (
                "Reset your password"
              )}
            </h2>

            <p>
              {mode === "login"
                ? "Your journey to better speaking continues."
                : mode === "signup"
                  ? "Start building your speaking confidence today."
                  : "Enter your email to begin account recovery."}
            </p>
          </div>

          {mode !== "forgot" && (
            <div className="mode-switch">
              <button
                type="button"
                className={mode === "login" ? "active" : ""}
                onClick={() => switchMode("login")}
              >
                Login
              </button>
              <button
                type="button"
                className={mode === "signup" ? "active" : ""}
                onClick={() => switchMode("signup")}
              >
                Sign up
              </button>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {mode === "signup" && (
              <label className="field">
                <UserRound size={18} />
                <input
                  type="text"
                  placeholder="Full name"
                  autoComplete="name"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  required
                />
              </label>
            )}

            <label className="field">
              <Mail size={18} />
              <input
                type="email"
                placeholder="Email address"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                  required
              />
            </label>

            {mode !== "forgot" && (
              <label className="field">
                <LockKeyhole size={18} />
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="Password (min. 8 characters)"
                  autoComplete={
                    mode === "signup" ? "new-password" : "current-password"
                  }
                  minLength={8}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                />
                <button
                  type="button"
                  className="visibility-button"
                  onClick={() => setShowPassword((current) => !current)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </label>
            )}

            {mode === "login" && (
              <div className="form-options">
                <label className="remember-option">
                  <input
                    type="checkbox"
                    checked={remember}
                    onChange={(event) => setRemember(event.target.checked)}
                  />
                  Remember me
                </label>

                <button
                  className="text-link"
                  type="button"
                  onClick={() => switchMode("forgot")}
                >
                  Forgot password?
                </button>
              </div>
            )}

            {message && (
              <div className="form-message" role="status">
                {message}
              </div>
            )}

  
            <button
              className="submit-button"
              type="button"
              onClick={() => {
                if (mode === "login") {
                  handleLogin();
                } else if (mode === "signup") {
                  handleSignup();
                } else {
                  handleSubmit();
                }
              }}
            >
              {mode === "login"
                ? "Login"
                : mode === "signup"
                  ? "Create account"
                  : "Send reset instructions"}
              <ArrowRight size={19} />
            </button>
          </form>

          <div className="auth-footer">
            {mode === "login" ? (
              <>
                Don't have an account?{" "}
                <button type="button" onClick={() => switchMode("signup")}>
                  Sign up
                </button>
              </>
            ) : (
              <>
                Already have an account?{" "}
                <button type="button" onClick={() => switchMode("login")}>
                  Sign in
                </button>
              </>
            )}
          </div>
        </div>

        <p className="privacy-note">
          <LockKeyhole size={13} />
          Your voice. Your progress. Your future.
        </p>
      </section>

      <div className="background-orb orb-one" />
      <div className="background-orb orb-two" />
    </main>
  );
}
