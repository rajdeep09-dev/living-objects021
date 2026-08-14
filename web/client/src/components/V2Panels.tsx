/**
 * Signal Loom compatibility entrypoint: the former mock v2 surface now
 * delegates to the authenticated v3 frontier instruments. Keeping this file
 * preserves imports for downstream consumers while ensuring the dashboard has
 * one source of truth and never renders fabricated organism data.
 */
import V3Panels from "./V3Panels";

type V2PanelsProps = {
  generation: number;
  onEvent?: (text: string, tone?: "cyan" | "copper" | "chartreuse" | "lavender") => void;
};

export default function V2Panels({ generation, onEvent }: V2PanelsProps) {
  return <V3Panels generation={generation} onEvent={onEvent} />;
}
