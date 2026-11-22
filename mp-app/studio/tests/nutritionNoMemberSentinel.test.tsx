import { afterEach, describe, expect, it, vi } from "vitest";
import { render, waitFor } from "@testing-library/react";
import { Nutrition } from "../src/pages/Nutrition";
import { useAppStore } from "../src/stores/appStore";

/**
 * WP 4.6 / F‑16 — وقتی هیچ عضوی انتخاب نشده، صفحهٔ تغذیه نباید با member_id=-1 درخواست بفرستد.
 * (sentinel منفی `?? -1` در Nutrition.tsx)
 */

afterEach(() => {
  vi.unstubAllGlobals();
  useAppStore.setState({ selectedMemberId: null });
});

describe("Nutrition — بدون عضو، بدون sentinel منفی", () => {
  it("does not request member_id=-1 when no member is selected", async () => {
    useAppStore.setState({ selectedMemberId: null });
    const fetchMock = vi.fn(async () => new Response("{}", { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<Nutrition />);
    await waitFor(() => expect(document.body.textContent).toContain("عضو"));

    const urls = fetchMock.mock.calls.map((c) => String(c[0]));
    const sentinel = urls.filter((u) => /[=/]-1(\b|$|&)/.test(u));
    expect(sentinel).toEqual([]);
  });
});
