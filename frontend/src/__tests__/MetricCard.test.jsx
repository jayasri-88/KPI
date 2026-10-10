import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import MetricCard from "../components/dashboard/MetricCard";

describe("MetricCard Component", () => {
  it("renders metric title and formatted numerical value", () => {
    render(
      <MetricCard
        title="Total Revenue"
        value="₹33,82,900"
        subtitle="Across all stores"
      />
    );

    expect(screen.getByText("Total Revenue")).toBeInTheDocument();
    expect(screen.getByText("₹33,82,900")).toBeInTheDocument();
    expect(screen.getByText("Across all stores")).toBeInTheDocument();
  });

  it("renders positive trend badge and percentage change", () => {
    render(
      <MetricCard
        title="Gross Profit"
        value="₹14,50,000"
        change={12.5}
        trend="up"
      />
    );

    expect(screen.getByText("+12.5%")).toBeInTheDocument();
  });

  it("renders negative trend badge correctly", () => {
    render(
      <MetricCard
        title="Order Volume"
        value="1,240"
        change={-5.2}
        trend="down"
      />
    );

    expect(screen.getByText("-5.2%")).toBeInTheDocument();
  });
});
