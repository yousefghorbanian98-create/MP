/// بازخورد ست‌به‌ست (G1 — M39) + outbox محدود و مالک‌محور (M87).
library;

export '../../core/offline_feedback_outbox.dart'
    show offlineFeedbackStoreProvider;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/offline_feedback_outbox.dart';
import '../../core/session.dart';

/// ارسال آنلاین بازخورد ست‌ها ← پیشنهاد جلسهٔ بعد (وزن/حجم + دلیل).
final submitSetFeedbackProvider =
    Provider<
      Future<Map<String, dynamic>?> Function(List<Map<String, dynamic>>)
    >((ref) {
      return (entries) async {
        final api = ref.read(apiClientProvider);
        final auth = ref.read(authProvider);
        final memberId = auth.memberId;
        if (memberId == null) return null;
        final r = await api.post('/programs/set-feedback', {
          'member_id': memberId,
          'entries': entries,
        });
        if (r is Map<String, dynamic>) return r;
        return null;
      };
    });

final offlineFeedbackOutboxProvider = Provider<OfflineFeedbackOutbox>(
  (ref) => OfflineFeedbackOutbox(ref.watch(offlineFeedbackStoreProvider)),
);

final offlineFeedbackSyncServiceProvider = Provider<OfflineFeedbackSyncService>(
  (ref) => OfflineFeedbackSyncService(ref.watch(offlineFeedbackStoreProvider)),
);

typedef EnqueueOfflineFeedback = Future<OfflineFeedbackQueueItem> Function({
  required int? programId,
  required List<Map<String, dynamic>> entries,
});

/// The member ID always comes from the current authenticated session; the
/// feedback widget cannot choose or override an owner.
final enqueueOfflineFeedbackProvider = Provider<EnqueueOfflineFeedback>((ref) {
  return ({required programId, required entries}) async {
    final ownerMemberId = ref.read(authProvider).memberId;
    if (ownerMemberId == null) {
      throw const OfflineFeedbackStoreException(
        'A signed-in member is required to queue feedback.',
      );
    }
    if (entries.length != 1) {
      throw const FormatException(
        'Only one structured set-feedback item can be queued at a time.',
      );
    }
    final entry = entries.single;
    final movementId = entry['movement_id'];
    final weight = entry['weight'];
    final targetReps = entry['target_reps'];
    final repsDone = entry['reps_done'];
    final rir = entry['rir'];
    if (movementId is! String ||
        weight is! num ||
        targetReps is! num ||
        repsDone is! num ||
        (rir != null && rir is! num)) {
      throw const FormatException(
        'The structured set-feedback payload is invalid.',
      );
    }
    // soreness, notes and all unknown fields are deliberately dropped here.
    return ref
        .read(offlineFeedbackOutboxProvider)
        .enqueue(
          ownerMemberId: ownerMemberId,
          programId: programId,
          movementId: movementId,
          weight: weight.toDouble(),
          targetReps: targetReps.toInt(),
          repsDone: repsDone.toInt(),
          rir: rir?.toDouble(),
        );
  };
});

final offlineFeedbackNetworkAvailableProvider =
    Provider<Future<bool> Function()>(
      (ref) => ref.read(offlineFeedbackStoreProvider).hasInternetNetwork,
    );

/// Rows are always read by the active member ID and the native query repeats
/// that owner predicate. Unsupported platforms intentionally expose no queue.
final offlineFeedbackQueueProvider =
    FutureProvider<List<OfflineFeedbackQueueItem>>((ref) async {
      final ownerMemberId = ref.watch(authProvider).memberId;
      final store = ref.watch(offlineFeedbackStoreProvider);
      if (ownerMemberId == null || !store.isSupported) return const [];
      return store.listForOwner(ownerMemberId, limit: 500);
    });

typedef SyncOfflineFeedbackQueue = Future<OfflineFeedbackSyncResult> Function();

final syncOfflineFeedbackQueueProvider = Provider<SyncOfflineFeedbackQueue>((
  ref,
) {
  return () async {
    final ownerMemberId = ref.read(authProvider).memberId;
    if (ownerMemberId == null)
      return const OfflineFeedbackSyncResult(authRequired: true);
    return ref
        .read(offlineFeedbackSyncServiceProvider)
        .syncOwner(
          currentMemberId: ownerMemberId,
          ownerMemberId: ownerMemberId,
          api: ref.read(apiClientProvider),
        );
  };
});
