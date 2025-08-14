import { route, parseBody, validateItem } from './handler';

describe('route()', () => {
  test('health', () => {
    expect(route('/api/health', 'GET')).toBe('HEALTH');
  });
  test('list', () => {
    expect(route('/api/items', 'GET')).toBe('LIST');
  });
  test('create', () => {
    expect(route('/api/items', 'POST')).toBe('CREATE');
  });
  test('not found', () => {
    expect(route('/foo', 'GET')).toBe('NOT_FOUND');
  });
});

describe('parseBody()', () => {
  test('parses valid json', () => {
    expect(parseBody('{\"a\":1}')).toEqual({ a: 1 });
  });
  test('handles null', () => {
    expect(parseBody(null)).toEqual({});
  });
  test('handles invalid json', () => {
    expect(parseBody('{oops}')).toEqual({});
  });
});

describe('validateItem()', () => {
  test('requires id and title', () => {
    expect(validateItem({})).toEqual({ ok: false, msg: 'id and title required' });
  });
  test('accepts valid item', () => {
    expect(validateItem({ id: '1', title: 'x' })).toEqual({ ok: true });
  });
});
