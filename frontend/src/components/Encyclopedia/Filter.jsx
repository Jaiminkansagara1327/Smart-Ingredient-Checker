export default function Filter({ selectedLetter, onSelectLetter }) {
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "40px" }}>
      {alphabet.map((letter) => {
        const isSelected = selectedLetter === letter;
        return (
          <button
            key={letter}
            onClick={() => onSelectLetter(isSelected ? "" : letter)}
            style={{
              width: "40px",
              height: "40px",
              borderRadius: "10px",
              border: "none",
              cursor: "pointer",
              fontWeight: "600",
              fontSize: "14px",
              background: isSelected ? "#2563eb" : "#e2e8f0",
              color: isSelected ? "#fff" : "#475569",
              transition: "all 0.2s ease",
            }}
          >
            {letter}
          </button>
        );
      })}

      {selectedLetter && (
        <button
          onClick={() => onSelectLetter("")}
          style={{
            padding: "0 16px",
            borderRadius: "10px",
            border: "none",
            background: "#ef4444",
            color: "#fff",
            cursor: "pointer",
            fontWeight: "600",
            fontSize: "14px",
          }}
        >
          Clear
        </button>
      )}
    </div>
  );
}