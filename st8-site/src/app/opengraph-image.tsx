import { ImageResponse } from "next/og";

export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          background: "#0a0a0a",
          color: "#ededed",
          fontSize: 72,
          fontWeight: 600,
        }}
      >
        <div style={{ display: "flex" }}>
          ST8<span style={{ color: "#d4af37" }}>-AI</span>
        </div>
        <div style={{ fontSize: 28, color: "#a3a3a3", marginTop: 24 }}>
          AI-автоматизация для бизнеса
        </div>
      </div>
    ),
    { ...size }
  );
}
