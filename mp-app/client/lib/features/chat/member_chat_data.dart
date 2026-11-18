/// قرارداد دادهٔ چت عضو — فقط از گفتگوهای متعلق به نشست جاری (M81).
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../core/session.dart';

class MemberChatConversation {
  const MemberChatConversation({
    required this.id,
    required this.memberId,
    required this.coachId,
    required this.subject,
    required this.status,
    required this.lastMessageAt,
    required this.createdAt,
  });

  final int id;
  final int memberId;
  final int coachId;
  final String subject;
  final String status;
  final String? lastMessageAt;
  final String? createdAt;

  String get title => subject.trim().isEmpty ? 'گفتگو #$id' : subject.trim();
}

class MemberChatMessage {
  const MemberChatMessage({
    required this.id,
    required this.conversationId,
    required this.senderId,
    required this.senderRole,
    required this.body,
    required this.isSystem,
    required this.readAt,
    required this.createdAt,
  });

  final int id;
  final int conversationId;
  final int senderId;
  final String senderRole;
  final String body;
  final bool isSystem;
  final String? readAt;
  final String? createdAt;
}

class MemberChatThread {
  const MemberChatThread({
    required this.conversationId,
    required this.messages,
    required this.unreadCount,
  });

  final int conversationId;
  final List<MemberChatMessage> messages;
  final int unreadCount;
}

/// شناسهٔ عضو فقط برای اعتبارسنجی پاسخ استفاده می‌شود؛ هرگز در URL/body
/// فهرست یا پیام قرار نمی‌گیرد. API هویت را از نشست Bearer استخراج می‌کند.
final memberChatConversationsProvider =
    FutureProvider<List<MemberChatConversation>>((ref) async {
  final memberId = ref.watch(
    authProvider.select((state) => state.memberId),
  );
  if (memberId == null) {
    throw ApiException('شناسهٔ عضو در نشست موجود نیست');
  }

  final api = ref.watch(apiClientProvider);
  final raw = await api.get('/chat/conversations');
  if (raw is! List) throw ApiException('ساختار فهرست گفتگوها معتبر نیست');

  final conversations = <MemberChatConversation>[];
  for (final row in raw) {
    if (row is! Map) throw ApiException('رکورد گفتگو معتبر نیست');
    final conversation = _parseConversation(Map<String, dynamic>.from(row));
    if (conversation.memberId != memberId) {
      throw ApiException('گفتگوی دریافتی به عضو جاری تعلق ندارد');
    }
    conversations.add(conversation);
  }
  return conversations;
});

final memberChatThreadProvider = FutureProvider.family<MemberChatThread, int>((
  ref,
  conversationId,
) async {
  final memberId = ref.watch(authProvider.select((state) => state.memberId));
  if (memberId == null) throw ApiException('شناسهٔ عضو در نشست موجود نیست');
  if (conversationId < 1) throw ApiException('شناسهٔ گفتگو نامعتبر است');

  final api = ref.watch(apiClientProvider);
  final raw = await api.get('/chat/conversations/$conversationId/messages');
  if (raw is! Map) throw ApiException('ساختار پیام‌های گفتگو معتبر نیست');
  final payload = Map<String, dynamic>.from(raw);
  if (payload['conversation_id'] != conversationId ||
      payload['messages'] is! List ||
      payload['unread_count'] is! int ||
      (payload['unread_count'] as int) < 0) {
    throw ApiException('پاسخ پیام‌ها با گفتگوی درخواستی هم‌خوان نیست');
  }

  final messages = <MemberChatMessage>[];
  for (final row in payload['messages'] as List) {
    if (row is! Map) throw ApiException('رکورد پیام معتبر نیست');
    messages.add(
      parseMemberChatMessage(Map<String, dynamic>.from(row), conversationId),
    );
  }
  return MemberChatThread(
    conversationId: conversationId,
    messages: messages,
    unreadCount: payload['unread_count'] as int,
  );
});

MemberChatConversation _parseConversation(Map<String, dynamic> row) {
  final id = row['id'];
  final memberId = row['member_id'];
  final coachId = row['coach_id'];
  final subject = row['subject'];
  final status = row['status'];
  if (id is! int ||
      id < 1 ||
      memberId is! int ||
      memberId < 1 ||
      coachId is! int ||
      coachId < 1 ||
      subject is! String ||
      status is! String ||
      !const {'open', 'closed'}.contains(status)) {
    throw ApiException('اطلاعات دریافتی گفتگو ناقص یا نامعتبر است');
  }
  return MemberChatConversation(
    id: id,
    memberId: memberId,
    coachId: coachId,
    subject: subject,
    status: status,
    lastMessageAt: _nullableTimestamp(
      row['last_message_at'],
      'زمان آخرین پیام',
    ),
    createdAt: _nullableTimestamp(row['created_at'], 'زمان ساخت گفتگو'),
  );
}

MemberChatMessage parseMemberChatMessage(
  Map<String, dynamic> row,
  int conversationId,
) {
  final id = row['id'];
  final responseConversationId = row['conversation_id'];
  final senderId = row['sender_id'];
  final senderRole = row['sender_role'];
  final body = row['body'];
  final isSystem = row['is_system'];
  if (id is! int ||
      id < 1 ||
      responseConversationId != conversationId ||
      senderId is! int ||
      senderId < 1 ||
      senderRole is! String ||
      !const {'member', 'coach'}.contains(senderRole) ||
      body is! String ||
      isSystem is! bool) {
    throw ApiException('اطلاعات دریافتی پیام ناقص یا نامعتبر است');
  }
  return MemberChatMessage(
    id: id,
    conversationId: conversationId,
    senderId: senderId,
    senderRole: senderRole,
    body: body,
    isSystem: isSystem,
    readAt: _nullableTimestamp(row['read_at'], 'وضعیت خواندن پیام'),
    createdAt: _nullableTimestamp(row['created_at'], 'زمان ارسال پیام'),
  );
}

String? _nullableTimestamp(Object? value, String label) {
  if (value == null) return null;
  if (value is! String || DateTime.tryParse(value) == null) {
    throw ApiException('$label معتبر نیست');
  }
  return value;
}
