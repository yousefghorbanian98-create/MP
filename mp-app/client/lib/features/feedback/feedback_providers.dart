/// بازخورد ست‌به‌ست (G1 — M39) — providers.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/session.dart';

/// ارسال بازخورد ست‌ها ← پیشنهاد جلسهٔ بعد (وزن/حجم + دلیل).
final submitSetFeedbackProvider =
    Provider<Future<Map<String, dynamic>?> Function(List<Map<String, dynamic>>)>((ref) {
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
