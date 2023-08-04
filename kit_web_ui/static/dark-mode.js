window.addEventListener("DOMContentLoaded", (event) => {
  /// Theme Toggle
  const systemIsDark = window.matchMedia(
    "(prefers-color-scheme: dark)"
  ).matches;
  const theme =
    localStorage.getItem("theme") ?? (systemIsDark ? "dark" : "light");

    document.documentElement.setAttribute('data-bs-theme', theme)
    localStorage.setItem("theme", theme);

    // set switcher icon
    icon = document.getElementById("toggle-theme-icon");
    icon.classList.remove("bi-sun-fill", "bi-moon-stars-fill");
    icon.classList.add(
      theme === "light" ? "bi-sun-fill" : "bi-moon-stars-fill"
    );

    document.getElementById("theme-toggle").addEventListener('click', () => {
      const currentTheme = localStorage.getItem("theme");
      const newTheme = currentTheme === "light" ? "dark" : "light";

      document.documentElement.setAttribute('data-bs-theme', newTheme);
      localStorage.setItem("theme", newTheme);

      // set switcher icon
      icon = document.getElementById("toggle-theme-icon");
      icon.classList.remove("bi-sun-fill", "bi-moon-stars-fill");
      icon.classList.add(
        newTheme === "light" ? "bi-sun-fill" : "bi-moon-stars-fill"
      );
    });
});
