/** セッション作成フォームのトピック選択値を分類する純粋関数。 */
export const TOPIC_NEW = "new";
export const TOPIC_NONE = "";

export type TopicChoice =
  | { kind: "none" }
  | { kind: "existing"; id: number }
  | { kind: "new"; title: string }
  | { kind: "error"; message: string };

export function classifyTopicSelection(
  selection: string | undefined,
  newTitle: string | undefined,
): TopicChoice {
  if (selection === TOPIC_NEW) {
    const title = (newTitle ?? "").trim();
    if (!title) {
      return { kind: "error", message: "新しいトピック名を入力してください" };
    }
    return { kind: "new", title };
  }
  if (selection && selection !== TOPIC_NONE) {
    return { kind: "existing", id: Number(selection) };
  }
  return { kind: "none" };
}
