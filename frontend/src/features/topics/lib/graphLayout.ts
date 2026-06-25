/** coverage に応じたノードの色（react-force-graph のキャンバス描画用）。 */
export function coverageColor(coverage: string): string {
  switch (coverage) {
    case "covered":
      return "#16a34a"; // green
    case "weak":
      return "#d97706"; // amber
    default:
      return "#94a3b8"; // slate (gap)
  }
}
