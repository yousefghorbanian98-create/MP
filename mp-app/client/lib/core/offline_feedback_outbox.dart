/// Android-only durable outbox for structured set feedback (M86/M87).
///
/// The native side owns the private SQLite database. This Dart layer validates
/// the narrow payload, binds every row to the active member, and acknowledges
/// writes only after the server returns an explicit per-item result.
library;

import 'dart:math';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'api_client.dart';

/// Fixed-width UTC text so SQLite lexical ordering matches time ordering.
String formatOfflineTimestamp(DateTime value) {
  final utc = value.toUtc();
  String two(int number) => number.toString().padLeft(2, '0');
  final fraction = (utc.millisecond * 1000 + utc.microsecond).toString().padLeft(6, '0');
  return '${utc.year.toString().padLeft(4, '0')}-${two(utc.month)}-${two(utc.day)}T${two(utc.hour)}:${two(utc.minute)}:${two(utc.second)}.${fraction}Z';
}

enum OfflineFeedbackStatus { pending, retry, conflict, failed, synced }

class OfflineFeedbackQueueItem {
  const OfflineFeedbackQueueItem({
    required this.id,
    required this.ownerMemberId,
    required this.clientId,
    required this.deviceId,
    required this.programId,
    required this.movementId,
    required this.weight,
    required this.targetReps,
    required this.repsDone,
    required this.rir,
    required this.createdAt,
    required this.updatedAt,
    required this.status,
    required this.attempts,
    required this.nextAttemptAt,
    required this.lastErrorCode,
    required this.syncedAt,
  });

  final int id;
  final int ownerMemberId;
  final String clientId;
  final String deviceId;
  final int? programId;
  final String movementId;
  final double weight;
  final int targetReps;
  final int repsDone;
  final double? rir;
  final String createdAt;
  final String updatedAt;
  final OfflineFeedbackStatus status;
  final int attempts;
  final String? nextAttemptAt;
  final String? lastErrorCode;
  final String? syncedAt;

  String get syncKey => '$deviceId:$clientId';

  /// Only the documented server allowlist is sent. Local owner, status, retry
  /// data, raw errors, soreness, notes, and credentials never leave this device.
  Map<String, Object?> toSyncItem() => {
        'client_id': clientId,
        'device_id': deviceId,
        'program_id': programId,
        'updated_at': updatedAt,
        'movement_id': movementId,
        'weight': weight,
        'target_reps': targetReps,
        'reps_done': repsDone,
        'rir': rir,
      };

  factory OfflineFeedbackQueueItem.fromMap(Map<Object?, Object?> raw) {
    final id = raw['id'];
    final ownerId = raw['owner_member_id'];
    final clientId = raw['client_id'];
    final deviceId = raw['device_id'];
    final movementId = raw['movement_id'];
    final weight = raw['weight'];
    final targetReps = raw['target_reps'];
    final repsDone = raw['reps_done'];
    final createdAt = raw['created_at'];
    final updatedAt = raw['updated_at'];
    final status = raw['status'];
    final attempts = raw['attempts'];
    if (id is! num || ownerId is! num || clientId is! String || deviceId is! String ||
        movementId is! String || weight is! num || targetReps is! num || repsDone is! num ||
        createdAt is! String || updatedAt is! String || status is! String || attempts is! num) {
      throw const FormatException('Offline feedback record is invalid');
    }
    final parsedStatus = OfflineFeedbackStatus.values.where((value) => value.name == status);
    if (parsedStatus.isEmpty) throw const FormatException('Offline feedback status is invalid');
    final programId = raw['program_id'];
    final rir = raw['rir'];
    final nextAttemptAt = raw['next_attempt_at'];
    final lastErrorCode = raw['last_error_code'];
    final syncedAt = raw['synced_at'];
    if ((programId != null && programId is! num) || (rir != null && rir is! num) ||
        (nextAttemptAt != null && nextAttemptAt is! String) ||
        (lastErrorCode != null && lastErrorCode is! String) ||
        (syncedAt != null && syncedAt is! String)) {
      throw const FormatException('Offline feedback metadata is invalid');
    }
    return OfflineFeedbackQueueItem(
      id: id.toInt(),
      ownerMemberId: ownerId.toInt(),
      clientId: clientId,
      deviceId: deviceId,
      programId: (programId as num?)?.toInt(),
      movementId: movementId,
      weight: weight.toDouble(),
      targetReps: targetReps.toInt(),
      repsDone: repsDone.toInt(),
      rir: (rir as num?)?.toDouble(),
      createdAt: createdAt,
      updatedAt: updatedAt,
      status: parsedStatus.first,
      attempts: attempts.toInt(),
      nextAttemptAt: nextAttemptAt as String?,
      lastErrorCode: lastErrorCode as String?,
      syncedAt: syncedAt as String?,
    );
  }
}

abstract interface class OfflineFeedbackLocalStore {
  bool get isSupported;
  Future<bool> hasInternetNetwork();
  Future<OfflineFeedbackQueueItem> enqueue(Map<String, Object?> record);
  Future<List<OfflineFeedbackQueueItem>> listForOwner(int ownerMemberId, {int limit = 100});
  Future<int> countUnresolved(int ownerMemberId);
  Future<List<OfflineFeedbackQueueItem>> listDue(
    int ownerMemberId, {
    required DateTime now,
    int limit = 100,
  });
  Future<void> markSynced(int ownerMemberId, int id, {required DateTime syncedAt});
  Future<void> markConflict(int ownerMemberId, int id, {required String errorCode});
  Future<void> markRetry(
    int ownerMemberId,
    int id, {
    required String errorCode,
    required DateTime nextAttemptAt,
    int maxAttempts = 5,
  });
  Future<void> manualRetry(int ownerMemberId, int id);
  Future<int> discardOwner(int ownerMemberId);
}

final offlineFeedbackStoreProvider = Provider<OfflineFeedbackLocalStore>(
  (ref) => MethodChannelOfflineFeedbackStore(),
);

class OfflineFeedbackStoreException implements Exception {
  const OfflineFeedbackStoreException(this.message);
  final String message;
  @override
  String toString() => message;
}

class MethodChannelOfflineFeedbackStore implements OfflineFeedbackLocalStore {
  MethodChannelOfflineFeedbackStore({MethodChannel? channel})
      : _channel = channel ?? const MethodChannel(_channelName);

  static const _channelName = 'ir.muscleparadise.mp_client/offline_feedback';
  static const _featureEnabled = bool.fromEnvironment(
    'MP_ANDROID_OFFLINE_FEEDBACK_ENABLED',
    defaultValue: false,
  );
  final MethodChannel _channel;

  @override
  bool get isSupported =>
      _featureEnabled && !kIsWeb && defaultTargetPlatform == TargetPlatform.android;

  void _requireSupported() {
    if (!isSupported) {
      throw const OfflineFeedbackStoreException('Offline feedback is available only on an explicitly enabled Android build.');
    }
  }

  Future<T> _invoke<T>(String method, [Map<String, Object?>? arguments]) async {
    _requireSupported();
    try {
      final result = await _channel.invokeMethod<T>(method, arguments);
      if (result == null) throw const FormatException('Native outbox returned no result');
      return result;
    } on PlatformException {
      throw const OfflineFeedbackStoreException('Android offline storage is unavailable.');
    } on MissingPluginException {
      throw const OfflineFeedbackStoreException('Android offline storage is unavailable.');
    }
  }

  @override
  Future<bool> hasInternetNetwork() async {
    if (!isSupported) return true;
    return _invoke<bool>('hasInternetNetwork');
  }

  @override
  Future<OfflineFeedbackQueueItem> enqueue(Map<String, Object?> record) async {
    final result = await _invoke<Map<dynamic, dynamic>>('enqueue', record);
    return OfflineFeedbackQueueItem.fromMap(result);
  }

  @override
  Future<List<OfflineFeedbackQueueItem>> listForOwner(int ownerMemberId, {int limit = 100}) async {
    final result = await _invoke<List<dynamic>>('listForOwner', {
      'owner_member_id': ownerMemberId,
      'limit': limit,
    });
    return result.map((item) => OfflineFeedbackQueueItem.fromMap(item as Map)).toList();
  }

  @override
  Future<int> countUnresolved(int ownerMemberId) =>
      _invoke<int>('countUnresolved', {'owner_member_id': ownerMemberId});

  @override
  Future<List<OfflineFeedbackQueueItem>> listDue(
    int ownerMemberId, {
    required DateTime now,
    int limit = 100,
  }) async {
    final result = await _invoke<List<dynamic>>('listDue', {
      'owner_member_id': ownerMemberId,
      'now': formatOfflineTimestamp(now),
      'limit': limit,
    });
    return result.map((item) => OfflineFeedbackQueueItem.fromMap(item as Map)).toList();
  }

  @override
  Future<void> markSynced(int ownerMemberId, int id, {required DateTime syncedAt}) async {
    await _invoke<bool>('markSynced', {
      'owner_member_id': ownerMemberId,
      'id': id,
      'synced_at': formatOfflineTimestamp(syncedAt),
    });
  }

  @override
  Future<void> markConflict(int ownerMemberId, int id, {required String errorCode}) async {
    await _invoke<bool>('markConflict', {
      'owner_member_id': ownerMemberId,
      'id': id,
      'error_code': errorCode,
    });
  }

  @override
  Future<void> markRetry(
    int ownerMemberId,
    int id, {
    required String errorCode,
    required DateTime nextAttemptAt,
    int maxAttempts = 5,
  }) async {
    await _invoke<bool>('markRetry', {
      'owner_member_id': ownerMemberId,
      'id': id,
      'error_code': errorCode,
      'next_attempt_at': formatOfflineTimestamp(nextAttemptAt),
      'max_attempts': maxAttempts,
    });
  }

  @override
  Future<void> manualRetry(int ownerMemberId, int id) async {
    await _invoke<bool>('manualRetry', {'owner_member_id': ownerMemberId, 'id': id});
  }

  @override
  Future<int> discardOwner(int ownerMemberId) =>
      _invoke<int>('discardOwner', {'owner_member_id': ownerMemberId});
}

class OfflineFeedbackOutbox {
  OfflineFeedbackOutbox(
    this.store, {
    DateTime Function()? clock,
    String Function()? idGenerator,
  })  : _clock = clock ?? DateTime.now,
        _idGenerator = idGenerator ?? _secureId;

  final OfflineFeedbackLocalStore store;
  final DateTime Function() _clock;
  final String Function() _idGenerator;
  Future<String>? _deviceIdFuture;

  static final Random _random = Random.secure();
  static const _devicePreferenceKey = 'mp_offline_feedback_device_id';

  static String _secureId() => List<int>.generate(16, (_) => _random.nextInt(256))
      .map((byte) => byte.toRadixString(16).padLeft(2, '0'))
      .join();

  Future<String> _deviceId() => _deviceIdFuture ??= () async {
        final preferences = await SharedPreferences.getInstance();
        final saved = preferences.getString(_devicePreferenceKey);
        if (saved != null && RegExp(r'^[a-f0-9]{32}$').hasMatch(saved)) return saved;
        final generated = _idGenerator();
        if (!RegExp(r'^[a-f0-9]{32}$').hasMatch(generated)) {
          throw const OfflineFeedbackStoreException('A stable local device ID could not be created.');
        }
        final stored = await preferences.setString(_devicePreferenceKey, generated);
        if (!stored) throw const OfflineFeedbackStoreException('A stable local device ID could not be saved.');
        return generated;
      }();

  Future<OfflineFeedbackQueueItem> enqueue({
    required int ownerMemberId,
    required int? programId,
    required String movementId,
    required double weight,
    required int targetReps,
    required int repsDone,
    required double? rir,
  }) async {
    if (!store.isSupported) {
      throw const OfflineFeedbackStoreException('Offline feedback is available only on an explicitly enabled Android build.');
    }
    if (ownerMemberId <= 0 ||
        (programId != null && programId <= 0) ||
        movementId.trim().isEmpty || movementId.length > 60 ||
        !weight.isFinite || weight < 0 || weight > 500 ||
        targetReps < 0 || targetReps > 200 ||
        repsDone < 0 || repsDone > 200 ||
        (rir != null && (!rir.isFinite || rir < 0 || rir > 10))) {
      throw const FormatException('Feedback is outside the offline allowlist or range.');
    }
    final now = _clock().toUtc();
    final timestamp = formatOfflineTimestamp(now);
    final deviceId = await _deviceId();
    final clientId = _idGenerator();
    if (!RegExp(r'^[a-f0-9]{32}$').hasMatch(clientId)) {
      throw const OfflineFeedbackStoreException('A stable local item ID could not be created.');
    }
    return store.enqueue({
      'owner_member_id': ownerMemberId,
      'client_id': clientId,
      'device_id': deviceId,
      'program_id': programId,
      'movement_id': movementId.trim(),
      'weight': weight,
      'target_reps': targetReps,
      'reps_done': repsDone,
      'rir': rir,
      'created_at': timestamp,
      'updated_at': timestamp,
    });
  }
}

class OfflineFeedbackSyncResult {
  const OfflineFeedbackSyncResult({
    this.synced = 0,
    this.conflicts = 0,
    this.retrying = 0,
    this.failed = 0,
    this.authRequired = false,
    this.notDue = false,
    this.invalidResponse = false,
    this.ownerMismatch = false,
  });

  final int synced;
  final int conflicts;
  final int retrying;
  final int failed;
  final bool authRequired;
  final bool notDue;
  final bool invalidResponse;
  final bool ownerMismatch;

  String get message {
    if (ownerMismatch) return 'صف متعلق به حساب دیگری است و ارسال نشد.';
    if (authRequired) return 'برای همگام‌سازی، با همان حساب دوباره وارد شوید.';
    if (invalidResponse) return 'پاسخ سرور قابل تأیید نبود؛ داده در صف تعارض نگه داشته شد.';
    if (notDue) return 'زمان تلاش بعدی هنوز نرسیده است.';
    if (conflicts > 0) return '$synced مورد همگام شد؛ $conflicts مورد برای بررسی نگه داشته شد.';
    if (failed > 0) return '$synced مورد همگام شد؛ $failed مورد پس از تلاش‌های خودکار ناموفق ماند.';
    if (retrying > 0) return '$synced مورد همگام شد؛ تلاش دوباره با فاصلهٔ زمانی انجام می‌شود.';
    if (synced == 0) return 'موردی برای همگام‌سازیِ اکنون آماده نیست.';
    return '$synced مورد پس از تأیید سرور همگام شد.';
  }
}

class OfflineFeedbackSyncService {
  OfflineFeedbackSyncService(this.store, {DateTime Function()? clock})
      : _clock = clock ?? DateTime.now;

  final OfflineFeedbackLocalStore store;
  final DateTime Function() _clock;
  static const _maxAttempts = 5;
  static const _maxBackoff = Duration(hours: 6);

  Future<OfflineFeedbackSyncResult> syncOwner({
    required int currentMemberId,
    required int ownerMemberId,
    required ApiClient api,
  }) async {
    if (!store.isSupported) {
      throw const OfflineFeedbackStoreException('Offline feedback is available only on an explicitly enabled Android build.');
    }
    if (currentMemberId <= 0 || currentMemberId != ownerMemberId) {
      return const OfflineFeedbackSyncResult(ownerMismatch: true);
    }
    if (api.accessToken == null || api.accessToken!.isEmpty) {
      return const OfflineFeedbackSyncResult(authRequired: true);
    }
    final now = _clock().toUtc();
    final rows = await store.listDue(ownerMemberId, now: now, limit: 100);
    if (rows.isEmpty) {
      final all = await store.listForOwner(ownerMemberId, limit: 500);
      final waiting = all.any((row) => row.status == OfflineFeedbackStatus.retry);
      return OfflineFeedbackSyncResult(notDue: waiting);
    }
    if (rows.any((row) => row.ownerMemberId != ownerMemberId ||
        (row.status != OfflineFeedbackStatus.pending && row.status != OfflineFeedbackStatus.retry))) {
      return const OfflineFeedbackSyncResult(ownerMismatch: true);
    }

    dynamic response;
    try {
      response = await api.post('/programs/sync/set-feedback', {
        'member_id': ownerMemberId,
        'items': rows.map((row) => row.toSyncItem()).toList(),
      });
    } on ApiException catch (error) {
      if (error.statusCode == 401 || error.statusCode == 403) {
        return const OfflineFeedbackSyncResult(authRequired: true);
      }
      if (error.statusCode != null && error.statusCode! < 500) {
        await _markAllConflict(rows, ownerMemberId, 'server_rejected');
        return OfflineFeedbackSyncResult(conflicts: rows.length);
      }
      return _retryAll(rows, ownerMemberId, now,
          errorCode: error.statusCode == null ? 'network' : 'server_5xx');
    } catch (_) {
      return _retryAll(rows, ownerMemberId, now, errorCode: 'network');
    }

    final parsed = _parseResponse(response, rows, ownerMemberId);
    if (parsed == null) {
      await _markAllConflict(rows, ownerMemberId, 'invalid_response');
      return OfflineFeedbackSyncResult(conflicts: rows.length, invalidResponse: true);
    }

    var synced = 0;
    var conflicts = 0;
    final ackedDuplicates = parsed.unchangedKeys;
    for (final row in rows) {
      final result = parsed.results[row.syncKey]!;
      final action = result['action'];
      final winner = result['winner'];
      final duplicateAck = ackedDuplicates.contains(row.syncKey) &&
          action == 'conflict_resolved' && winner == 'server';
      final clientAck = (action == 'accept' || action == 'conflict_resolved') && winner == 'client';
      if (duplicateAck || clientAck) {
        await store.markSynced(ownerMemberId, row.id, syncedAt: _clock().toUtc());
        synced++;
      } else if (action == 'reject_stale') {
        await store.markConflict(ownerMemberId, row.id, errorCode: 'server_stale');
        conflicts++;
      } else if (action == 'reject_clock_skew') {
        await store.markConflict(ownerMemberId, row.id, errorCode: 'clock_skew');
        conflicts++;
      } else {
        await store.markConflict(ownerMemberId, row.id, errorCode: 'invalid_response');
        conflicts++;
      }
    }
    return OfflineFeedbackSyncResult(synced: synced, conflicts: conflicts);
  }

  Future<void> retryFailed(int ownerMemberId) async {
    final rows = await store.listForOwner(ownerMemberId, limit: 500);
    for (final row in rows) {
      if (row.ownerMemberId == ownerMemberId && row.status == OfflineFeedbackStatus.failed) {
        await store.manualRetry(ownerMemberId, row.id);
      }
    }
  }

  Future<OfflineFeedbackSyncResult> _retryAll(
    List<OfflineFeedbackQueueItem> rows,
    int ownerMemberId,
    DateTime now, {
    required String errorCode,
  }) async {
    var retrying = 0;
    var failed = 0;
    for (final row in rows) {
      final exponent = row.attempts.clamp(0, 10).toInt();
      final seconds = min(_maxBackoff.inSeconds, 30 * (1 << exponent));
      await store.markRetry(
        ownerMemberId,
        row.id,
        errorCode: errorCode,
        nextAttemptAt: now.add(Duration(seconds: seconds)),
        maxAttempts: _maxAttempts,
      );
      if (row.attempts + 1 >= _maxAttempts) {
        failed++;
      } else {
        retrying++;
      }
    }
    return OfflineFeedbackSyncResult(retrying: retrying, failed: failed);
  }

  Future<void> _markAllConflict(
    List<OfflineFeedbackQueueItem> rows,
    int ownerMemberId,
    String errorCode,
  ) async {
    for (final row in rows) {
      await store.markConflict(ownerMemberId, row.id, errorCode: errorCode);
    }
  }

  _ParsedSyncResponse? _parseResponse(
    dynamic raw,
    List<OfflineFeedbackQueueItem> rows,
    int expectedOwnerMemberId,
  ) {
    if (raw is! Map || raw['member_id'] is! num ||
        (raw['member_id'] as num).toInt() != expectedOwnerMemberId ||
        raw['results'] is! List || raw['unchanged_keys'] is! List ||
        raw['counts'] is! Map || raw['counts']['received'] is! num ||
        (raw['counts']['received'] as num).toInt() != rows.length) {
      return null;
    }
    final unchanged = <String>{};
    for (final key in raw['unchanged_keys'] as List) {
      if (key is! String) return null;
      unchanged.add(key);
    }
    final results = <String, Map<String, dynamic>>{};
    for (final item in raw['results'] as List) {
      if (item is! Map || item['entity_key'] is! String || item['action'] is! String) return null;
      final key = item['entity_key'] as String;
      if (results.containsKey(key)) return null;
      results[key] = Map<String, dynamic>.from(item);
    }
    final expected = rows.map((row) => row.syncKey).toSet();
    if (results.length != rows.length || !results.keys.toSet().containsAll(expected) ||
        !expected.containsAll(results.keys) || !expected.containsAll(unchanged)) {
      return null;
    }
    for (final result in results.values) {
      if (result['winner'] != null && result['winner'] is! String) return null;
    }
    return _ParsedSyncResponse(results: results, unchangedKeys: unchanged);
  }
}

class _ParsedSyncResponse {
  const _ParsedSyncResponse({required this.results, required this.unchangedKeys});
  final Map<String, Map<String, dynamic>> results;
  final Set<String> unchangedKeys;
}
