"use client";

import * as React from "react";
import { MonitorIcon, MoonIcon, SunIcon } from "lucide-react";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@repo/ui/components/select";
import { cn } from "@repo/ui/lib/utils";

const themeOptions = [
  { icon: MonitorIcon, label: "System", value: "system" },
  { icon: SunIcon, label: "Light", value: "light" },
  { icon: MoonIcon, label: "Dark", value: "dark" },
] as const;

type ThemeValue = (typeof themeOptions)[number]["value"];

type ThemeContextValue = {
  resolvedTheme: Exclude<ThemeValue, "system">;
  setTheme: (theme: ThemeValue) => void;
  theme: ThemeValue;
};

const ThemeContext = React.createContext<ThemeContextValue | null>(null);

type ThemeSelectorProps = {
  ariaLabel?: string;
  className?: string;
  labels?: Partial<Record<ThemeValue, string>>;
};

type ThemeProviderProps = {
  children: React.ReactNode;
  defaultTheme?: ThemeValue;
  disableTransitionOnChange?: boolean;
  storageKey?: string;
};

function ThemeProvider({
  children,
  defaultTheme = "system",
  disableTransitionOnChange = true,
  storageKey = "theme",
}: ThemeProviderProps) {
  const [theme, setThemeState] = React.useState<ThemeValue>(() => {
    try {
      return getThemeValue(localStorage.getItem(storageKey) ?? defaultTheme);
    } catch {
      return defaultTheme;
    }
  });
  const [systemTheme, setSystemTheme] = React.useState<"light" | "dark">(() =>
    window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light",
  );
  const resolvedTheme = theme === "system" ? systemTheme : theme;

  React.useLayoutEffect(() => {
    const root = document.documentElement;
    const transitionStyle = disableTransitionOnChange ? document.createElement("style") : null;
    if (transitionStyle) {
      transitionStyle.textContent = "*,*::before,*::after{transition:none!important}";
      document.head.append(transitionStyle);
    }
    root.classList.remove("light", "dark");
    root.classList.add(resolvedTheme);
    root.style.colorScheme = resolvedTheme;
    if (transitionStyle) {
      window.getComputedStyle(document.body);
      window.setTimeout(() => transitionStyle.remove(), 1);
    }
  }, [disableTransitionOnChange, resolvedTheme]);

  React.useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const updateSystemTheme = () => setSystemTheme(media.matches ? "dark" : "light");
    media.addEventListener("change", updateSystemTheme);
    return () => media.removeEventListener("change", updateSystemTheme);
  }, []);

  React.useEffect(() => {
    const updateStoredTheme = (event: StorageEvent) => {
      if (event.key === storageKey) setThemeState(getThemeValue(event.newValue ?? defaultTheme));
    };
    window.addEventListener("storage", updateStoredTheme);
    return () => window.removeEventListener("storage", updateStoredTheme);
  }, [defaultTheme, storageKey]);

  const setTheme = React.useCallback(
    (value: ThemeValue) => {
      try {
        localStorage.setItem(storageKey, value);
      } catch {
        // The selected theme still applies when browser storage is unavailable.
      }
      setThemeState(value);
    },
    [storageKey],
  );

  return (
    <ThemeContext.Provider value={{ resolvedTheme, setTheme, theme }}>
      {children}
    </ThemeContext.Provider>
  );
}

function useTheme() {
  const context = React.useContext(ThemeContext);
  if (!context) throw new Error("useTheme must be used within ThemeProvider.");
  return context;
}

function ThemeSelector({ ariaLabel = "Theme", className, labels }: ThemeSelectorProps) {
  const { setTheme, theme } = useTheme();
  const activeTheme = getThemeValue(theme);

  return (
    <Select value={activeTheme} onValueChange={(value) => setTheme(getThemeValue(value))}>
      <SelectTrigger
        aria-label={ariaLabel}
        className={cn(
          "h-8 min-w-[6.25rem] rounded-md border-border/70 bg-background/80 px-2 text-xs font-semibold text-foreground shadow-none hover:bg-accent focus-visible:ring-2",
          className,
        )}
        size="sm"
      >
        <SelectValue />
      </SelectTrigger>
      <SelectContent align="end" className="min-w-32">
        {themeOptions.map((option) => {
          const Icon = option.icon;

          return (
            <SelectItem key={option.value} className="text-xs font-medium" value={option.value}>
              <Icon className="size-3.5" />
              {labels?.[option.value] ?? option.label}
            </SelectItem>
          );
        })}
      </SelectContent>
    </Select>
  );
}

function getThemeValue(value: string | undefined): ThemeValue {
  return themeOptions.some((option) => option.value === value) ? (value as ThemeValue) : "system";
}

export { ThemeProvider, ThemeSelector, useTheme };
