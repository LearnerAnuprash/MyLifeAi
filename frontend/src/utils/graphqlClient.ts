import { useAuthStore } from '@/store/authStore';

const GRAPHQL_ENDPOINT = import.meta.env.VITE_API_URL || 'http://localhost:8000/graphql';

interface GraphQLResponse<T> {
  data?: T;
  errors?: Array<{ message: string; extensions?: { code: string } }>;
}

export interface GraphQLRequestAuth {
  accessToken?: string;
  refreshToken?: string;
}

export async function graphqlRequest<T>(
  query: string,
  variables: object = {},
  auth: GraphQLRequestAuth | string = {}
): Promise<GraphQLResponse<T>> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  const { accessToken, refreshToken } =
    typeof auth === 'string' ? { accessToken: auth, refreshToken: undefined } : auth;

  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  if (refreshToken) {
    headers['X-Refresh-Token'] = refreshToken;
  }

  const response = await fetch(GRAPHQL_ENDPOINT, {
    method: 'POST',
    headers,
    body: JSON.stringify({ query, variables }),
  });

  if (!response.ok) {
    throw new Error(`GraphQL request failed: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

export async function graphqlRequestWithAuth<T>(
  query: string,
  variables: object = {}
): Promise<GraphQLResponse<T>> {
  const { accessToken } = useAuthStore.getState();
  return graphqlRequest<T>(query, variables, { accessToken: accessToken || undefined });
}

// GraphQL WebSocket subscription client (for future use)
export class GraphQLWSClient {
  private ws: WebSocket | null = null;
  private messageId = 0;
  private pendingRequests = new Map<number, { resolve: (value: any) => void; reject: (error: Error) => void }>();
  private subscriptions = new Map<string, (data: any) => void>();

  connect(token: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const wsUrl = GRAPHQL_ENDPOINT.replace('http', 'ws');
      this.ws = new WebSocket(`${wsUrl}?token=${token}`);

      this.ws.onopen = () => {
        // Send connection init
        this.send({ type: 'connection_init', payload: { Authorization: `Bearer ${token}` } });
        resolve();
      };

      this.ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        this.handleMessage(message);
      };

      this.ws.onerror = () => {
        reject(new Error('WebSocket connection failed'));
      };

      this.ws.onclose = () => {
        this.pendingRequests.forEach(({ reject }) => {
          reject(new Error('WebSocket connection closed'));
        });
        this.pendingRequests.clear();
      };
    });
  }

  private send(message: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  private handleMessage(message: any) {
    switch (message.type) {
      case 'connection_ack':
        break;
      case 'data':
        if (message.id && this.pendingRequests.has(message.id)) {
          const { resolve } = this.pendingRequests.get(message.id)!;
          this.pendingRequests.delete(message.id);
          resolve(message.payload);
        }
        if (message.payload?.data) {
          // Subscription data
          const subscriptionId = message.payload.data.subscriptionId;
          if (subscriptionId && this.subscriptions.has(subscriptionId)) {
            this.subscriptions.get(subscriptionId)!(message.payload.data);
          }
        }
        break;
      case 'error':
        if (message.id && this.pendingRequests.has(message.id)) {
          const { reject } = this.pendingRequests.get(message.id)!;
          this.pendingRequests.delete(message.id);
          reject(new Error(message.payload?.message || 'GraphQL error'));
        }
        break;
      case 'complete':
        if (message.id && this.subscriptions.has(message.id)) {
          this.subscriptions.delete(message.id);
        }
        break;
    }
  }

  subscribe(query: string, variables: Record<string, any>, callback: (data: any) => void): string {
    const id = `sub_${++this.messageId}`;
    this.subscriptions.set(id, callback);

    this.send({
      id,
      type: 'start',
      payload: { query, variables },
    });

    return id;
  }

  unsubscribe(id: string) {
    this.send({ id, type: 'stop' });
    this.subscriptions.delete(id);
  }

  disconnect() {
    this.ws?.close();
    this.ws = null;
  }
}