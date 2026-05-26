import { useState, useMemo, useEffect } from "react";
import SearchBar from "../components/encyclopedia/SearchBar";
import Filter from "../components/encyclopedia/Filter";
import AdditiveGrid from "../components/encyclopedia/AdditiveGrid";

export default function Encyclopedia() {
  // 1. Existing search and filter states
  const [search, setSearch] = useState("");
  const [selectedLetter, setSelectedLetter] = useState("");

  // 2. New state container to hold dynamic backend data
  const [additivesList, setAdditivesList] = useState([]); 

  // 3. Automatically fetch your additives list from the Python backend on page mount
  useEffect(() => {
  fetch("/api/additives/") 
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failed to fetch additives from backend");
      }
      return response.json();
    })
    .then((data) => {
      setAdditivesList(data); // Safely drop the server response array into state
    })
    .catch((error) => {
      console.error("Backend Connection Error:", error);
    });
}, []);

  // 4. Optimized live filtering computing across your dynamic backend list
  const filteredAdditives = useMemo(() => {
    return additivesList.filter((additive) => {
      // Safely check if the additive name matches the typed search string
      const matchesSearch = additive.name.toLowerCase().includes(search.toLowerCase());
      
      // If a letter pill is selected, match the starting character; otherwise pass true
      const matchesLetter = selectedLetter ? additive.name.startsWith(selectedLetter) : true;
      
      return matchesSearch && matchesLetter;
    });
  }, [additivesList, search, selectedLetter]); // Tracks additivesList updates alongside user filter interaction

  // Add a quick guard condition right before  return statement:
  if (!additivesList || additivesList.length === 0) {
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
        <div className="history-loading" style={{ textAlign: "center", padding: "40px" }}>
          <div className="spinner-minimal"></div>
          <p style={{ color: 'var(--color-text-tertiary)', marginTop: "12px" }}>
            wait a moment
          </p>
        </div>
      </div>
    );
  }
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