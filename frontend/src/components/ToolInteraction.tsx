import type { ToolInteraction as ToolInteractionType } from "../api/client";
import "./ToolInteraction.css";

type ToolInteractionProps = {
  interaction: ToolInteractionType;
};

export function ToolInteraction({ interaction }: ToolInteractionProps) {
  if (interaction.type === "tool_use") {
    return (
      <div className="tool-interaction tool-interaction--use">
        <div className="tool-interaction__header">
          <span className="tool-interaction__icon">🔧</span>
          <span className="tool-interaction__name">
            Calling: <strong>{interaction.name}</strong>
          </span>
        </div>
        {interaction.input && (
          <details className="tool-interaction__details">
            <summary>View parameters</summary>
            <pre className="tool-interaction__json">
              {JSON.stringify(interaction.input, null, 2)}
            </pre>
          </details>
        )}
      </div>
    );
  }

  if (interaction.type === "tool_result") {
    const contentStr =
      typeof interaction.content === "string"
        ? interaction.content
        : JSON.stringify(interaction.content, null, 2);

    return (
      <div
        className={`tool-interaction tool-interaction--result ${
          interaction.is_error ? "tool-interaction--error" : ""
        }`}
      >
        <div className="tool-interaction__header">
          <span className="tool-interaction__icon">
            {interaction.is_error ? "❌" : "✅"}
          </span>
          <span className="tool-interaction__name">
            {interaction.is_error ? "Error" : "Result received"}
          </span>
        </div>
        {contentStr && (
          <details className="tool-interaction__details">
            <summary>View response</summary>
            <pre className="tool-interaction__json">{contentStr}</pre>
          </details>
        )}
      </div>
    );
  }

  return null;
}
