import { describe, it, expect, beforeEach, vi } from "vitest";
import { extractErrorMessage, api } from "../services/api";

describe("Frontend API Service & Error Extraction", () => {
  it("extracts structured error message from { error: { message } } response", () => {
    const error = {
      response: {
        data: {
          error: {
            code: "VALIDATION_ERROR",
            message: "Request payload validation failed.",
          },
        },
      },
    };
    expect(extractErrorMessage(error)).toBe("Request payload validation failed.");
  });

  it("extracts detail message from standard FastAPI { detail: '...' }", () => {
    const error = {
      response: {
        data: {
          detail: "Store with ID '123' not found.",
        },
      },
    };
    expect(extractErrorMessage(error)).toBe("Store with ID '123' not found.");
  });

  it("extracts and formats array of Pydantic validation errors", () => {
    const error = {
      response: {
        data: {
          detail: [
            { loc: ["body", "email"], msg: "Invalid email format" },
            { loc: ["body", "password"], msg: "Password too short" },
          ],
        },
      },
    };
    const message = extractErrorMessage(error);
    expect(message).toContain("Invalid email format");
    expect(message).toContain("Password too short");
  });

  it("falls back to generic error message when no response payload exists", () => {
    const error = new Error("Network connection dropped");
    expect(extractErrorMessage(error)).toBe("Network connection dropped");
    expect(extractErrorMessage(null)).toBe("An unexpected error occurred.");
  });
});
