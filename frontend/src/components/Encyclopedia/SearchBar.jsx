export default function SearchBar({ value, onChange }) {
  return (
    <input
      type="text"
      placeholder="Search additives..."
      value={value}
      onChange={(e) => onChange(e.target.value)}
      style={{
        width: "100%",
        padding: "14px 18px",
        borderRadius: "14px",
        border: "1px solid #e2e8f0",
        marginBottom: "30px",
        fontSize: "16px",
        outline: "none",
        boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
        transition: "all 0.2s",
      }}
    />
  );
}