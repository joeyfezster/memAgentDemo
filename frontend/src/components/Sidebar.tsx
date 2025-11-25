import { type Conversation } from "../api/client";
import "./Sidebar.css";

type SidebarProps = {
  conversations: Conversation[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewChat: () => void;
};

export default function Sidebar({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewChat,
}: SidebarProps) {
  return (
    <div className="sidebar">
      <button className="new-chat-button" onClick={onNewChat}>
        + New Chat
      </button>
      <div className="conversation-list" data-testid="conversation-list">
        {conversations.map((conv) => (
          <div
            key={conv.id}
            className={`conversation-item ${
              conv.id === activeConversationId ? "active" : ""
            }`}
            onClick={() => onSelectConversation(conv.id)}
            data-testid="conversation-item"
          >
            <div className="conversation-title">
              {conv.title || "New conversation"}
            </div>
            <div className="conversation-timestamp">
              {new Date(conv.updated_at).toLocaleString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
