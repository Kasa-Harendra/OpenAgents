import React from 'react';
import { Message, useChatStore } from '../stores/chatStore';
import ChatMessage from './ChatMessage';
import ThoughtLine from './ThoughtLine/ThoughtLine';
import { HugeiconsIcon } from '@hugeicons/react';
import { Tick02Icon } from '@hugeicons/core-free-icons';

interface SystemMessageGroupProps {
  messages: Message[];
}

export const SystemMessageGroup: React.FC<SystemMessageGroupProps> = ({ messages }) => {
  const { chats, activeChatId } = useChatStore();
  
  if (!messages.length) return null;

  const activeChat = chats.find(c => c.id === activeChatId);
  const isTyping = activeChat?.isTyping ?? false;
  const lastMsgInChat = activeChat?.messages[activeChat.messages.length - 1];
  const isLatestMessage = lastMsgInChat?.id === messages[messages.length - 1]?.id;

  const isWorking = messages[messages.length - 1]?.type !== 'tool_output' && isTyping && isLatestMessage;

  return (
    <div className="my-1 w-full">
      <ThoughtLine
        className="w-full"
        working={isWorking}
        label={`System Activity`}
        doneLabel={`System Activity (${messages.length} steps)`}
        showTimer={true}
        shimmer={false}
        collapsible={true}
        collapseOnSettle={false}
        fontSize={14}
      >
        <div className="thought-line__steps pl-1 pt-1 pb-1 w-full">
          {messages.map((m, i) => {
            const done = !isWorking || i < messages.length - 1;
            return (
              <div key={m.id} className="thought-line__step flex items-start gap-2 w-full" data-done={done ? '' : undefined}>
                <span className="thought-line__mark mt-2 shrink-0" aria-hidden="true" style={{ opacity: done ? 0.55 : 1 }}>
                  {done ? (
                    <HugeiconsIcon icon={Tick02Icon} size="1.2em" strokeWidth={2.5} />
                  ) : (
                    <i className="thought-line__pulse" />
                  )}
                </span>
                <div className="flex-1 min-w-0">
                  <ChatMessage message={m} />
                </div>
              </div>
            );
          })}
        </div>
      </ThoughtLine>
    </div>
  );
};

export default SystemMessageGroup;
