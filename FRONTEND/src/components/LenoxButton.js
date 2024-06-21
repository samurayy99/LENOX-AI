"use client";  // Mark this as a client component


export default function LenoxButton() {
  return (
    <a
      href="http://localhost:5000"
      style={{
        padding: "10px 20px",
        fontSize: "16px",
        margin: "20px auto",
        display: "block",
        backgroundColor: "#0070f3",
        color: "#ffffff",
        border: "none",
        borderRadius: "5px",
        textAlign: "center",
        textDecoration: "none",
        cursor: "pointer",
      }}
    >
      Lenox AI
    </a>
  );
}
