/// M87 — allowlist, owner binding, idempotent ACK, retry and conflict handling.
library;

import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:mp_client/core/api_client.dart';
import 'package:mp_client/core/offline_feedback_outbox.dart';
import 'package:mp_client/core/session.dart';
import 'package:mp_client/features/feedback/feedback_providers.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _device = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa';
final _now = DateTime.utc(2026, 11, 17, 12);

OfflineFeedbackQueueItem _item({
  int id = 1,
  int owner = 3,
  OfflineFeedbackStatus status = OfflineFeedbackStatus.pending,
  int attempts = 0,
  String? nextAttemptAt,
}) => OfflineFeedbackQueueItem(
      id: id,
      ownerMemberId: owner,
      clientId: 'c$id',
      deviceId: _device,
      programId: 12,
      movementId: 'squat',
      weight: 80,
      targetReps: 10,
      repsDone: 9,
      rir: 2,
      createdAt: _now.toIso8601String(),
      updatedAt: _now.toIso8601String(),
      status: status,
      attempts: attempts,
      nextAttemptAt: nextAttemptAt,
      lastErrorCode: null,
      syncedAt: null,
    );

class _MemoryStore implements OfflineFeedbackLocalStore {
  _MemoryStore({this.network = true});
  bool network;
  int _nextId = 1;
  final rows = <OfflineFeedbackQueueItem>[];
  Map<String, Object?>? lastInserted;

  @override
  bool get isSupported => true;

  @override
  Future<bool> hasInternetNetwork() async => network;

  @override
  Future<OfflineFeedbackQueueItem> enqueue(Map<String, Object?> record) async {
    lastInserted = Map<String, Object?>.from(record);
    final item = OfflineFeedbackQueueItem.fromMap({
      ...record,
      'id': _nextId++,
      'status': 'pending',
      'attempts': 0,
      'next_attempt_at': null,
      'last_error_code': null,
      'synced_at': null,
    });
    rows.add(item);
    return item;
  }

  @override
  Future<List<OfflineFeedbackQueueItem>> listForOwner(int ownerMemberId, {int limit = 100}) async =>
      rows.where((row) => row.ownerMemberId == ownerMemberId).take(limit).toList();

  @override
  Future<int> countUnresolved(int ownerMemberId) async => rows
      .where((row) => row.ownerMemberId == ownerMemberId && row.status != OfflineFeedbackStatus.synced)
      .length;

  @override
  Future<List<OfflineFeedbackQueueItem>> listDue(
    int ownerMemberId, {
    required DateTime now,
    int limit = 100,
  }) async => rows.where((row) {
        if (row.ownerMemberId != ownerMemberId) return false;
        if (row.status == OfflineFeedbackStatus.pending) return true;
        if (row.status != OfflineFeedbackStatus.retry) return false;
        final due = row.nextAttemptAt == null ? null : DateTime.tryParse(row.nextAttemptAt!);
        return due == null || !due.isAfter(now);
      }).take(limit).toList();

  @override
  Future<void> markSynced(int ownerMemberId, int id, {required DateTime syncedAt}) async {
    _replace(ownerMemberId, id, (row) => _copy(row, status: OfflineFeedbackStatus.synced, syncedAt: syncedAt.toIso8601String()));
  }

  @override
  Future<void> markConflict(int ownerMemberId, int id, {required String errorCode}) async {
    _replace(ownerMemberId, id, (row) => _copy(row, status: OfflineFeedbackStatus.conflict, lastErrorCode: errorCode));
  }

  @override
  Future<void> markRetry(
    int ownerMemberId,
    int id, {
    required String errorCode,
    required DateTime nextAttemptAt,
    int maxAttempts = 5,
  }) async {
    _replace(ownerMemberId, id, (row) {
      final attempts = row.attempts + 1;
      return _copy(
        row,
        status: attempts >= maxAttempts ? OfflineFeedbackStatus.failed : OfflineFeedbackStatus.retry,
        attempts: attempts,
        nextAttemptAt: attempts >= maxAttempts ? null : nextAttemptAt.toIso8601String(),
        lastErrorCode: errorCode,
      );
    });
  }

  @override
  Future<void> manualRetry(int ownerMemberId, int id) async {
    _replace(ownerMemberId, id, (row) => _copy(
          row,
          status: OfflineFeedbackStatus.pending,
          attempts: 0,
          nextAttemptAt: null,
          lastErrorCode: null,
        ));
  }

  @override
  Future<int> discardOwner(int ownerMemberId) async {
    final before = rows.length;
    rows.removeWhere((row) => row.ownerMemberId == ownerMemberId);
    return before - rows.length;
  }

  void _replace(int ownerMemberId, int id, OfflineFeedbackQueueItem Function(OfflineFeedbackQueueItem) update) {
    final index = rows.indexWhere((row) => row.ownerMemberId == ownerMemberId && row.id == id);
    if (index < 0) throw StateError('owner-scoped row not found');
    rows[index] = update(rows[index]);
  }

  OfflineFeedbackQueueItem _copy(
    OfflineFeedbackQueueItem row, {
    OfflineFeedbackStatus? status,
    int? attempts,
    String? nextAttemptAt,
    String? lastErrorCode,
    String? syncedAt,
  }) => OfflineFeedbackQueueItem(
        id: row.id,
        ownerMemberId: row.ownerMemberId,
        clientId: row.clientId,
        deviceId: row.deviceId,
        programId: row.programId,
        movementId: row.movementId,
        weight: row.weight,
        targetReps: row.targetReps,
        repsDone: row.repsDone,
        rir: row.rir,
        createdAt: row.createdAt,
        updatedAt: row.updatedAt,
        status: status ?? row.status,
        attempts: attempts ?? row.attempts,
        nextAttemptAt: nextAttemptAt,
        lastErrorCode: lastErrorCode,
        syncedAt: syncedAt ?? row.syncedAt,
      );
}

class _FakeHttpClient extends http.BaseClient {
  _FakeHttpClient(this.statusCode, this.payload);
  final int statusCode;
  final Object payload;
  final calls = <http.Request>[];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final original = request as http.Request;
    calls.add(original);
    final bytes = utf8.encode(jsonEncode(payload));
    return http.StreamedResponse(
      Stream.value(bytes),
      statusCode,
      contentLength: bytes.length,
      headers: {'content-type': 'application/json'},
      request: request,
    );
  }
}

Map<String, dynamic> _response({
  required String action,
  required String? winner,
  List<String> unchanged = const [],
}) => {
      'member_id': 3,
      'results': [
        {
          'entity_key': '$_device:c1',
          'action': action,
          'winner': winner,
        }
      ],
      'counts': {'received': 1, 'applied': 1, 'rejected': 0},
      'applied_keys': <String>[],
      'unchanged_keys': unchanged,
    };

ApiClient _api(_FakeHttpClient client) => ApiClient(
      httpClient: client,
      baseUrl: 'https://api.example.test/api/v1',
    )..accessToken = 'test-access-token';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() => SharedPreferences.setMockInitialValues({}));

  test('stored timestamps use fixed-width UTC text for stable FIFO/backoff ordering', () {
    final early = formatOfflineTimestamp(DateTime.utc(2026, 11, 17, 12, 0, 0, 0, 100));
    final late = formatOfflineTimestamp(DateTime.utc(2026, 11, 17, 12, 0, 0, 100, 0));
    expect(early, '2026-11-17T12:00:00.000100Z');
    expect(late, '2026-11-17T12:00:00.100000Z');
    expect(early.compareTo(late), lessThan(0));
  });

  test('outbox persists only the allowlisted fields and keeps a stable device ID', () async {
    final store = _MemoryStore();
    final ids = <String>[
      'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
      'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
      'cccccccccccccccccccccccccccccccc',
    ].iterator;
    final outbox = OfflineFeedbackOutbox(
      store,
      clock: () => _now,
      idGenerator: () => ids.moveNext() ? ids.current : 'dddddddddddddddddddddddddddddddd',
    );

    final first = await outbox.enqueue(
      ownerMemberId: 3,
      programId: 12,
      movementId: 'squat',
      weight: 80,
      targetReps: 10,
      repsDone: 9,
      rir: 2,
    );
    await outbox.enqueue(
      ownerMemberId: 3,
      programId: 12,
      movementId: 'press',
      weight: 20,
      targetReps: 8,
      repsDone: 8,
      rir: null,
    );

    expect(first.ownerMemberId, 3);
    expect(store.rows[0].deviceId, store.rows[1].deviceId);
    expect(store.rows[0].clientId, isNot(store.rows[1].clientId));
    expect(store.lastInserted!.keys.toSet(), {
      'owner_member_id', 'client_id', 'device_id', 'program_id', 'movement_id',
      'weight', 'target_reps', 'reps_done', 'rir', 'created_at', 'updated_at',
    });
    expect(store.lastInserted!.containsKey('soreness'), isFalse);
    expect(store.lastInserted!.containsKey('notes'), isFalse);
    expect(store.lastInserted!.containsKey('access_token'), isFalse);
  });

  test('network availability provider reports offline status', () async {
    final store = _MemoryStore(network: false);
    final container = ProviderContainer(overrides: [
      offlineFeedbackStoreProvider.overrideWithValue(store),
    ]);
    addTearDown(container.dispose);

    final isOnline =
        await container.read(offlineFeedbackNetworkAvailableProvider)();

    expect(isOnline, isFalse);
  });

  test('enqueue provider binds the session owner and drops soreness and free-form fields', () async {
    final store = _MemoryStore();
    final container = ProviderContainer(overrides: [
      offlineFeedbackStoreProvider.overrideWithValue(store),
      authProvider.overrideWith((ref) => AuthController.test(
            const AuthState(accessToken: 'token', memberId: 3),
          )),
    ]);
    addTearDown(container.dispose);

    await container.read(enqueueOfflineFeedbackProvider)(
      programId: 12,
      entries: [
        {
          'movement_id': 'squat',
          'weight': 80.0,
          'target_reps': 10,
          'reps_done': 9,
          'rir': 2.0,
          'soreness': 8,
          'notes': 'free-form must not enter the outbox',
          'member_id': 999,
        },
      ],
    );

    expect(store.lastInserted!['owner_member_id'], 3);
    expect(store.lastInserted!.containsKey('soreness'), isFalse);
    expect(store.lastInserted!.containsKey('notes'), isFalse);
    expect(store.lastInserted!.containsKey('member_id'), isFalse);
  });

  test('logout needs an explicit keep-or-discard choice for unresolved rows', () async {
    final store = _MemoryStore()..rows.add(_item());
    final auth = AuthController.test(
      const AuthState(accessToken: 'token', memberId: 3),
      offlineStore: store,
    );

    await expectLater(auth.logout(), throwsA(isA<PendingOfflineFeedbackException>()));
    expect(auth.state.loggedIn, isTrue);
    expect(store.rows.single.status, OfflineFeedbackStatus.pending);

    await auth.logout(keepPendingFeedback: true);
    expect(auth.state.loggedIn, isFalse);
    expect(store.rows.single.ownerMemberId, 3);
    expect(store.rows.single.status, OfflineFeedbackStatus.pending);
  });

  test('explicit discard removes only the selected owner rows', () async {
    final store = _MemoryStore()
      ..rows.add(_item(owner: 3))
      ..rows.add(_item(id: 2, owner: 4));
    final auth = AuthController.test(
      const AuthState(accessToken: 'token', memberId: 3),
      offlineStore: store,
    );

    await auth.logout(discardPendingFeedback: true);

    expect(store.rows.map((row) => row.ownerMemberId), [4]);
    expect(auth.state.loggedIn, isFalse);
  });

  test('same-device duplicate with explicit unchanged_keys is acknowledged', () async {
    final store = _MemoryStore()..rows.add(_item());
    final httpClient = _FakeHttpClient(
      200,
      _response(
        action: 'conflict_resolved',
        winner: 'server',
        unchanged: ['$_device:c1'],
      ),
    );
    final service = OfflineFeedbackSyncService(store, clock: () => _now.add(const Duration(seconds: 1)));

    final result = await service.syncOwner(currentMemberId: 3, ownerMemberId: 3, api: _api(httpClient));

    expect(result.synced, 1);
    expect(result.conflicts, 0);
    expect(store.rows.single.status, OfflineFeedbackStatus.synced);
    final body = jsonDecode(httpClient.calls.single.body) as Map<String, dynamic>;
    expect(body['member_id'], 3);
    expect((body['items'] as List).single, {
      'client_id': 'c1',
      'device_id': _device,
      'program_id': 12,
      'updated_at': _now.toIso8601String(),
      'movement_id': 'squat',
      'weight': 80.0,
      'target_reps': 10,
      'reps_done': 9,
      'rir': 2.0,
    });
  });

  test('stale server winner is retained as a visible conflict', () async {
    final store = _MemoryStore()..rows.add(_item());
    final httpClient = _FakeHttpClient(200, _response(action: 'reject_stale', winner: 'server'));
    final service = OfflineFeedbackSyncService(store, clock: () => _now);

    final result = await service.syncOwner(currentMemberId: 3, ownerMemberId: 3, api: _api(httpClient));

    expect(result.conflicts, 1);
    expect(store.rows.single.status, OfflineFeedbackStatus.conflict);
    expect(store.rows.single.lastErrorCode, 'server_stale');
  });

  test('HTTP 5xx stores only a redacted retry code; auth failure stops without sending as another owner', () async {
    final store = _MemoryStore()..rows.add(_item());
    final service = OfflineFeedbackSyncService(store, clock: () => _now);
    final failedApi = _api(_FakeHttpClient(503, {'detail': 'synthetic private response'}));
    final retry = await service.syncOwner(currentMemberId: 3, ownerMemberId: 3, api: failedApi);
    expect(retry.retrying, 1);
    expect(store.rows.single.status, OfflineFeedbackStatus.retry);
    expect(store.rows.single.lastErrorCode, 'server_5xx');
    expect(store.rows.single.lastErrorCode, isNot(contains('synthetic')));

    await store.manualRetry(3, 1);
    final forbiddenClient = _FakeHttpClient(403, {'detail': 'forbidden'});
    final auth = await service.syncOwner(currentMemberId: 3, ownerMemberId: 3, api: _api(forbiddenClient));
    expect(auth.authRequired, isTrue);
    expect(forbiddenClient.calls, hasLength(1));

    final other = _FakeHttpClient(200, _response(action: 'accept', winner: 'client'));
    final mismatch = await service.syncOwner(currentMemberId: 3, ownerMemberId: 4, api: _api(other));
    expect(mismatch.ownerMismatch, isTrue);
    expect(other.calls, isEmpty);
  });

  test('a response claiming another owner never acknowledges this owner’s write', () async {
    final store = _MemoryStore()..rows.add(_item());
    final payload = _response(action: 'accept', winner: 'client')..['member_id'] = 4;
    final api = _api(_FakeHttpClient(200, payload));
    final service = OfflineFeedbackSyncService(store, clock: () => _now);

    final result = await service.syncOwner(currentMemberId: 3, ownerMemberId: 3, api: api);

    expect(result.invalidResponse, isTrue);
    expect(store.rows.single.status, OfflineFeedbackStatus.conflict);
    expect(store.rows.single.lastErrorCode, 'invalid_response');
  });

  test('an incomplete response never silently deletes or acknowledges a write', () async {
    final store = _MemoryStore()..rows.add(_item());
    final api = _api(_FakeHttpClient(200, {'results': [], 'counts': {'received': 0}}));
    final service = OfflineFeedbackSyncService(store, clock: () => _now);

    final result = await service.syncOwner(currentMemberId: 3, ownerMemberId: 3, api: api);

    expect(result.invalidResponse, isTrue);
    expect(store.rows.single.status, OfflineFeedbackStatus.conflict);
    expect(store.rows.single.lastErrorCode, 'invalid_response');
  });
}
