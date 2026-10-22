import React, { useState } from 'react';
import { Message, useChatStore } from '../stores/chatStore';
import ChatMessage from './ChatMessage';
import ThoughtLine from './ThoughtLine/ThoughtLine';
import { HugeiconsIcon } from '@hugeicons/react';
import { Tick02Icon } from '@hugeicons/core-free-icons';
import { Copy, Check } from 'lucide-react';

interface SystemMessageGroupProps {
  messages: Message[];
}

export const SystemMessageGroup: React.FC<SystemMessageGroupProps> = ({ messages }) => {
  const { chats, activeChatId } = useChatStore();
  const [copiedGroup, setCopiedGroup] = useState(false);
  
  if (!messages.length) return null;

  const activeChat = chats.find(c => c.id === activeChatId);
  const isTyping = activeChat?.isTyping ?? false;
  const lastMsgInChat = activeChat?.messages[activeChat.messages.length - 1];
  const isLatestMessage = lastMsgInChat?.id === messages[messages.length - 1]?.id;

  const isWorking = messages[messages.length - 1]?.type !== 'tool_output' && isTyping && isLatestMessage;

  const handleCopyGroup = async (e: React.MouseEvent) => {
    e.stopPropagation();
    const groupText = messages
      .map(m => {
        const header = `[${m.agentName || 'System'} ${m.type?.replace('_', ' ') || 'message'}]`;
        const body = typeof m.content === 'object' ? JSON.stringify(m.content, null, 2) : String(m.content ?? '');
        return `${header}\n${body}`;
      })
      .join('\n\n');

    if (!groupText) return;

    let success = false;
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(groupText);
        success = true;
      } else {
        const textArea = document.createElement('textarea');
        textArea.value = groupText;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        success = document.execCommand('copy');
        textArea.remove();
      }
    } catch (err) {
      console.error('Failed to copy to clipboard', err);
    }

    if (success) {
      setCopiedGroup(true);
      setTimeout(() => setCopiedGroup(false), 2000);
    }
  };

  return (
    <div className="my-1 w-full flex items-start justify-between gap-2 group/sysgroup">
      <div className="flex-1 min-w-0">
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

      <button
        type="button"
        onClick={handleCopyGroup}
        className="mt-0.5 p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary/50 flex items-center gap-1 shrink-0"
        title={copiedGroup ? "Copied all steps!" : "Copy all system activity"}
        aria-label="Copy all system activity"
      >
        {copiedGroup ? (
          <>
            <Check size={12} className="text-green-500" />
            <span className="text-[10px] text-green-500 font-medium">Copied</span>
          </>
        ) : (
          <Copy size={12} />
        )}
      </button>
    </div>
  );
};

export default SystemMessageGroup;
