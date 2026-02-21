export function Icon({ name }: { name: "dashboard" | "changes" | "scan" | "runs" | "assets" | "seed" }) {
  const common = {
    width: 16,
    height: 16,
    viewBox: "0 0 16 16",
    fill: "none",
    xmlns: "http://www.w3.org/2000/svg",
  } as const;

  // Minimal inline icons (Linear-ish).
  if (name === "dashboard") {
    return (
      <svg {...common}>
        <path
          d="M3.2 3.2h4.9v4.9H3.2V3.2Zm4.7 0h4.9v2.9H7.9V3.2ZM7.9 7.9h4.9v4.9H7.9V7.9ZM3.2 9.1h4.9v3.7H3.2V9.1Z"
          stroke="currentColor"
          strokeWidth="1.2"
          strokeLinejoin="round"
        />
      </svg>
    );
  }

  if (name === "changes") {
    return (
      <svg {...common}>
        <path
          d="M3 4.5h10M3 8h7M3 11.5h10"
          stroke="currentColor"
          strokeWidth="1.4"
          strokeLinecap="round"
        />
      </svg>
    );
  }

  if (name === "scan") {
    return (
      <svg {...common}>
        <path
          d="M7 3.2a4.8 4.8 0 1 1 0 9.6 4.8 4.8 0 0 1 0-9.6Z"
          stroke="currentColor"
          strokeWidth="1.4"
        />
        <path
          d="M10.6 10.6 13 13"
          stroke="currentColor"
          strokeWidth="1.4"
          strokeLinecap="round"
        />
      </svg>
    );
  }

  if (name === "runs") {
    return (
      <svg {...common}>
        <path
          d="M4 4h8M4 8h8M4 12h8"
          stroke="currentColor"
          strokeWidth="1.4"
          strokeLinecap="round"
        />
      </svg>
    );
  }

  if (name === "seed") {
    return (
      <svg {...common}>
        <path
          d="M8 2.5c2.6 2.1 3.9 4 3.9 5.6A3.9 3.9 0 0 1 8 12a3.9 3.9 0 0 1-3.9-3.9C4.1 6.5 5.4 4.6 8 2.5Z"
          stroke="currentColor"
          strokeWidth="1.4"
        />
        <path
          d="M8 6.1v4.1"
          stroke="currentColor"
          strokeWidth="1.4"
          strokeLinecap="round"
        />
      </svg>
    );
  }

  return (
    <svg {...common}>
      <path
        d="M3.5 5.5h9M3.5 10.5h9M6 3.5v9"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
      />
    </svg>
  );
}
