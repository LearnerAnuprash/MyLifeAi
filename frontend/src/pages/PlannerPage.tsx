import { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Button, Input, List, Avatar, Spin, Flex, Space, Typography, Card, Divider } from 'antd';
import { SendOutlined, RobotOutlined, LoadingOutlined, CopyOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { graphqlRequestWithAuth } from '@/utils/graphqlClient';
import { useAuthStore } from '@/store/authStore';
import clsx from 'clsx';

const { Text, Paragraph } = Typography;

const CONVERSATIONS_QUERY = `
  query Conversations($first: Int) {
    conversations(first: $first) {
      edges {
        node {
          id
          title
          modelProvider
          modelName
          createdAt
          updatedAt
          messages {
            id
            role
            content
            createdAt
          }
        }
      }
    }
  }
`;

const CREATE_CONVERSATION_MUTATION = `
  mutation CreateConversation($input: CreateConversationInput!) {
    createConversation(input: $input) {
      id
      title
    }
  }
`;

const SEND_MESSAGE_MUTATION = `
  mutation SendMessage($input: SendMessageInput!) {
    sendMessage(input: $input) {
      userMessage {
        id
        role
        content
        createdAt
      }
      assistantMessage {
        id
        role
        content
        createdAt
      }
    }
  }
`;

const DELETE_CONVERSATION_MUTATION = `
  mutation DeleteConversation($id: UUID!) {
    deleteConversation(id: $id)
  }
`;

type Message = {
  id: string;
  role: 'USER' | 'ASSISTANT' | 'SYSTEM' | 'TOOL';
  content: string;
  createdAt: string;
};

type Conversation = {
  id: string;
  title?: string;
  modelProvider: string;
  modelName: string;
  createdAt: string;
  updatedAt: string;
  messages: Message[];
};

export function PlannerPage() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [newConversationTitle, setNewConversationTitle] = useState('');
  const [showNewConversation, setShowNewConversation] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // Fetch conversations
  const { data: conversationsData, isLoading, refetch } = useQuery({
    queryKey: ['conversations'],
    queryFn: async () => {
      const response = await graphqlRequestWithAuth<{ conversations: { edges: Array<{ node: Conversation }> } }>(
        CONVERSATIONS_QUERY,
        { first: 20 }
      );
      return response.data?.conversations.edges.map(e => e.node) || [];
    },
    enabled: !!user,
  });

  useEffect(() => {
    if (conversationsData) {
      setConversations(conversationsData);
      if (!activeConversationId && conversationsData.length > 0) {
        setActiveConversationId(conversationsData[0].id);
      }
    }
  }, [conversationsData]);

  // Scroll to bottom when messages change
  const activeConversation = conversations.find(c => c.id === activeConversationId);
  useEffect(() => {
    scrollToBottom();
  }, [activeConversation?.messages.length]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Mutations
  const createConversationMutation = useMutation({
    mutationFn: async (title: string) => {
      const response = await graphqlRequestWithAuth<{ createConversation: Conversation }>(
        CREATE_CONVERSATION_MUTATION,
        { input: { title } }
      );
      return response.data?.createConversation;
    },
    onSuccess: (newConv) => {
      setConversations(prev => [newConv, ...prev]);
      setActiveConversationId(newConv.id);
      setShowNewConversation(false);
      setNewConversationTitle('');
    },
    onError: (error: Error) => alert(error.message),
  });

  const sendMessageMutation = useMutation({
    mutationFn: async ({ conversationId, content }: { conversationId: string; content: string }) => {
      const response = await graphqlRequestWithAuth<{ sendMessage: { userMessage: Message; assistantMessage: Message } }>(
        SEND_MESSAGE_MUTATION,
        { input: { conversationId, content } }
      );
      return response.data?.sendMessage;
    },
    onSuccess: (result, variables) => {
      if (result) {
        setConversations(prev => prev.map(conv => {
          if (conv.id === variables.conversationId) {
            return {
              ...conv,
              messages: [...conv.messages, result.userMessage, result.assistantMessage],
              updatedAt: new Date().toISOString(),
            };
          }
          return conv;
        }));
      }
      setIsSending(false);
    },
    onError: (error: Error) => {
      alert(error.message);
      setIsSending(false);
    },
  });

  const deleteConversationMutation = useMutation({
    mutationFn: async (id: string) => {
      await graphqlRequestWithAuth(DELETE_CONVERSATION_MUTATION, { id });
      return id;
    },
    onSuccess: (id) => {
      setConversations(prev => prev.filter(c => c.id !== id));
      if (activeConversationId === id) {
        setActiveConversationId(conversations[0]?.id || null);
      }
    },
    onError: (error: Error) => alert(error.message),
  });

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || !activeConversationId || isSending) return;

    const content = inputValue;
    setInputValue('');
    setIsSending(true);
    sendMessageMutation.mutate({ conversationId: activeConversationId, content });
  };

  const handleNewConversation = () => {
    if (!newConversationTitle.trim()) return;
    createConversationMutation.mutate(newConversationTitle);
  };

  const handleDeleteConversation = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Delete this conversation?')) {
      deleteConversationMutation.mutate(id);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6 animate-in">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">AI Planner</h1>
          <p className="text-[var(--color-text-secondary)]">Brainstorm, plan, and organize with AI</p>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowNewConversation(true)}>
          New Chat
        </Button>
      </div>

      {/* New Conversation Modal */}
      {showNewConversation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 animate-in" onClick={() => setShowNewConversation(false)}>
          <Card className="w-full max-w-md" style={{ borderRadius: 12 }} onClick={e => e.stopPropagation()}>
            <div className="p-6 space-y-4">
              <h3 className="text-lg font-semibold">New Conversation</h3>
              <Input
                value={newConversationTitle}
                onChange={e => setNewConversationTitle(e.target.value)}
                placeholder="Conversation title (optional)"
                onPressEnter={handleNewConversation}
                autoFocus
              />
              <Flex justify="end" gap={3}>
                <Button onClick={() => setShowNewConversation(false)}>Cancel</Button>
                <Button type="primary" onClick={handleNewConversation} loading={createConversationMutation.isPending}>
                  Create
                </Button>
              </Flex>
            </div>
          </Card>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar - Conversation List */}
        <aside className="w-80 lg:w-96 border-r border-[var(--color-border-primary)] bg-[var(--color-bg-secondary)] flex flex-col hidden lg:flex">
          <div className="p-4 border-b border-[var(--color-border-primary)]">
            <h3 className="font-medium text-[var(--color-text-primary)]">Conversations</h3>
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-1">
            {conversations.length === 0 ? (
              <div className="text-center py-8 text-[var(--color-text-tertiary)]">
                <RobotOutlined className="text-4xl mb-2 opacity-30" />
                <p>No conversations yet</p>
                <Button type="text" size="small" onClick={() => setShowNewConversation(true)} className="mt-2">
                  Start a new chat
                </Button>
              </div>
            ) : (
              conversations.map(conv => (
                <Button
                  key={conv.id}
                  type={activeConversationId === conv.id ? 'primary' : 'default'}
                  danger={activeConversationId !== conv.id}
                  block
                  className={clsx(
                    'justify-start gap-2 text-left h-auto py-3 px-3',
                    activeConversationId === conv.id ? 'bg-[var(--color-primary-bg)] border-[var(--color-primary-border)]' : ''
                  )}
                  onClick={() => setActiveConversationId(conv.id)}
                >
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">
                      {conv.title || 'Untitled conversation'}
                    </p>
                    <p className="text-xs text-[var(--color-text-tertiary)] truncate">
                      {formatRelativeTime(conv.updatedAt)}
                    </p>
                  </div>
                  <Button
                    type="text"
                    size="small"
                    icon={<DeleteOutlined />}
                    danger
                    onClick={e => handleDeleteConversation(conv.id, e)}
                  />
                </Button>
              ))
            )}
          </div>
        </aside>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col min-w-0">
          {activeConversation ? (
            <>
              {/* Conversation Header */}
              <div className="p-4 border-b border-[var(--color-border-primary)] bg-[var(--color-bg-secondary)] flex items-center justify-between">
                <div>
                  <h2 className="font-semibold text-[var(--color-text-primary)]">
                    {activeConversation.title || 'Untitled conversation'}
                  </h2>
                  <p className="text-sm text-[var(--color-text-tertiary)]">
                    {activeConversation.modelProvider} / {activeConversation.modelName}
                  </p>
                </div>
              </div>

              {/* Messages */}
              <div
                ref={messagesContainerRef}
                className="flex-1 overflow-y-auto p-6 space-y-6"
                style={{ scrollBehavior: 'smooth' }}
              >
                {activeConversation.messages.map((message, index) => (
                  <MessageBubble key={message.id} message={message} index={index} />
                ))}

                {isSending && (
                  <div className="flex justify-start">
                    <div className="flex items-center gap-2 max-w-[80%]">
                      <Avatar size={32} icon={<RobotOutlined />} style={{ background: 'var(--color-primary-bg)', color: 'var(--color-primary-text)' }} />
                      <div className="bg-[var(--color-bg-tertiary)] rounded-2xl rounded-tl-sm p-4 animate-pulse">
                        <div className="flex gap-1">
                          <span className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                          <span className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                          <span className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="p-4 border-t border-[var(--color-border-primary)] bg-[var(--color-bg-secondary)]">
                <form onSubmit={handleSendMessage} className="flex gap-3">
                  <Input.TextArea
                    value={inputValue}
                    onChange={e => setInputValue(e.target.value)}
                    placeholder="Message AI Planner... (Shift+Enter for new line)"
                    rows={1}
                    autoSize={{ minRows: 1, maxRows: 6 }}
                    className="flex-1"
                    onKeyDown={e => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSendMessage(e);
                      }
                    }}
                    disabled={isSending}
                  />
                  <Button
                    type="primary"
                    htmlType="submit"
                    icon={<SendOutlined />}
                    loading={isSending}
                    disabled={!inputValue.trim() || isSending}
                    style={{ height: 'auto', alignSelf: 'flex-end', marginBottom: 8 }}
                  >
                    Send
                  </Button>
                </form>
                <p className="text-xs text-[var(--color-text-tertiary)] text-center mt-2">
                  Press Enter to send, Shift+Enter for new line
                </p>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <Card className="max-w-2xl text-center p-8" style={{ borderRadius: 16 }}>
                <RobotOutlined className="text-6xl text-primary-500 mb-4" />
                <h2 className="text-2xl font-bold text-[var(--color-text-primary)] mb-2">Welcome to AI Planner</h2>
                <p className="text-[var(--color-text-secondary)] mb-6">
                  Start a conversation to brainstorm, plan your week, organize events, or get help with any life management task.
                </p>
                <Button type="primary" size="large" icon={<PlusOutlined />} onClick={() => setShowNewConversation(true)}>
                  Start New Conversation
                </Button>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ message, index }: { message: any; index: number }) {
  const isUser = message.role === 'USER';
  const isAssistant = message.role === 'ASSISTANT';

  return (
    <div className={clsx('flex gap-3 animate-in', isUser && 'justify-end')}>
      {!isUser && (
        <Avatar size={32} icon={<RobotOutlined />} style={{ background: 'var(--color-primary-bg)', color: 'var(--color-primary-text)', flexShrink: 0 }} />
      )}

      <div className={clsx('max-w-[80%]', isUser ? 'order-2' : 'order-1')}>
        <div
          className={clsx(
            'rounded-2xl p-4',
            isUser
              ? 'bg-primary-500 text-white rounded-br-sm'
              : 'bg-[var(--color-bg-tertiary)] text-[var(--color-text-primary)] rounded-bl-sm'
          )}
        >
          <Paragraph className="whitespace-pre-wrap m-0">{message.content}</Paragraph>
        </div>
        <div className={clsx('text-xs mt-1 px-1', isUser ? 'text-right text-primary-400' : 'text-[var(--color-text-tertiary)]')}>
          {formatRelativeTime(message.createdAt)}
        </div>
      </div>

      {isUser && (
        <Avatar size={32} icon={<UserOutlined />} style={{ background: 'var(--color-primary-bg)', color: 'var(--color-primary-text)', flexShrink: 0 }} />
      )}
    </div>
  );
}

function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

import { UserOutlined } from '@ant-design/icons';
import { PlusOutlined } from '@ant-design/icons';