import { Routes, Route, Navigate } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import DataOverview from "./pages/DataOverview";
import Prediction from "./pages/Prediction";
import Simulation from "./pages/Simulation";

const navItems = [
    { label: "Data Overview", path: "/" },
    { label: "Prediction", path: "/predict" },
    { label: "Simulation", path: "/simulation" },
];

const App = () => {
    return (
        <div className="app-shell">
            <Sidebar items={navItems} />
            <main className="content-area">
                <Routes>
                    <Route path="/" element={<DataOverview />} />
                    <Route path="/predict" element={<Prediction />} />
                    <Route path="/simulation" element={<Simulation />} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
            </main>
        </div>
    );
};

export default App;
