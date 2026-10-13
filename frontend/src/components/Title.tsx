import { NavLink } from "react-router-dom";

export function Title() {
    return (
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-white/[0.08] px-10 py-6">
            <h1 className="flex items-center gap-2 text-xl font-semibold tracking-tight text-white">
                <span className="h-2 w-2 rounded-full bg-[#00C805]" />
                NBA Fantasy GM
            </h1>
            <nav className="flex items-center gap-5 text-sm font-medium">
                <NavLink
                    to="/"
                    className={({ isActive }) =>
                        isActive ? "text-white" : "text-white/40 hover:text-white"
                    }
                >
                    Players
                </NavLink>
                <NavLink
                    to="/rosters"
                    className={({ isActive }) =>
                        isActive ? "text-white" : "text-white/40 hover:text-white"
                    }
                >
                    Rosters
                </NavLink>
            </nav>
        </header>
    )
}