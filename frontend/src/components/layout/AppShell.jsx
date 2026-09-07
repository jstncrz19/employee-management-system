import { useState } from "react";

import Sidebar from "./Sidebar";
import Header from "./Header";

function AppShell({ children }) {
  const [menuOpen, setMenuOpen] = useState(false);

  const toggleMenu = () => {
    setMenuOpen((open) => !open);
  };

  const closeMenu = () => {
    setMenuOpen(false);
  };

  return (
    <div className="app-shell">
      <Sidebar open={menuOpen} onClose={closeMenu} />
      <div className="app-main">
        <Header onMenuToggle={toggleMenu} />
        <div className="app-content">{children}</div>
      </div>
    </div>
  );
}

export default AppShell;