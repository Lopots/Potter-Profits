export function normalizeApiTimestamp(value?: string | null) {
  if (!value) {
    return null;
  }

  return /z$/i.test(value) || /[+-]\d{2}:\d{2}$/.test(value)
    ? value
    : `${value}Z`;
}

export function formatEasternTimestamp(value?: string | null) {
  if (!value) {
    return "Not yet";
  }

  const normalizedValue = normalizeApiTimestamp(value);
  if (!normalizedValue) {
    return "Not yet";
  }

  return new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
    hour12: true,
    timeZoneName: "short",
  }).format(new Date(normalizedValue));
}
