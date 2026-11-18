/// گفتگوی عضو با مربی — از API فعلی چت و نشست جاری استفاده می‌کند (M81).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../core/membership.dart';
import '../../core/session.dart';
import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';
import 'member_chat_data.dart';

class MemberChatPage extends ConsumerStatefulWidget {
  const MemberChatPage({super.key});

  @override
  ConsumerState<MemberChatPage> createState() => _MemberChatPageState();
}

class _MemberChatPageState extends ConsumerState<MemberChatPage> {
  final _messageController = TextEditingController();
  MemberChatConversation? _activeConversation;
  bool _sending = false;
  bool _markingRead = false;
  String? _actionError;
  String? _actionNotice;

  @override
  void dispose() {
    _messageController.dispose();
    super.dispose();
  }

  void _openConversation(MemberChatConversation conversation) {
    setState(() {
      _activeConversation = conversation;
      _actionError = null;
      _actionNotice = null;
    });
    ref.invalidate(memberChatThreadProvider(conversation.id));
  }

  void _showConversationList() {
    setState(() {
      _activeConversation = null;
      _actionError = null;
      _actionNotice = null;
      _messageController.clear();
    });
  }

  Future<void> _refreshConversations() async {
    try {
      await ref
          .refresh(memberChatConversationsProvider.future)
          .then<void>((_) {});
    } catch (_) {
      // خطا در AsyncValue نمایش داده می‌شود؛ refresh indicator نباید آن را
      // به empty یا خطای ثانویه تبدیل کند.
    }
  }

  Future<void> _sendMessage(MemberChatConversation conversation) async {
    final body = _messageController.text.trim();
    if (_sending || body.isEmpty || conversation.status == 'closed') return;
    if (body.length > 2000) {
      setState(() => _actionError = 'پیام نباید بیش از ۲۰۰۰ نویسه باشد');
      return;
    }

    setState(() {
      _sending = true;
      _actionError = null;
      _actionNotice = null;
    });
    try {
      final api = ref.read(apiClientProvider);
      final raw = await api.post(
        '/chat/conversations/${conversation.id}/messages',
        {'body': body},
      );
      if (raw is! Map) throw ApiException('پاسخ ارسال پیام معتبر نیست');
      final sent = parseMemberChatMessage(
        Map<String, dynamic>.from(raw),
        conversation.id,
      );
      if (sent.senderRole != 'member' || sent.body != body) {
        throw ApiException('تأیید ارسال پیام با نشست عضو هم‌خوان نیست');
      }
      if (!mounted) return;
      _messageController.clear();
      setState(() => _actionNotice = 'پیام ارسال شد');
      ref.invalidate(memberChatThreadProvider(conversation.id));
      ref.invalidate(memberChatConversationsProvider);
    } catch (error) {
      if (!mounted) return;
      // متن در کادر می‌ماند تا در خطای شبکه/سرور از دست نرود.
      setState(() => _actionError = 'ارسال پیام ناموفق بود: $error');
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  Future<void> _markRead(
    MemberChatConversation conversation,
    int unreadCount,
  ) async {
    if (_markingRead || unreadCount < 1) return;
    setState(() {
      _markingRead = true;
      _actionError = null;
      _actionNotice = null;
    });
    try {
      final api = ref.read(apiClientProvider);
      final raw = await api.post(
        '/chat/conversations/${conversation.id}/read',
        const <String, dynamic>{},
      );
      if (raw is! Map ||
          raw['marked_read'] is! int ||
          (raw['marked_read'] as int) < 0) {
        throw ApiException('پاسخ ثبت خوانده‌شدن معتبر نیست');
      }
      final count = raw['marked_read'] as int;
      if (!mounted) return;
      setState(
        () => _actionNotice = '${_persianDigits('$count')} پیام خوانده شد',
      );
      ref.invalidate(memberChatThreadProvider(conversation.id));
    } catch (error) {
      if (!mounted) return;
      setState(() => _actionError = 'ثبت خوانده‌شدن ناموفق بود: $error');
    } finally {
      if (mounted) setState(() => _markingRead = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final conversation = _activeConversation;
    return Scaffold(
      appBar: AppBar(
        automaticallyImplyLeading: conversation == null,
        leading: conversation == null
            ? null
            : IconButton(
                tooltip: 'بازگشت به گفتگوها',
                onPressed: _showConversationList,
                icon: const Icon(Icons.arrow_back),
              ),
        title: Text(conversation?.title ?? 'گفتگو با مربی'),
        backgroundColor: MpColors.background,
        surfaceTintColor: Colors.transparent,
        actions: [
          if (conversation == null)
            IconButton(
              tooltip: 'تازه‌سازی گفتگوها',
              onPressed: () => ref.invalidate(memberChatConversationsProvider),
              icon: const Icon(Icons.refresh),
            ),
        ],
      ),
      body: SafeArea(
        child:
            conversation == null ? _conversationList() : _thread(conversation),
      ),
    );
  }

  Widget _conversationList() {
    final conversations = ref.watch(memberChatConversationsProvider);
    return conversations.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (error, _) => Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, color: MpColors.danger, size: 38),
              const SizedBox(height: 8),
              Text(
                'دریافت گفتگوها ناموفق بود: $error',
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 10),
              OutlinedButton(
                onPressed: () =>
                    ref.invalidate(memberChatConversationsProvider),
                child: const Text('تلاش دوباره'),
              ),
            ],
          ),
        ),
      ),
      data: (rows) => RefreshIndicator(
        onRefresh: _refreshConversations,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          children: [
            const GlassCard(
              child: Row(
                children: [
                  Icon(
                    Icons.forum_outlined,
                    color: MpColors.primaryLight,
                    size: 26,
                  ),
                  SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'پیام‌ها و پاسخ‌های مربی در این بخش نگه‌داری می‌شوند.',
                      style: TextStyle(height: 1.5),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            if (rows.isEmpty)
              const GlassCard(
                child: Padding(
                  padding: EdgeInsets.symmetric(vertical: 18, horizontal: 8),
                  child: Column(
                    children: [
                      Icon(
                        Icons.chat_bubble_outline,
                        size: 38,
                        color: MpColors.textSecondary,
                      ),
                      SizedBox(height: 8),
                      Text(
                        'هنوز گفتگویی ندارید',
                        style: TextStyle(fontWeight: FontWeight.w700),
                      ),
                      SizedBox(height: 6),
                      Text(
                        'برای آغاز گفتگو، از مربی خود بخواهید در سامانهٔ مجموعه به شما پیام بدهد.',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: MpColors.textSecondary,
                          height: 1.5,
                        ),
                      ),
                    ],
                  ),
                ),
              )
            else
              for (final item in rows) ...[
                _ConversationTile(
                  conversation: item,
                  onTap: () => _openConversation(item),
                ),
                const SizedBox(height: 10),
              ],
          ],
        ),
      ),
    );
  }

  Widget _thread(MemberChatConversation conversation) {
    final thread = ref.watch(memberChatThreadProvider(conversation.id));
    return thread.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (error, _) => Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, color: MpColors.danger, size: 38),
              const SizedBox(height: 8),
              Text(
                'دریافت پیام‌ها ناموفق بود: $error',
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 10),
              OutlinedButton(
                onPressed: () =>
                    ref.invalidate(memberChatThreadProvider(conversation.id)),
                child: const Text('تلاش دوباره'),
              ),
            ],
          ),
        ),
      ),
      data: (payload) => Column(
        children: [
          _threadStatus(conversation),
          if (_actionError != null)
            _ActionMessage(message: _actionError!, isError: true),
          if (_actionNotice != null)
            _ActionMessage(message: _actionNotice!, isError: false),
          if (payload.unreadCount > 0)
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 4, 12, 8),
              child: OutlinedButton.icon(
                key: const ValueKey('member-chat-mark-read'),
                onPressed: _markingRead
                    ? null
                    : () => _markRead(conversation, payload.unreadCount),
                icon: _markingRead
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.mark_chat_read_outlined),
                label: Text(
                  _markingRead
                      ? 'در حال ثبت…'
                      : '${_persianDigits('${payload.unreadCount}')} پیام خوانده‌نشده · علامت‌گذاری',
                ),
              ),
            ),
          Expanded(child: _messageList(payload.messages)),
          if (conversation.status == 'closed')
            const Padding(
              padding: EdgeInsets.all(14),
              child: Text(
                'این گفتگو بسته شده است و پیام تازه نمی‌پذیرد.',
                textAlign: TextAlign.center,
                style: TextStyle(color: MpColors.textSecondary),
              ),
            )
          else
            _composer(conversation),
        ],
      ),
    );
  }

  Widget _threadStatus(MemberChatConversation conversation) => Padding(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
        child: Row(
          children: [
            const Icon(Icons.support_agent,
                color: MpColors.primaryLight, size: 22),
            const SizedBox(width: 8),
            const Expanded(
              child: Text(
                'گفتگو با مربی',
                style: TextStyle(fontWeight: FontWeight.w700),
              ),
            ),
            if (conversation.status == 'closed')
              const Chip(
                  label: Text('بسته'), visualDensity: VisualDensity.compact),
          ],
        ),
      );

  Widget _messageList(List<MemberChatMessage> messages) {
    if (messages.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Text(
            'هنوز پیامی در این گفتگو نیست. پیام خود را بنویسید.',
            textAlign: TextAlign.center,
            style: TextStyle(color: MpColors.textSecondary),
          ),
        ),
      );
    }
    return ListView.separated(
      key: const ValueKey('member-chat-message-list'),
      reverse: false,
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
      itemCount: messages.length,
      separatorBuilder: (_, __) => const SizedBox(height: 8),
      itemBuilder: (context, index) => _MessageBubble(message: messages[index]),
    );
  }

  Widget _composer(MemberChatConversation conversation) => SafeArea(
        top: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Expanded(
                child: TextField(
                  key: const ValueKey('member-chat-composer'),
                  controller: _messageController,
                  enabled: !_sending,
                  textDirection: TextDirection.rtl,
                  minLines: 1,
                  maxLines: 4,
                  maxLength: 2000,
                  decoration: const InputDecoration(
                    hintText: 'پیام خود را بنویسید…',
                    filled: true,
                    counterText: '',
                    border: OutlineInputBorder(),
                    contentPadding: EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 10,
                    ),
                  ),
                  onChanged: (_) => setState(() {
                    _actionError = null;
                  }),
                ),
              ),
              const SizedBox(width: 8),
              IconButton.filled(
                tooltip: 'ارسال پیام',
                onPressed: _sending || _messageController.text.trim().isEmpty
                    ? null
                    : () => _sendMessage(conversation),
                icon: _sending
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.send),
              ),
            ],
          ),
        ),
      );
}

class _ConversationTile extends StatelessWidget {
  const _ConversationTile({required this.conversation, required this.onTap});

  final MemberChatConversation conversation;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final date = _formatChatTime(conversation.lastMessageAt);
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: GlassCard(
          child: Row(
            children: [
              const CircleAvatar(
                backgroundColor: Color(0x2234D399),
                child: Icon(Icons.forum_outlined, color: MpColors.primaryLight),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      conversation.title,
                      style: const TextStyle(fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      conversation.status == 'closed'
                          ? 'گفتگو بسته شده'
                          : date == null
                              ? 'هنوز پیامی ندارد'
                              : 'آخرین پیام · $date',
                      style: const TextStyle(
                        fontSize: 12,
                        color: MpColors.textSecondary,
                      ),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_left, color: MpColors.textSecondary),
            ],
          ),
        ),
      ),
    );
  }
}

class _MessageBubble extends StatelessWidget {
  const _MessageBubble({required this.message});

  final MemberChatMessage message;

  @override
  Widget build(BuildContext context) {
    final isOwn = message.senderRole == 'member';
    final alignment = message.isSystem
        ? Alignment.center
        : isOwn
            ? AlignmentDirectional.centerEnd
            : AlignmentDirectional.centerStart;
    final color = message.isSystem
        ? MpColors.surface
        : isOwn
            ? MpColors.primary.withOpacity(0.22)
            : MpColors.surface.withOpacity(0.92);
    final sender = message.isSystem
        ? 'پیام سامانه'
        : isOwn
            ? 'شما'
            : 'مربی';
    final time = _formatChatTime(message.createdAt);

    return Align(
      alignment: alignment,
      child: ConstrainedBox(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.sizeOf(context).width * 0.82,
        ),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 10),
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: MpColors.primary.withOpacity(0.14)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(message.body, style: const TextStyle(height: 1.45)),
              const SizedBox(height: 5),
              Text(
                [
                  sender,
                  if (time != null) time,
                  if (message.readAt != null) 'خوانده‌شده',
                ].join(' · '),
                style: const TextStyle(
                  fontSize: 10,
                  color: MpColors.textSecondary,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ActionMessage extends StatelessWidget {
  const _ActionMessage({required this.message, required this.isError});

  final String message;
  final bool isError;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        child: Text(
          message,
          textAlign: TextAlign.center,
          style: TextStyle(
            color: isError ? MpColors.danger : MpColors.primaryLight,
          ),
        ),
      );
}

String? _formatChatTime(String? iso) {
  if (iso == null) return null;
  final parsed = DateTime.tryParse(iso);
  if (parsed == null) return null;
  final local = parsed.toLocal();
  final time =
      '${local.hour.toString().padLeft(2, '0')}:${local.minute.toString().padLeft(2, '0')}';
  return '${formatJalaliDate(local)} · ${_persianDigits(time)}';
}

String _persianDigits(String value) => value.replaceAllMapped(
      RegExp(r'\d'),
      (match) => '۰۱۲۳۴۵۶۷۸۹'[int.parse(match.group(0)!)],
    );
