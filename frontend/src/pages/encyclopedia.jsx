import { useState, useMemo, useEffect } from "react";
import SearchBar from "../components/encyclopedia/SearchBar";
import Filter from "../components/encyclopedia/Filter";
import AdditiveGrid from "../components/encyclopedia/AdditiveGrid";

export default function Encyclopedia() {
  // 1. Search, filter, loading, and error states
  const [search, setSearch] = useState("");
  const [selectedLetter, setSelectedLetter] = useState("");
  const [additivesList, setAdditivesList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 2. Fetch function to be called on mount and on retry
  const fetchAdditives = () => {
    setLoading(true);
    setError(null);
    fetch("/api/additives/")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to fetch additives from the server");
        }
        return response.json();
      })
      .then((data) => {
        setAdditivesList(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Backend Connection Error:", err);
        setError("Unable to connect to the server. Please verify your connection and try again.");
        setLoading(false);
      });
  };

  // 3. Automatically fetch your additives list from the Python backend on page mount
  useEffect(() => {
    fetchAdditives();
  }, []);

  // 4. Optimized live filtering computing across your dynamic backend list
  const filteredAdditives = useMemo(() => {
    return additivesList.filter((additive) => {
      // Safely check if the additive name matches the typed search string
      const matchesSearch = additive.name.toLowerCase().includes(search.toLowerCase());
      
      // If a letter pill is selected, match the starting character case-insensitively; otherwise pass true
      const matchesLetter = selectedLetter 
        ? additive.name.toLowerCase().startsWith(selectedLetter.toLowerCase()) 
        : true;
      
      return matchesSearch && matchesLetter;
    });
  }, [additivesList, search, selectedLetter]);

  // Loading view
  if (loading) {
    return (
      <div className="main-content" style={{ padding: "40px 20px", maxWidth: "1200px", margin: "0 auto" }}>
        <div style={{ textAlign: "center", marginBottom: "32px" }}>
          <h1 style={{ fontSize: "2.5rem", fontWeight: "800", color: "#1e293b", letterSpacing: "-0.03em" }}>
            Food Additives Encyclopedia
          </h1>
          <p style={{ fontSize: "1.1rem", color: "#64748b", marginTop: "8px" }}>
            Search and explore a comprehensive database of dietary ingredients, preservatives, and coloring agents.
          </p>
        </div>

        <SearchBar value={search} onChange={setSearch} />
        <Filter selectedLetter={selectedLetter} onSelectLetter={setSelectedLetter} />
        
        {/* Loading Spinner Area */}
        <div className="history-loading" style={{ textAlign: "center", padding: "60px 40px" }}>
          <div className="spinner-minimal" style={{ margin: "0 auto" }}></div>
          <p style={{ color: 'var(--color-text-tertiary)', marginTop: "16px", fontSize: "1.05rem", fontWeight: "500" }}>
            Loading additives database...
          </p>
        </div>
      </div>
    );
  }

  // Error view
  if (error) {
    return (
      <div className="main-content" style={{ padding: "40px 20px", maxWidth: "1200px", margin: "0 auto" }}>
        <div style={{ textAlign: "center", marginBottom: "32px" }}>
          <h1 style={{ fontSize: "2.5rem", fontWeight: "800", color: "#1e293b", letterSpacing: "-0.03em" }}>
            Food Additives Encyclopedia
          </h1>
          <p style={{ fontSize: "1.1rem", color: "#64748b", marginTop: "8px" }}>
            Search and explore a comprehensive database of dietary ingredients, preservatives, and coloring agents.
          </p>
        </div>

        <SearchBar value={search} onChange={setSearch} />
        <Filter selectedLetter={selectedLetter} onSelectLetter={setSelectedLetter} />

        <div style={{
          textAlign: "center",
          padding: "48px 32px",
          background: "linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%)",
          border: "1px solid #fca5a5",
          borderRadius: "24px",
          color: "#991b1b",
          boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
          maxWidth: "600px",
          margin: "40px auto"
        }}>
          <div style={{ fontSize: "3rem", marginBottom: "16px" }}>⚠️</div>
          <h2 style={{ fontWeight: "700", fontSize: "1.4rem", color: "#7f1d1d", margin: "0 0 8px 0" }}>Connection Error</h2>
          <p style={{ fontSize: "1rem", color: "#991b1b", lineHeight: "1.5", margin: "0 0 24px 0" }}>{error}</p>
          <button 
            onClick={fetchAdditives}
            style={{
              padding: "12px 28px",
              background: "#dc2626",
              color: "#fff",
              border: "none",
              borderRadius: "12px",
              cursor: "pointer",
              fontWeight: "600",
              fontSize: "0.95rem",
              boxShadow: "0 4px 6px -1px rgba(220, 38, 38, 0.3)",
              transition: "all 0.2s ease"
            }}
            onMouseOver={(e) => {
              e.target.style.background = "#b91c1c";
              e.target.style.boxShadow = "0 6px 12px -1px rgba(185, 28, 28, 0.4)";
              e.target.style.transform = "translateY(-1px)";
            }}
            onMouseOut={(e) => {
              e.target.style.background = "#dc2626";
              e.target.style.boxShadow = "0 4px 6px -1px rgba(220, 38, 38, 0.3)";
              e.target.style.transform = "translateY(0)";
            }}
          >
            Retry Loading
          </button>
        </div>
      </div>
    );
  }

  // Loaded/Ready view
  return (
    <div className="main-content" style={{ padding: "40px 20px", maxWidth: "1200px", margin: "0 auto" }}>
      <div style={{ textAlign: "center", marginBottom: "32px" }}>
        <h1 style={{ fontSize: "2.5rem", fontWeight: "800", color: "#1e293b", letterSpacing: "-0.03em" }}>
          Food Additives Encyclopedia
        </h1>
        <p style={{ fontSize: "1.1rem", color: "#64748b", marginTop: "8px" }}>
          Search and explore a comprehensive database of dietary ingredients, preservatives, and coloring agents.
        </p>
      </div>

      <SearchBar value={search} onChange={setSearch} />
      <Filter selectedLetter={selectedLetter} onSelectLetter={setSelectedLetter} />
      
      <AdditiveGrid items={filteredAdditives} />
    </div>
  );
}