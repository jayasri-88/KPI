/**
 * Financial and Numeric Formatters for Retail KPI Platform
 */

export const formatCurrency = (value, options = {}) => {
  const { compact = false, symbol = "₹" } = options;
  const num = Number(value) || 0;

  if (compact) {
    if (Math.abs(num) >= 10000000) {
      return `${symbol}${(num / 10000000).toFixed(2)} Cr`;
    }
    if (Math.abs(num) >= 100000) {
      return `${symbol}${(num / 100000).toFixed(2)} L`;
    }
    if (Math.abs(num) >= 1000) {
      return `${symbol}${(num / 1000).toFixed(1)}k`;
    }
  }

  return `${symbol}${num.toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
};

export const formatCompactNumber = (value) => {
  const num = Number(value) || 0;
  if (Math.abs(num) >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  }
  if (Math.abs(num) >= 1000) {
    return `${(num / 1000).toFixed(1)}k`;
  }
  return num.toLocaleString();
};

export const formatPercent = (value, showPlus = true) => {
  const num = Number(value) || 0;
  const prefix = showPlus && num > 0 ? "+" : "";
  return `${prefix}${num.toFixed(1)}%`;
};

export const formatDate = (dateInput) => {
  if (!dateInput) return "N/A";
  const date = new Date(dateInput);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
};
