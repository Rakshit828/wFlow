import React, { createContext, useContext } from "react";
import { Routes, Route, Navigate, NavLink, useNavigate, useLocation, Outlet } from "react-router-dom";
import {
  Moon,
  Sun,
  Monitor,
  Zap,
  ArrowLeft,
  FileJson,
  Loader2,
  Compass,
} from "lucide-react";
import { Dashboard } from "./components/dashboard/Dashboard";
import { ExplorePage } from "./components/explore/ExplorePage";
import { LandingPage } from "./components/landing/LandingPage";
import { SignInPage } from "./components/auth/SignInPage";
import { WorkflowEditorPage } from "./components/canvas/WorkflowEditorPage";
import { useAuthStore } from "./store/useAuthStore";
import { redirectToGoogleLogin } from "./api/auth";

type ThemeMode = "light" | "dark" | "system";

type ThemeContextType = {
  theme: ThemeMode;
  cycleTheme: () => void;
};

const ThemeContext = createContext<ThemeContextType | null>(null);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) throw new Error("useTheme must be used within ThemeProvider");
  return context;
};

interface RouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<RouteProps> = ({ children }) => {
  const { status } = useAuthStore();
  if (status === "unauthenticated") {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
};

const PublicRoute: React.FC<RouteProps> = ({ children }) => {
  const { status } = useAuthStore();
  if (status === "authenticated") {
    return <Navigate to="/dashboard" replace />;
  }
  return <>{children}</>;
};

const GoogleLoginRedirect: React.FC = () => {
  React.useEffect(() => {
    redirectToGoogleLogin();
  }, []);

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center gap-3 text-muted-foreground">
      <Loader2 className="text-primary animate-spin" size={32} />
      <p className="text-sm">Redirecting to Google Login…</p>
    </div>
  );
};

const AppLayout: React.FC = () => {
  const { user } = useAuthStore();
  const location = useLocation();
  const navigate = useNavigate();
  const { theme, cycleTheme } = useTheme();
  const [jsonOpen, setJsonOpen] = React.useState(false);

  const themeIcon =
    theme === "dark" ? (
      <Moon size={14} />
    ) : theme === "light" ? (
      <Sun size={14} />
    ) : (
      <Monitor size={14} />
    );

  const isEditor = location.pathname.startsWith("/workflow");
  const isExplore = location.pathname === "/explore";
  const pageSubtitle = isEditor ? "Editor" : isExplore ? "Explore" : "Dashboard";

  return (
    <div className="h-screen w-screen flex flex-col bg-background text-foreground overflow-hidden">
      <header className="h-14 flex items-center justify-between px-4 border-b border-border bg-card/80 backdrop-blur-md z-50 shrink-0">
        <div className="flex items-center gap-3">
          {isEditor && (
            <button
              type="button"
              onClick={() => navigate("/dashboard")}
              className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors mr-2"
            >
              <ArrowLeft size={16} />
              <span className="hidden sm:inline">Dashboard</span>
            </button>
          )}
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-primary/10 border border-primary/20">
              <Zap className="text-primary" size={16} />
            </div>
            <h1 className="text-base font-bold tracking-wide">
              wFlow
              <span className="text-[11px] ml-1.5 text-muted-foreground font-normal uppercase tracking-widest">
                {pageSubtitle}
              </span>
            </h1>
          </div>

          {/* Navigation links — hidden when inside the editor */}
          {!isEditor && (
            <nav className="hidden sm:flex items-center gap-1 ml-4 bg-card/60 rounded-lg border border-border p-0.5">
              <NavLink
                to="/dashboard"
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                    isActive
                      ? "bg-primary/10 text-primary shadow-sm"
                      : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                  }`
                }
              >
                <Zap size={12} />
                Dashboard
              </NavLink>
              <NavLink
                to="/explore"
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                    isActive
                      ? "bg-violet-500/10 text-violet-400 shadow-sm"
                      : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                  }`
                }
              >
                <Compass size={12} />
                Explore
              </NavLink>
            </nav>
          )}

          {user?.email && (
            <span className="hidden lg:inline text-xs text-muted-foreground truncate max-w-[180px]">
              {user.email}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {isEditor && (
            <button
              type="button"
              onClick={() => setJsonOpen(!jsonOpen)}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-sm font-semibold transition-all border ${
                jsonOpen
                  ? "bg-primary/10 text-primary border-primary/30"
                  : "bg-card text-muted-foreground border-border hover:text-foreground"
              }`}
            >
              <FileJson size={14} />
              JSON
            </button>
          )}
          <button
            type="button"
            onClick={cycleTheme}
            className="p-2 rounded-lg bg-card text-muted-foreground hover:text-foreground border border-border hover:border-primary/30 transition-all"
            title={`Theme: ${theme}`}
          >
            {themeIcon}
          </button>
        </div>
      </header>

      <main className="flex-1 overflow-hidden relative">
        <Outlet context={{ jsonOpen, setJsonOpen }} />
      </main>
    </div>
  );
};

function App() {
  const { status, checkSession } = useAuthStore();
  const navigate = useNavigate();
  const [theme, setTheme] = React.useState<ThemeMode>(() => {
    if (typeof window !== "undefined") {
      return (localStorage.getItem("wflow-theme") as ThemeMode) || "system";
    }
    return "system";
  });

  React.useEffect(() => {
    checkSession();
  }, [checkSession]);

  React.useEffect(() => {
    localStorage.setItem("wflow-theme", theme);
    const root = document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
    } else if (theme === "light") {
      root.classList.remove("dark");
    } else {
      const prefersDark = window.matchMedia(
        "(prefers-color-scheme: dark)",
      ).matches;
      root.classList.toggle("dark", prefersDark);
    }
  }, [theme]);

  const cycleTheme = () => {
    const order: ThemeMode[] = ["dark", "light", "system"];
    const idx = order.indexOf(theme);
    setTheme(order[(idx + 1) % order.length]);
  };

  if (status === "loading") {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center gap-3 text-muted-foreground">
        <Loader2 className="text-primary animate-spin" size={32} />
        <p className="text-sm">Loading wFlow…</p>
      </div>
    );
  }

  return (
    <ThemeContext.Provider value={{ theme, cycleTheme }}>
      <Routes>
        {/* Public Routes */}
        <Route
          path="/"
          element={
            <PublicRoute>
              <LandingPage onGetStarted={() => navigate("/signin")} />
            </PublicRoute>
          }
        />
        <Route
          path="/signin"
          element={
            <PublicRoute>
              <SignInPage onBack={() => navigate("/")} />
            </PublicRoute>
          }
        />
        <Route path="/login/google" element={<GoogleLoginRedirect />} />

        {/* Protected Routes inside AppLayout */}
        <Route
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/explore" element={<ExplorePage />} />
          <Route path="/workflow" element={<WorkflowEditorPage />} />
          <Route path="/workflow/:id" element={<WorkflowEditorPage />} />
        </Route>

        {/* Fallback Catch-All */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </ThemeContext.Provider>
  );
}

export default App;
