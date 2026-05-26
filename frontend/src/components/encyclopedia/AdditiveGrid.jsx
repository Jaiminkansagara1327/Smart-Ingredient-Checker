import AdditiveCard from "./AdditiveCard";

export default function AdditiveGrid({ items }) {
  if (!items?.length) {
    return (
      <div
        style={{
          textAlign: "center",
          padding: "60px 20px",
          background: "#fff",
          borderRadius: "20px",
          border: "2px dashed #e2e8f0",
          color: "#6b7280",
        }}
      >
        <p style={{ fontWeight: "600", fontSize: "1.1rem" }}>No additives found matching your criteria.</p>
        <p style={{ fontSize: "0.95rem", marginTop: "4px" }}>Try shifting your letters grid selection or typing a different phrase.</p>
      </div>
    );
  }

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
        gap: "24px",
      }}
    >
      {items.map((item) => (
        <AdditiveCard key={item.id} item={item} />
      ))}
    </div>
  );
}