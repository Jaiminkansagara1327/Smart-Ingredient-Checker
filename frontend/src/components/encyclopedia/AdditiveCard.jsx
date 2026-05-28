export default function AdditiveCard({ item }) {
  const getStatusConfig = (status) => {
    switch (status) {
      case "Safe":
        return { dot: "#22c55e", bg: "#f0fdf4", text: "#166534", border: "#86efac" };
      case "Caution":
        return { dot: "#eab308", bg: "#fefce8", text: "#854d0e", border: "#fde047" };
      case "Avoid":
        return { dot: "#ef4444", bg: "#fef2f2", text: "#991b1b", border: "#fca5a5" };
      default:
        return { dot: "#9ca3af", bg: "#f3f4f6", text: "#1f2937", border: "#cbd5e1" };
    }
  };

  const badge = getStatusConfig(item.status);

  return (
    <div
      style={{
        background: "#fff",
        borderRadius: "20px",
        padding: "28px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        border: `3px solid ${badge.border}`,
        boxShadow: "0 4px 6px -1px rgba(0,0,0,0.01), 0 2px 4px -1px rgba(0,0,0,0.01)",
      }}
    >
      <div>
        <h2 style={{ fontSize: "1.5rem", fontWeight: "700", marginBottom: "4px", color: "#111827", letterSpacing: "-0.02em" }}>
          {item.name}
        </h2>
        <p style={{ color: "#94a3b8", fontSize: "0.9rem", marginBottom: "16px", fontWeight: "500" }}>
          {item.role}
        </p>

        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            marginBottom: "20px",
            padding: "6px 12px",
            borderRadius: "999px",
            background: badge.bg,
            color: badge.text,
            fontSize: "0.85rem",
            fontWeight: "700",
          }}
        >
          <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: badge.dot }} />
          {item.status}
        </div>

        <p style={{ color: "#475569", lineHeight: "1.6", fontSize: "0.95rem" }}>
          {item.description}
        </p>
      </div>
    </div>
  );
}