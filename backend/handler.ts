import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, ScanCommand, PutCommand } from '@aws-sdk/lib-dynamodb';

const client = new DynamoDBClient({});
const ddb = DynamoDBDocumentClient.from(client);
const TABLE_NAME = process.env.TABLE_NAME!;

function json(statusCode: number, body: any): APIGatewayProxyResult {
  return {
    statusCode,
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(body)
  };
}

export function route(path: string, method: string): string {
  if (path.endsWith('/health') && method === 'GET') return 'HEALTH';
  if (path.endsWith('/items') && method === 'GET') return 'LIST';
  if (path.endsWith('/items') && method === 'POST') return 'CREATE';
  return 'NOT_FOUND';
}

export function parseBody(body: string | null): any {
  if (!body) return {};
  try { return JSON.parse(body); } catch { return {}; }
}

export function validateItem(item: any): { ok: boolean; msg?: string } {
  if (!item || typeof item !== 'object') return { ok: false, msg: 'Invalid JSON' };
  if (!item.id || !item.title) return { ok: false, msg: 'id and title required' };
  return { ok: true };
}

export const handler = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
  const r = route(event.path, event.httpMethod);

  if (r === 'HEALTH') {
    return json(200, { ok: true });
  }

  if (r === 'LIST') {
    const data = await ddb.send(new ScanCommand({ TableName: TABLE_NAME, Limit: 50 }));
    return json(200, { items: data.Items ?? [] });
  }

  if (r === 'CREATE') {
    const body = parseBody(event.body);
    const v = validateItem(body);
    if (!v.ok) return json(400, { error: v.msg });
    await ddb.send(new PutCommand({ TableName: TABLE_NAME, Item: body }));
    return json(201, { saved: true, item: body });
  }

  return json(404, { error: 'Not found' });
};
